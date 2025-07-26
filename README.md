
# Fastapi-Autogen-team Python Package

[![check.yml](https://github.com/lgcorzo/fastapi-autogen-team/actions/workflows/check.yml/badge.svg)](https://github.com/lgcorzo/fastapi-autogen-team/actions/workflows/check.yml)
[![publish.yml](https://github.com/lgcorzo/fastapi-autogen-team/actions/workflows/publish.yml/badge.svg)](https://github.com/lgcorzo/fastapi-autogen-team/actions/workflows/publish.yml)
[![Documentation](https://img.shields.io/badge/documentation-available-brightgreen.svg)](https://lgcorzo.github.io/fastapi-autogen-team/)
[![License](https://img.shields.io/github/license/lgcorzo/fastapi-autogen-team)](https://github.com/lgcorzo/fastapi-autogen-team/blob/main/LICENCE.txt)
[![Release](https://img.shields.io/github/v/release/lgcorzo/fastapi-autogen-team)](https://github.com/lgcorzo/fastapi-autogen-team/releases)

**This repository contains a Python codebase with best practices designed to support your MLOps initiatives if the project fasyapi-autogen-teams**

The package leverages several tools and tips to make your MLOps experience as flexible, robust, and productive as possible. You can use this package as part of your MLOps toolkit or platform (e.g., Model Registry, Experiment Tracking, Realtime Inference).



# Table of Contents

- [Fastapi-Autogen-team Python Package](#fastapi-autogen-team-python-package)
- [Table of Contents](#table-of-contents)
- [Install](#install)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Next Steps](#next-steps)
  - [Automation](#automation)
  - [Workflows](#workflows)
    - [1. **Project Purpose**](#1-project-purpose)
    - [2. **Project Setup**](#2-project-setup)
    - [3. **Project Structure**](#3-project-structure)
    - [4. **Implementing the Streaming Interface**](#4-implementing-the-streaming-interface)
    - [5. **Request Handling**](#5-request-handling)
    - [6. **Performance Optimization**](#6-performance-optimization)
    - [7. **Testing**](#7-testing)
    - [8. **Conclusion**](#8-conclusion)
  - [References:](#references)
- [📘 RAG with Confluence (AutoGen v2)](#-rag-with-confluence-autogen-v2)
  - [🎯 Objective](#-objective)
  - [🔐 Prerequisites](#-prerequisites)
  - [🧱 `confluence_search_tool.py`: AutoGen Tool Example](#-confluence_search_toolpy-autogen-tool-example)
  - [🤖 Integrating with an AutoGen Agent](#-integrating-with-an-autogen-agent)
  - [🧪 Example Usage](#-example-usage)
  - [🧠 CQL Translator Prompt Template (Agent)](#-cql-translator-prompt-template-agent)
    - [Usage Example](#usage-example)
  - [✅ Next Steps](#-next-steps)

# Install

This section details the requirements, actions, and next steps to kickstart your MLOps project.

## Prerequisites

*   Python>=3.11: to benefit from the latest features and performance improvements
*   Poetry>=1.8.2: to initialize the project virtual environment and its dependencies

## Installation

1.  Clone this GitHub repository on your computer

    ```bash
    # with ssh (recommended)
    $ git clone git@github.com:lgcorzo/fastapi-autogen-team.git
    or https
    $ git clone https://github.com/lgcorzo/fastapi-autogen-team
    ```
2.  Run the project installation with poetry ( install poetry in the base  env )

    ```bash
    $ cd fastapi-autogen-team/
    $ poetry env use $(which python)
    $ poetry install
    $ poetry env activate
    ```

    ```bash
    $ poetry run invoke containers.build
    ```

## Next Steps

Going from there, there are dozens of ways to integrate this package to your MLOps platform. For instance, you can use Databricks or AWS as your compute platform and model registry. It's up to you to adapt the package code to the solution you target.

Debugging in VS Code is possible with the following configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Poetry evaluations Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/fastapi_autogen_team/main.py", // Adjust the entry point path
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}", // Set the working directory to the project root
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            } // Ensure module discovery
        }
    ]
}
```

In production, you can build, ship, and run the project as a Python package:

```bash
poetry build
poetry publish # optional
python -m pip install [package]
[package] confs/inference.yaml

## added mocogpt for integration test if you need to simualte a chatgpt call
poetry add --group checks "mocogpt[cli]@git+https://github.com/lgcorzo/mocogpt.git"
```

## Automation

This project includes several automation tasks to easily repeat common actions. You can invoke the actions from the command line or VS Code extension.

```bash
# execute the project DAG
$ inv projects
# create a code archive
$ inv packages
# list other actions
$ inv --list
```

**Available tasks**:

*   **checks.all (checks)** - Run all check tasks.
*   **checks.code** - Check the codes with ruff.
*   **checks.coverage** - Check the coverage with coverage.
*   **checks.format** - Check the formats with ruff.
*   **checks.poetry** - Check poetry config files.
*   **checks.security** - Check the security with bandit.
*   **checks.test** - Check the tests with pytest.
*   **checks.type** - Check the types with mypy.
*   **cleans.all (cleans)** - Run all tools and folders tasks.
*   **cleans.cache** - Clean the cache folder.
*   **cleans.coverage** - Clean the coverage tool.
*   **cleans.dist** - Clean the dist folder.
*   **cleans.docs** - Clean the docs folder.
*   **cleans.environment** - Clean the project environment file.
*   **cleans.folders** - Run all folders tasks.
*   **cleans.mypy** - Clean the mypy tool.
*   **cleans.outputs** - Clean the outputs folder.
*   **cleans.poetry** - Clean poetry lock file.
*   **cleans.pytest** - Clean the pytest tool.
*   **cleans.projects** - Run all projects tasks.
*   **cleans.python** - Clean python caches and bytecodes.
*   **cleans.requirements** - Clean the project requirements file.
*   **cleans.reset** - Run all tools, folders, and sources tasks.
*   **cleans.ruff** - Clean the ruff tool.
*   **cleans.sources** - Run all sources tasks.
*   **cleans.tools** - Run all tools tasks.
*   **cleans.venv** - Clean the venv folder.
*   **commits.all (commits)** - Run all commit tasks.
*   **commits.bump** - Bump the version of the package.
*   **commits.commit** - Commit all changes with a message.
*   **commits.info** - Print a guide for messages.
*   **containers.all (containers)** - Run all container tasks.
*   **containers.build** - Build the container image with the given tag.
*   **containers.compose** - Start up docker compose.
*   **containers.run** - Run the container image with the given tag.
*   **docs.all (docs)** - Run all docs tasks.
*   **docs.api** - Document the API with pdoc using the given format and output directory.
*   **docs.serve** - Serve the API docs with pdoc using the given format and computer port.
*   **formats.all** - (formats) Run all format tasks.
*   **formats.imports** - Format python imports with ruff.
*   **formats.sources** - Format python sources with ruff.
*   **installs.all (installs)** - Run all install tasks.
*   **installs.poetry** - Install poetry packages.
*   **installs.pre-commit** - Install pre-commit hooks on git.
*   **packages.all (packages)** - Run all package tasks.
*   **packages.build** - Build a python package with the given format.
*   **projects.all (projects)** - Run all project tasks.
*   **projects.environment** - Export the project environment file.
*   **projects.requirements** - Export the project requirements file.

## Workflows

This package supports two GitHub Workflows in `.github/workflows`:

*   `check.yml`: Validate the quality of the package on each Pull Request
*   `publish.yml`: Build and publish the docs and packages on code release.

You can use and extend these workflows to automate repetitive package management tasks.


### 1. **Project Purpose**
The   project  want  to  create  a streaming interface for OpenAI-compatible models using **FastAPI** and **Microsoft AutoGen**. It uses **Server-Sent Events (SSE)** to enable real-time updates for client-server communication, suitable for applications like **LiteLLM** and **openai compatibel apps**.

![1743105581333](image/README/1743105581333.png)

---

### 2. **Project Setup**
   - **Installation:** 
     - Steps include cloning a GitHub repository and setting up a Python environment (with Python 3.11 and Poetry).
     - Key dependencies are `FastAPI` and `ag2`.

   - **Environment Variables:** 
     - An OpenAI API key is required, which should be stored in environment variables or an `.env` file.

   - **Running the Server:** 
     - Instructions include running a script (`run.sh`) to start the FastAPI server.
   - **Deploy the image**:  
     - generated qith the poetry run invoke containers.build command
   

---

### 3. **Project Structure**
   - **Main Files:**
     - `src/fastapi_autogen_team/main.py`: Entry point for the FastAPI application; handles environment variables and routes.
     - `src/fastapi_autogen_team/data_model.py`: Defines request/response models using Pydantic (compatible with OpenAI).
     - `src/fastapi_autogen_team/autogen_workflow_team.py`: Contains logic for the AutoGen workflows and interactions.
     - `src/fastapi_autogen_team/autogen_server.py`: Implements handling of streaming and non-streaming client requests.

```mermaid
classDiagram
    class Input {
        messages: list[Message]
        model: str
        stream: bool
    }
    class Message {
        role: str
        content: str
    }
    class Output {
        choices: list[dict]
    }
    class ModelInformation {
        id: str
        name: str
    }
    class AutogenWorkflow {
        llm_config: dict
        user: str
        queue: Queue
        run(message: str, stream: bool) : ChatResult
    }

    Input -- Message : contains
    Output -- dict : contains
    AutogenWorkflow -- Queue : uses
```

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant autogen_server.py
    participant autogen_workflow_team.py
    participant AutoGen Agent

    Client->>FastAPI: POST /chat/completions
    FastAPI->>autogen_server.py: serve_autogen(Input)
    autogen_server.py->>autogen_workflow_team.py: AutogenWorkflow.run(message, stream)
    autogen_workflow_team.py->>AutoGen Agent: Send message
    AutoGen Agent-->>autogen_workflow_team.py: Receive response
    autogen_workflow_team.py-->>autogen_server.py: Return response
    autogen_server.py-->>FastAPI: Return response
    FastAPI-->>Client: Return response
```

---

### 4. **Implementing the Streaming Interface**
   - **FastAPI Application:**
     - Routes are defined for features like redirecting to documentation (`GET /`), returning model information (`GET /models`), and handling chat completions (`POST /chat/completions`).

   - **Data Models:** 
     - Uses Pydantic to define:
       - `ModelInformation`: Stores model details.
       - `Input`: Represents an OpenAI-compatible request.
       - `Output`: Represents the response.
       - `Message`: A message in the request.

   - **AutoGen Workflow:**
     - Defines an interaction pattern between agents, such as `UserProxy` and AI agents like fictional comedians. Messages are processed via queues for streaming.

   - **Queue Management:**
     - Ensures real-time response by queueing intermediate messages for streaming to the client.

   - **Streaming Logic:** 
     - Uses **monkey patching** to modify the behavior of functions to stream responses.

---

### 5. **Request Handling**
   - **Serve Autogen:**
     - Processes client requests, creating AutoGen workflows for streaming or non-streaming responses.
   - **Streaming Response:** 
     - Server-Sent Events (SSE) are implemented to send real-time updates for streaming requests.
   - **Non-Streaming Response:** 
     - A full response is returned in a single payload.

---

### 6. **Performance Optimization**
 -  the project use   **uvicorn** for improved scalability and efficiency, enabling multi-worker setups for FastAPI applications.

---

### 7. **Testing**
   - **Testing the Server:** 
     - Includes examples using `curl` to query the server for chat completions.
   - **Response Format:**
     - Outputs data in a format compatible with OpenAI, supporting real-time updates for agent interactions.

---

### 8. **Conclusion**
Summarizes the significance of the streaming interface for enabling real-time interaction with OpenAI-compatible APIs. Links to additional resources like GitHub, AutoGen documentation, and FastAPI guides are provided.

---

Would you like me to delve deeper into any specific section?




## References: 
https://newsletter.victordibia.com/p/integrating-autogen-agents-into-your
https://medium.com/@moustafa.abdelbaky/building-an-openai-compatible-streaming-interface-using-server-sent-events-with-fastapi-and-8f014420bca7

Here is the **restructured, ordered, and translated version** of your document in **clear English**, organized into logical sections for better readability and production readiness:

---

# 📘 RAG with Confluence (AutoGen v2)

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

* ✅ A **Confluence Cloud** account.
* ✅ An **API token** from your Atlassian account:
  [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
* ✅ Your **Atlassian email address**.
* ✅ The base domain of your Confluence instance (e.g. `https://yourcompany.atlassian.net/wiki`).

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

* Trigger `confluence_search_tool`
* Search for pages matching `"auto-nesting"` in the `DOCS` space
* Return up to 3 relevant results with clean snippets and URLs

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
