from metadata_utils import load_algorithm_metadata

def generate_markdown_table():
    metadata = load_algorithm_metadata()
    rows = [
        "| Name | Type | Description | Supports Online | Parameters |",
        "|------|------|-------------|------------------|------------|"
    ]
    for name, info in metadata.items():
        params = ', '.join(info.get("parameters", {}).keys())
        row = f"| {name} | {info['type']} | {info['description']} | {info['supports_online']} | {params} |"
        rows.append(row)
    return "\n".join(rows)

if __name__ == "__main__":
    print(generate_markdown_table())
