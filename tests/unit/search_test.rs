use fastapi_autogen_team::infrastructure::tools::search::{SearchTool};
use rig::tool::Tool;

#[tokio::test]
async fn test_search_tool_definition() {
    let tool = SearchTool;
    let def = tool.definition("test".to_string()).await;
    assert_eq!(def.name, "search");
    assert!(def.description.contains("R2R"));
}
