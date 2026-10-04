# 实验 10-1 Summary：共享上下文中的多角色转换

## 文件与证据范围

- 首次探针：`comparison-coding-kimi-k3.json`（仅本地保留）
- 约束复测：`comparison-coding-short-kimi-k3.json`（仅本地保留）
- 固定输入：`coding-one-task.json`、`coding-short-answer.json`
- 个人节流包装器：`chapter10/experiment/run_10_1_paced.py`
- 原实验运行器：`chapter10/multi-role-transfer/run_comparison.py`
- 首次探针 SHA-256：`03CBD0A24A35E1FD3D5D3466FA77FC0CD05CEF5F1587E8C72F451ADEE5729D35`
- 约束复测 SHA-256：`C75241A8C0F7FB076816CC163C044757954F07C1AC235C81D914684DBEDF80CF`

原始 JSON 含完整模型请求、响应和共享轨迹，只在本地保存；本摘要只保留脱敏指标与必要的工具证据。

## 环境与离线验证

```text
操作系统：Windows
Conda 环境：agentbook
Python：3.11.16
openai：3.13.0
python-dotenv：1.2.3
pytest：9.1.1
模型：kimi-k3
接口：https://api.moonshot.cn/v1
```

离线测试：

```bat
python -m pytest -q tests
```

结果为 `14 passed in 1.23s`。这证明本地 `execute_python`、超时控制和工具分发测试通过，不代表真实模型任务准确率。

## 对照设计

两条路径使用同一模型、同一任务、同一工具实现、同一角色规程、同一最大步数和全量共享历史，仅改变角色规程如何进入 Context：

| 路径 | 角色规程 | 工具可见性 | 静态前缀 |
| --- | --- | --- | --- |
| Transfer | `transfer_to_agent` 后替换 system prompt | 只暴露当前角色工具 | 角色切换时变化 |
| Skill | `load_skill` 把 `SKILL.md` 追加为 tool result | 工具 schema 固定，由 Harness 策略门授权 | 全程稳定 |

个人实验只选一个无需联网的 coding 任务。它要求模型真实调用 `execute_python` 计算斐波那契数列，再使用 writing 能力生成短答案。每个任务只做一组配对，且用 `--skip-boundary` 跳过正式 campaign 的边界集。

## 主要结果：澄清长度约束后的成功配对

| 指标 | Transfer | Skill |
| --- | ---: | ---: |
| 确定性验收 | 通过 | 通过 |
| 能力顺序 | `triage → coding → writing` | `triage → coding → writing` |
| 实际工具序列 | `transfer → execute_python → transfer` | `load triage → load coding → execute_python → load writing → count_characters` |
| API 调用 | 4 | 6 |
| 输入 token | 3,410 | 9,535 |
| 输出 token | 1,152 | 764 |
| 缓存输入 token | 512 | 6,656 |
| 未缓存输入 token | 2,898 | 2,879 |
| 缓存比例 | 15.0% | 69.8% |
| 唯一静态前缀 | 3 | 1 |
| 前缀变化次数 | 2 | 0 |
| 可评分成稿长度 | 29 | 54 |

两条路径都形成正确的能力顺序、真实调用 `execute_python`，并输出第 20 项 `6765`、前 20 项总和 `17710`。另用独立本地 Python 断言核对：

```text
F20= 6765 sum= 17710 count= 20
```

仓库的 `coding` 评分器并不独立核对这两个数值；它主要检查是否执行代码、成稿是否非空且不超过 120 字符、可审计性以及能力顺序。因此独立断言是额外的正确性证据。

## 首次探针：机制成功但格式门禁失败

| 指标 | Transfer | Skill |
| --- | ---: | ---: |
| 执行正确性 | 1 | 1 |
| 可审计性 | 1 | 1 |
| 必需能力顺序 | 1 | 1 |
| 任务约束 | 0 | 0 |
| 可评分成稿长度 | 312 | 141 |
| 最终验收 | 未通过 | 未通过 |

首次任务要求计算完整数列并“用不超过 120 个中文字符解释”，容易让模型只把解释段视为长度约束，而评分器检查的是完整可交付文本的总字符数。为避免混淆，复测明确规定最终回答只能有一句、总字符数不超过 120、不得列出全部数列或添加标题和字数说明。

这不是删除失败数据后只保留成功结果：首次 JSON 与哈希仍被保留，它说明输出约束的措辞本身会影响端到端验收。

## 两条有信息量的失败轨迹

### Transfer 的编码恢复

Transfer 首次生成的脚本在 Windows GBK 终端打印 `✔`，触发 `UnicodeEncodeError`。工具结果仍保留此前已打印的数列与总和，但 coding 角色没有直接忽略错误，而是去掉特殊字符后再次执行，输出：

```text
len = 20
sum = 17710
F22 - 1 = 17710
OK
```

这展示了共享轨迹中的真实执行反馈如何带来下一轮修复。第二次成功任务没有遇到该编码问题。

### Skill 没有遵守字数工具结果

首次 Skill 路径调用 `count_characters`，工具明确返回：

```text
总字符数=141, 其中中文字符=28
```

模型最终却声称“约 104 字符，符合 ≤120”，并继续输出超限内容。它证明“调用了校验工具”不等于“正确读取并遵守工具 observation”。

## 前缀稳定性与 token

成功配对中，Transfer 有 3 个唯一静态前缀、发生 2 次变化；Skill 始终只有 1 个静态前缀、变化 0 次。这符合两种架构的实现：Transfer 在角色边界替换 system prompt 与工具集，Skill 保持静态前缀并把规程追加到轨迹末尾。

Skill 的总输入比 Transfer 多 6,125 token，因为它显式加载三个 Skill，且多做两次模型调用；但缓存输入多 6,144 token，最终未缓存输入反而少 19 token。这个单例说明“总输入更多”和“未缓存输入更多”不是一回事，但不能据此推断普遍成本优势，实际费用还取决于服务商缓存计价与不同任务长度。

## 请求节流与耗时边界

Moonshot 账户限制为 3 RPM。原运行器没有请求节流，因此个人包装器在相邻顶层 Chat Completions 调用之间等待 21 秒。它不修改任务、编排器、评分器或结果 schema，但等待时间会计入 `elapsed_seconds`。

因此本次 Transfer 与 Skill 的墙钟时间不能用于比较架构原生延迟。Skill 多两个 API 调用，也会机械地多承受约两段节流等待。笔记只保留调用数和 token 指标，不把个人环境下的 latency delta 写成架构结论。

## 本次证据支持的结论

1. 两条路径都能在共享历史上自主形成 `triage → coding → writing` 的能力链，并利用真实 Python 执行反馈完成任务。
2. Transfer 通过替换 system prompt 和工具集形成更强的 schema 隔离，但每次角色切换都会改变静态前缀。
3. Skill 通过稳定前缀获得更高缓存比例，但需要把角色规程追加进轨迹，并依赖 Harness 策略门形成硬工具边界。
4. 工具调用成功、数值正确、能力顺序正确仍不足以保证端到端通过；最终格式约束也是任务的一部分。

## 局限

1. 每个任务只有一组配对，`paired_n=1`，没有统计效力。
2. 两条路径共用同一模型与角色规程，结果不能外推到其他模型、提示词或工具集。
3. 任务仅覆盖 coding→writing，没有覆盖真实检索、数据冲突、注入攻击或高风险副作用。
4. 使用个人节流器后无法比较原生延迟。
5. `coding` 评分器没有独立数学真值门禁，本次额外用本地断言校验数值。
6. Skill 的高缓存比例是这一提供商、本次请求长度与单次轨迹下的观测，不是普遍保证。

