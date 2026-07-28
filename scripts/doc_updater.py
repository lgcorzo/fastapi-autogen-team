import os
import sys
import subprocess
import glob
import re

KNOWLEDGE_DIR = '.knowledge'
INDEX_FILE = os.path.join(KNOWLEDGE_DIR, 'index.md')

def get_last_commit():
    try:
        res = subprocess.run(["git", "log", "-n", "1", "--format=%H"], capture_output=True, text=True, check=True)
        return res.stdout.strip()[:7]
    except Exception:
        return "unknown"

def get_changed_files():
    try:
        res = subprocess.run(["git", "diff", "HEAD~1", "--name-only"], capture_output=True, text=True, check=True)
        files = res.stdout.splitlines()
        changed = [f for f in files if (f.startswith("src/") or f.startswith("code/")) and f.endswith(".rs")]
        return changed
    except Exception:
        try:
            res = subprocess.run(["git", "show", "--name-only", "--format="], capture_output=True, text=True, check=True)
            files = res.stdout.splitlines()
            changed = [f for f in files if (f.startswith("src/") or f.startswith("code/")) and f.endswith(".rs")]
            return changed
        except Exception as e2:
            print(f"Error getting changed files: {e2}")
            return []

def extract_rust_info(content):
    # More robust extraction avoiding matches in comments or strings.
    structs = re.findall(r'^[ \t]*(?:pub\s+)?struct\s+(\w+)', content, re.MULTILINE)
    enums = re.findall(r'^[ \t]*(?:pub\s+)?enum\s+(\w+)', content, re.MULTILINE)
    funcs = re.findall(r'^[ \t]*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*\(', content, re.MULTILINE)

    # Only match uses that start on a new line
    imports = re.findall(r'^[ \t]*use\s+([a-zA-Z0-9_:\*\{\}\s,]+);', content, re.MULTILINE)
    return structs, enums, funcs, imports

def generate_mermaid(structs, enums, funcs, filename, existing_content=None):
    # Check if there are existing diagrams
    existing_class_diagram = None
    existing_flowchart = None

    if existing_content:
        # Match classDiagram blocks
        class_match = re.search(r'```mermaid\s+classDiagram.*?```', existing_content, re.DOTALL)
        if class_match:
            existing_class_diagram = class_match.group(0)

        # Match sequenceDiagram or flowchart blocks
        flow_match = re.search(r'```mermaid\s+(?:sequenceDiagram|flowchart).*?```', existing_content, re.DOTALL)
        if flow_match:
            existing_flowchart = flow_match.group(0)

    # Generate default diagrams only if not existing
    class_diagram = ""
    if existing_class_diagram:
        class_diagram = existing_class_diagram
    else:
        class_diagram = "```mermaid\nclassDiagram\n"
        class_name = os.path.basename(filename).replace(".rs", "").capitalize()
        if class_name == "Mod":
            class_name = os.path.basename(os.path.dirname(filename)).capitalize() + "Mod"

        class_diagram += f"    class {class_name} {{\n"
        for f in funcs:
            class_diagram += f"        +{f}()\n"
        for s in structs:
            class_diagram += f"        +struct {s}\n"
        for e in enums:
            class_diagram += f"        +enum {e}\n"
        class_diagram += "    }\n```"

    flowchart = ""
    if existing_flowchart:
        flowchart = existing_flowchart
    else:
        flowchart = "```mermaid\nflowchart TD\n"
        class_name = os.path.basename(filename).replace(".rs", "").capitalize()
        if class_name == "Mod":
            class_name = os.path.basename(os.path.dirname(filename)).capitalize() + "Mod"
        flowchart += f"    Start --> {class_name}\n"
        flowchart += f"    {class_name} --> End\n```"

    return class_diagram, flowchart

def generate_okf(filepath, commit_hash):
    filename_slug = filepath.replace("/", "-").replace(".rs", ".md")
    okf_path = os.path.join(KNOWLEDGE_DIR, filename_slug)

    if not os.path.exists(filepath):
        print(f"File {filepath} no longer exists. Pruning {okf_path}.")
        if os.path.exists(okf_path):
            os.remove(okf_path)
        return None

    with open(filepath, 'r') as f:
        content = f.read()

    existing_content = None
    if os.path.exists(okf_path):
        with open(okf_path, 'r') as f:
            existing_content = f.read()

    structs, enums, funcs, imports = extract_rust_info(content)
    class_diagram, flowchart = generate_mermaid(structs, enums, funcs, filepath, existing_content)

    description = f"Documentation for {filepath}."
    if existing_content:
        m = re.search(r'^description:\s*"(.*?)"', existing_content, re.MULTILINE)
        if m:
            description = m.group(1)

    doc_type = "module" if filepath.endswith("mod.rs") else ("script" if "main.rs" in filepath or "bin/" in filepath else "class")
    title = os.path.basename(filepath).replace(".rs", "").capitalize()
    if title.lower() == "mod":
        title = os.path.basename(os.path.dirname(filepath)).capitalize() + " Module"

    deps_list = []
    for imp in imports:
        imp_clean = " ".join(imp.split())
        deps_list.append(f"- `{imp_clean}`")

    deps = "\n".join(deps_list)
    if not deps:
        deps = "None"

    okf_content = f"""---
type: {doc_type}
title: "{title}"
source_path: "{filepath}"
description: "{description}"
tags: [{doc_type}, rust]
last_verified_commit: "{commit_hash}"
---
Source File: `{filepath}`

## Component Overview

This module defines the {title} component.

## Architecture

### Class Diagram
{class_diagram}

### Execution Flow
{flowchart}

## Dependencies
{deps}
"""

    if existing_content:
        new_content = re.sub(r'^last_verified_commit:\s*".*?"', f'last_verified_commit: "{commit_hash}"', existing_content, flags=re.MULTILINE)

        if "## Dependencies" in new_content:
            new_content = re.sub(r'## Dependencies\n.*', f'## Dependencies\n{deps}\n', new_content, flags=re.DOTALL)

        return okf_path, new_content

    return okf_path, okf_content

def update_index():
    if not os.path.exists(INDEX_FILE):
        content = "# Knowledge Base\n\nTable of Contents:\n\n"
    else:
        with open(INDEX_FILE, 'r') as f:
            content = f.read()

    md_files = glob.glob(os.path.join(KNOWLEDGE_DIR, '*.md'))
    md_files = [f for f in md_files if os.path.basename(f) != 'index.md']
    md_files.sort()

    new_toc = []
    for f in md_files:
        filename = os.path.basename(f)
        source_path = ""
        with open(f, 'r') as mdf:
            mdf_content = mdf.read()
            match = re.search(r'^source_path:\s*"([^"]+)"', mdf_content, re.MULTILINE)
            if match:
                source_path = match.group(1)
            else:
                source_path = filename.replace('.md', '.rs').replace('-', '/')

        new_toc.append(f"- [[{filename}]] - `{source_path}`")

    toc_text = '\n'.join(new_toc)

    if "Table of Contents:" in content:
        new_content = re.sub(r'Table of Contents:\n+((?:- \[\[.*?\n)*)?', f"Table of Contents:\n\n{toc_text}\n\n", content, flags=re.MULTILINE)
    else:
        new_content = content + "\n\nTable of Contents:\n\n" + toc_text + "\n"

    with open(INDEX_FILE, 'w') as f:
        f.write(new_content)

def main():
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)

    commit_hash = get_last_commit()
    changed_files = get_changed_files()

    if not changed_files:
        print("No files changed in the last commit based on git show. We will only update index.md just in case.")

    updated = []
    for filepath in changed_files:
        res = generate_okf(filepath, commit_hash)
        if res:
            okf_path, content = res
            with open(okf_path, 'w') as f:
                f.write(content)
            updated.append(okf_path)
            print(f"Updated {okf_path}")

    if updated or not changed_files or any(not os.path.exists(f) for f in changed_files):
        update_index()
        print("Synchronized index.md")

    print(f"Total files updated: {len(updated)}")

if __name__ == "__main__":
    main()
