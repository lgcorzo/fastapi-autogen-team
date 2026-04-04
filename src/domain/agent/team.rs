use crate::application::dtos::Input;
use crate::infrastructure::tools::search::SearchTool;
use futures::{future::join_all, StreamExt};
use rig::agent::MultiTurnStreamItem;
use rig::client::CompletionClient;
use rig::completion::Prompt;
use rig::providers::openai;
use rig::streaming::{StreamedAssistantContent, StreamingPrompt};
use std::env;

pub struct AgentTeam {
    client: openai::Client,
}

impl AgentTeam {
    pub async fn new() -> anyhow::Result<Self> {
        let api_key = env::var("LITELLM_API_KEY").expect("LITELLM_API_KEY must be set");
        let base_url =
            env::var("LITELLM_BASE_URL").unwrap_or_else(|_| "http://litellm:4000/v1".to_string());

        // Rig 0.34.0 OpenAI client builder
        let client = openai::Client::builder()
            .api_key(&api_key)
            .base_url(&base_url)
            .build()?;

        Ok(Self { client })
    }

    pub async fn run(&self, input: Input) -> anyhow::Result<String> {
        let client = self.client.clone().completions_api();

        // 1. Planner Agent: Decomposed query (Strictly one-per-line)
        let planner = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Planner. Analyze the user message and break it down into AT MOST 5 focused search queries in English. \
                      Return ONLY the search queries, one per line. \
                      DO NOT return JSON. DO NOT return follow-up questions. DO NOT use markdown formatting. \
                      If you are done, simply return the queries. \
                      Example output:\nWhat is the weather in Tokyo?\nHow to make sushi?")
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

        // 2. RAG Searcher: Execute tools
        let rag_searcher = client
            .agent("minimax-m2.7:cloud")
            .preamble("You are the RAG_searcher. Use the search tool to find information. Once you have the results, summarize them and stop.")
            .tool(SearchTool)
            .default_max_turns(5)
            .build();

        let mut search_tasks = Vec::new();
        for query in queries.lines().take(5) {
            let trimmed = query.trim().to_string();
            if trimmed.is_empty()
                || trimmed.starts_with('{')
                || trimmed.starts_with('}')
                || trimmed.starts_with('[')
            {
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
        let qa = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Quality Assurance agent. Synthesize the results into a final response in the user's original language. \
                      Always provide a helpful answer based on the search results provided. \
                      If no relevant information was found, state it clearly. \
                      IMPORTANT: End your response with the word: TERMINATE")
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

    pub async fn run_stream(
        &self,
        input: Input,
    ) -> anyhow::Result<impl futures::Stream<Item = anyhow::Result<String>>> {
        let client = self.client.clone().completions_api();

        // 1. Planner Agent: Decomposed query (Strictly one-per-line)
        let planner = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Planner. Analyze the user message and break it down into AT MOST 5 focused search queries in English. \
                      Return ONLY the search queries, one per line. \
                      DO NOT return JSON. DO NOT return follow-up questions. DO NOT use markdown formatting. \
                      If you are done, simply return the queries. \
                      Example output:\nWhat is the weather in Tokyo?\nHow to make sushi?")
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

        // 2. RAG Searcher: Execute tools
        let rag_searcher = client
            .agent("minimax-m2.7:cloud")
            .preamble("You are the RAG_searcher. Use the search tool to find information. Once you have the results, summarize them and stop.")
            .tool(SearchTool)
            .default_max_turns(5)
            .build();

        let mut search_tasks = Vec::new();
        for query in queries.lines().take(5) {
            let trimmed = query.trim().to_string();
            if trimmed.is_empty()
                || trimmed.starts_with('{')
                || trimmed.starts_with('}')
                || trimmed.starts_with('[')
            {
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

        // 3. QA Agent: Final Synthesis (Streaming)
        let qa = client.agent("minimax-m2.7:cloud")
            .preamble("You are the Quality Assurance agent. Synthesize the results into a final response in the user's original language. \
                      Always provide a helpful answer based on the search results provided. \
                      If no relevant information was found, state it clearly. \
                      IMPORTANT: End your response with the word: TERMINATE")
            .default_max_turns(5)
            .build();

        let stream = qa
            .stream_prompt(format!(
                "User query: {}\n\nResults found:\n{}",
                last_message, all_results
            ))
            .await;

        Ok(stream.map(|res| match res {
            Ok(MultiTurnStreamItem::StreamAssistantItem(StreamedAssistantContent::Text(text))) => {
                Ok(text.text)
            }
            Ok(_) => Ok("".to_string()),
            Err(e) => Err(anyhow::anyhow!(e)),
        }))
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
