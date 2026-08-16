import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import shutil
import argparse
import tree_sitter
import tree_sitter_rust

language = tree_sitter.Language(tree_sitter_rust.language())
parser = tree_sitter.Parser(language)


def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def mirror_directory(src_dir, target_dir):
    src_path = Path(src_dir)
    target_path = Path(target_dir) / "modules"
    if not src_path.exists():
        return []
    files_to_process = []
    for root, dirs, files in os.walk(src_path):
        current_root = Path(root)
        rel_path = current_root.relative_to(src_path)
        current_target = target_path / src_path.name / rel_path
        current_target.mkdir(parents=True, exist_ok=True)
        for file in files:
            if file.endswith('.rs'):
                source_file = current_root / file
                target_file = current_target / f"{file[:-3]}.md"
                files_to_process.append((source_file, target_file, current_root))
    return files_to_process


def parse_rust_file(filepath):
    with open(filepath, "rb") as f:
        source_code = f.read()

    tree = parser.parse(source_code)

    classes = {}
    methods = []
    dependencies = []
    relations = []

    def get_text(node):
        return source_code[node.start_byte:node.end_byte].decode("utf-8")

    def walk_file(node):
        if node.type == "use_declaration":
            dependencies.append(get_text(node))
        elif node.type == "struct_item":
            struct_name_node = node.child_by_field_name("name")
            if struct_name_node:
                struct_name = get_text(struct_name_node)
                fields = []
                raw_fields = []
                body = node.child_by_field_name("body")
                if body and body.type == "field_declaration_list":
                    for field in body.children:
                        if field.type == "field_declaration":
                            fname = get_text(field.child_by_field_name("name"))
                            ftype = get_text(field.child_by_field_name("type"))
                            visibility = "-"
                            for c in field.children:
                                if c.type == "visibility_modifier":
                                    visibility = "+"
                                    break
                            fields.append(f"{visibility}{ftype} {fname}")
                            raw_fields.append((fname, ftype))

                            rel_type = ''.join(c for c in ftype.split('<')[0] if c.isalnum() or c == '_')
                            if rel_type and rel_type[0].isupper() and rel_type != struct_name:
                                relations.append(f"{struct_name} --> {rel_type} : Association")
                elif body and body.type == "ordered_field_declaration_list":
                     visibility = "-"
                     for field in body.children:
                         if field.type == "visibility_modifier":
                             visibility = "+"
                         elif field.type not in (",", "(", ")"):
                             ftype = get_text(field)
                             fields.append(f"{visibility}{ftype}")
                             raw_fields.append(("", ftype))

                             rel_type = ''.join(c for c in ftype.split('<')[0] if c.isalnum() or c == '_')
                             if rel_type and rel_type[0].isupper() and rel_type != struct_name:
                                 relations.append(f"{struct_name} --> {rel_type} : Association")
                             visibility = "-"


                classes[struct_name] = {
                    "type": "class",
                    "fields": fields,
                    "raw_fields": raw_fields,
                    "methods": [],
                    "line": node.start_point[0] + 1
                }
        elif node.type == "enum_item":
            enum_name_node = node.child_by_field_name("name")
            if enum_name_node:
                enum_name = get_text(enum_name_node)
                fields = []
                raw_fields = []
                body = node.child_by_field_name("body")
                if body and body.type == "enum_variant_list":
                    for variant in body.children:
                        if variant.type == "enum_variant":
                            vname = get_text(variant.child_by_field_name("name"))
                            variant_types = []
                            vbody = variant.child_by_field_name("body")
                            if vbody:
                                if vbody.type == "field_declaration_list":
                                    for field in vbody.children:
                                        if field.type == "field_declaration":
                                            fname = get_text(field.child_by_field_name("name"))
                                            ftype = get_text(field.child_by_field_name("type"))
                                            variant_types.append(f"{fname}: {ftype}")
                                elif vbody.type == "ordered_field_declaration_list":
                                    for field in vbody.children:
                                        if field.type not in (",", "(", ")"):
                                            variant_types.append(get_text(field))

                            if variant_types:
                                type_str = f"variant({', '.join(variant_types)})"
                            else:
                                type_str = "variant"

                            fields.append(vname)
                            raw_fields.append((vname, type_str))
                classes[enum_name] = {
                    "type": "<<enumeration>>",
                    "fields": fields,
                    "raw_fields": raw_fields,
                    "methods": [],
                    "line": node.start_point[0] + 1
                }
        elif node.type == "trait_item":
            trait_name_node = node.child_by_field_name("name")
            if trait_name_node:
                trait_name = get_text(trait_name_node)
                trait_methods = []
                body = node.child_by_field_name("body")
                if body and body.type == "declaration_list":
                    for child in body.children:
                        if child.type in ("function_item", "function_signature_item"):
                            fname = get_text(child.child_by_field_name("name"))
                            trait_methods.append(f"+{fname}()")

                            params_str = ""
                            params_node = child.child_by_field_name("parameters")
                            if params_node:
                                params_str = get_text(params_node)[1:-1]

                            ret_type_str = "()"
                            ret_type_node = child.child_by_field_name("return_type")
                            if ret_type_node:
                                ret_type_str = get_text(ret_type_node)

                            methods.append({
                                "name": fname,
                                "struct": trait_name,
                                "line": child.start_point[0] + 1,
                                "calls": [],
                                "params": params_str,
                                "ret_type": ret_type_str,
                                "is_pub": "+"
                            })
                classes[trait_name] = {
                    "type": "<<interface>>",
                    "fields": [],
                    "raw_fields": [],
                    "methods": trait_methods,
                    "line": node.start_point[0] + 1
                }
        elif node.type == "impl_item":
            type_node = node.child_by_field_name("type")
            trait_node = node.child_by_field_name("trait")

            if type_node:
                struct_name = get_text(type_node)
                if trait_node:
                    trait_name = get_text(trait_node)
                    clean_trait = trait_name.split('::')[-1]
                    relations.append(f"{clean_trait} <|.. {struct_name} : Realization")

                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        if child.type in ("function_item", "function_signature_item"):
                            fname = get_text(child.child_by_field_name("name"))
                            visibility = "-"
                            for c in child.children:
                                if c.type == "visibility_modifier":
                                    visibility = "+"
                                    break
                            method_sig = f"{visibility}{fname}()"

                            params_str = ""
                            params_node = child.child_by_field_name("parameters")
                            if params_node:
                                params_str = get_text(params_node)[1:-1]

                            ret_type_str = "()"
                            ret_type_node = child.child_by_field_name("return_type")
                            if ret_type_node:
                                ret_type_str = get_text(ret_type_node)

                            calls = []
                            def extract_calls(n):
                                if n.type == "call_expression":
                                    func_node = n.child_by_field_name("function")
                                    if func_node:
                                        if func_node.type == "field_expression":
                                            cname = get_text(func_node.child_by_field_name("field"))
                                        elif func_node.type == "identifier":
                                            cname = get_text(func_node)
                                        else:
                                            cname = get_text(func_node)
                                        if cname not in ['if', 'while', 'for', 'match', 'Some', 'Ok', 'Err', 'String', 'Vec', 'Box', 'format!', 'println!', 'tracing::info!', 'tracing::debug!', 'tracing::error!', 'tracing::warn!', 'panic!']:
                                            calls.append(cname)
                                for c in n.children:
                                    extract_calls(c)
                            extract_calls(child)

                            methods.append({
                                "name": fname,
                                "struct": struct_name,
                                "line": child.start_point[0] + 1,
                                "calls": calls,
                                "params": params_str,
                                "ret_type": ret_type_str,
                                "is_pub": visibility
                            })

                            if struct_name in classes:
                                classes[struct_name]["methods"].append(method_sig)
                            else:
                                classes[struct_name] = {
                                    "type": "class",
                                    "fields": [],
                                    "raw_fields": [],
                                    "methods": [method_sig],
                                    "line": node.start_point[0] + 1
                                }
        elif node.type == "function_item" and node.parent.type == "source_file":
            fname = get_text(node.child_by_field_name("name"))
            visibility = "-"
            for c in node.children:
                if c.type == "visibility_modifier":
                    visibility = "+"
                    break

            params_str = ""
            params_node = node.child_by_field_name("parameters")
            if params_node:
                params_str = get_text(params_node)[1:-1]

            ret_type_str = "()"
            ret_type_node = node.child_by_field_name("return_type")
            if ret_type_node:
                ret_type_str = get_text(ret_type_node)

            calls = []
            def extract_calls(n):
                if n.type == "call_expression":
                    func_node = n.child_by_field_name("function")
                    if func_node:
                        if func_node.type == "field_expression":
                            cname = get_text(func_node.child_by_field_name("field"))
                        elif func_node.type == "identifier":
                            cname = get_text(func_node)
                        else:
                            cname = get_text(func_node)
                        if cname not in ['if', 'while', 'for', 'match', 'Some', 'Ok', 'Err', 'String', 'Vec', 'Box', 'format!', 'println!', 'tracing::info!', 'tracing::debug!', 'tracing::error!', 'tracing::warn!', 'panic!']:
                            calls.append(cname)
                for c in n.children:
                    extract_calls(c)
            extract_calls(node)

            methods.append({
                "name": fname,
                "struct": None,
                "line": node.start_point[0] + 1,
                "calls": calls,
                "params": params_str,
                "ret_type": ret_type_str,
                "is_pub": visibility
            })

        for child in node.children:
            if node.type not in ["impl_item", "struct_item", "enum_item", "trait_item", "use_declaration"]:
                walk_file(child)

    walk_file(tree.root_node)

    if not classes:
        import pathlib
        p = pathlib.Path(filepath)
        mod_name = p.name.split('.')[0].capitalize()
        if mod_name == "Mod":
            mod_name = p.parent.name.capitalize() + "Module"

        mod_methods = []
        for m in methods:
            if m["struct"] is None:
                mod_methods.append(f"+{m['name']}()")
        classes[mod_name] = {"type": "<<module>>", "fields": [], "raw_fields": [], "methods": mod_methods, "line": 1}

    return {
        "classes": classes,
        "methods": methods,
        "dependencies": sorted(list(set(dependencies))),
        "relations": sorted(list(set(relations)))
    }

def generate_plantuml_class_diagram(ast):
    plantuml = "```plantuml\n@startuml\n"
    for name, data in ast["classes"].items():
        plantuml += f"    class {name} {{\n"
        if data["type"] != "class":
            plantuml += f"        {data['type']}\n"
        for f in data["fields"]:
            plantuml += f"        {f}\n"
        for m in data["methods"]:
            plantuml += f"        {m}\n"
        plantuml += "    }\n"
    for rel in ast["relations"]:
        plantuml += f"    {rel}\n"
    if not ast["classes"]:
        plantuml += "    class Module {\n        <<module>>\n    }\n"
    plantuml += "@enduml\n```\n"
    return plantuml

def generate_plantuml_sequence_diagram(ast):
    plantuml = "```plantuml\n@startuml\n    autonumber\n    participant \"Client Interface\" as Caller\n"
    if not ast["methods"]:
        return plantuml + "    Caller->Svc: Invoke\n@enduml\n```\n"

    main_actor = list(ast["classes"].keys())[0] if ast["classes"] else "Svc"
    plantuml += f"    participant {main_actor} as Svc\n"

    for m in ast["methods"][:5]:  # limit to top 5 methods for clarity
        actor = m["struct"] if m["struct"] else main_actor
        plantuml += f"    Caller->Svc: {m['name']}()\n"
        for call in m.get("calls", [])[:3]: # limit inner calls
             plantuml += f"    Svc->Svc: {call}()\n"
        plantuml += f"    Svc-->Caller: Returns execution status\n"

    plantuml += "@enduml\n```\n"
    return plantuml

def generate_okf_markdown(filepath, rel_dir, ast, commit_hash):
    title = filepath.name.split('.')[0].capitalize()
    if title == "Mod":
         title = filepath.parent.name.capitalize() + "Module"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    class_diagram = generate_plantuml_class_diagram(ast)
    seq_diagram = generate_plantuml_sequence_diagram(ast)

    deps_list = "\n".join([f"- `{dep}`" for dep in ast["dependencies"]]) if ast["dependencies"] else "- None"

    citations = ""
    for name, data in ast["classes"].items():
         citations += f"* Class `{name}`: `{filepath.as_posix()}:L{data['line']}`\n"
    for m in ast["methods"]:
         cls_str = f" in `{m['struct']}`" if m['struct'] else ""
         citations += f"* Method `{m['name']}`{cls_str}: `{filepath.as_posix()}:L{m['line']}`\n"
    if not citations:
         citations = "* No direct classes or functions extracted."

    # Data Structures & Properties
    data_structs = "## 3. Data Structures, Structs & Class Properties\n\n"
    has_structs = False
    for name, data in ast["classes"].items():
        if data.get("raw_fields"):
            has_structs = True
            data_structs += f"### {name}\n"
            data_structs += "| Property | Type | Description |\n"
            data_structs += "| :--- | :--- | :--- |\n"
            for fname, ftype in data["raw_fields"]:
                if not fname: fname = "N/A"
                data_structs += f"| `{fname}` | `{ftype}` | Field of {name} |\n"
            data_structs += "\n"
    if not has_structs:
        data_structs += "No notable data structures or fields in this module.\n\n"

    # Methods & Functions Breakdown
    method_breakdown = "## 4. Comprehensive Methods & Functions Breakdown\n\n"
    has_methods = False
    for m in ast["methods"]:
        has_methods = True
        cls_str = f"{m['struct']}::" if m['struct'] else ""
        method_breakdown += f"### `{cls_str}{m['name']}`\n"
        method_breakdown += f"* **Visibility:** {m['is_pub']}\n"
        method_breakdown += f"* **Source Line Citation:** `{filepath.as_posix()}:L{m['line']}`\n\n"

        # Parameters
        method_breakdown += "#### Input Parameters\n"
        method_breakdown += "| Parameter | Data Type | Required / Default | Semantic Description |\n"
        method_breakdown += "| :--- | :--- | :--- | :--- |\n"
        if m["params"]:
            for param in m["params"].split(','):
                param = param.strip()
                if param:
                    parts = param.split(':')
                    if len(parts) == 2:
                        pname, ptype = parts[0].strip(), parts[1].strip()
                        method_breakdown += f"| `{pname}` | `{ptype}` | Required | Parameter |\n"
                    else:
                        method_breakdown += f"| `{param}` | `self` | Required | Instance reference |\n"
        else:
            method_breakdown += "| None | None | N/A | No parameters |\n"
        method_breakdown += "\n"

        # Return Value
        method_breakdown += "#### Return Value & Output Shape\n"
        method_breakdown += "| Return Type | Scenario | Description |\n"
        method_breakdown += "| :--- | :--- | :--- |\n"
        method_breakdown += f"| `{m['ret_type']}` | Success | Result of the operation |\n\n"

    if not has_methods:
        method_breakdown += "No methods or functions defined in this module.\n\n"


    markdown = f"""---
iso_doc_type: "Specification"
iso_viewpoint: "ComponentView"
type: "module"
title: "Module: {title}"
source_path: "{filepath.as_posix()}"
description: "Detailed architecture and specifications for the {title} module."
tags: ["core", "module", "okf", "iso42010"]
last_verified_commit: "{commit_hash}"
timestamp: "{timestamp}"
---

# Module Specification: {title}

* **Source Reference:** `{filepath.as_posix()}`
* **Package Dependency:**
{deps_list}

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `{title}` module extracted directly from the codebase.

## 2. UML 2.0 Diagrams
### Class & Inheritance Architecture
{class_diagram}

### Execution Flow & Runtime Behavior
{seq_diagram}

{data_structs}

{method_breakdown}

## 5. Source Code Citations & Index
{citations}
"""
    return markdown

def generate_base_structure(target_dir):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Architecture Overview
    arch_dir = Path(target_dir) / "architecture"
    arch_dir.mkdir(parents=True, exist_ok=True)
    with open(arch_dir / "iso_42010_overview.md", 'w', encoding='utf-8') as f:
        f.write(f"""---
iso_doc_type: "Description"
iso_viewpoint: "ArchitectureDescription"
type: "architecture"
title: "ISO/IEC/IEEE 42010 Architecture Description"
description: "Master architecture description artifact defining stakeholders, viewpoints, and system views."
tags: ["iso42010", "architecture", "okf"]
timestamp: "{timestamp}"
---

# ISO/IEC/IEEE 42010 Architecture Description

## 1. Entity of Interest (EoI) & Identification
* **System Name:** rust-agent-team
* **Target Environment:** Linux / Windows / MacOS
* **Primary Source Repository:** `.`

## 2. Stakeholder Perspectives & Concerns Matrix
| Stakeholder Persona | Primary Concerns | Framing ISO Viewpoint | Governed Wiki Page |
| :--- | :--- | :--- | :--- |
| **System Architect** | System modularity, extensibility, dependency boundaries | Component View | [Architecture/ComponentStructure](./component_structure.md) |
| **Security Officer** | Auth token validation, encryption, blast radius | Security View | [Architecture/SecurityView](./security_view.md) |
| **Lead Developer** | Execution flows, function contracts, error states | Sequence View | [Architecture/RuntimeSequences](./runtime_sequences.md) |
| **DevOps Lead** | Deployment environment, dependencies, CLI hooks | Deployment View | [Architecture/DeploymentView](./deployment_view.md) |

## 3. Viewpoints Framework & Index
- 🌐 [Architecture/SystemContext](./system_context.md) — Context View & External Boundaries.
- 📦 [Architecture/ComponentStructure](./component_structure.md) — Component View & UML 2.0 Class Diagrams.
- 🔄 [Architecture/RuntimeSequences](./runtime_sequences.md) — Sequence View & Interaction Diagrams.
- 🔐 [Architecture/SecurityView](./security_view.md) — Security View & Data Protection Rules.
- 📝 [Architecture/ADR/ADR_001_AST_Engine](./adr/adr_001_ast_engine.md) — Architecture Decision Records.
""")

    # Other basic architecture files
    for view in ["system_context", "component_structure", "runtime_sequences", "deployment_view", "security_view"]:
        with open(arch_dir / f"{view}.md", 'w', encoding='utf-8') as f:
            f.write(f"""---
iso_doc_type: "Description"
iso_viewpoint: "ArchitectureDescription"
type: "architecture"
title: "{view.replace('_', ' ').title()}"
description: "Architecture view for {view}"
tags: ["iso42010", "architecture", "okf"]
timestamp: "{timestamp}"
---

# {view.replace('_', ' ').title()}

Placeholder for architecture view.
""")

    adr_dir = arch_dir / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    with open(adr_dir / "adr_001_ast_engine.md", 'w', encoding='utf-8') as f:
        f.write(f"""---
iso_doc_type: "Description"
iso_viewpoint: "ArchitectureDecision"
type: "adr"
title: "ADR 001: Local AST Parsing Over Heavy External LLM Databases"
description: "Decision record documenting choice of local Graphify/Pyreverse AST scripts over complex external LLM search servers."
tags: ["adr", "iso42010", "decision"]
timestamp: "{timestamp}"
---

# Architecture Decision Record (ADR 001)

## 1. Status
**ACCEPTED**
""")

    # Specifications
    spec_dir = Path(target_dir) / "specifications"
    spec_dir.mkdir(parents=True, exist_ok=True)
    for spec in ["srs_requirements", "api_contracts"]:
        with open(spec_dir / f"{spec}.md", 'w', encoding='utf-8') as f:
            f.write(f"""---
iso_doc_type: "Specification"
iso_viewpoint: "ComponentView"
type: "specification"
title: "{spec.replace('_', ' ').title()}"
description: "Specification doc"
tags: ["iso15289", "specification", "okf"]
timestamp: "{timestamp}"
---

# {spec.replace('_', ' ').title()}

Placeholder for specification.
""")

    # Quality
    qual_dir = Path(target_dir) / "quality"
    qual_dir.mkdir(parents=True, exist_ok=True)
    with open(qual_dir / "iso_25010_quality.md", 'w', encoding='utf-8') as f:
        f.write(f"""---
iso_doc_type: "Report"
iso_viewpoint: "QualityView"
type: "quality"
title: "ISO/IEC 25010 Software Quality Assessment"
description: "Evaluation of system quality characteristics against international SQuaRE standards."
tags: ["iso25010", "quality", "square"]
timestamp: "{timestamp}"
---

# ISO/IEC 25010 Software Quality Assessment

Placeholder matrix.
""")

    # User guides
    ug_dir = Path(target_dir) / "user_guides"
    ug_dir.mkdir(parents=True, exist_ok=True)
    with open(ug_dir / "developer_guide.md", 'w', encoding='utf-8') as f:
        f.write(f"""---
iso_doc_type: "Procedure"
iso_viewpoint: "DevelopmentView"
type: "user_guide"
title: "Developer Guide"
description: "Guide for developers"
tags: ["iso26514", "guide", "okf"]
timestamp: "{timestamp}"
---

# Developer Guide

Placeholder for guide.
""")

    # Create other required directories
    for d in ["api", "classes", "diagrams", "dependencies", "glossary", "decisions", "generated"]:
        (Path(target_dir) / d).mkdir(parents=True, exist_ok=True)


def generate_index_and_logs(target_dir, files_processed, commit_hash):
    index_path = Path(target_dir) / "index.md"
    logs_path = Path(target_dir) / "logs.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate Index
    index_content = f"""---
iso_doc_type: "Description"
iso_viewpoint: "ContextView"
type: "index"
title: "Master Knowledge Hub & Navigation Map"
description: "Root index for openwiki documentation"
tags: ["iso15289", "index", "okf"]
timestamp: "{timestamp}"
---

# OpenWiki Technical Index

## ISO Documentation

- [Architecture Overview](./architecture/iso_42010_overview.md)
- [Quality Assessment](./quality/iso_25010_quality.md)
- [Developer Guide](./user_guides/developer_guide.md)

## Modules

"""
    for src, dst, _ in sorted(files_processed, key=lambda x: x[1]):
        rel_dst = dst.relative_to(target_dir)
        index_content += f"- [{src.name}](./{rel_dst.as_posix()}) (Source: `{src.as_posix()}`)\n"

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    # Generate SUMMARY.md
    summary_path = Path(target_dir) / "SUMMARY.md"
    summary_content = "# SUMMARY\n\n## Navigation\n\n## Table of contents\n\n## Architecture overview\n\n## Module list\n"
    for src, dst, _ in sorted(files_processed, key=lambda x: x[1]):
        rel_dst = dst.relative_to(target_dir)
        summary_content += f"- [{src.name}](./{rel_dst.as_posix()})\n"
    summary_content += "\n## Alphabetical class index\n\n"

    # Collect classes and methods from all ASTs to generate indexes
    all_classes = []
    all_methods = []
    for src, dst, _ in files_processed:
        ast_data = parse_rust_file(src)
        rel_dst = dst.relative_to(target_dir)
        link = f"./{rel_dst.as_posix()}"

        for class_name, class_info in ast_data["classes"].items():
            all_classes.append((class_name, class_info["type"], link))

        for method_info in ast_data["methods"]:
            if method_info["is_pub"] == "+":
                all_methods.append((method_info["name"], method_info["struct"], link))

    all_classes.sort(key=lambda x: x[0].lower())
    for class_name, type_str, link in all_classes:
        clean_type = type_str.replace("<<", "").replace(">>", "")
        if clean_type == "class":
            clean_type = "struct"
        summary_content += f"- [{class_name} ({clean_type})]({link})\n"

    summary_content += "\n## Public API index\n\n"
    all_methods.sort(key=lambda x: x[0].lower())
    for method_name, struct_name, link in all_methods:
        if struct_name:
            display_name = f"{struct_name}::{method_name}"
        else:
            display_name = method_name
        summary_content += f"- [{display_name}]({link})\n"

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)

    # Generate/Append Changelog

    log_entry = f"""---
iso_doc_type: "Report"
iso_viewpoint: "History"
type: "log"
title: "Incremental Audit Log & Git Diff History"
description: "Log of documentation generation"
tags: ["iso15289", "log", "okf"]
timestamp: "{timestamp}"
---

## Update: {timestamp}

- Synchronized `{len(files_processed)}` files from source code to OpenWiki structure.
- Commit hash: `{commit_hash}`

"""

    if logs_path.exists():
        with open(logs_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## Update: {timestamp}\n- Synchronized `{len(files_processed)}` files.\n- Commit hash: `{commit_hash}`\n")
    else:
        with open(logs_path, 'w', encoding='utf-8') as f:
            f.write("# OpenWiki Changelog\n\n" + log_entry)

def main():
    parser = argparse.ArgumentParser(description="AST Documentation Generator")
    parser.add_argument("--mode", choices=["full", "diff"], default="full", help="Execution mode: full or diff")
    args = parser.parse_args()

    target_dir = "openwiki"

    if args.mode == "full":
        shutil.rmtree(target_dir, ignore_errors=True)

    Path(target_dir).mkdir(parents=True, exist_ok=True)
    commit_hash = get_git_commit()

    generate_base_structure(target_dir)

    all_files = mirror_directory("src", target_dir)

    files_to_process = []
    if args.mode == "diff":
        try:
            changed_files_raw = subprocess.check_output(["git", "diff", "--name-only", "origin/main...HEAD"]).decode("utf-8").splitlines()
        except Exception:
            try:
                changed_files_raw = subprocess.check_output(["git", "show", "--name-only", "--format="]).decode("utf-8").splitlines()
            except Exception:
                changed_files_raw = []

        changed_rs = {f for f in changed_files_raw if f.endswith(".rs")}

        for src, dst, rel_root in all_files:
            if src.as_posix() in changed_rs:
                files_to_process.append((src, dst, rel_root))
    else:
        files_to_process = all_files

    print(f"Discovered {len(files_to_process)} files to process in {args.mode} mode.")

    for src, dst, rel_root in files_to_process:
        ast = parse_rust_file(src)
        md = generate_okf_markdown(src, rel_root, ast, commit_hash)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(md)

    if args.mode == "full":
        generate_index_and_logs(target_dir, files_to_process, commit_hash)
    else:
        generate_index_and_logs(target_dir, all_files, commit_hash)

    print(f"Generated index and changelog in {target_dir}")

if __name__ == "__main__":
    main()
