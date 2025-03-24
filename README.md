
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
- [Tools](#tools)
  - [Automation](#automation-1)
    - [Commits: Commitizen](#commits-commitizen)
    - [Git Hooks: Pre-Commit](#git-hooks-pre-commit)
    - [Tasks: PyInvoke](#tasks-pyinvoke)
  - [CI/CD](#cicd)
    - [Runner: GitHub Actions](#runner-github-actions)
  - [CLI](#cli)
    - [Logging: Opentelemetry](#logging-opentelemetry)
  - [Code](#code)
    - [Coverage: Coverage](#coverage-coverage)
    - [Editor: VS Code](#editor-vs-code)
    - [Formatting: Ruff](#formatting-ruff)
    - [Quality: Ruff](#quality-ruff)
    - [Security: Bandit](#security-bandit)
    - [Testing: Pytest](#testing-pytest)
    - [Typing: Mypy](#typing-mypy)
    - [Code Versioning: Git](#code-versioning-git)
    - [Data Versioning: DVC](#data-versioning-dvc)
      - [**Motivations**](#motivations)
      - [**Features**](#features)
      - [**Limitations**](#limitations)
      - [**Alternatives**](#alternatives)
      - [**Additional Resources**](#additional-resources)
  - [Configs](#configs)
    - [Format: YAML](#format-yaml)
    - [Validator: Pydantic](#validator-pydantic)
  - [Data](#data)
    - [Container: Pandas](#container-pandas)
    - [Format: Parquet](#format-parquet)
    - [Schema: Pandera](#schema-pandera)
  - [Docs](#docs)
    - [API: pdoc](#api-pdoc)
    - [Format: Google](#format-google)
    - [Hosting: GitHub Pages](#hosting-github-pages)
  - [Package](#package)
    - [Evolution: Changelog](#evolution-changelog)
    - [Format: Wheel](#format-wheel)
    - [Manager: Poetry](#manager-poetry)
    - [Runtime: Docker](#runtime-docker)
  - [Programming](#programming)
    - [Language: Python](#language-python)
    - [Version: Pyenv](#version-pyenv)
  - [testing:](#testing)
  - [Observability](#observability)

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
2.  Run the project installation with poetry

    ```bash
    $ cd fastapi-autogen-team/
    $ poetry install
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

# Tools

This section motivates the use of developer tools to improve your coding experience.

## Automation

Pre-defined actions to automate your project development.

### Commits: Commitizen

*   **Motivations**:
    *   Format your code commits
    *   Generate a standard changelog
    *   Integrate well with SemVer and PEP 440
*   **Limitations**:
    *   Learning curve for new users
*   **Alternatives**:
    *   Do It Yourself (DIY)

### Git Hooks: Pre-Commit

*   **Motivations**:
    *   Check your code locally before a commit
    *   Avoid wasting resources on your CI/CD
    *   Can perform extra actions (e.g., file cleanup)
*   **Limitations**:
    *   Add overhead before your commit
*   **Alternatives**:
    *   Git Hooks: less convenient to use

### Tasks: PyInvoke

*   **Motivations**:
    *   Automate project workflows
    *   Sane syntax compared to alternatives
    *   Good trade-off between power/simplicity
*   **Limitations**:
    *   Not familiar to most developers
*   **Alternatives**:
    *   Make: most popular, but awful syntax

## CI/CD

Execution of automated workflows on code push and releases.

### Runner: GitHub Actions

*   **Motivations**:
    *   Native on GitHub
    *   Simple workflow syntax
    *   Lots of configs if needed
*   **Limitations**:
    *   SaaS Service
*   **Alternatives**:
    *   GitLab: can be installed on-premise

## CLI

### Logging: Opentelemetry
*   **Motivations**:
    *   Show progress to the user
    *   Work fine out of the box
    *   Saner logging syntax
*   **Limitations**:
    *   Doesn't let you deviate from the base usage
*   **Alternatives**:
    *   Logging: available by default, but feel dated

## Code

Edition, validation, and versioning of your project source code.

### Coverage: Coverage

https://krijnvanderburg.medium.com/automatically-generate-and-visualize-python-code-coverage-308e65627925

*   **Motivations**:
    *   Report code covered by tests
    *   Identify code path to test
    *   Show maturity to users
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   None?

### Editor: VS Code

*   **Motivations**:
    *   Open source
    *   Free, simple, open source
    *   Great plugins for Python development
*   **Limitations**:
    *   Require some configuration for Python
*   **Alternatives**:
    *   PyCharm: provide a lot, cost a lot
    *   Vim: I love it, but there is a VS Code plugin
    *   Spacemacs: I love it even more, but not everybody loves LISP

### Formatting: Ruff

*   **Motivations**:
    *   Super fast compared to others
    *   Don't waste time arranging your code
    *   Make your code more readable/maintainable
*   **Limitations**:
    *   Still in version 0.x, but more and more adopted
*   **Alternatives**:
    *   YAPF: more config options that you don't need
    *   Isort + Black: slower and need two tools

### Quality: Ruff

*   **Motivations**:
    *   Improve your code quality
    *   Super fast compared to others
    *   Great integration with VS Code
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   PyLint: too slow and too complex system
    *   Flake8: too much plugins, I prefer Pylint in practice

### Security: Bandit

*   **Motivations**:
    *   Detect security issues
    *   Complement linting solutions
    *   Not to heavy to use and enable
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   None

### Testing: Pytest

*   **Motivations**:
    *   Write tests or pay the price
    *   Super easy to write new test cases
    *   Tons of good plugins (xdist, sugar, cov, ...)
*   **Limitations**:
    *   Doesn't support parallel execution out of the box
*   **Alternatives**:
    *   Unittest: more verbose, less fun

### Typing: Mypy

*   **Motivations**:
    *   Static typing is cool!
    *   Communicate types to use
    *   Official type checker for Python
*   **Limitations**:
    *   Can have overhead for complex typing
*   **Alternatives**:
    *   PyRight: check big code base by MicroSoft
    *   PyType: check big code base by Google
    *   Pyre: check big code base by Facebook

### Code Versioning: Git

*   **Motivations**:
    *   If you don't version your code, you are a fool
    *   Most popular source code manager (what else?)
    *   Provide hooks to perform automation on some events
*   **Limitations**:
    *   Git can be hard: https://xkcd.com/1597/
*   **Alternatives**:
    *   Mercurial: loved it back then, but git is the only real option

### Data Versioning: DVC

#### **Motivations**

*   **Version Control for Data:** Just as versioning code is essential, versioning data ensures reproducibility, collaboration, and traceability in machine learning workflows.
*   **Integration with Git:** DVC works seamlessly with Git, enabling you to track datasets and models alongside code.
*   **Automation and Pipelines:** DVC provides tools for creating pipelines, automating data processing, and ensuring consistent workflows across teams.
*   **Scalability:** Handles large datasets without burdening Git by storing data in external storage solutions.

#### **Features**

*   **Data and Model Tracking:** Tracks datasets, models, and experiments without including large files in Git repositories.
*   **External Storage Support:** Supports various storage backends, including AWS S3, Google Cloud Storage, Azure, SSH, and local file systems.
*   **Reproducible Pipelines:** Allows users to define and execute machine learning workflows with dependencies and outputs tracked automatically.
*   **Experiment Management:** Simplifies running and tracking multiple experiments, making comparisons straightforward.

#### **Limitations**

*   **Learning Curve:** Requires understanding of Git and DVC-specific concepts to fully leverage its capabilities.
*   **Complexity for Small Projects:** Overhead may not be justified for simple projects or teams unfamiliar with Git.
*   **Storage Configuration:** Initial setup for remote storage can be tedious for non-technical users.
*   **Dependency on Git:** Full functionality depends on having a properly configured Git repository.

#### **Alternatives**

*   **Git LFS:** Focuses on large file versioning but lacks pipeline and experiment management capabilities.
*   **Pachyderm:** Offers data versioning and pipeline management but is more suited for large-scale, enterprise environments.
*   **LakeFS:** A Git-like version control system specifically for data lakes.
*   **Quilt:** Simplifies dataset sharing and versioning with a user-friendly UI.

#### **Additional Resources**

*   **Getting Started with DVC:** Official tutorial for beginners.
*   **DVC Pipelines Guide:** Learn to create reproducible pipelines.
*   **Remote Storage Setup:** Detailed instructions on configuring remote storage.
*   **DVC vs Git LFS:** A comparison of DVC and Git LFS.

## Configs

Manage the configs files of your project to change executions.

### Format: YAML

*   **Motivations**:
    *   Change execution without changing code
    *   Readable syntax, support comments
    *   Allow to use OmegaConf <3
*   **Limitations**:
    *   Not supported out of the box by Python
*   **Alternatives**:
    *   JSON: no comments, more verbose
    *   TOML: less suited to config merge/sharing


### Validator: Pydantic

*   **Motivations**:
    *   Validate your config before execution
    *   Pydantic should be builtin (period)
    *   Super charge your Python class
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   Dataclass: simpler, but much less powerful
    *   Attrs: no validation, less intuitive to use

## Data

Define the datasets to provide data inputs and outputs.

### Container: Pandas

*   **Motivations**:
    *   Load data files in memory
    *   Lingua franca for Python
    *   Most popular options
*   **Limitations**:
    *   Lot of gotchas
*   **Alternatives**:
    *   Polars: faster, saner, but less integrations
    *   Pyspark: powerful, popular, distributed, so much overhead
    *   Dask, Ray, Modin, Vaex, ...: less integration (even if it looks like pandas)

### Format: Parquet

*   **Motivations**:
    *   Store your data on disk
    *   Column-oriented (good for analysis)
    *   Much more efficient and saner than text based
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   CSV: human readable, but that's the sole benefit
    *   Avro: good alternative for row-oriented workflow

### Schema: Pandera

*   **Motivations**:
    *   Typing for dataframe
    *   Communicate data fields
    *   Support pandas and others
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   Great Expectations: powerful, but much more difficult to integrate

## Docs

Generate and share the project documentations.

### API: pdoc

*   **Motivations**:
    *   Share docs with others
    *   Simple tool, only does API docs
    *   Get the job done, get out of your way
*   **Limitations**:
    *   Only support API docs (i.e., no custom docs)
*   **Alternatives**:
    *   Sphinx: Most complete, overkill for simple projects
    *   Mkdocs: no support for API doc, which is the core feature

### Format: Google

*   **Motivations**:
    *   Common style for docstrings
    *   Most writeable out of alternatives
    *   I often write a single line for simplicity
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   Numpy: less writeable
    *   Sphinx: baroque style

### Hosting: GitHub Pages

*   **Motivations**:
    *   Easy to setup
    *   Free and simple
    *   Integrated with GitHub
*   **Limitations**:
    *   Only support static content
*   **Alternatives**:
    *   ReadTheDocs: provide more features


## Package

Define and build modern Python package.

### Evolution: Changelog

*   **Motivation**:
    *   Communicate changes to user
    *   Can be updated with Commitizen
    *   Standardized with Keep a Changelog
*   **Limitations**:
    *   None
*   **Alternatives**:
    *   None

### Format: Wheel

*   **Motivations**:
    *   Has several advantages
    *   Create source code archive
    *   Most modern Python format
*   **Limitations**:
    *   Doesn't ship with C/C++ dependencies (e.g., CUDA)
        *   i.e., use Docker containers for this case
*   **Alternatives**:
    *   Source: older format, less powerful
    *   Conda: slow and hard to manage

### Manager: Poetry

*   **Motivations**:
    *   Define and build Python package
    *   Most popular solution by GitHub stars
    *   Pack every metadata in a single static file
*   **Limitations**:
    *   Cannot add dependencies beyond Python (e.g., CUDA)
        *   i.e., use Docker container for this use case
*   **Alternatives**:
    *   Setuptools: dynamic file is slower and more risky
    *   Pdm, Hatch, PipEnv: https://xkcd.com/1987/

### Runtime: Docker

*   **Motivations**:
    *   Create isolated runtime
    *   Container is the de facto standard
    *   Package C/C++ dependencies with your project
*   **Limitations**:
    *   Some company might block Docker Desktop, you should use alternatives
*   **Alternatives**:
    *   Conda: slow and heavy resolver

## Programming
.

### Language: Python

*   **Motivations**:
    *   Great language for AI/ML projects
    *   Robust with additional tools
    *   Hundreds of great libs
*   **Limitations**:
    *   Slow without C bindings
*   **Alternatives**:
    *   R: specific purpose language
    *   Julia: specific purpose language

### Version: Pyenv

*   **Motivations**:
    *   Switch between Python version
    *   Allow to select the best version
    *   Support global and local dispatch
*   **Limitations**:
    *   Require some shell configurations
*   **Alternatives**:
    *   Manual installation: time consuming
  
## testing:
  You can query the autogen agents using the following command:

  ``` bash
    curl -X 'POST' \
      'http://localhost:4100/autogen/api/v1beta/chat/completions' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "model": "internal-gpt",
      "messages": [
        {
          "role": "user",
          "content": "Get the local time form the system"
        }
      ],
      "temperature": 1,
      "top_p": 1,
      "presence_penalty": 0,
      "frequency_penalty": 0,
      "stream": true
    }'
  ``` 
Note that you must provide the entire conversation history to the backend, as the server expects input in OpenAI format.

## Observability

This section focuses on the project's observability features, providing insights into the system's behavior and performance.  This includes reproducibility, monitoring, alerting, lineage tracking, explainability, and infrastructure monitoring.
