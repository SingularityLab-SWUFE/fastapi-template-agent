from pathlib import Path
import shutil

root = Path.cwd()
copier_dir = root / ".copier"

for f in ["README.md", "pyproject.toml", ".env"]:
    src = copier_dir / f
    dst = root / f
    if src.exists():
        dst.unlink(missing_ok=True)
        shutil.move(src, dst)
