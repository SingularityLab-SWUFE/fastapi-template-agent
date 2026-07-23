import json
import re
import subprocess
from pathlib import Path


packages = json.loads(
    subprocess.check_output(["uv", "pip", "list", "--format", "json"], text=True)
)
versions = {package["name"]: package["version"] for package in packages}


def replace_version(match: re.Match[str]) -> str:
    version = versions.get(match["name"])
    return f"{match[1]}{version}" if version else match[0]


pyproject = Path("pyproject.toml")
pattern = r'(?m)^(\s*"(?P<name>[\w.-]+)(?:\[[^]]+\])?>=)[^"]+'
pyproject.write_text(re.sub(pattern, replace_version, pyproject.read_text()))
