# 实验 3-9 Summary：`offline-demo.json` 可读版

## 文件与命令

- 原始结果：`offline-demo.json`
- 实验入口：`chapter3/agentic-rag-for-user-memory/offline_demo.py`
- 用例：`layer2_01_multiple_vehicles`

```bat
python offline_demo.py --output "..\experiment\output\3-9_agentic-rag-memory\offline-demo.json"
```

本次使用本地 BM25 离线检索，不需要 API Key 或端口 4242 的检索服务。

## JSON 字段说明

| 字段 | 含义 |
| --- | --- |
| `test_id` | 本次运行使用的评估用例 ID。 |
| `question` | 用来检索历史记忆的当前用户问题。 |
| `num_sessions` | 被索引的历史会话数量。 |
| `num_chunks` | 历史会话切分后得到的记忆块总数。 |
| `top_k` | 每次查询最多返回的记忆块数量。 |
| `naive` | 朴素单次检索的查询数、召回块数和证据覆盖率。 |
| `agentic` | 多轮检索的查询数、去重召回块数、证据覆盖率和查询轨迹。 |
| `coverage` | 每条预设决定性证据是否出现在召回内容中。 |
| `recall` | 已覆盖证据数除以预设决定性证据总数。 |
| `trace` | Agentic 路线每次查询及其命中的记忆块 ID。 |

## 实验输入

当前问题：

```text
I need to schedule service for my car. Can you tell me what services I have scheduled?
```

基础数据：

| 项目 | JSON 记录值 |
| --- | ---: |
| 历史会话数 | 2 |
| 记忆块数 | 6 |
| 每次查询的 `top_k` | 3 |

用例包含两条需要同时找回的决定性证据：

1. 本田已确认预约，确认号为 `FS-447291`。
2. 特斯拉 Model 3 是用户拥有的第二辆车。

## 两种策略结果

| 指标 | 朴素单次检索 | Agentic 多轮检索 |
| --- | ---: | ---: |
| 查询次数 | 1 | 5 |
| 检索到的去重记忆块数 | 3 | 5 |
| 找到 `FS-447291` | 否 | 是 |
| 找到 Tesla Model 3 | 是 | 是 |
| 决定性证据召回率 | 50% | 100% |
| 是否具备完整消歧所需证据 | 否 | 是 |

朴素检索找到了 Tesla Model 3 的存在，但没有找回包含本田预约确认号的记忆块，因此覆盖 1/2 条决定性证据。

Agentic 路线在首轮检索后继续针对发现的车辆实体发起聚焦查询，最终覆盖 2/2 条决定性证据。

## Agentic 查询轨迹

JSON 共保存 5 次查询：

| 次序 | 查询 | 命中数 | 命中会话类型 |
| ---: | --- | ---: | --- |
| 1 | `I need to schedule service for my car. Can you tell me what services I have scheduled?` | 3 | 保养会话 2 块、保险会话 1 块 |
| 2 | `Honda service appointment scheduled` | 3 | 保养会话 3 块 |
| 3 | `Tesla service appointment scheduled` | 3 | 保养会话 2 块、保险会话 1 块 |
| 4 | `Honda Accord service appointment scheduled` | 3 | 保养会话 3 块 |
| 5 | `Tesla Model service appointment scheduled` | 3 | 保养会话 2 块、保险会话 1 块 |

每次查询都最多返回 3 块，但不同查询会重复命中相同块。`agentic.num_retrieved = 5` 表示五次查询合并、按 `chunk_id` 去重后共有 5 个记忆块，不是总命中次数 15。

## 必要说明

- `recall = 1.0` 只表示本用例预设的两条决定性证据都被召回，不代表回答准确率为 100%，也不代表对其他用例同样有效。
- “能完整消歧作答”是根据两条证据是否全部覆盖推导的结果。本离线脚本没有调用 LLM，也没有生成或评测最终自然语言答案。
- Agentic 查询由离线规则生成：脚本从首轮结果中抽取车辆实体，再拼接聚焦查询；这不是模型自主推理轨迹。
- 本次本地后端只运行 BM25。日志中的 `IndexMode.HYBRID` 是配置对象的模式值，不表示离线路径实际执行了向量检索。
- JSON 保存查询、块 ID 和聚合指标，不保存每个命中块的完整文本；需要追查原文时，应回到测试用例 YAML 和 CMD 轨迹。
