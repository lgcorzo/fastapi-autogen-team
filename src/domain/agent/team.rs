use crate::application::dtos::Input;
use crate::infrastructure::tools::confluence::ConfluenceTool;
use crate::infrastructure::tools::jira::JiraTool;
use crate::infrastructure::tools::r2r::R2RTool;
use async_stream::stream;
use futures::{future::join_all, Stream, StreamExt};
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
    if l.starts_with('{') || l.starts_with('}') {
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

        let last_message = input
            .messages
            .last()
            .and_then(|m| match &m.content {
                crate::application::dtos::ContentType::String(s) => Some(s.clone()),
                _ => None,
            })
            .unwrap_or_default();

        // 0. Language Detection & Translation (Parallel)
        let language_detector = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are an expert linguist. Identify the language of the following text. \
                 Reply ONLY with the name of the language (e.g., Spanish, French, English) \
                 and absolutely nothing else.",
            )
            .build();

        let translator = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are an expert translator. Translate the following user input into clear, \
                 concise English. If it is already in English, return it exactly as is. \
                 Output ONLY the English text without any additional commentary.",
            )
            .build();

        let (detected_language_res, english_message_res) = futures::join!(
            async { language_detector.prompt(&last_message).await },
            async { translator.prompt(&last_message).await }
        );

        let detected_language = detected_language_res.unwrap_or_else(|_| "English".to_string());
        let detected_language = detected_language.trim().to_string();
        let english_message = english_message_res.unwrap_or_else(|_| last_message.clone());

        tracing::info!("Detected input language: {}", detected_language);
        tracing::info!("Translated input: {}", english_message);

        // 1. Planner Agent
        let planner = client
            .agent("ollama/qwen2.5:7b")
            .preamble(
                "You are the Planner. Analyze the user message and break it down into AT MOST 5 \
                 focused search queries in English. \
                 For each query, decide which tool is best: \
                 - Use [JIRA] for tasks, issues, or project management related queries. \
                 - Use [CONFLUENCE] for documentation, wiki pages, or general project info. \
                 - Use [R2R] for general knowledge or internal document search. \
                 CRITICAL: Return ONLY the search queries prefixed with the tool name, one per line. \
                 Example output: \
                 [JIRA] status of task PROJ-123 \
                 [CONFLUENCE] how to set up the dev environment \
                 [R2R] latest advances in AI",
            )
            .default_max_turns(5)
            .build();

        let queries = planner.prompt(&english_message).await?;
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

        // 2. Specialized RAG Searchers
        let jira_searcher = client.agent("ollama/qwen2.5:7b")
            .preamble("You are the Jira searcher. Use the 'jira_search' tool to find tasks or issues. Summarize the findings and stop.")
            .tool(JiraTool).build();
        let confluence_searcher = client.agent("ollama/qwen2.5:7b")
            .preamble("You are the Confluence searcher. Use the 'confluence_search' tool to find documentation. Summarize the findings and stop.")
            .tool(ConfluenceTool).build();
        let r2r_searcher = client.agent("ollama/qwen2.5:7b")
            .preamble("You are the R2R searcher. Use the 'r2r_search' tool to find internal information. Summarize the findings and stop.")
            .tool(R2RTool).build();

        let mut search_tasks = Vec::new();
        for query_line in raw_lines.into_iter().take(5) {
            let trimmed = query_line.trim().to_string();
            if !is_valid_query_line(&trimmed) {
                continue;
            }

            let (tool_tag, actual_query) = if trimmed.starts_with("[JIRA]") {
                ("JIRA", trimmed.trim_start_matches("[JIRA]").trim())
            } else if trimmed.starts_with("[CONFLUENCE]") {
                (
                    "CONFLUENCE",
                    trimmed.trim_start_matches("[CONFLUENCE]").trim(),
                )
            } else if trimmed.starts_with("[R2R]") {
                ("R2R", trimmed.trim_start_matches("[R2R]").trim())
            } else {
                ("R2R", trimmed.as_str()) // Default to R2R if no tag
            };

            let searcher = match tool_tag {
                "JIRA" => jira_searcher.clone(),
                "CONFLUENCE" => confluence_searcher.clone(),
                _ => r2r_searcher.clone(),
            };

            let q = actual_query.to_string();
            search_tasks.push(async move {
                tracing::info!("Executing {} search for: {}", tool_tag, q);
                match searcher.prompt(q).await {
                    Ok(res) => res,
                    Err(e) => format!("{} search error: {}", tool_tag, e),
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
        let qa_preamble = format!(
            "You are the Quality Assurance agent. Synthesize the search results into a helpful final \
             response. You MUST reply in the language identified as: {}. \
             Even if the search results are in English, your final response MUST be translated to {}. \
             Always provide a helpful answer based on the search results provided. \
             If no relevant information was found, state it clearly. \
             IMPORTANT: End your response with the word: TERMINATE",
            detected_language, detected_language
        );

        let qa = client
            .agent("ollama/qwen2.5:7b")
            .preamble(&qa_preamble)
            .default_max_turns(5)
            .build();

        let final_response = qa
            .prompt(format!(
                "Original User Query: {}\n\nSearch Results (in English):\n{}",
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
        let team_client = self.client.clone();
        let client = team_client.completions_api();

        let s = stream! {
            let last_message = input
                .messages
                .last()
                .and_then(|m| match &m.content {
                    crate::application::dtos::ContentType::String(s) => Some(s.clone()),
                    _ => None,
                })
                .unwrap_or_default();

            // 0. Language Detection & Translation (Parallel)
            let language_detector = client
                .agent("ollama/qwen2.5:7b")
                .preamble(
                    "You are an expert linguist. Identify the language of the following text. \
                     Reply ONLY with the name of the language (e.g., Spanish, French, English) \
                     and absolutely nothing else.",
                )
                .build();

            let translator = client
                .agent("ollama/qwen2.5:7b")
                .preamble(
                    "You are an expert translator. Translate the following user input into clear, \
                     concise English. If it is already in English, return it exactly as is. \
                     Output ONLY the English text without any additional commentary."
                )
                .build();

            let (detected_language_res, english_message_res) = futures::join!(
                async { language_detector.prompt(&last_message).await },
                async { translator.prompt(&last_message).await }
            );

            let detected_language = detected_language_res.unwrap_or_else(|_| "English".to_string());
            let detected_language = detected_language.trim().to_string();
            let english_message = english_message_res.unwrap_or_else(|_| last_message.clone());

            tracing::info!("Detected input language: {}", detected_language);
            tracing::info!("Translated input: {}", english_message);

            yield Ok::<AgentEvent, anyhow::Error>(AgentEvent::Progress {
                stage: "preprocessing".to_string(),
                message: format!("Detected language: {}. Translated input to English.", detected_language),
            });

            // 1. Planner Agent
            let planner = client
                .agent("ollama/qwen2.5:7b")
                .preamble(
                    "You are the Planner. Analyze the user message and break it down into AT MOST 5 \
                     focused search queries in English. \
                     For each query, decide which tool is best: \
                     - Use [JIRA] for tasks, issues, or project management related queries. \
                     - Use [CONFLUENCE] for documentation, wiki pages, or general project info. \
                     - Use [R2R] for general knowledge or internal document search. \
                     CRITICAL: Return ONLY the search queries prefixed with the tool name, one per line. \
                     Example output: \
                     [JIRA] status of task PROJ-123 \
                     [CONFLUENCE] how to set up the dev environment \
                     [R2R] latest advances in AI",
                )
                .default_max_turns(5)
                .build();

            // Run planner
            let planner_res = planner.prompt(&english_message).await;
            if let Err(e) = planner_res {
                yield Err::<AgentEvent, anyhow::Error>(anyhow::anyhow!("Planner error: {}", e));
                return;
            }
            let queries = planner_res.unwrap();
            tracing::info!("Planner queries: {}", queries);

            // Parsing logic (same as run)
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

            let query_lines: Vec<String> = raw_lines
                .into_iter()
                .filter(|l| is_valid_query_line(l))
                .take(5)
                .collect();

            let query_count = query_lines.len();

            // Yield planner progress immediately after planning
            yield Ok::<AgentEvent, anyhow::Error>(AgentEvent::Progress {
                stage: "planner".to_string(),
                message: format!(
                    "Planner generated {} search quer{}",
                    query_count,
                    if query_count == 1 { "y" } else { "ies" }
                ),
            });

            // 2. Specialized RAG Searchers
            let jira_searcher = client.agent("ollama/qwen2.5:7b")
                .preamble("You are the Jira searcher. Use the 'jira_search' tool to find tasks or issues. Summarize the findings and stop.")
                .tool(JiraTool).build();
            let confluence_searcher = client.agent("ollama/qwen2.5:7b")
                .preamble("You are the Confluence searcher. Use the 'confluence_search' tool to find documentation. Summarize the findings and stop.")
                .tool(ConfluenceTool).build();
            let r2r_searcher = client.agent("ollama/qwen2.5:7b")
                .preamble("You are the R2R searcher. Use the 'r2r_search' tool to find internal information. Summarize the findings and stop.")
                .tool(R2RTool).build();

            let mut all_results = String::new();
            for (i, query_line) in query_lines.iter().enumerate() {
                let trimmed = query_line.trim().to_string();

                let (tool_tag, actual_query) = if trimmed.starts_with("[JIRA]") {
                    ("JIRA", trimmed.trim_start_matches("[JIRA]").trim())
                } else if trimmed.starts_with("[CONFLUENCE]") {
                    ("CONFLUENCE", trimmed.trim_start_matches("[CONFLUENCE]").trim())
                } else if trimmed.starts_with("[R2R]") {
                    ("R2R", trimmed.trim_start_matches("[R2R]").trim())
                } else {
                    ("R2R", trimmed.as_str()) // Default to R2R if no tag
                };

                let searcher = match tool_tag {
                    "JIRA" => jira_searcher.clone(),
                    "CONFLUENCE" => confluence_searcher.clone(),
                    _ => r2r_searcher.clone(),
                };

                tracing::info!("Executing {} search for: {}", tool_tag, actual_query);
                let res = match searcher.prompt(actual_query.to_string()).await {
                    Ok(r) => r,
                    Err(e) => format!("{} search error: {}", tool_tag, e),
                };

                all_results.push_str(&res);
                all_results.push_str("\n---\n");

                // Yield progress for each completed search
                yield Ok::<AgentEvent, anyhow::Error>(AgentEvent::Progress {
                    stage: "searcher".to_string(),
                    message: format!("{} search {}/{} completed", tool_tag, i + 1, query_count),
                });
            }

            // 3. QA Agent: Final Synthesis (Streaming)
            let qa_preamble = format!(
                "You are the Quality Assurance agent. Synthesize the search results into a helpful final \
                 response. You MUST reply in the language identified as: {}. \
                 Even if the search results are in English, your final response MUST be translated to {}. \
                 Always provide a helpful answer based on the search results provided. \
                 If no relevant information was found, state it clearly. \
                 IMPORTANT: End your response with the word: TERMINATE",
                detected_language, detected_language
            );

            let qa = client
                .agent("ollama/qwen2.5:7b")
                .preamble(&qa_preamble)
                .default_max_turns(5)
                .build();

            let mut qa_raw_stream = qa.stream_prompt(format!(
                "Original User Query: {}\n\nSearch Results (in English):\n{}",
                last_message, all_results
            )).await;

            while let Some(res) = qa_raw_stream.next().await {
                match res {
                    Ok(MultiTurnStreamItem::StreamAssistantItem(StreamedAssistantContent::Text(text))) => {
                        yield Ok::<AgentEvent, anyhow::Error>(AgentEvent::Delta(text.text));
                    }
                    Ok(_) => {
                        yield Ok::<AgentEvent, anyhow::Error>(AgentEvent::Delta(String::new()));
                    }
                    Err(e) => {
                        yield Err(anyhow::anyhow!("QA stream error: {}", e));
                    }
                }
            }

            yield Ok(AgentEvent::Done);
        };

        let pinned_stream: Pin<Box<dyn Stream<Item = anyhow::Result<AgentEvent>> + Send>> =
            Box::pin(s);
        Ok(pinned_stream)
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
