use crate::application::dtos::Input;
use crate::infrastructure::tools::search::SearchTool;
use futures::{future::join_all, stream, Stream, StreamExt};
use rig::agent::MultiTurnStreamItem;
use rig::client::CompletionClient;
use rig::completion::Prompt;
use rig::providers::openai;
use rig::streaming::{StreamedAssistantContent, StreamingPrompt};
use serde_json;
use std::env;
use std::pin::Pin;

/// Events emitted by the agent pipeline during SSE streaming.
///
/// `Progress` events are emitted after the planner and each RAG search.
/// `Delta` events carry individual QA token chunks.
/// `Done` signals end-of-stream.
/// Progress events are **only** produced on the streaming path (`run_stream`).
#[derive(Debug)]
pub enum AgentEvent {
    Progress { stage: String, message: String },
    Delta(String),
    Done,
}

/// Returns `true` when a planner output line is a valid standalone search query.
/// Rejects: empty lines, JSON structural tokens, quoted strings, the literal
/// TERMINATE keyword, and lines that are too short to be meaningful queries.
fn is_valid_query_line(line: &str) -> bool {
    let l = line.trim();
    if l.len() < 5 {
        return false;
    }
    if l.starts_with('{') || l.starts_with('}') || l.starts_with('[') || l.starts_with(']') {
        return false;
    }
    // Reject JSON key/value fragments (e.g. `"title": "..."`, `"follow_ups":` etc.)
    if l.starts_with('"') {
        return false;
    }
    // Reject lines that are solely the TERMINATE stop-word
    if l.eq_ignore_ascii_case("terminate") || l.ends_with("TERMINATE") {
        return false;
    }
    true
}

pub struct AgentTeam {
    client: openai::Client,
}

impl AgentTeam {
    pub async fn new() -> anyhow::Result<Self> {
        let api_key = env::var("LITELLM_API_KEY").expect("LITELLM_API_KEY must be set");
        let base_url =
            env::var("LITELLM_BASE_URL").unwrap_or_else(|_| "http://litellm:4000/v1".to_string());

        let client = openai::Client::builder()
            .api_key(&api_key)
            .base_url(&base_url)
            .build()?;

        Ok(Self { client })
    }

    pub async fn run(&self, input: Input) -> anyhow::Result<String> {
        let client = self.client.clone().completions_api();

        // 1. Planner Agent
        let planner = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are the Planner. Analyze the user message and break it down into AT MOST 5 \
                 focused search queries in English. \
                 CRITICAL: Return ONLY the search queries, one per line. \
                 DO NOT return JSON. DO NOT return follow-up questions. \
                 DO NOT use markdown formatting. If you are done, simply return the queries. \
                 Example output:\nWhat is the weather in Tokyo?\nHow to make sushi?",
            )
            .default_max_turns(5)
            .build();

        let last_message = input
            .messages
            .last()
            .and_then(|m| match &m.content {
                crate::application::dtos::ContentType::String(s) => Some(s.clone()),
                _ => None,
            })
            .unwrap_or_default();

        let queries = planner.prompt(&last_message).await?;
        tracing::info!("Planner queries: {}", queries);

        // Robust parsing: Handle accidental JSON structure from model
        let raw_lines: Vec<String> = if queries.trim().starts_with('{') {
            match serde_json::from_str::<serde_json::Value>(&queries) {
                Ok(v) => {
                    if let Some(arr) = v.get("follow_ups").and_then(|f| f.as_array()) {
                        arr.iter()
                            .filter_map(|v| v.as_str().map(|s| s.to_string()))
                            .collect()
                    } else if let Some(arr) = v.get("queries").and_then(|f| f.as_array()) {
                        arr.iter()
                            .filter_map(|v| v.as_str().map(|s| s.to_string()))
                            .collect()
                    } else {
                        queries.lines().map(|l| l.trim().to_string()).collect()
                    }
                }
                Err(_) => queries.lines().map(|l| l.trim().to_string()).collect(),
            }
        } else {
            queries.lines().map(|l| l.trim().to_string()).collect()
        };

        // 2. RAG Searcher
        let rag_searcher = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are the RAG_searcher. Use the search tool to find information. \
                 Once you have the results, summarize them and stop.",
            )
            .tool(SearchTool)
            .default_max_turns(5)
            .build();

        let mut search_tasks = Vec::new();
        for query in raw_lines.into_iter().take(5) {
            let trimmed = query.trim().to_string();
            if !is_valid_query_line(&trimmed) {
                continue;
            }
            let searcher = rag_searcher.clone();
            search_tasks.push(async move {
                tracing::info!("Executing RAG search for: {}", trimmed);
                match searcher.prompt(trimmed).await {
                    Ok(res) => res,
                    Err(e) => format!("Search error: {}", e),
                }
            });
        }

        let results = join_all(search_tasks).await;
        let mut all_results = String::new();
        for res in results {
            all_results.push_str(&res);
            all_results.push_str("\n---\n");
        }

        // 3. QA Agent: Final Synthesis
        let qa = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are the Quality Assurance agent. Synthesize the results into a final \
                 response in the user's original language. Always provide a helpful answer \
                 based on the search results provided. If no relevant information was found, \
                 state it clearly. IMPORTANT: End your response with the word: TERMINATE",
            )
            .default_max_turns(5)
            .build();

        let final_response = qa
            .prompt(format!(
                "User query: {}\n\nResults found:\n{}",
                last_message, all_results
            ))
            .await?;

        Ok(final_response)
    }

    /// Run the agent pipeline with full SSE progress streaming.
    ///
    /// Emits:
    /// - `AgentEvent::Progress` after the planner stage and after each RAG search.
    /// - `AgentEvent::Delta` for each streaming token from the QA agent.
    /// - `AgentEvent::Done` once all tokens have been emitted.
    ///
    /// Progress events are **not** produced by the non-streaming `run()` method.
    pub async fn run_stream(
        &self,
        input: Input,
    ) -> anyhow::Result<Pin<Box<dyn Stream<Item = anyhow::Result<AgentEvent>> + Send>>> {
        let client = self.client.clone().completions_api();

        // 1. Planner Agent
        let planner = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are the Planner. Analyze the user message and break it down into AT MOST 5 \
                 focused search queries in English. \
                 CRITICAL: Return ONLY the search queries, one per line. \
                 DO NOT return JSON. DO NOT return follow-up questions. \
                 DO NOT use markdown formatting. If you are done, simply return the queries. \
                 Example output:\nWhat is the weather in Tokyo?\nHow to make sushi?",
            )
            .default_max_turns(5)
            .build();

        let last_message = input
            .messages
            .last()
            .and_then(|m| match &m.content {
                crate::application::dtos::ContentType::String(s) => Some(s.clone()),
                _ => None,
            })
            .unwrap_or_default();

        let queries = planner.prompt(&last_message).await?;
        tracing::info!("Planner queries: {}", queries);

        // Robust parsing: Handle accidental JSON structure from model
        let raw_lines: Vec<String> = if queries.trim().starts_with('{') {
            match serde_json::from_str::<serde_json::Value>(&queries) {
                Ok(v) => {
                    if let Some(arr) = v.get("follow_ups").and_then(|f| f.as_array()) {
                        arr.iter()
                            .filter_map(|v| v.as_str().map(|s| s.to_string()))
                            .collect()
                    } else if let Some(arr) = v.get("queries").and_then(|f| f.as_array()) {
                        arr.iter()
                            .filter_map(|v| v.as_str().map(|s| s.to_string()))
                            .collect()
                    } else {
                        queries.lines().map(|l| l.trim().to_string()).collect()
                    }
                }
                Err(_) => queries.lines().map(|l| l.trim().to_string()).collect(),
            }
        } else {
            queries.lines().map(|l| l.trim().to_string()).collect()
        };

        // Collect valid query lines — uses the shared validator to reject JSON
        // fragments, TERMINATE, and other planner noise.
        let query_lines: Vec<String> = raw_lines
            .into_iter()
            .filter(|l| is_valid_query_line(l))
            .take(5)
            .collect();

        let query_count = query_lines.len();

        // Planner progress event
        let mut progress_events: Vec<anyhow::Result<AgentEvent>> = vec![Ok(AgentEvent::Progress {
            stage: "planner".to_string(),
            message: format!(
                "Planner generated {} search quer{}",
                query_count,
                if query_count == 1 { "y" } else { "ies" }
            ),
        })];

        // 2. RAG Searcher
        let rag_searcher = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are the RAG_searcher. Use the search tool to find information. \
                 Once you have the results, summarize them and stop.",
            )
            .tool(SearchTool)
            .default_max_turns(5)
            .build();

        let mut search_tasks = Vec::new();
        for query in &query_lines {
            let trimmed = query.clone();
            let searcher = rag_searcher.clone();
            search_tasks.push(async move {
                tracing::info!("Executing RAG search for: {}", trimmed);
                match searcher.prompt(trimmed).await {
                    Ok(res) => res,
                    Err(e) => format!("Search error: {}", e),
                }
            });
        }

        let results = join_all(search_tasks).await;
        let mut all_results = String::new();
        for (i, res) in results.iter().enumerate() {
            all_results.push_str(res);
            all_results.push_str("\n---\n");
            progress_events.push(Ok(AgentEvent::Progress {
                stage: "searcher".to_string(),
                message: format!("Search {}/{} completed", i + 1, query_count),
            }));
        }

        // 3. QA Agent: Final Synthesis (Streaming)
        let qa = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are the Quality Assurance agent. Synthesize the results into a final \
                 response in the user's original language. Always provide a helpful answer \
                 based on the search results provided. If no relevant information was found, \
                 state it clearly. IMPORTANT: End your response with the word: TERMINATE",
            )
            .default_max_turns(5)
            .build();

        let qa_raw_stream = qa
            .stream_prompt(format!(
                "User query: {}\n\nResults found:\n{}",
                last_message, all_results
            ))
            .await;

        let delta_stream = qa_raw_stream.map(|res| match res {
            Ok(MultiTurnStreamItem::StreamAssistantItem(StreamedAssistantContent::Text(text))) => {
                Ok(AgentEvent::Delta(text.text))
            }
            Ok(_) => Ok(AgentEvent::Delta(String::new())),
            Err(e) => Err(anyhow::anyhow!(e)),
        });

        let done_stream = stream::once(async { Ok::<AgentEvent, anyhow::Error>(AgentEvent::Done) });

        let combined = stream::iter(progress_events)
            .chain(delta_stream)
            .chain(done_stream);

        Ok(Box::pin(combined))
    }

    pub fn new_mock() -> Self {
        let client = openai::Client::builder()
            .api_key("none")
            .base_url("http://localhost:0/v1")
            .build()
            .unwrap();
        Self { client }
    }

    pub fn new_test(base_url: &str) -> Self {
        let client = openai::Client::builder()
            .api_key("none")
            .base_url(base_url)
            .build()
            .unwrap();
        Self { client }
    }
}
