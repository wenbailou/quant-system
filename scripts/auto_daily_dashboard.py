"""一键生成决策仪表盘并推送到 GitHub Pages。

供每日定时任务调用：生成 → 导出 HTML → 推送部署。
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="生成并推送每日决策仪表盘")
    parser.add_argument("--skip-walkforward", action="store_true",
                        help="跳过耗时的 walk-forward 回测")
    parser.add_argument("--html", default=None, help="HTML 输出路径")
    args = parser.parse_args()

    py = sys.executable
    html = args.html or "reports/dashboard_latest.html"

    # 1. 生成仪表盘（含 HTML）
    gen = subprocess.run(
        [py, str(REPO / "scripts" / "run_daily_decision.py"),
         "--skip-walkforward", "--html", html],
        cwd=REPO, capture_output=True, text=True,
    )
    print(gen.stdout)
    if gen.returncode != 0:
        print(gen.stderr)
        print("✗ 生成失败")
        return 1

    # 2. 推送部署
    deploy = subprocess.run(
        [py, str(REPO / "scripts" / "deploy_gh_pages.py"), "--source",
         str(REPO / html)],
        cwd=REPO, capture_output=True, text=True,
    )
    print(deploy.stdout)
    if deploy.returncode != 0:
        print(deploy.stderr)
        print("✗ 推送失败")
        return 1

    print("✓ 每日看盘任务完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())