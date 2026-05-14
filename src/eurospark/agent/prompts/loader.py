import os

def load_md(filename: str) -> str:
    """Helper to read markdown files from the current directory."""
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, f"{filename}.md")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()