from pathlib import Path
import shutil
import sys

root = Path.cwd()
copier_dir = root / ".copier"
git_platform = sys.argv[1] if len(sys.argv) > 1 else "github"

for f in ["README.md", "pyproject.toml", ".env", "config.yaml"]:
    src = copier_dir / f
    dst = root / f
    if src.exists():
        dst.unlink(missing_ok=True)
        shutil.move(src, dst)

if git_platform == "gitlab":
    shutil.rmtree(root / ".github", ignore_errors=True)
else:
    shutil.rmtree(root / ".gitlab", ignore_errors=True)
