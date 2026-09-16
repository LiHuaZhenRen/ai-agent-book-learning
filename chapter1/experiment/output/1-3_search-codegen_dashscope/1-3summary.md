# 实验 1-3 Summary：`evidence.json` 可读版

## 文件与命令

本次运行目录：

```text
chapter1/experiment/output/1-3_search-codegen_dashscope
```

生成文件：

| 文件 | 含义 |
|---|---|
| `evidence.json` | 实验主证据，包含验收结果、任务输出、验证项和精简后的 API 记录。 |
| `receipts.json` | 原始 provider turn 记录，不含 API Key。 |
| `manifest.json` | 本次运行的清单、输入参数和 artifact hash。 |
| `evidence.sha256` | `evidence.json` 的 SHA-256 校验文件。 |
| `receipts.sha256` | `receipts.json` 的 SHA-256 校验文件。 |

运行命令：

```bat
python run_experiment_1_3.py --backends dashscope --reasoning high --output-dir ..\experiment\output\1-3_search-codegen_dashscope
```

## Manifest 摘要

这些字段来自 `manifest.json`：

| 字段 | 值 |
|---|---|
| `experiment_id` | `1-3` |
| `run_id` | `1-3_search-codegen_dashscope` |
| `created_at` | `2026-09-15T06:02:31.472787+00:00` |
| `backends` | `dashscope` |
| `reasoning` | `high` |
| `acceptance_passed` | `true` |
| `acceptance_backend` | `dashscope` |
| `evidence.json sha256` | `22ba9fe202c10cbb48fb3f4ae578c4a6c09f64d8664cea0f36d39b7750b84ab7` |
| `receipts.json sha256` | `47bcb87ffd16d8eddcadcbdc89b636637dfa2cd8f94a977f32df6b98ea18139e` |

## 验收结果

这些字段来自 `evidence.json -> acceptance`：

| 字段 | 值 |
|---|---|
| `policy` | 多提供商验收；不强制绑定 OpenAI 官方账号，只要 provider 的 Responses API 能闭合 hosted search + code execution 循环即可。 |
| `eligible_acceptance_backends` | `openai`, `dashscope` |
| `eligible_backends_attempted` | `dashscope` |
| `acceptance_backend` | `dashscope` |
| `passed` | `true` |
| `openrouter_is_diagnostic_not_acceptance` | `false` |

DashScope 子结果：

| 字段 | 值 |
|---|---|
| `started` | `true` |
| `requested_model` | `qwen3.7-plus` |
| `asean_passed` | `true` |
| `clarification_passed` | `true` |

## 运行概况

这些字段来自 `evidence.json -> runs[0]`：

| 字段 | 值 |
|---|---|
| `backend` | `dashscope` |
| `requested_model` | `qwen3.7-plus` |
| `base_url` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `api_turn_count` | 3 |
| `input_tokens` | 124,050 |
| `output_tokens` | 26,505 |
| `total_tokens` | 150,555 |
| `reported_cost_available` | `false` |

3 个 API turn 分别对应：

| Turn | 内容 |
|---|---|
| 1 | 东盟 10 国首都距离任务。 |
| 2 | 含糊的比特币技术分析请求，模型先提出澄清问题。 |
| 3 | 用户补充数据源和指标后，模型继续搜索并执行代码分析。 |

## 任务 A：东盟首都最近距离

任务要求：

```text
Research the current official capitals and reliable coordinates for the ten ASEAN member states.
Use hosted web search and cite sources.
Use hosted Python, not mental arithmetic, to enumerate all 45 capital pairs with the haversine formula.
```

验证结果来自 `evidence.json -> runs[0].asean_validation`：

| 检查项 | 结果 |
|---|---|
| `request_succeeded` | `true` |
| `model_identity_exact` | `true` |
| `web_search_completed` | `true` |
| `code_interpreter_completed` | `true` |
| `url_citations_present` | `true` |
| `closest_pair_matches_independent_reference` | `true` |
| `distance_reported` | `true` |
| `passed` | `true` |

输出 item 类型：

```text
reasoning -> web_search_call -> reasoning -> web_search_call -> reasoning -> code_interpreter_call -> reasoning -> code_interpreter_call -> reasoning -> message
```

工具调用摘要：

| 类型 | 次数 |
|---|---:|
| `web_search_call` | 2 |
| `code_interpreter_call` | 2 |
| URL citations | 109 |

独立参考结果：

| 字段 | 值 |
|---|---|
| 最近首都对 | `Kuala Lumpur` / `Singapore` |
| 独立参考距离 | 309.3 km |
| 枚举 pair 数 | 45 |

模型最终答案中识别的最近首都对：

```text
Kuala Lumpur (Malaysia) and Singapore (Singapore)
```

模型答案中报告的距离为约 `315.55 km`，与独立参考使用坐标不同，但最近首都对一致，因此验证通过。

## 任务 B：比特币技术分析与澄清

原始请求：

```text
搜索最近一个月的比特币走势，做技术分析。
```

第一轮验证重点：请求含糊时，模型必须先澄清，不能直接调用工具。

第一轮结果：

| 字段 | 值 |
|---|---|
| `first_tool_calls` | 0 |
| `first_turn_clarified_before_tools` | `true` |

第一轮回答：

```text
您偏好使用哪个数据源（例如 Binance、Coinbase、CoinMarketCap 等）？需要分析哪些技术指标（例如 MA、MACD、RSI、布林带等）？
```

用户补充：

```text
使用 CoinGecko 的 BTC/USD 日线收盘价；分析 MA7、MA20、RSI14、MACD(12,26,9)、区间收益和最大回撤，如代码环境支持请绘制收盘价走势图。请搜索数据并用托管 Python 工具实际计算，再给出含来源的报告和交易建议。
```

第二轮验证结果：

| 检查项 | 结果 |
|---|---|
| `continuation_used_previous_response_id` | `true` |
| `followup_succeeded` | `true` |
| `followup_web_search_completed` | `true` |
| `followup_code_interpreter_completed` | `true` |
| `followup_citations_present` | `true` |
| `followup_reports_ma_rsi_macd` | `true` |
| `passed` | `true` |

第二轮输出 item 类型：

```text
reasoning -> code_interpreter_call -> reasoning -> web_search_call -> reasoning -> web_search_call -> reasoning -> web_search_call -> reasoning -> code_interpreter_call -> reasoning -> message
```

第二轮工具调用摘要：

| 类型 | 次数 |
|---|---:|
| `web_search_call` | 3 |
| `code_interpreter_call` | 2 |
| URL citations | 65 |

模型报告中的关键指标：

| 指标 | 数值 |
|---|---:|
| 区间收益率 | +22.78% |
| 最大回撤 | -3.20% |
| MA7 | $77,250.66 |
| MA20 | $78,214.41 |
| RSI14 | 36.45 |
| MACD DIF | 1507.07 |
| MACD DEA | 2247.93 |
| MACD 柱状图 | -1481.72 |

