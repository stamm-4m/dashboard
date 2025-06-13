import os
import yaml
import textwrap

metadata_path = os.path.join(os.path.dirname(__file__), "..", "algorithm_metadata.yaml")
output_md_path = os.path.join(os.path.dirname(__file__), "..", "drift_algorithms.md")

def generate_markdown_table() -> str:
    if not os.path.exists(metadata_path):
        return "No metadata available."

    with open(metadata_path, "r") as f:
        metadata = yaml.safe_load(f)

    rows = [
        "| Name | Type | Class | Description | Supports Online | Parameters |",
        "|------|------|--------|-------------|------------------|------------|"
    ]

    for name, info in metadata.items():
        algo_name = info.get("name", name)
        algo_type = info.get("type", "unknown")
        class_name = info.get("class", name)
        description = info.get("description", "No description provided").strip()
        short_desc = textwrap.shorten(description, width=100, placeholder="...")
        supports_online = str(info.get("supports_online", False)).lower()
        parameters = info.get("parameters", {})
        param_list = ', '.join(parameters.keys()) if parameters else ""

        row = f"| {algo_name} | {algo_type} | {class_name} | {short_desc} | {supports_online} | {param_list} |"
        rows.append(row)

    markdown = "\n".join(rows)

    # Write to .md file
    with open(output_md_path, "w") as f:
        f.write("# Drift Detection Algorithms\n\n")
        f.write(markdown)

    return markdown
