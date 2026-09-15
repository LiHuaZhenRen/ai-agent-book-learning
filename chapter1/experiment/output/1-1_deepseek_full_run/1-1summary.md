# 实验 1-1 Summary：`evidence.json` 可读版

## 文件与命令

- 原始证据文件：`evidence.json`
- 校验文件：`evidence.sha256`
- 运行目录：`chapter1/context`
- 命令中使用的服务商与模型：DeepSeek / `deepseek-v4-flash`

```bat
python run_experiment_1_1.py --provider deepseek --model deepseek-v4-flash --modes full no_history no_reasoning no_tool_calls no_tool_results --output-dir ..\experiment\output\1-1_deepseek_full_run
```

## 顶层验证结果

这些字段来自 `evidence.json -> analysis`：

| 字段 | 值 |
|---|---|
| `exact_five_arms_present` | `true` |
| `all_context_contracts_passed` | `true` |
| `direct_real_api_evidence` | `true` |
| `experiment_execution_accepted` | `true` |
| `all_manuscript_behavior_claims_observed` | `true` |

Token 用量：

| 字段 | 值 |
|---|---:|
| `prompt_tokens` | 18,680 |
| `completion_tokens` | 4,350 |
| `total_tokens` | 23,030 |
| `cached_prompt_tokens` | 15,232 |
| `reasoning_tokens` | 1,087 |

## 实验任务

Agent 需要把四个季度收入统一换算成美元，再计算全年总收入和季度平均值：

| 项目 | 原始金额 |
|---|---:|
| Q1 | 2.5 million USD |
| Q2 | 2.1 million EUR |
| Q3 | 1.8 million GBP |
| Q4 | 380 million JPY |

标准结果：

```text
Annual total = $9,602,895.73
Quarterly average = $2,400,723.93
```

## Arms 结果表

这些字段来自 `evidence.json -> arms[]`：

| Mode | Outcome | Iterations | Tool Calls | Reasoning Steps | API Turns | Context Contract | Final Answer |
|---|---|---:|---:|---:|---:|---|---|
| `full` | `correct` | 3 | 5 | 3 | 3 | passed | `$9,602,895.73`; `$2,400,723.93` |
| `no_history` | `no_terminal_response` | 5 | 15 | 5 | 5 | passed | 无 |
| `no_reasoning` | `incorrect` | 3 | 5 | 3 | 3 | passed | `9.60 million USD`; `2.40 million USD` |
| `no_tool_calls` | `no_unsupported_numbers` | 1 | 0 | 1 | 1 | passed | 输出了类工具调用文本，但没有真实工具执行 |
| `no_tool_results` | `no_terminal_response` | 5 | 13 | 5 | 5 | passed | 无 |

## 各 Arm 轨迹摘要

### `full`

可读化轨迹：

1. 调用 `convert_currency`：`2,100,000 EUR -> 2,282,608.70 USD`
2. 调用 `convert_currency`：`1,800,000 GBP -> 2,278,481.01 USD`
3. 调用 `convert_currency`：`380,000,000 JPY -> 2,541,806.02 USD`
4. 调用 `calculate`：`2500000 + 2282608.7 + 2278481.01 + 2541806.02 = 9602895.73`
5. 调用 `calculate`：`9602895.73 / 4 = 2400723.9325`
6. 输出最终答案。

### `no_history`

可读化轨迹：

1. 共运行 5 次模型迭代。
2. 共记录 15 次工具调用。
3. 多次重复调用 `convert_currency`。
4. 没有形成最终答案，结果为 `no_terminal_response`。

### `no_reasoning`

可读化轨迹：

1. 共运行 3 次模型迭代。
2. 共记录 5 次工具调用。
3. 最终输出了答案，但答案是 `9.60 million USD` 和 `2.40 million USD`。
4. Harness 将该 arm 判定为 `incorrect`。

### `no_tool_calls`

可读化轨迹：

1. 共运行 1 次模型迭代。
2. 工具调用数为 0。
3. 模型输出了类似工具调用的文本标记。
4. 因为请求中没有真实 `tools` 定义，脚本没有执行任何工具。

### `no_tool_results`

可读化轨迹：

1. 共运行 5 次模型迭代。
2. 共记录 13 次工具调用。
3. 多次调用 `convert_currency`，并尝试过不同金额或不同方向的换算。
4. 没有形成最终答案，结果为 `no_terminal_response`。

## 字段说明

`evidence.json` 中最常看的字段：

| 字段 | 含义 |
|---|---|
| `arms[]` | 五组上下文消融实验的逐组结果。 |
| `arms[].mode` | 当前消融模式，例如 `full`、`no_history`。 |
| `arms[].outcome` | Harness 对这一组运行结果的分类。 |
| `arms[].iterations` | 模型循环次数。 |
| `arms[].tool_calls` | 工具调用和工具结果记录。 |
| `arms[].reasoning_steps` | Provider 返回的模型推理内容记录。 |
| `arms[].api_turns` | 每一轮真实 API 请求和响应。 |
| `arms[].context_contract` | 检查该模式是否真的移除或保留了指定上下文部分。 |
| `analysis` | 脚本对五组实验的总体验证结果。 |

## 必要说明

- `no_tool_calls` 的结果不是“模型完全没有想调用工具”，而是“没有可执行的工具定义，所以没有真实 tool call 被执行”。
- `no_reasoning` 移除的是历史中的 `reasoning_content`，不是禁止模型在当前轮重新推理。
- `no_tool_results` 中工具实际被执行了，但工具观察结果没有写回模型上下文。
