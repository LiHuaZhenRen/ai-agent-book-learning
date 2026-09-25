# 实验 4-1 Summary：主动工具发现（离线机制对照）

## 文件与证据范围

- 原始结果：`offline-all-tasks.json`（仅本地保留，不默认提交 Git）
- 预跑结果：`probe-finance-news.json`（仅本地保留）
- 完整实验：8 个任务 × 3 种策略，共 24 条记录
- 原始结果 SHA-256：`1CC3F80D5B3781BE2923862138213F67F916EFB8DFA10B7F7FD39D707959CE01`
- 实验入口：`chapter4/active-tool-discovery/demo.py`

原始 JSON 中未检出 API Key、组织 ID 等敏感标识。本次运行完全离线，没有请求模型 API、网页、股票、新闻、日历或其他外部服务。

## 环境与命令

```text
操作系统：Windows
Conda 环境：agentbook
Python：3.11.16
tiktoken：0.14.0
模型字段：mock-offline
嵌入器：local-hash-512
工具库：126 个工具
```

正式命令：

```bat
python demo.py --offline --strategies full,prefilter,discovery --tool-set-size 126 --top-k 4 --prefilter-n 10 --max-steps 10 --output "..\experiment\output\4-1_active-tool-discovery\offline-all-tasks.json"
```

安装 `tiktoken` 后，`python -m pip check` 仍报告当前共享环境中若干既有包缺少可选或间接依赖，例如 `scipy`、`filelock`、`markupsafe`。这些包不在本次离线路径上，因此没有为本实验继续修改共享环境。

`demo.py --help` 仍显示旧编号“实验 8-4”，而 Chapter 4 README、实验账本和当前目录都把主动工具发现编号为 4-1；这是仓库重编号后的帮助文本遗留，不影响本次代码路径。

## 三种策略

| 策略 | 工具如何进入 Context |
| --- | --- |
| 全量注入 `full` | 一开始把 126 个工具的完整 schema 全部写入 system prompt。 |
| 检索预筛选 `prefilter` | 只按原始任务做一次本地相似度检索，把 top-10 工具写入 system prompt。 |
| 主动发现 `discovery` | system 只保留基础工具和 `discover_tools`；执行中针对每个能力缺口分别检索 top-4，再把新 schema 追加到对话。 |

## 聚合结果

| 策略 | 精确选对 | 能力槽位完成 | `finished` | 总注入 token | 平均注入 token | 平均暴露工具 | 平均本地耗时 | 发现调用 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 全量注入 | 8/8 | 8/8 | 8/8 | 93,040 | 11,630.0 | 126 | 0.0056s | 0 |
| 检索预筛选 | 4/8 | 4/8 | 8/8 | 8,236 | 1,029.5 | 10 | 0.0058s | 0 |
| 主动发现 | 8/8 | 8/8 | 8/8 | 7,796 | 974.5 | 10 | 0.0101s | 14 |

相对全量注入，主动发现的总注入 token 减少 91.6%，约为前者的 1/11.9。六个双能力任务各调用两次 `discover_tools`，两个单能力诱导任务各调用一次，共 14 次。

## 逐任务结果

| 任务 | 全量 token / 精确 | 预筛选 token / 精确 | 主动发现 token / 精确 | 主动发现轨迹（省略 `finish`） |
| --- | ---: | ---: | ---: | --- |
| `finance+news` | 11,630 / 是 | 1,022 / 是 | 1,019 / 是 | `discover → get_stock_price → discover → search_news` |
| `arxiv+download` | 11,630 / 是 | 997 / 是 | 1,084 / 是 | `discover → arxiv_search → discover → download_file` |
| `github+viz` | 11,630 / 是 | 1,069 / 是 | 1,166 / 是 | `discover → github_list_contributors → discover → render_chart` |
| `weather+calendar` | 11,630 / 是 | 1,087 / 是 | 1,070 / 是 | `discover → get_weather_forecast → discover → create_calendar_event` |
| `forex+weather` | 11,630 / 是 | 1,043 / 否 | 1,085 / 是 | `discover → get_forex_rate → discover → get_current_weather` |
| `crypto+news` | 11,630 / 是 | 1,043 / 否 | 1,004 / 是 | `discover → get_crypto_price → discover → search_news` |
| `opinion(诱导)` | 11,630 / 是 | 965 / 否 | 660 / 是 | `discover → search_news` |
| `academic(诱导)` | 11,630 / 是 | 1,010 / 否 | 708 / 是 | `discover → arxiv_search` |

## 预筛选四次失败的准确解释

四次失败不能全部概括为“top-10 没有召回任何可接受工具”。

| 任务 | 实际情况 |
| --- | --- |
| `crypto+news` | top-10 没有 `get_crypto_price`，只执行了 `search_news`，属于真实的能力漏召回。 |
| `academic(诱导)` | top-10 没有任一可接受的学术检索工具，属于真实的能力漏召回。 |
| `forex+weather` | top-10 已包含判分可接受的 `convert_currency`，但脚本模型固定尝试首选 `get_forex_rate`；后者不可用后就放弃外汇子任务。 |
| `opinion(诱导)` | top-10 已包含可接受的 `get_news_by_source` 与 `get_top_headlines`，但脚本模型固定尝试 `search_news`；后者不可用后没有改选替代工具。 |

因此，本次 4/8 同时包含“一次性检索漏能力”和“脚本路由器不会在等价工具间改选”两类原因。它不能单独证明真实 LLM 的预筛选准确率只有 50%。

## 离线模式真正执行了什么

1. `LocalEmbedder` 把中文单字、中文二元组和英文词哈希进 512 维词袋向量，再用余弦相似度检索工具；它不是神经网络语义嵌入。
2. `MockChatClient` 用正则关键词把任务映射到固定首选工具，并输出规定格式的 JSON action；它不是 LLM 推理。
3. `_run_loop` 是真实执行的本地 Harness：解析 action、检查工具是否可用、运行工具、回填 observation，并继续下一步。
4. `TOOL_IMPLS` 全部调用 `_mock_result`。`search_news`、股票、天气、下载、日历等只返回固定 JSON，没有联网，也没有外部副作用。
5. `grade()` 只检查实际调用的工具名是否覆盖预设能力槽位，并检查是否误用通用兜底工具；它不评估参数、工具结果或最终答案事实正确性。

## 字段边界

- `injected_tokens` 是用 `tiktoken` 的 `o200k_base`（失败时回退 `cl100k_base`）对实际渲染的工具 schema 文本计数，因此是本地真实计算；它不是服务商账单 token。
- `latency_s` 是本机脚本墙钟时间，主要反映哈希检索和循环开销。毫秒级差异不能外推为真实 LLM/API 延迟。
- `finished=true` 只表示脚本模型最终输出了 `finish`。预筛选 8/8 finished 但只有 4/8 能力槽位完成，说明“正常停止”不等于“任务完成”。
- mock 参数由固定 `_ARG_HINTS` 生成，可能出现“以太坊查询却传 AAPL”或“东京天气却传北京”。判分忽略参数，所以 8/8 不代表端到端答案正确。
- 全量注入 8/8 也不代表 126 工具不会干扰真实模型；脚本路由器不会因 11,630 token 的工具墙产生长上下文退化。

## 本次证据能支持的结论

1. 在相同 schema 渲染方式下，按需发现能把工具文本注入量从每任务 11,630 降到约 1,000 token。
2. 对跨领域任务按每个能力缺口分别检索，可以避开一次性用整句任务检索时的部分召回缺口。
3. 主动发现把工具选择变成多轮 Action—Observation 控制过程，需要用更多本地步骤换更小的 Context。
4. 这是一条可复现的控制面与 Context 组织机制自检，不是模型智能、真实网页搜索或真实外部工具调用实验。

本次证据不能证明真实 LLM 在主动发现策略下准确率必然提升，也不能代替仓库账本中使用真实 Ollama、真实 MCP schema 与真实工具的正式 4-1 campaign。
