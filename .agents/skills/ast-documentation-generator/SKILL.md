# ASKILL: AST Documentation Generator for Jules using OKF + UML

## Purpose

This Askill generates **complete technical documentation** for an entire software project using **AST (Abstract Syntax Tree)** analysis instead of regular text parsing, ensuring that the generated documentation is always synchronized with the real implementation.

The documentation follows the **OKF (Open Knowledge Framework)** structure and is intended to be consumed by **OpenWiki**, allowing Jules and other AI agents to understand the codebase with high precision.

The skill operates in two modes:

* **full** → Rebuild the complete project documentation.
* **diff** → Update only the documentation affected by files modified in a Pull Request.

---

# Objectives

The generated documentation must become the single source of truth for the project.

It must allow:

* AI agents (Jules, Copilot, Claude Code, Cursor, etc.) to understand the project.
* Developers to navigate the architecture.
* Automatic generation of UML diagrams.
* Automatic synchronization with Pull Requests.
* Semantic search through OpenWiki.

---

# General Rules

## NEVER parse source code using regex.

Always use the language AST.

Examples:

* Python → tree-sitter-python / ast
* C# → Roslyn
* Java → JavaParser
* TypeScript → ts-morph
* JavaScript → Babel
* C/C++ → Clang
* Go → go/ast
* Rust → syn

AST is mandatory.

---

# Documentation Output Folder

All generated documentation SHALL be stored inside:

```
openwiki/
```

This folder is completely generated.

Developers must never manually edit its contents.

---

# Execution Modes

## Mode FULL

Parameter

```
mode=full
```

Workflow

1. Delete the entire

```
openwiki/
```

directory.

2. Create it again.

3. Scan the complete repository.

4. Build the dependency graph.

5. Generate UML.

6. Generate OKF documentation.

7. Generate navigation indexes.

8. Generate summaries.

9. Validate links.

10. Finish.

The documentation must always represent the exact current state of the repository.

---

## Mode DIFF

Parameter

```
mode=diff
```

Workflow

Obtain the changed files from the Pull Request.

For every modified source file:

* Parse again.
* Update its documentation.
* Regenerate affected UML diagrams.
* Update dependency graphs.
* Update impacted indexes.
* Preserve all unaffected documentation.

Only modified documentation should change.

---

# Repository Scan

The skill shall recursively inspect every source folder.

Ignored folders

```
.git
.github
.vscode
.idea
node_modules
dist
bin
obj
target
coverage
__pycache__
```

Everything else is documented.

---

# Documentation Granularity

Every source file must have its own documentation page.

No exceptions.

Example

```
src/

    api.py

    models.py

    auth.py
```

Produces

```
openwiki/

    api.md

    models.md

    auth.md
```

---

# Each File Documentation

Every file must include:

* Purpose
* Responsibilities
* Dependencies
* Imported modules
* Exported classes
* Exported interfaces
* Exported functions
* Public API
* Internal architecture
* Execution flow
* Sequence explanation
* UML
* Examples

---

# Public Classes

Every public class must include

## Overview

Explain in natural language:

* Why it exists.
* What business capability it provides.
* How it collaborates with other classes.

---

## Constructor

Document every constructor.

Explain:

* Parameters
* Dependencies
* Initialization

---

## Attributes

Document every public property.

Explain:

* Type
* Purpose
* Constraints

---

## Public Methods

Every public method MUST be documented.

Never skip one.

Documentation includes

### Description

Natural language explaining exactly what the method does.

### Inputs

For every parameter:

* name
* type
* meaning
* valid values
* optional?
* default value

### Output

Describe:

* return type
* semantic meaning
* possible null values
* exceptions

### Side Effects

Explain

* Database updates
* File operations
* Network calls
* Cache
* State changes

### Complexity

When possible:

```
Time Complexity

Space Complexity
```

### Example

Generate a usage example.

---

# Private Methods

Private methods receive lightweight documentation including:

* Purpose
* Parameters
* Return value

---

# Module Overview

Each file begins with

```
Purpose

Responsibilities

Main Workflow

Dependencies
```

---

# Dependency Analysis

Using AST, identify

Imports

Inheritance

Composition

Aggregation

Interface implementation

Generics

Callbacks

Events

Dependency Injection

Generate a dependency section.

---

# UML Generation

Automatically generate PlantUML diagrams.

Required diagrams

## Class Diagram

Classes

Interfaces

Inheritance

Composition

Associations

---

## Package Diagram

Folders

Packages

Modules

---

## Sequence Diagram

For important workflows.

---

## Component Diagram

Subsystem interactions.

---

## Dependency Graph

Show module dependencies.

---

# Call Graph

Generate call graphs for public APIs.

---

# Architecture Documentation

Automatically detect

Layers

Controllers

Services

Repositories

Entities

Value Objects

DTOs

Factories

Builders

Adapters

Ports

Domain Models

Application Services

Infrastructure

---

# OKF Structure

The generated documentation follows:

```
openwiki/

    index.md

    SUMMARY.md

    architecture/

    modules/

    api/

    classes/

    diagrams/

    dependencies/

    glossary/

    decisions/

    generated/
```

---

# Cross References

Every page links to

Parent module

Child modules

Dependencies

Used by

Calls

Called from

Related classes

Related interfaces

Related diagrams

---

# Index Generation

Automatically generate

```
SUMMARY.md
```

Navigation

Table of contents

Architecture overview

Module list

Alphabetical class index

Public API index

---

# Language

Documentation must be written in high-quality technical English.

Descriptions should be written in clear natural language suitable for both developers and AI agents.

Avoid copying code verbatim.

Explain intent, behavior, and architectural role rather than implementation details.

---

# Incremental Updates

Diff mode shall

Identify changed files.

Determine impacted dependencies.

Regenerate only affected pages.

Update indexes.

Update UML.

Update references.

---

# Validation

Before completion verify:

No broken links.

Every public method documented.

Every public class documented.

Every source file documented.

Every UML generated successfully.

Navigation is valid.

No orphan pages.

---

# Output Quality Requirements

The generated documentation should be:

* Deterministic.
* Reproducible.
* AST-based.
* AI-friendly.
* Human-readable.
* Free of duplicated information.
* Suitable for semantic indexing by OpenWiki.

---

# Success Criteria

The Askill is considered successful only if:

* 100% of source files have documentation.
* 100% of public classes are documented.
* 100% of public methods are documented with natural language descriptions, parameters, return values, and side effects.
* UML diagrams are generated and linked.
* Dependency graphs are complete.
* The `openwiki/` directory is fully regenerated in `full` mode.
* Only impacted documentation is regenerated in `diff` mode.
* The resulting documentation can be consumed directly by OpenWiki and used by Jules as an accurate, continuously synchronized representation of the entire codebase.
