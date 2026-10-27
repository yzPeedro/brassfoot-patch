"""Publish the current static site to the configured gh-pages branch."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, encoding="utf-8").strip()


def main():
    git("fetch", "origin", "gh-pages")
    with tempfile.TemporaryDirectory(prefix="brasfoot-pages-") as temporary:
        checkout = Path(temporary).resolve() / "site"
        git("worktree", "add", "--detach", str(checkout), "origin/gh-pages")
        try:
            for path in checkout.iterdir():
                if path.name == ".git":
                    continue
                if path.is_symlink():
                    path.unlink()
                elif path.resolve().parent != checkout.resolve():
                    raise ValueError("unexpected publication path")
                elif path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            shutil.copytree(ROOT / "site", checkout, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("tests", "*.test.js"))
            git("add", "-A", cwd=checkout)
            if git("status", "--porcelain", cwd=checkout):
                git("commit", "-m", "publish: Brasfoot Mega Patch website [skip ci]", cwd=checkout)
                git("push", "origin", "HEAD:gh-pages", cwd=checkout)
            print("Published gh-pages commit " + git("rev-parse", "HEAD", cwd=checkout))
        finally:
            git("worktree", "remove", str(checkout))
    # A branch push made by GitHub Actions needs an explicit Pages build request.
    subprocess.run(["gh", "api", "--method", "POST", "repos/yzPeedro/brassfoot-patch/pages/builds"], check=True)


if __name__ == "__main__":
    main()
