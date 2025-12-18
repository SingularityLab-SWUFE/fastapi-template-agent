from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _normalized_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if not data.endswith(b"\n"):
        data += b"\n"
    return data


def _targets(root: Path) -> list[Path]:
    return [
        root / "CLAUDE.md",
        root / ".clinerules",
        root / ".cursorrules",
        root / ".github" / "copilot-instructions.md",
    ]


def _sync() -> int:
    root = _repo_root()
    source = root / "AGENTS.md"
    source_data = _normalized_bytes(source)

    for target in _targets(root):
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or _normalized_bytes(target) != source_data:
            target.write_bytes(source_data)

    return 0


def _check() -> int:
    root = _repo_root()
    source = root / "AGENTS.md"
    source_data = _normalized_bytes(source)

    bad = [
        str(target.relative_to(root))
        for target in _targets(root)
        if not target.exists() or _normalized_bytes(target) != source_data
    ]

    if bad:
        sys.stderr.write("agent rules not synced:\\n")
        sys.stderr.write("\\n".join(bad) + "\\n")
        return 1

    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "sync":
        return _sync()
    if len(argv) == 2 and argv[1] == "check":
        return _check()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
