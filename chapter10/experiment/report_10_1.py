"""Render a credential-free report for the personal Experiment 10-1 runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULT_DIR = HERE / "output" / "10-1_multi-role-transfer"
IMAGE_DIR = HERE / "images" / "10-1_multi-role-transfer"
PROBE_FILE = RESULT_DIR / "comparison-coding-kimi-k3.json"
PRIMARY_FILE = RESULT_DIR / "comparison-coding-short-kimi-k3.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run_by_path(payload: dict, path: str) -> dict:
    return next(run for run in payload["runs"] if run["path"] == path)


def percent(value: float) -> str:
    return f"{value:.1%}"


def print_report(probe: dict, primary: dict) -> None:
    print("=" * 122)
    print("实验 10-1 个人成对报告：system-prompt Transfer vs Skill loading（model=kimi-k3）")
    print("=" * 122)
    print(f"首次探针 SHA-256: {sha256(PROBE_FILE)}")
    print(f"约束复测 SHA-256: {sha256(PRIMARY_FILE)}")
    print()
    print("主要结果：澄清最终成稿必须整体不超过 120 字符后，两条路径均通过")
    print("-" * 122)
    print(
        f"{'Path':<10}{'Pass':<7}{'Calls':>7}{'Input':>10}{'Cached':>10}"
        f"{'Uncached':>11}{'Cache%':>9}{'Prefixes':>10}{'Changes':>10}{'Chars':>8}"
    )
    print("-" * 122)
    for path in ("transfer", "skill"):
        run = run_by_path(primary, path)
        metrics = run["metrics"]
        print(
            f"{path:<10}{str(run['outcome']['pass']):<7}{metrics['api_calls']:>7}"
            f"{metrics['input_tokens']:>10,}{metrics['cached_input_tokens']:>10,}"
            f"{metrics['uncached_input_tokens']:>11,}{percent(metrics['cache_hit_rate']):>9}"
            f"{metrics['unique_static_prefixes']:>10}{metrics['prefix_changed_calls']:>10}"
            f"{run['outcome']['length']:>8}"
        )
    print("-" * 122)
    transfer = run_by_path(primary, "transfer")
    skill = run_by_path(primary, "skill")
    print(f"Transfer handoff: {transfer['handoff_chain']}")
    print(f"Skill loads:      {' -> '.join(skill['loaded_skills'])}")
    print(f"Transfer answer:  {transfer['outcome']['deliverable']}")
    print(f"Skill answer:     {skill['outcome']['deliverable']}")
    print()
    print("首次探针：核心机制成功，但两条路径都因完整成稿超过 120 字符而未通过")
    print("-" * 122)
    for path in ("transfer", "skill"):
        run = run_by_path(probe, path)
        dims = run["outcome"]["dimensions"]
        print(
            f"{path:<10} pass={run['outcome']['pass']} chars={run['outcome']['length']} "
            f"execution={dims['执行正确性']} constraint={dims['任务约束']} "
            f"audit={dims['可审计性']} sequence={dims['required_capability_sequence']}"
        )
    print()
    print("边界：elapsed_seconds 包含个人包装器的 21 秒请求间隔，不用于比较架构原生延迟。")
    print("边界：paired_n=1 只能验证机制并形成个案观察，不能推断总体优劣或统计显著性。")


def render_plots(probe: dict, primary: dict) -> None:
    mpl_config = Path(tempfile.gettempdir()) / "agentbook-matplotlib-cache"
    mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_config))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    paths = ["Transfer", "Skill"]
    runs = [run_by_path(primary, "transfer"), run_by_path(primary, "skill")]
    uncached = [run["metrics"]["uncached_input_tokens"] for run in runs]
    cached = [run["metrics"]["cached_input_tokens"] for run in runs]
    cache_rates = [run["metrics"]["cache_hit_rate"] for run in runs]
    unique_prefixes = [run["metrics"]["unique_static_prefixes"] for run in runs]
    prefix_changes = [run["metrics"]["prefix_changed_calls"] for run in runs]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    x = np.arange(2)
    axes[0].bar(x, uncached, color="#E07A5F", label="Uncached input")
    axes[0].bar(x, cached, bottom=uncached, color="#81B29A", label="Cached input")
    axes[0].set_xticks(x, paths)
    axes[0].set_ylabel("Prompt tokens")
    axes[0].set_title("Input-token composition")
    axes[0].legend(frameon=False)
    for i, run in enumerate(runs):
        total = run["metrics"]["input_tokens"]
        axes[0].text(i, total + 170, f"{total:,}\ncache {cache_rates[i]:.1%}", ha="center")

    width = 0.34
    axes[1].bar(x - width / 2, unique_prefixes, width, color="#3D405B", label="Unique prefixes")
    axes[1].bar(x + width / 2, prefix_changes, width, color="#F2CC8F", label="Prefix changes")
    axes[1].set_xticks(x, paths)
    axes[1].set_ylabel("Count")
    axes[1].set_title("Static-prefix stability")
    axes[1].set_ylim(0, max(unique_prefixes + prefix_changes) + 1)
    axes[1].legend(frameon=False)
    fig.suptitle("Experiment 10-1: successful paired run (kimi-k3)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "10-1-prefix-cache-comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    labels = ["Probe\nTransfer", "Probe\nSkill", "Clarified\nTransfer", "Clarified\nSkill"]
    lengths = [
        run_by_path(probe, "transfer")["outcome"]["length"],
        run_by_path(probe, "skill")["outcome"]["length"],
        run_by_path(primary, "transfer")["outcome"]["length"],
        run_by_path(primary, "skill")["outcome"]["length"],
    ]
    passed = [False, False, True, True]
    colors = ["#E07A5F" if not ok else "#81B29A" for ok in passed]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.bar(np.arange(4), lengths, color=colors)
    ax.axhline(120, color="#C1121F", linestyle="--", linewidth=1.5, label="120-character limit")
    ax.set_xticks(np.arange(4), labels)
    ax.set_ylabel("Scored deliverable length")
    ax.set_title("Constraint failure and controlled recovery", fontweight="bold")
    ax.legend(frameon=False)
    for bar, value, ok in zip(bars, lengths, passed):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 7, f"{value}\n{'PASS' if ok else 'FAIL'}", ha="center")
    ax.set_ylim(0, max(lengths) * 1.18)
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "10-1-constraint-recovery.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"plots saved to {IMAGE_DIR}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", action="store_true", help="生成两张脱敏对比图")
    args = parser.parse_args()
    missing = [str(path) for path in (PROBE_FILE, PRIMARY_FILE) if not path.is_file()]
    if missing:
        raise SystemExit("缺少结果文件：\n" + "\n".join(missing))
    probe = load(PROBE_FILE)
    primary = load(PRIMARY_FILE)
    print_report(probe, primary)
    if args.plot:
        render_plots(probe, primary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
