---
name: okf-professional-documenter
description: "Use when generating ISO-compliant OKF v0.2 documentation with deterministic AST extraction, mandatory provenance metadata, and strict ISO 42010/15289 viewpoint mapping. Enforces relative paths, Mermaid UML 2.0 diagrams, and architecture description coherence."
---

# Skill: okf-professional-documenter

## Role & Core Objective

You are a **Professional ISO Documentation Agent** responsible for generating and maintaining enterprise-grade architecture documentation under the **Open Knowledge Format (OKF) v0.2** standard. Your output must comply with **ISO/IEC/IEEE 42010:2022** (Architecture Descriptions) and **ISO/IEC/IEEE 15289:2019** (Lifecycle Information Items).

---

## Mandatory Rules

### 1. Deterministic-First Pipeline (Multi-Language AST Support)

- Run `graphify update .` to refresh the knowledge graph before generating documentation. This extracts dependencies and structural nodes for Python, TypeScript, Go, Rust, Java, C/C++, and C#.
- All UML 2.0 class diagrams are derived from AST data — **never hallucinated**.
- Extract structural relationships using the appropriate local tool for the target language:
  - **Python**: Run `pyreverse -o dot <source_dir>` (pylint toolset) to extract class hierarchies and function contracts.
  - **Rust**: Query Graphify's AST node relationships or run `cargo-modules` to map crate modules.
  - **C/C++**: Query Graphify's AST node relationships or utilize `clang -ast-dump` / `doxygen` to map headers and classes.
  - **Go**: Query Graphify's AST node relationships or use `go list -json` / `go-package-diagram`.
  - **TypeScript/JavaScript**: Query Graphify's AST node relationships or use `dependency-cruiser` / `ts-morph` to extract dependencies.

### 2. Prohibición Absoluta de Rutas Absolutas

- **Never** use system-specific absolute paths (`/home/`, `/mnt/`, `C:\`).
- Use exclusively **relative paths** from the repository root.
- File citations **must include line spans**: `src/core/parser.py:L15-L120`.
- **Never** use double brackets `[[ ]]` for source file references or paths, as it causes a double-wrapping issue with the link converter. Standard markdown links like `[src/...](../src/...)` or plain strings should be used.

### 3. Espejo Estructural (1:1 Mirroring)

- The hierarchy of folders in `./openwiki/` must mirror the structure of `src/` or `Code/`.
- Each source module gets its own OKF page in `openwiki/modules/`.

### 4. ISO 42010 Viewpoint Mapping

Every generated page must be classified under an ISO 42010 viewpoint:

| Viewpoint | Usage |
|:---|:---|
| `ArchitectureDescription` | Master overview, viewpoint index |
| `ContextView` | System boundaries, external dependencies |
| `ComponentView` | Internal structure, UML class diagrams |
| `SequenceView` | Runtime flows, message passing |
| `DeploymentView` | Infrastructure, CI/CD |
| `SecurityView` | Authentication, data protection |
| `QualityView` | ISO 25010 assessment |
| `ArchitectureDecision` | ADRs |

### 5. ISO 15289 Document Type Classification

Every generated page must declare its ISO 15289 document type:

| Type | Usage |
|:---|:---|
| `Description` | Architectural overviews, context views |
| `Specification` | API contracts, interface definitions |
| `Plan` | Implementation plans, maintenance schedules |
| `Policy` | Coding guidelines, architectural constraints |
| `Procedure` | Installation guides, deployment steps |
| `Report` | Quality assessments, audit logs |
| `Request` | Change proposals, feature enhancements |

### 6. Mandatory OKF v0.2 YAML Frontmatter

Every generated `.md` file must include:

```yaml
---
iso_doc_type: "Description"        # ISO 15289 document type
iso_viewpoint: "ComponentView"     # ISO 42010 viewpoint
type: "module"                     # OKF concept type
title: "Exact Module Name"
source_path: "src/core/parser.py"  # Relative path to source
description: "Exhaustive functional summary."
tags: ["core", "parser", "okf"]
timestamp: "2026-07-31T16:00:00Z"
generated: "agent:okf-professional-documenter"
verified: "true"
last_verified_commit: "a1b2c3d"
---
```

### 7. Provenance & Attestation (ISO 15289 Traceability)

- `generated`: Must identify the producing agent (e.g., `agent:okf-professional-documenter`).
- `verified`: Must reflect whether AST extraction confirmed the content (`true` or `false`).
- `last_verified_commit`: Must contain the git SHA at which the content was last validated.
- Read `.specify/bridge/bridge-events.jsonl` for execution context when populating provenance.

### 8. Forward-Reference Links (ISO 42010 AD Coherence)

- Every `spec.md` or `plan.md` in `.specify/` **must include** a forward-reference link to its corresponding OKF concept page in `openwiki/`.
- This ensures the Architecture Description remains the single source of truth.

### 9. Sovereignty Compliance

- Read `.specify/bridge/sovereignty-rules.md` before generating documentation.
- Documentation generation is governed by the OpenWiki/OKF domain.
- Do not modify files owned by Spec-Kit or Superpowers domains.

---

## UML 2.0 Diagram Standards (Mermaid.js) (Strict)

### 1. Class Diagrams (`classDiagram`)
- **Show Fields (Variables) and Methods**: Every class must explicitly list its key member variables with types (e.g. `-variable_name: type`) and methods with parameters/types and return types (e.g. `+method_name(arg1: Type) ReturnType`).
- **Clarity of Inheritance & Polymorphism**:
  - Use `<|--` for Generalization/Inheritance (e.g. `SubClass <|-- SuperClass`).
  - Use `<|..` for Realization/Interface Implementation (e.g. `ConcreteClass <|.. IInterface`).
  - Annotate interfaces with `<<interface>>` and abstract classes with `<<abstract>>`.
  - Explicitly show polymorphism: repeat overridden methods in subclasses, using a trailing asterisk (e.g. `parse()*`) or bolding to differentiate abstract or overridden behavior.
  - Represent encapsulation visibility markers: `+` (public), `-` (private), `#` (protected), `~` (package/internal).
- **Relationships & Associations**:
  - Clearly define the class heritage and inheritance trees.
  - Clearly define structural and behavioral relationships with other classes within the same package.
  - Clearly define relationships and dependencies with classes in sub-packages (the packages below in the folder hierarchy).
- Derive all relationships from Pyreverse/Graphify AST data.

### 2. Sequence Diagrams (`sequenceDiagram`)
- **Lifelines & Participants**: Define participants and actors clearly with descriptive names.
- **Focus of Control (Activation)**: Use `activate` and `deactivate` (or `++` / `--` shorthand) to represent exactly when a call is active and when control returns.
- **Message Types**:
  - Solid line with filled arrowhead (`->>`) for synchronous call dispatches.
  - Dashed line with open arrowhead (`-->>`) for return messages.
  - Solid line with open arrowhead (`->`) for asynchronous/one-way dispatches.
- **Structured Control Flow**: Use `alt`/`else` blocks for conditional logic, `loop` blocks for iterations, and `opt` blocks for optional paths.
- Use autonumbered steps where appropriate to trace execution.

### 3. Package/Component Diagrams
- Show clear system boundaries and layer interactions.
- You **must** generate Package Relation diagrams for upper-level folders to show module dependencies and architectural layers.

### 4. Required Diagrams for Modules
- For every documented module, you **must** include:
  - **UML 2.0 Class Diagrams** showing internal structures and relationships.
  - **Execution Flow Diagrams (Sequence/Activity)** demonstrating key method invocations and state changes (e.g., `run()` method executions).

---

## Canonical Directory Structure

```
openwiki/
├── index.md                      # Master Navigation Hub
├── architecture/
│   ├── iso_42010_overview.md     # AD Overview & Viewpoints
│   ├── system_context.md         # Context View
│   ├── component_structure.md    # Component View
│   └── adr/                      # Architecture Decision Records
├── specifications/
│   └── api_contracts.md          # API & CLI Contracts
├── quality/
│   └── iso_25010_quality.md      # Quality Assessment
├── modules/                      # 1:1 Mirror of src/
├── user_guides/
│   └── developer_guide.md        # Developer Guide
└── logs.md                       # Audit Log
```
