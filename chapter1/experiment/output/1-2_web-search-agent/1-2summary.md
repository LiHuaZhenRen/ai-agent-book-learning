# 实验 1-2 Summary

## 文件与命令

本实验相关输出文件：

| 文件 | 含义 |
| --- | --- |
| `offline-demo.json` | 离线演示模式输出，不是真实搜索。 |
| `kimi-context-caching.json` | 第一次真实 Kimi 运行，返回 429 错误。 |
| `kimi-context-caching-retry1.json` | 第二次真实 Kimi 运行，成功完成。 |

## JSON 字段说明

JSON 文件主要包含：

| 字段 | 含义 |
| --- | --- |
| `question` | 本次提问内容。 |
| `trace` | 简化后的 ReAct 轨迹，也就是终端里看到的 thought、action、observation、answer。 |
| `answer` | 最终回答或错误信息。 |
| `api_turns` | 更底层的 API 调用记录，包括工具定义获取、模型请求、Formula 执行、再次请求模型等。 |
| `provider` | 服务商，本次成功运行为 `moonshot`。 |
| `model` | 模型，本次成功运行为 `kimi-k3`。 |
| `base_url` | API 地址，本次为 `https://api.moonshot.cn/v1`。 |

## `offline-demo.json` 可读化

离线演示问题：

```text
Moonshot AI 的 Context Caching 是什么技术？
```

离线演示轨迹：

| Step | Type | 内容 |
| --- | --- | --- |
| 1 | thought | 判断需要搜索 Context Caching 的定义。 |
| 1 | action | 调用 `web_search`，查询 `Moonshot AI Context Caching 是什么`。 |
| 1 | observation | 返回预置示例：Context Caching 是复用上下文前缀的缓存机制。 |
| 2 | thought | 判断还需要了解适用场景。 |
| 2 | action | 调用 `web_search`，查询 `Context Caching 适用场景 计费`。 |
| 2 | observation | 返回预置示例：适用于多轮对话、长文档问答、固定系统提示等。 |
| 3 | answer | 输出离线示例答案。 |

离线演示答案注明了“本段来自离线示例轨迹，非真实搜索结果”。

## `kimi-context-caching.json` 可读化

第一次真实 Kimi 运行没有形成 ReAct 轨迹：

| 字段 | 值 |
| --- | --- |
| `provider` | `moonshot` |
| `model` | `kimi-k3` |
| `trace_count` | 0 |
| `answer` | `HTTP 429 Too Many Requests` / `engine_overloaded_error` |

保存的错误信息：

```text
搜索过程中出现错误: Error code: 429 - The engine is currently overloaded, please try again later
```

## `kimi-context-caching-retry1.json` 可读化

成功运行的基本信息：

| 字段 | 值 |
| --- | --- |
| `question` | `Moonshot AI Context Caching 是什么？请用两三句话回答` |
| `provider` | `moonshot` |
| `model` | `kimi-k3` |
| `trace_count` | 5 |
| `api_turn_count` | 4 |

### ReAct Trace

| Iteration | Type | 内容 |
| --- | --- | --- |
| 1 | thought | 模型判断需要先搜索，以确保回答准确。 |
| 1 | action | 调用 `web_search`，参数为 `{"query":"Moonshot AI Context Caching 是什么 API 缓存 计费","classes":["all","code"]}`。 |
| 1 | observation | 工具返回 `MOONSHOT ENCRYPTED` 开头的 observation。 |
| 2 | thought | 模型综合搜索结果，整理 Context Caching 的定义、成本、首字响应、适用场景和费用。 |
| 2 | answer | 输出最终回答。 |

最终回答：

```text
Moonshot AI（Kimi）的 Context Caching 是把请求中重复出现的长上下文 Tokens 预先缓存成可复用 Cache，后续请求命中后只需为增量内容和调用付费，从而显著降低成本、并加快首字响应。官方称在规模化、重复度高的 Prompt 场景最高可省约 90% 成本，适合固定文档问答、预设 QA Bot、代码库/知识库分析和复杂 Agent；但它会收取 Cache 创建、按分钟存储及命中调用等费用。
```

### API Turns

成功运行共有 4 个底层 API turn：

| API Turn | Kind | 作用 |
| --- | --- | --- |
| 1 | `formula_tools` | 获取 `moonshot/web-search:latest` 的工具定义。 |
| 2 | `chat_completion` | 把问题和工具定义发给 `kimi-k3`，模型返回 tool call。 |
| 3 | `formula_fiber` | 执行托管的 `web_search` 工具。 |
| 4 | `chat_completion` | 把工具 observation 放回上下文，模型生成最终答案。 |

两次 `chat_completion` 的 token 记录：

| Chat Turn | Finish Reason | Prompt Tokens | Completion Tokens | Total Tokens | Reasoning Tokens | Cached Tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `tool_calls` | 336 | 113 | 449 | 31 | - |
| 2 | `stop` | 1,735 | 215 | 1,950 | 96 | 256 |

## 必要说明

- `--max-steps 3` 是最大迭代上限，不表示一定运行 3 轮。本次成功运行在第 2 轮已经得到 `finish_reason = stop`，因此正常结束。
- `MOONSHOT ENCRYPTED` 是 Moonshot Formula 返回的加密 observation。本 summary 只记录它的存在和后续模型回答，不展开原始加密内容。
- CMD 输出偏向人类阅读；JSON 输出偏向后续审计，所以 JSON 中会出现比终端更多的底层 API 记录。
