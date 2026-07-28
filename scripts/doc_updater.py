import sys
import os
import re
import subprocess
from pathlib import Path

def get_git_commit(filepath):
    try:
        res = subprocess.run(["git", "log", "-n", "1", "--format=%h", "--", filepath], capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        if out: return out
        res2 = subprocess.run(["git", "log", "-n", "1", "--format=%h"], capture_output=True, text=True, check=True)
        return res2.stdout.strip()
    except Exception:
        return "unknown"

def generate_doc_filename(filepath):
    base = os.path.splitext(filepath)[0]
    return base.replace("/", "-") + ".md"

def parse_dependencies(filepath):
    dependencies = []
    if not os.path.exists(filepath):
        return dependencies
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("use "):
                dep = line.replace("use ", "").rstrip(";")
                dependencies.append(dep)
            elif line.startswith("mod "):
                dep = line.replace("mod ", "").rstrip(";")
                dependencies.append(f"mod {dep}")
    return sorted(list(set(dependencies)))

def generate_mermaid_ast(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return "classDiagram\n    class Component {\n    }\n"

    classes = {}

    # structs
    struct_pattern = re.compile(r'struct\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*\{([^}]*)\}', re.MULTILINE)
    for m in struct_pattern.finditer(content):
        name = m.group(1)
        fields_str = m.group(2)
        fields = []
        for line in fields_str.split('\n'):
            line = line.strip().split('//')[0]
            if ':' in line:
                parts = line.split(':', 1)
                fname = parts[0].replace('pub ', '').strip()
                ftype = parts[1].split(',')[0].strip().replace("<", "~").replace(">", "~").replace(" ", "_")
                fields.append(f"+{ftype} {fname}")
        classes[name] = {"type": "class", "fields": fields, "methods": []}

    # enums
    enum_pattern = re.compile(r'enum\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*\{([^}]*)\}', re.MULTILINE)
    for m in enum_pattern.finditer(content):
        name = m.group(1)
        fields_str = m.group(2)
        fields = []
        for line in fields_str.split('\n'):
            line = line.strip().split('//')[0]
            if line and not line.startswith('#'):
                v = line.split(',')[0].strip().split('(')[0].split('{')[0].strip()
                if v:
                    fields.append(v)
        classes[name] = {"type": "<<enumeration>>", "fields": fields, "methods": []}

    # very rough functions
    fn_pattern = re.compile(r'(pub\s+)?(async\s+)?fn\s+([A-Za-z0-9_]+)\s*\((.*?)\)', re.MULTILINE)
    functions = []
    for m in fn_pattern.finditer(content):
        fname = m.group(3)
        args = m.group(4)
        is_pub = "+" if m.group(1) else "-"
        functions.append(f"{is_pub}{fname}()")

    if not classes:
        # If no struct/enum, maybe just a module class with functions
        mod_name = os.path.basename(filepath).split('.')[0].capitalize()
        if mod_name == "Mod":
            mod_name = os.path.basename(os.path.dirname(filepath)).capitalize() + "Module"
        classes[mod_name] = {"type": "<<module>>", "fields": [], "methods": functions}

    mermaid = "classDiagram\n"
    for name, data in classes.items():
        mermaid += f"    class {name} {{\n"
        if data["type"] == "<<enumeration>>" or data["type"] == "<<module>>":
            mermaid += f"        {data['type']}\n"
        for f in data["fields"]:
            mermaid += f"        {f}\n"
        for m in data["methods"]:
            mermaid += f"        {m}\n"
        mermaid += "    }\n"

    if not classes:
        return "classDiagram\n    class Module {\n    }\n"
    return mermaid

def update_or_create_doc(filepath, doc_path, commit):
    if not os.path.exists(filepath):
        # file was deleted, prune doc
        if os.path.exists(doc_path):
            os.remove(doc_path)
            return "deleted"
        return "ignored"

    dependencies = parse_dependencies(filepath)
    dep_text = "## Dependencies\n" + "\n".join([f"- `{dep}`" for dep in dependencies]) if dependencies else "## Dependencies\n- None"

    if os.path.exists(doc_path):
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        old_commit = ""
        m = re.search(r'last_verified_commit:\s*"(.*?)"', content)
        if m:
            old_commit = m.group(1)

        # Update dependencies, being careful not to overwrite the rest of the file
        # We replace the dependency section by looking for the next markdown header or end of file
        dep_section_pattern = re.compile(r'(## Dependencies\n.*?)(?=\n## |$)', re.DOTALL)
        if dep_section_pattern.search(content):
            content = dep_section_pattern.sub(dep_text, content)
        else:
            content += "\n\n" + dep_text

        # Update mermaid ast only if it was using default
        if "```mermaid\nclassDiagram\n    class " in content and "classDiagram\n    class Module" in content:
            mermaid_ast = generate_mermaid_ast(filepath)
            content = re.sub(r'```mermaid\nclassDiagram.*?\n```', f'```mermaid\n{mermaid_ast}```', content, flags=re.DOTALL)

        if old_commit != commit:
            content = re.sub(r'last_verified_commit:\s*".*?"', f'last_verified_commit: "{commit}"', content)

        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return "updated"
    else:
        title = os.path.basename(filepath).split('.')[0].capitalize()
        if title == "Mod":
            title = os.path.basename(os.path.dirname(filepath)).capitalize() + "Module"

        mermaid_ast = generate_mermaid_ast(filepath)

        template = f"""---
type: module
title: "{title}"
source_path: "{filepath}"
description: "Documentation for {filepath}."
tags: [module, rust]
last_verified_commit: "{commit}"
---
Source File: `{filepath}`

## Component Overview

This module defines the `{title}` component.

## Architecture

### Class Diagram
```mermaid
{mermaid_ast}```

### Execution Flow
```mermaid
flowchart TD
    Start --> End
```

{dep_text}
"""
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(template)
        return "created"

def get_original_extension(doc):
    # Try to find what file generated this doc by looking at the source_path in the file
    doc_path = os.path.join(".knowledge", doc)
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("source_path:"):
                    return line.split('"')[1]
    except:
        pass
    # Fallback heuristic
    return doc.replace("-", "/").replace(".md", ".rs")

def update_index():
    index_path = ".knowledge/index.md"
    docs = sorted([d for d in os.listdir(".knowledge") if d.endswith(".md") and d != "index.md"])

    lines = [
        "# Knowledge Base\n\n",
        "Table of Contents:\n\n"
    ]

    for doc in docs:
        filepath = get_original_extension(doc)
        lines.append(f"- [[{doc}]] - `{filepath}`\n")

    with open(index_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    if len(sys.argv) < 2:
        return

    changed_files = sys.argv[1:]

    if not os.path.exists(".knowledge"):
        os.makedirs(".knowledge")

    summary = []

    for filepath in changed_files:
        if not (filepath.startswith("src/") or filepath.startswith("code/")):
            continue

        commit = get_git_commit(filepath)
        doc_filename = generate_doc_filename(filepath)
        doc_path = os.path.join(".knowledge", doc_filename)

        status = update_or_create_doc(filepath, doc_path, commit)
        summary.append(f"{filepath} -> {doc_path} ({status})")

    update_index()

    print("Documentation Update Summary:")
    for s in summary:
        print(s)

if __name__ == "__main__":
    main()
