import os
import re
from pathlib import Path
from datetime import datetime, timezone

def mirror_directory(src_dir, target_dir):
    src_path = Path(src_dir)
    target_path = Path(target_dir)
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

                    rel_type = re.sub(r'[^a-zA-Z0-9_]', '', ftype.split('<')[0])
                    if rel_type and rel_type[0].isupper() and rel_type != name:
                        relations.append(f"{name} --> {rel_type} : Association")
                elif m.group(3):
                    ftype = field_line.strip()
                    clean_ftype = ftype.replace("<", "~").replace(">", "~").replace(" ", "_")
                    fields.append(f"+{clean_ftype}")

                    rel_type = re.sub(r'[^a-zA-Z0-9_]', '', ftype.split('<')[0])
                    if rel_type and rel_type[0].isupper() and rel_type != name:
                        relations.append(f"{name} --> {rel_type} : Association")

        classes[name] = {"type": "class", "fields": fields, "methods": [], "line": line_num}

    # Extract Enums
    enum_pattern = re.compile(r'(?:pub\s+)?(?:pub\([^)]+\)\s+)?enum\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*\{([^}]*)\}', re.MULTILINE)
    for m in enum_pattern.finditer(content_no_comments):
        name = m.group(1)
        fields_str = m.group(2)
        line_num = content_no_comments[:m.start()].count('\n') + 1

        fields = []
        for line in fields_str.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                v = line.split(',')[0].strip().split('(')[0].split('{')[0].strip()
                if v: fields.append(v)
        classes[name] = {"type": "<<enumeration>>", "fields": fields, "methods": [], "line": line_num}

    # Extract Traits
    trait_pattern = re.compile(r'(?:pub\s+)?(?:pub\([^)]+\)\s+)?trait\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*\{([^}]*)\}', re.MULTILINE)
    for m in trait_pattern.finditer(content_no_comments):
        name = m.group(1)
        methods_str = m.group(2)
        line_num = content_no_comments[:m.start()].count('\n') + 1

        trait_methods = []
        fn_pattern_trait = re.compile(r'(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\((.*?)\)')
        for fm in fn_pattern_trait.finditer(methods_str):
            trait_methods.append(f"+{fm.group(1)}()")

        classes[name] = {"type": "<<interface>>", "fields": [], "methods": trait_methods, "line": line_num}

    # Extract Impls and Methods
    impl_pattern = re.compile(r'impl\s+(?:<[^>]*>\s+)?([A-Za-z0-9_:]+)(?:\s+for\s+([A-Za-z0-9_<>]+))?\s*\{', re.MULTILINE)
    for m in impl_pattern.finditer(content_no_comments):
        trait_name = m.group(1) if m.group(2) else None
        struct_name = m.group(2).split('<')[0] if m.group(2) else m.group(1)

        impl_body = extract_body(content_no_comments, m.end() - 1)

        if trait_name and trait_name != struct_name:
            clean_trait = trait_name.split('::')[-1]
            relations.append(f"{clean_trait} <|.. {struct_name} : Realization")

        fn_pattern = re.compile(r'(pub\s+)?(?:pub\([^)]+\)\s+)?(async\s+)?fn\s+([A-Za-z0-9_]+)\s*\((.*?)\)')
        for fm in fn_pattern.finditer(impl_body):
            fname = fm.group(3)
            is_pub = "+" if fm.group(1) else "-"
            method_sig = f"{is_pub}{fname}()"

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
                classes[struct_name] = {"type": "class", "fields": [], "methods": [method_sig], "line": content_no_comments[:m.start()].count('\n') + 1}

            methods.append({"name": fname, "struct": struct_name, "line": content_no_comments[:m.start() + fm.start()].count('\n') + 1, "calls": calls})

    # Global functions
    fn_pattern_global = re.compile(r'^(?:pub\s+)?(?:pub\([^)]+\)\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\((.*?)\)', re.MULTILINE)
    for m in fn_pattern_global.finditer(content_no_comments):
        fname = m.group(1)
        fn_body = extract_body(content_no_comments, m.end() - 1)
        calls = []
        call_pattern = re.compile(r'\b([A-Za-z0-9_]+)\s*\(')
        for cm in call_pattern.finditer(fn_body):
            cname = cm.group(1)
            if cname not in ['if', 'while', 'for', 'match', 'Some', 'Ok', 'Err', 'String', 'Vec', 'Box', 'format', 'println', 'tracing', 'info', 'debug', 'error', 'warn', 'panic']:
                calls.append(cname)

        methods.append({"name": fname, "struct": None, "line": content_no_comments[:m.start()].count('\n') + 1, "calls": calls})

    if not classes:
        mod_name = filepath.name.split('.')[0].capitalize()
        if mod_name == "Mod":
            mod_name = filepath.parent.name.capitalize() + "Module"

        mod_methods = []
        for m in methods:
            if m["struct"] is None:
                mod_methods.append(f"+{m['name']}()")
        classes[mod_name] = {"type": "<<module>>", "fields": [], "methods": mod_methods, "line": 1}

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

def generate_okf_markdown(filepath, rel_dir, ast):
    title = filepath.name.split('.')[0].capitalize()
    if title == "Mod":
         title = filepath.parent.name.capitalize() + "Module"
    # Keep timestamp static for tests to avoid diff churn if not needed, but instructions say we should generate it.
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    class_diagram = generate_mermaid_class_diagram(ast)
    seq_diagram = generate_mermaid_sequence_diagram(ast)

    deps_list = "\n".join([f"- `{dep}`" for dep in ast["dependencies"]]) if ast["dependencies"] else "- None"

    citations = ""
    for name, data in ast["classes"].items():
         citations += f"* Class `{name}`: `{filepath.as_posix()}:{data['line']}`\n"
    for m in ast["methods"]:
         cls_str = f" in `{m['struct']}`" if m['struct'] else ""
         citations += f"* Method `{m['name']}`{cls_str}: `{filepath.as_posix()}:{m['line']}`\n"
    if not citations:
         citations = "* No direct classes or functions extracted."

    markdown = f"""---
type: "module-architecture"
title: "{title}"
description: "Technical architecture and class hierarchy for {title}"
tags: ["architecture", "uml", "pyreverse", "openwiki"]
timestamp: "{timestamp}"
---

# Module Name: {title}

* **Source Directory Reference:** `{rel_dir.as_posix()}/`
* **Package Dependency:**
{deps_list}

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `{title}` module extracted directly from the codebase.

## 2. UML 2.0 Class & Inheritance Architecture (Deterministic)
The following class diagram models the object-oriented structure, explicit inheritance hierarchies, and polymorphic interface implementations derived from local AST analysis:

{class_diagram}

## 3. Package & Class Relations

* **Inheritance & Polymorphism:** Detailed breakdown of abstract base classes, interfaces, and concrete overrides.
* **Dependencies:** How classes within this package collaborate externally.

## 4. Execution Flow & Runtime Behavior

The following sequence diagram outlines the execution lifecycle and message passing during core operations:

{seq_diagram}

---

* **Source Citations:**
{citations}
"""
    return markdown

def generate_index_and_logs(target_dir, files_processed):
    index_path = Path(target_dir) / "index.md"
    logs_path = Path(target_dir) / "logs.md"

    # Generate Index
    index_content = "# OpenWiki Technical Index\n\n## Modules\n\n"
    for src, dst, _ in sorted(files_processed, key=lambda x: x[1]):
        rel_dst = dst.relative_to(target_dir)
        index_content += f"- [{src.name}](./{rel_dst.as_posix()}) (Source: `{src.as_posix()}`)\n"

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    # Generate/Append Changelog
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = f"## Update: {timestamp}\n\n- Synchronized `{len(files_processed)}` files from source code to OpenWiki structure.\n\n"

    if logs_path.exists():
        with open(logs_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    else:
        with open(logs_path, 'w', encoding='utf-8') as f:
            f.write("# OpenWiki Changelog\n\n" + log_entry)

def main():
    target_dir = "openwiki"
    Path(target_dir).mkdir(exist_ok=True)

    files = mirror_directory("src", target_dir)
    print(f"Discovered {len(files)} files to process.")

    for src, dst, rel_root in files:
        ast = parse_rust_file(src)
        md = generate_okf_markdown(src, rel_root, ast)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(md)

    generate_index_and_logs(target_dir, files)
    print(f"Generated index and changelog in {target_dir}")

if __name__ == "__main__":
    main()
