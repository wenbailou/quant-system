"""把最新生成的决策仪表盘推送到 GitHub Pages。

流程：
1. 读取 reports/dashboard_latest.html（由 run_daily_decision.py 生成）
2. 复制为 index.html，提交到 gh-pages 分支
3. 推送到远端 origin/gh-pages

使用临时 worktree，避免污染主工作区。
认证通过环境变量 GH_TOKEN 或已配置的 git 凭据。
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "reports" / "dashboard_latest.html"
REMOTE = "origin"
BRANCH = "gh-pages"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd or REPO, capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="推送决策仪表盘到 GitHub Pages")
    parser.add_argument("--source", default=str(SOURCE), help="仪表盘 HTML 源文件")
    args = parser.parse_args()

    src = Path(args.source)
    if not src.exists():
        print(f"✗ 未找到仪表盘文件：{src}")
        print("  请先运行：python scripts/run_daily_decision.py --skip-walkforward --html reports/dashboard_latest.html")
        return 1

    # 1. 确保远端 gh-pages 分支存在并同步
    run(["git", "fetch", REMOTE, BRANCH])

    # 2. 创建临时 worktree 检出 gh-pages
    with tempfile.TemporaryDirectory(prefix="ghpages_") as tmp:
        wt = Path(tmp)
        r = run(["git", "worktree", "add", str(wt), "--track", "-B", BRANCH, f"{REMOTE}/{BRANCH}"])
        if r.returncode != 0:
            # 可能远端分支不存在，用本地分支或新建
            r = run(["git", "worktree", "add", str(wt), BRANCH])
            if r.returncode != 0:
                print(f"✗ 无法检出 gh-pages worktree：{r.stderr.strip()}")
                return 1

        # 3. 复制最新的仪表盘为 index.html
        shutil.copy2(src, wt / "index.html")
        print("✓ 已复制仪表盘到 index.html")

        # 4. 提交
        r = run(["git", "add", "index.html"], cwd=wt)
        r = run(["git", "commit", "-m", "Update dashboard"], cwd=wt)
        if r.returncode != 0 and "nothing to commit" in r.stdout:
            print("✓ 无变化，无需提交")
        elif r.returncode != 0:
            print(f"✗ 提交失败：{r.stderr.strip()}")
            return 1
        else:
            print("✓ 已提交更新")

        # 5. 推送
        r = run(["git", "push", REMOTE, BRANCH], cwd=wt)
        if r.returncode != 0:
            print(f"✗ 推送失败：{r.stderr.strip()}")
            return 1
        print("✓ 已推送到 GitHub Pages")

    # 6. 清理 worktree
    run(["git", "worktree", "prune"])
    print("✓ 完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())