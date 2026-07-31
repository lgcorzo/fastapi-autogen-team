import os
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone

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

def extract_body(content, start_idx):
    brace_count = 0
    in_string = False
    in_char = False
    escape = False
    i = start_idx
    body_start = -1

    while i < len(content):
        c = content[i]
        if escape:
            escape = False
            i += 1
            continue
        if c == '\\':
            escape = True
        elif c == '"' and not in_char:
            in_string = not in_string
        elif c == "'" and not in_string:
            in_char = not in_char
        elif not in_string and not in_char:
            if c == '{':
                if brace_count == 0:
                    body_start = i + 1
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0 and body_start != -1:
                    return content[body_start:i]
        i += 1
    return ""

def parse_rust_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    classes = {}
    methods = []
    dependencies = []
    relations = []

    content_no_comments = re.sub(r'//.*', '', content)
    content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)

    for line in content_no_comments.split('\n'):
        line = line.strip()
        if line.startswith('use '):
            dep = line.replace('use ', '').rstrip(';')
            dependencies.append(dep)
        elif line.startswith('mod '):
            dep = line.replace('mod ', '').rstrip(';')
            dependencies.append(f"mod {dep}")

    # Extract Structs
    struct_pattern = re.compile(r'(?:pub\s+)?(?:pub\([^)]+\)\s+)?struct\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*(?:\{([^}]*)\}|\(([^)]*)\);)', re.MULTILINE)
    for m in struct_pattern.finditer(content_no_comments):
        name = m.group(1)
        fields_str = m.group(2) if m.group(2) else (m.group(3) if m.group(3) else "")
        line_num = content_no_comments[:m.start()].count('\n') + 1

        fields = []
        raw_fields = []
        if fields_str:
            for field_line in fields_str.split(',' if m.group(3) else '\n'):
                field_line = field_line.strip()
                if not field_line or field_line.startswith('#'): continue
                if ':' in field_line:
                    parts = field_line.split(':', 1)
                    fname = parts[0].replace('pub ', '').replace('pub(crate) ', '').strip()
                    ftype = parts[1].strip()
                    clean_ftype = ftype.replace("<", "~").replace(">", "~").replace(" ", "_")
                    fields.append(f"+{clean_ftype} {fname}")
                    raw_fields.append((fname, ftype))

                    rel_type = re.sub(r'[^a-zA-Z0-9_]', '', ftype.split('<')[0])
                    if rel_type and rel_type[0].isupper() and rel_type != name:
                        relations.append(f"{name} --> {rel_type} : Association")
                elif m.group(3):
                    ftype = field_line.strip()
                    clean_ftype = ftype.replace("<", "~").replace(">", "~").replace(" ", "_")
                    fields.append(f"+{clean_ftype}")
                    raw_fields.append(("", ftype))

                    rel_type = re.sub(r'[^a-zA-Z0-9_]', '', ftype.split('<')[0])
                    if rel_type and rel_type[0].isupper() and rel_type != name:
                        relations.append(f"{name} --> {rel_type} : Association")

        classes[name] = {"type": "class", "fields": fields, "raw_fields": raw_fields, "methods": [], "line": line_num}

    # Extract Enums
    enum_pattern = re.compile(r'(?:pub\s+)?(?:pub\([^)]+\)\s+)?enum\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*\{([^}]*)\}', re.MULTILINE)
    for m in enum_pattern.finditer(content_no_comments):
        name = m.group(1)
        fields_str = m.group(2)
        line_num = content_no_comments[:m.start()].count('\n') + 1

        fields = []
        raw_fields = []
        for line in fields_str.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                v = line.split(',')[0].strip().split('(')[0].split('{')[0].strip()
                if v:
                    fields.append(v)
                    raw_fields.append((v, "variant"))
        classes[name] = {"type": "<<enumeration>>", "fields": fields, "raw_fields": raw_fields, "methods": [], "line": line_num}

    # Extract Traits
    trait_pattern = re.compile(r'(?:pub\s+)?(?:pub\([^)]+\)\s+)?trait\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*\{([^}]*)\}', re.MULTILINE)
    for m in trait_pattern.finditer(content_no_comments):
        name = m.group(1)
        methods_str = m.group(2)
        line_num = content_no_comments[:m.start()].count('\n') + 1

        trait_methods = []
        fn_pattern_trait = re.compile(r'(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\((.*?)\)(?:\s*->\s*([^;{]+))?')
        for fm in fn_pattern_trait.finditer(methods_str):
            fname = fm.group(1)
            params = fm.group(2)
            ret_type = fm.group(3).strip() if fm.group(3) else "()"
            trait_methods.append(f"+{fname}()")
            methods.append({
                "name": fname,
                "struct": name,
                "line": line_num,
                "calls": [],
                "params": params,
                "ret_type": ret_type,
                "is_pub": "+"
            })

        classes[name] = {"type": "<<interface>>", "fields": [], "raw_fields": [], "methods": trait_methods, "line": line_num}

    # Extract Impls and Methods
    impl_pattern = re.compile(r'impl\s+(?:<[^>]*>\s+)?([A-Za-z0-9_:]+)(?:\s+for\s+([A-Za-z0-9_<>]+))?\s*\{', re.MULTILINE)
    for m in impl_pattern.finditer(content_no_comments):
        trait_name = m.group(1) if m.group(2) else None
        struct_name = m.group(2).split('<')[0] if m.group(2) else m.group(1)

        impl_body = extract_body(content_no_comments, m.end() - 1)

        if trait_name and trait_name != struct_name:
            clean_trait = trait_name.split('::')[-1]
            relations.append(f"{clean_trait} <|.. {struct_name} : Realization")

        fn_pattern = re.compile(r'(pub\s+)?(?:pub\([^)]+\)\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\((.*?)\)(?:\s*->\s*([^{]+))?\s*\{')
        for fm in fn_pattern.finditer(impl_body):
            fname = fm.group(2)
            is_pub = "+" if fm.group(1) else "-"
            method_sig = f"{is_pub}{fname}()"
            params = fm.group(3)
            ret_type = fm.group(4).strip() if fm.group(4) else "()"

            # extract inner calls
            fn_body = extract_body(impl_body, fm.end() - 1)
            calls = []
            # Find obj.method() or function()
            call_pattern = re.compile(r'\b([A-Za-z0-9_]+)\s*\(')
            for cm in call_pattern.finditer(fn_body):
                cname = cm.group(1)
                if cname not in ['if', 'while', 'for', 'match', 'Some', 'Ok', 'Err', 'String', 'Vec', 'Box', 'format', 'println', 'tracing', 'info', 'debug', 'error', 'warn', 'panic']:
                    calls.append(cname)

            if struct_name in classes:
                classes[struct_name]["methods"].append(method_sig)
            elif not trait_name:
                classes[struct_name] = {"type": "class", "fields": [], "raw_fields": [], "methods": [method_sig], "line": content_no_comments[:m.start()].count('\n') + 1}

            methods.append({"name": fname, "struct": struct_name, "line": content_no_comments[:m.start() + fm.start()].count('\n') + 1, "calls": calls, "params": params, "ret_type": ret_type, "is_pub": is_pub})

    # Global functions
    fn_pattern_global = re.compile(r'^(?:pub\s+)?(?:pub\([^)]+\)\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\((.*?)\)(?:\s*->\s*([^{]+))?\s*\{', re.MULTILINE)
    for m in fn_pattern_global.finditer(content_no_comments):
        fname = m.group(1)
        params = m.group(2)
        ret_type = m.group(3).strip() if m.group(3) else "()"

        fn_body = extract_body(content_no_comments, m.end() - 1)
        calls = []
        call_pattern = re.compile(r'\b([A-Za-z0-9_]+)\s*\(')
        for cm in call_pattern.finditer(fn_body):
            cname = cm.group(1)
            if cname not in ['if', 'while', 'for', 'match', 'Some', 'Ok', 'Err', 'String', 'Vec', 'Box', 'format', 'println', 'tracing', 'info', 'debug', 'error', 'warn', 'panic']:
                calls.append(cname)

        methods.append({"name": fname, "struct": None, "line": content_no_comments[:m.start()].count('\n') + 1, "calls": calls, "params": params, "ret_type": ret_type, "is_pub": "+"})

    if not classes:
        mod_name = filepath.name.split('.')[0].capitalize()
        if mod_name == "Mod":
            mod_name = filepath.parent.name.capitalize() + "Module"

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

def generate_mermaid_class_diagram(ast):
    mermaid = "```mermaid\nclassDiagram\n    direction BT\n"
    for name, data in ast["classes"].items():
        mermaid += f"    class {name} {{\n"
        if data["type"] != "class":
            mermaid += f"        {data['type']}\n"
        for f in data["fields"]:
            mermaid += f"        {f}\n"
        for m in data["methods"]:
            mermaid += f"        {m}\n"
        mermaid += "    }\n"
    for rel in ast["relations"]:
        mermaid += f"    {rel}\n"
    if not ast["classes"]:
        mermaid += "    class Module {\n        <<module>>\n    }\n"
    mermaid += "```\n"
    return mermaid

def generate_mermaid_sequence_diagram(ast):
    mermaid = "```mermaid\nsequenceDiagram\n    autonumber\n    participant Caller as Client Interface\n"
    if not ast["methods"]:
        return mermaid + "    Caller->>Svc: Invoke\n```\n"

    main_actor = list(ast["classes"].keys())[0] if ast["classes"] else "Svc"
    mermaid += f"    participant Svc as {main_actor}\n"

    for m in ast["methods"][:5]:  # limit to top 5 methods for clarity
        actor = m["struct"] if m["struct"] else main_actor
        mermaid += f"    Caller->>Svc: {m['name']}()\n"
        for call in m.get("calls", [])[:3]: # limit inner calls
             mermaid += f"    Svc->>Svc: {call}()\n"
        mermaid += f"    Svc-->>Caller: Returns execution status\n"

    mermaid += "```\n"
    return mermaid

def generate_okf_markdown(filepath, rel_dir, ast, commit_hash):
    title = filepath.name.split('.')[0].capitalize()
    if title == "Mod":
         title = filepath.parent.name.capitalize() + "Module"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    class_diagram = generate_mermaid_class_diagram(ast)
    seq_diagram = generate_mermaid_sequence_diagram(ast)

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
| **System Architect** | System modularity, extensibility, dependency boundaries | Component View | [[Architecture/ComponentStructure]] |
| **Security Officer** | Auth token validation, encryption, blast radius | Security View | [[Architecture/SecurityView]] |
| **Lead Developer** | Execution flows, function contracts, error states | Sequence View | [[Architecture/RuntimeSequences]] |
| **DevOps Lead** | Deployment environment, dependencies, CLI hooks | Deployment View | [[Architecture/DeploymentView]] |

## 3. Viewpoints Framework & Index
- 🌐 [[Architecture/SystemContext]] — Context View & External Boundaries.
- 📦 [[Architecture/ComponentStructure]] — Component View & UML 2.0 Class Diagrams.
- 🔄 [[Architecture/RuntimeSequences]] — Sequence View & Interaction Diagrams.
- 🔐 [[Architecture/SecurityView]] — Security View & Data Protection Rules.
- 📝 [[Architecture/ADR/ADR_001_AST_Engine]] — Architecture Decision Records.
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

- [[Architecture Overview|./architecture/iso_42010_overview.md]]
- [[Quality Assessment|./quality/iso_25010_quality.md]]
- [[Developer Guide|./user_guides/developer_guide.md]]

## Modules

"""
    for src, dst, _ in sorted(files_processed, key=lambda x: x[1]):
        rel_dst = dst.relative_to(target_dir)
        index_content += f"- [{src.name}](./{rel_dst.as_posix()}) (Source: `{src.as_posix()}`)\n"

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

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
    target_dir = "openwiki"
    Path(target_dir).mkdir(exist_ok=True)
    commit_hash = get_git_commit()

    generate_base_structure(target_dir)

    files = mirror_directory("src", target_dir)
    print(f"Discovered {len(files)} files to process.")

    for src, dst, rel_root in files:
        ast = parse_rust_file(src)
        md = generate_okf_markdown(src, rel_root, ast, commit_hash)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(md)

    generate_index_and_logs(target_dir, files, commit_hash)
    print(f"Generated index and changelog in {target_dir}")

if __name__ == "__main__":
    main()
