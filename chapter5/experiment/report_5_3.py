"""Render a credential-free report for the personal Experiment 5-3 run."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULT_DIR = HERE / "output" / "5-3_code-for-math"
RESULT_FILES = [
    RESULT_DIR / "probe-p1-kimi-k3.json",
    RESULT_DIR / "result-p6-kimi-k3.json",
    RESULT_DIR / "result-p11-kimi-k3.json",
]


def load_row(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") or payload.get("results") or payload.get("problems")
    if not rows or len(rows) != 1:
        raise ValueError(f"expected exactly one row in {path}")
    row = dict(rows[0])
    row["_provider"] = payload.get("provider")
    row["_model"] = payload.get("model")
    row["_file"] = path.name
    return row


def token_total(receipts: list[dict]) -> int:
    return sum(int((item.get("usage") or {}).get("total_tokens") or 0) for item in receipts)


def finish_reason(row: dict, arm: str) -> str:
    receipts = ((row.get(f"{arm}_evidence") or {}).get("provider_receipts") or [])
    return str(receipts[-1].get("finish_reason") or "-") if receipts else "-"


def exact_p_value(cot_only: int, code_only: int) -> float:
    discordant = cot_only + code_only
    if not discordant:
        return 1.0
    tail = sum(math.comb(discordant, i) for i in range(min(cot_only, code_only) + 1))
    return min(1.0, 2 * tail / (2**discordant))


def print_table(rows: list[dict]) -> None:
    print("=" * 112)
    print("实验 5-3 个人三题配对报告（同一模型：kimi-k3；CoT vs 代码辅助）")
    print("=" * 112)
    print(
        f"{'题':<4}{'考点':<35}{'真值':>7}  "
        f"{'CoT':>7}{'完成':>7}{'token':>8}{'耗时(s)':>10}  "
        f"{'代码':>7}{'完成':>7}{'调用':>6}{'token':>8}{'耗时(s)':>10}"
    )
    print("-" * 112)

    cot_tokens = code_tokens = 0
    cot_seconds = code_seconds = 0.0
    cot_ok = code_ok = calls = math_tasks = 0
    cot_only = code_only = 0

    for row in rows:
        cot_receipts = ((row.get("cot_evidence") or {}).get("provider_receipts") or [])
        code_receipts = ((row.get("code_evidence") or {}).get("provider_receipts") or [])
        ct = token_total(cot_receipts)
        dt = token_total(code_receipts)
        cp = "None" if row.get("cot_pred") is None else str(row.get("cot_pred"))
        dp = "None" if row.get("code_pred") is None else str(row.get("code_pred"))
        cok = bool(row.get("cot_ok"))
        dok = bool(row.get("code_ok"))
        cot_ok += int(cok)
        code_ok += int(dok)
        cot_only += int(cok and not dok)
        code_only += int(dok and not cok)
        cot_tokens += ct
        code_tokens += dt
        cot_seconds += float(row.get("cot_duration_s") or 0)
        code_seconds += float(row.get("code_duration_s") or 0)
        calls += int(row.get("tool_calls") or 0)
        math_tasks += int(bool(row.get("used_math_library")))
        print(
            f"{str(row['id']):<4}{row['topic']:<35}{row['answer']:>7}  "
            f"{cp:>7}{('是' if cok else '否'):>7}{ct:>8}{float(row.get('cot_duration_s') or 0):>10.3f}  "
            f"{dp:>7}{('是' if dok else '否'):>7}{int(row.get('tool_calls') or 0):>6}"
            f"{dt:>8}{float(row.get('code_duration_s') or 0):>10.3f}"
        )

    n = len(rows)
    p_value = exact_p_value(cot_only, code_only)
    print("-" * 112)
    print(f"准确率：CoT {cot_ok}/{n} = {cot_ok/n:.1%}；代码辅助 {code_ok}/{n} = {code_ok/n:.1%}；差值 {(code_ok-cot_ok)/n:+.1%}")
    print(f"总 token：CoT {cot_tokens:,}；代码辅助 {code_tokens:,}（本批少 {cot_tokens-code_tokens:,}）")
    print(f"总耗时：CoT {cot_seconds:.3f}s；代码辅助 {code_seconds:.3f}s")
    print(f"沙箱调用：{calls} 次；使用 SymPy/NumPy/SciPy 的任务：{math_tasks}/{n}")
    print(f"不一致对：仅 CoT 正确={cot_only}，仅代码正确={code_only}；双侧精确配对 p={p_value:.3f}")
    print("注：第 6 题 CoT 的 finish_reason=length，预测 None 表示预算内未给最终答案，不是算出错误数字。")


def print_task(row: dict, compact: bool = False) -> None:
    task_id = row["id"]
    print("=" * 88)
    print(f"任务 {task_id}: {row['topic']}（真值={row['answer']}）")
    print("=" * 88)
    print(
        f"CoT: 预测={row.get('cot_pred')}，正确={row.get('cot_ok')}，"
        f"finish_reason={finish_reason(row, 'cot')}，耗时={row.get('cot_duration_s')}s"
    )
    cot_text = row.get("cot_text") or "<无可见最终文本>"
    print("\n--- CoT 最终可见文本 ---\n" + cot_text)
    print(
        f"\n代码辅助: 预测={row.get('code_pred')}，正确={row.get('code_ok')}，"
        f"工具调用={row.get('tool_calls')}，耗时={row.get('code_duration_s')}s"
    )
    codes = row.get("generated_code") or []
    traces = ((row.get("code_evidence") or {}).get("tool_traces") or [])
    if compact:
        print("\n--- 模型生成代码中的关键行（由原始 JSON 提取） ---")
        markers = (
            "repr_set = set()", "for a in", "for b in", "repr_set.add",
            "import sympy", "fac = sp.factorint", "count_thm =", "sets equal?",
        )
        for line in (codes[0].splitlines() if codes else []):
            if any(marker in line for marker in markers):
                print(line)
        print("\n--- 沙箱关键结果（由原始 JSON 提取） ---")
        result_lines = (traces[0].get("result", "").splitlines() if traces else [])
        result_markers = (
            "max_a ", "count brute ", "count theorem ", "sets equal? ",
            "brute-not-thm ", "thm-not-brute ",
        )
        for line in result_lines:
            if line.startswith(result_markers):
                print(line)
        final_lines = [
            line for line in (row.get("code_text") or "").splitlines()
            if "FINAL ANSWER:" in line
        ]
        print("\n--- 代码辅助最终答案 ---")
        print(final_lines[-1] if final_lines else "<未找到 FINAL ANSWER>")
        return

    for index, code in enumerate(codes, 1):
        print(f"\n--- 模型生成代码 #{index} ---\n{code}")
    for index, trace in enumerate(traces, 1):
        print(f"\n--- 沙箱结果 #{index} ---\n{trace.get('result', '')}")
    print("\n--- 代码辅助最终回答 ---\n" + (row.get("code_text") or "<无可见最终文本>"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=int, choices=[1, 6, 11], help="显示某题的脱敏详细轨迹")
    parser.add_argument("--compact", action="store_true", help="配合 --task 输出适合截图的关键证据")
    args = parser.parse_args()
    missing = [str(path) for path in RESULT_FILES if not path.is_file()]
    if missing:
        raise SystemExit("缺少结果文件：\n" + "\n".join(missing))
    rows = [load_row(path) for path in RESULT_FILES]
    if args.task is None:
        print_table(rows)
    else:
        print_task(next(row for row in rows if int(row["id"]) == args.task), compact=args.compact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
