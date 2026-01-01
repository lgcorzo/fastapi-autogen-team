# Backlog for Class Diagram Implementation

- [Backlog for Class Diagram Implementation](#backlog-for-class-diagram-implementation)
  - [**Features/packages**](#featurespackages)
    - [**FE: main**](#fe-main)
    - [**FE: Tasks for CI/CD**](#fe-tasks-for-cicd)
  - [UML packages relations](#uml-packages-relations)
- [📘 RAG with Confluence (AutoGen v2)](#-rag-with-confluence-autogen-v2)
  - [🎯 Objective](#-objective)
  - [🔐 Prerequisites](#-prerequisites)
  - [🧱 `confluence_search_tool.py`: AutoGen Tool Example](#-confluence_search_toolpy-autogen-tool-example)
  - [🤖 Integrating with an AutoGen Agent](#-integrating-with-an-autogen-agent)
  - [🧪 Example Usage](#-example-usage)
  - [🧠 CQL Translator Prompt Template (Agent)](#-cql-translator-prompt-template-agent)
    - [Usage Example](#usage-example)
  - [✅ Next Steps](#-next-steps)

---

## **Features/packages**

### **FE: main**

The foundational components of the system that ensure efficient functionality across various modules:

- **[US: Schemas](Schemas_stories.md)**: Define structured data formats for input, output, and intermediate processes, ensuring consistency and validation throughout the pipeline.

### **FE: Tasks for CI/CD**

Break down operational processes into manageable, modular tasks

- **US: Checks**: Validate system and code integrity with automated checks for errors, standards, and best practices.
- **US: Cleans**: Perform data cleaning and preprocessing to ensure data quality and consistency.
- **US: Commits**: Automate code versioning and commit standards for collaborative development.
- **US: Containers**: Build and manage containerized environments for consistent deployments across platforms.
- **US: Docs**: Generate and maintain documentation for all modules, ensuring clear usage and collaboration.
- **US: Formats**: Enforce code formatting standards for readability and maintainability.
- **US: Installs**: Manage dependency installation for smooth setup across different environments.
- **US: MLFlow**: Integrate with MLFlow for experiment tracking, model registry, and deployment workflows.
- **US: Packages**: Organize and manage Python or other language packages for modularized codebases.
- **US: Projects**: Create and maintain projects, ensuring that each has the structure, configuration, and tools needed for success.
- **[GitOps Deployment](gitops_deployment.md)**: Detailed guide on how to deploy this project using FluxCD and how to manage the `GITOPS_TOKEN`.

## UML packages relations

---

## 📘 RAG with Confluence (AutoGen v2)

The goal is to retrieve relevant content from **Confluence Cloud** using its REST API and **CQL (Confluence Query Language)**. This enables real-time information access for RAG (Retrieval-Augmented Generation) applications.

We will implement an **AutoGen v2 (ag2) tool** that queries Confluence using CQL and returns clean page content to be used by a conversational agent.

---

## 🎯 Objective

Build a tool named `confluence_search_tool` that:

1. Queries the **Confluence Cloud REST API** using CQL.
2. Returns relevant content from pages, cleaned of HTML.
3. Can be called by an AutoGen agent in a RAG system as an external knowledge source.

---

## 🔐 Prerequisites

To connect to Confluence, you'll need:

- ✅ A **Confluence Cloud** account.
- ✅ An **API token** from your Atlassian account:
  [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
- ✅ Your **Atlassian email address**.
- ✅ The base domain of your Confluence instance (e.g. `https://yourcompany.atlassian.net/wiki`).

---

## 🧱 `confluence_search_tool.py`: AutoGen Tool Example

```python
import requests
from autogen import Tool
import base64
from bs4 import BeautifulSoup

class ConfluenceSearchTool(Tool):
    def __init__(self, confluence_base_url, email, api_token, space_key=None):
        super().__init__(name="confluence_search_tool", description="Searches Confluence pages using CQL")
        self.base_url = confluence_base_url
        self.email = email
        self.api_token = api_token
        self.space_key = space_key

        token_bytes = f"{email}:{api_token}".encode("utf-8")
        self.auth_header = {
            "Authorization": f"Basic {base64.b64encode(token_bytes).decode('utf-8')}",
            "Accept": "application/json"
        }

    def cql_search(self, query):
        url = f"{self.base_url}/rest/api/content/search"
        params = {
            "cql": query,
            "expand": "body.storage,version"
        }
        response = requests.get(url, headers=self.auth_header, params=params)
        response.raise_for_status()
        return response.json()

    def parse_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n")

    def run(self, query: str) -> str:
        cql = f'type="page" AND text~"{query}"'
        if self.space_key:
            cql += f' AND space="{self.space_key}"'

        try:
            results = self.cql_search(cql)
            pages = results.get("results", [])
            if not pages:
                return "No relevant results found in Confluence."

            output = []
            for page in pages[:3]:
                title = page["title"]
                content_html = page["body"]["storage"]["value"]
                content_text = self.parse_html(content_html)
                snippet = content_text[:1000] + ("..." if len(content_text) > 1000 else "")
                url = f"{self.base_url}/spaces/{page['space']['key']}/pages/{page['id']}"
                output.append(f"📄 **{title}**\n{snippet}\n🔗 {url}")

            return "\n\n".join(output)

        except Exception as e:
            return f"Error querying Confluence: {str(e)}"
```

---

## 🤖 Integrating with an AutoGen Agent

```python
from autogen import ConversableAgent
from confluence_search_tool import ConfluenceSearchTool

confluence_tool = ConfluenceSearchTool(
    confluence_base_url="https://yourcompany.atlassian.net/wiki",
    email="you@yourcompany.com",
    api_token="your_token",
    space_key="DOCS"  # Optional
)

rag_agent = ConversableAgent(
    name="RAG_searcher",
    llm_config={"config_list": config_list},
    tools=[confluence_tool]
)
```

---

## 🧪 Example Usage

Ask your agent:

> What documentation exists about the auto-nesting module in version 2024?

The agent will:

- Trigger `confluence_search_tool`
- Search for pages matching `"auto-nesting"` in the `DOCS` space
- Return up to 3 relevant results with clean snippets and URLs

---

## 🧠 CQL Translator Prompt Template (Agent)

You can also create a helper agent that **transforms natural language into CQL queries**:

```python
cql_prompt = """
You are a CQL (Confluence Query Language) expert. Your task is to convert natural language questions into valid CQL queries to retrieve content from Confluence Cloud.

## Rules:
- Always return only the raw CQL query string, nothing else.
- The default content type is "page".
- Use `text ~ "..."` to match content.
- If the user asks about labels, versions, or categories, use `label = "..."` or `label in (...)`.
- If the user mentions a specific space, use `space = "..."`.
- If a date range is included, use `lastmodified >=` or `created >=` (ISO 8601 format: YYYY-MM-DD).
- When appropriate, combine multiple conditions with AND/OR.

## Examples:

### User:
Find documentation about microjoints issues

### CQL:
type = "page" AND text ~ "microjoints" AND text ~ "issue"

---

### User:
Tickets related to nesting failures in the DOCS space

### CQL:
space = "DOCS" AND type = "page" AND text ~ "nesting" AND text ~ "failure"

---

### User:
Pages labeled with cutting or laser in engineering space

### CQL:
space = "ENGINEERING" AND label in ("cutting", "laser") AND type = "page"

---

### User:
All pages mentioning bending created after January 1, 2024

### CQL:
type = "page" AND text ~ "bending" AND created >= "2024-01-01"

---

Now process this user query:

{query}
"""
```

---

### Usage Example

```python
from autogen import ConversableAgent

CQL_translator = ConversableAgent(
    name="CQL_Translator",
    llm_config={
        "config_list": config_list,
        "temperature": 0,
        "system_message": "You are an expert in transforming text into CQL queries."
    },
    prompt_template=cql_prompt
)
```

Then use it like this:

```python
query = "Show me documents about laser failures in the MANUALS space"
CQL_translator.generate_reply(messages=[{"role": "user", "content": query}])
```

---

## ✅ Next Steps

Would you like help with:

1. A production-grade version (with retries, logging, pagination)?
2. Combining this tool with your Azure AI Search vector index?
3. Integrating it into your current `ManualsRAGnWorkflow` flow?

Let me know what you'd like to prioritize.
