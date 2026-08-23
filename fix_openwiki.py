import sys
with open("generate_openwiki.py", "r") as f:
    content = f.read()

content = content.replace(
"""    summary_content += "\\n## Alphabetical class index\\n\\n## Public API index\\n\"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)""",
"""    summary_content += "\\n## Alphabetical class index\\n\\n"

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
        summary_content += f"- [{class_name} ({clean_type})]({link})\\n"

    summary_content += "\\n## Public API index\\n\\n"
    all_methods.sort(key=lambda x: x[0].lower())
    for method_name, struct_name, link in all_methods:
        if struct_name:
            display_name = f"{struct_name}::{method_name}"
        else:
            display_name = method_name
        summary_content += f"- [{display_name}]({link})\\n"

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)"""
)

with open("generate_openwiki.py", "w") as f:
    f.write(content)
