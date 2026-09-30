# 实验 5-3 Summary：代码辅助数学推理个人三题对照

## 证据范围

本次个人实验使用同一个 Moonshot `kimi-k3` 模型，在三个固定数学题上分别运行纯 CoT 与代码辅助两臂。它是学习用小样本配对对照，不是仓库正式的 30 题 AIME 2024 campaign。

主要原始 JSON（仅本地保存）：

| 任务 | 文件 | SHA-256 |
| --- | --- | --- |
| 题 1：容斥 | `probe-p1-kimi-k3.json` | `629EBF6412F67311F1B085789006FD4AC98918EDBEFFE3B76D4EFCBBD5A2D422` |
| 题 6：二平方和去重 | `result-p6-kimi-k3.json` | `9A863245ACA05D84887C6D1335A301CD9A2DA3A584B463CF35D68F508718919C` |
| 题 11：圆内格点 | `result-p11-kimi-k3.json` | `0EE43563D6D42039EF1A229F71D0D26FD72D080A433D982C71424916286F78EA` |

另保留失败探针 `probe-p1.json`（SHA-256 `7F31CDE886468F9B51D71C4FBBBDD1357D0FE317F4F41052048F0AFA15D21AB1`）：`kimi-k2.6` 的 CoT 臂答对 925，但代码臂在模型生成代码前返回 400，因为 thinking 模式与 `tool_choice='required'` 不兼容。它没有被成功运行覆盖。

两个单题输入从仓库 `problems.json` 原样抽取并逐字段核对：

| 输入 | SHA-256 |
| --- | --- |
| `problem-6.json` | `E6088C6B95F55F2394F37A573956A7D3E8EF2A13C754E6FBEFBA981EF33D2AFD` |
| `problem-11.json` | `7BC4B7B9D1367648695FF712416FA158EB8734A8E53E73995FAD33A9C764EB12` |

原始 JSON 含 provider response ID，因此默认忽略、不提交 Git。公开 summary 不保存 API Key、response ID 或账户标识。

## 环境

```text
Windows / Anaconda Prompt
Conda 环境：agentbook
Python：3.11.16
openai：3.13.0
sympy：1.14.0
numpy：2.4.6
scipy：1.17.1
mpmath：1.3.0
provider：moonshot
model：kimi-k3
```

用户级目录中的不完整 SymPy 曾遮蔽 Conda 环境，导致 `mpmath` 缺失。后续在当前 CMD 设置 `PYTHONNOUSERSITE=1`，并把实验所需数学依赖安装到 `C:\Users\asus\.conda\envs\agentbook\Lib\site-packages`。

## 离线自检

```bat
python demo.py --selfcheck --verbose
```

结果为 `参考解命中真值：11/11`。这只证明题库参考代码、真值、依赖与子进程执行链一致；此步骤没有调用 LLM，不能算作代码辅助 Agent 的 100% 准确率。

## 真实运行命令

三次成功运行均使用相同 provider、模型、模式和脚本，只替换题目文件与输出路径：

```bat
python demo.py --provider moonshot --model kimi-k3 --mode both --limit 1 --verbose --output "..\experiment\output\5-3_code-for-math\probe-p1-kimi-k3.json"

python demo.py --provider moonshot --model kimi-k3 --mode both --problems "..\experiment\input\5-3_code-for-math\problem-6.json" --verbose --output "..\experiment\output\5-3_code-for-math\result-p6-kimi-k3.json"

python demo.py --provider moonshot --model kimi-k3 --mode both --problems "..\experiment\input\5-3_code-for-math\problem-11.json" --verbose --output "..\experiment\output\5-3_code-for-math\result-p11-kimi-k3.json"
```

每个命令只含一个题目；运行间隔至少 65 秒，以适配账户 3 RPM 限制。

## 三题结果

| 题 | 考点 | 真值 | CoT 预测 | CoT 结束 | CoT token | CoT 耗时 | 代码预测 | 工具调用 | 数学库 | 代码 token | 代码耗时 |
| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| 1 | 容斥 | 925 | 925 ✓ | `stop` | 792 | 31.516s | 925 ✓ | 1 | 否 | 1,493 | 20.172s |
| 6 | 二平方和去重 | 330 | `None` ✗ | `length` | 4,272 | 126.453s | 330 ✓ | 1 | 是 | 2,027 | 28.859s |
| 11 | 严格圆内格点 | 1,245 | 1,245 ✓ | `stop` | 2,138 | 53.515s | 1,245 ✓ | 1 | 否 | 2,147 | 24.625s |

聚合：

| 指标 | 纯 CoT | 代码辅助 |
| --- | ---: | ---: |
| 正确题数 | 2/3 | 3/3 |
| 准确率 | 66.7% | 100.0% |
| 总 token | 7,202 | 5,667 |
| 总耗时 | 211.484s | 73.656s |
| 沙箱调用 | 0 | 3 |

准确率差为 +33.3 个百分点，但只有一个不一致对（仅代码正确=1、仅 CoT 正确=0），双侧精确配对检验 `p=1.0`。本批不能证明代码辅助具有统计显著优势。

## 第 6 题的正确归因

第 6 题的 CoT 不是“算出错误数字”。provider receipt 显示它生成了 4,096 completion tokens，`finish_reason='length'`，但 `content` 中没有可提取的 `FINAL ANSWER`，所以预测为 `None`。这应记录为“在相同输出预算内未完成可判分答案”。JSON 没有保存 Kimi 的不可见 reasoning 内容，因此不能进一步断言它在数学推导哪一步失败。

代码臂生成一段 `set` 去重枚举，又使用 SymPy `factorint` 按二平方和定理构造第二个集合；两种方法都得到 330，集合完全一致。这一题的 `used_math_library=true`。

## 第 1、11 题的轨迹

- 题 1：代码用容斥公式算出 925，再用循环暴力验证；未使用 SymPy/NumPy/SciPy，所以 `used_math_library=false`，但确实执行了沙箱。
- 题 11：CoT 正确使用 `floor(sqrt(399-x^2))` 处理严格不等式；代码一边遍历所有有序整数对，一边用 `isqrt(r-1)` 按每个 x 汇总，两种算法均得到 1,245。

## Token 与耗时边界

本批代码臂总 token 比 CoT 少 1,535，耗时也更短，但差异主要由第 6 题 CoT 达到 4,096 token 上限且耗时 126.453 秒造成。不能据此概括“代码辅助总是更省 token 或更快”：题 1、11 的代码臂需要额外的工具 schema、tool call 和 tool result，题 11 的代码总 token 还略高于 CoT。

`duration_s` 是每个实验臂的客户端墙钟时间，包含真实 provider 请求与本地子进程执行；每题只运行一次，不能用于统计延迟结论。

## 字段与验收边界

- `tool_calls=1` 表示 Harness 实际收到 function call 并执行了一次 `run_python`，不是模型在文本中假装写代码。
- `used_math_library` 只匹配生成代码中是否出现 `sympy`、`numpy` 或 `scipy`，不表示代码是否真正执行。
- `cot_ok/code_ok` 只比较提取出的整数与题库真值，不评估证明质量。
- JSON 顶层 `experiment='5-1'` 是项目重编号前留下的历史标签；当前书稿与 Chapter 5 索引将其编号为 5-3。
- JSON 的 `official_complete=false` 是正确的：正式门禁要求固定的 30 题 AIME 2024 数据集；本次是三题个人学习对照。
- 仓库正式 30 题结果是代码 53.3%、CoT 36.7%、`p=0.125`，同样没有支持“显著提升”的原假设；不能用正式结果替代本次个人运行，也不能反过来把本次 3/3 当作正式复现。

## 证据能证明什么

本次证据支持：

1. `kimi-k3` 在三个代码臂都生成了真实 function call，Harness 共执行三次本地 Python 子进程。
2. 代码可以把枚举、去重和边界检查转移给确定性执行器，并把 stdout 作为 observation 回填给模型。
3. 在这三个固定题目和相同预算下，代码臂覆盖 3/3，CoT 覆盖 2/3。
4. provider/model 的工具协议兼容性是 Harness 的一部分；`kimi-k2.6` 与 `required` 的失败发生在数学推理之前。

本次证据不能证明：

1. 代码辅助对更大题集具有统计显著优势。
2. 代码辅助天然更快、更省 token 或永远不低于 CoT。
3. 生成代码本身必然正确、安全或具有生产级隔离。
4. 3/3 等于正式 AIME benchmark 的准确率。
