# 实验 2-3 Summary：KV Cache 友好的上下文设计

## 文件与证据范围

本次个人实验使用以下六份原始 JSON 作为主要机器证据：

| 模式 | 原始文件 | JSON 结果 |
| --- | --- | :---: |
| 正确模式 | `probe-correct-v2.json` | 成功 |
| 动态系统提示 | `probe-dynamic-system.json` | 成功 |
| 动态用户资料 | `probe-dynamic_profile.json` | 成功 |
| 打乱工具顺序 | `probe-shuffled-tools.json` | 成功 |
| 滑动窗口 | `probe-sliding_window.json` | 成功 |
| 纯文本历史 | `probe-text_format.json` | 失败 |

另保留 `probe-correct.json`，它是第一次正确模式探针：模型在前三轮执行了 5 次工具调用，第四轮请求因账户 `3 RPM` 限制返回 429，结果为 `success=false`。该失败文件没有被后续成功运行覆盖。

原始 JSON 只保留在本地，不默认提交 Git。六份主要 JSON 均未检出组织 ID 或 `ak-...` 标识；终端中的 429 错误曾包含服务商组织与 Key 标识，截图必须遮挡。

## 环境与运行配置

```text
操作系统：Windows
Conda 环境：agentbook
Python：3.11.16
模型：kimi-k2.6
API：Moonshot OpenAI-compatible chat completions
工具根目录：chapter2/kv-cache
本地工具：find、read_file、grep
账户限制：3 requests per minute
```

首次运行前，本地共享包尚未注册到环境，出现：

```text
ModuleNotFoundError: No module named 'agentbook'
```

随后使用以下命令只注册本地 editable package，不更新依赖：

```bat
python -m pip install -e ..\.. --no-deps
```

六个主要模式使用同一个受控任务，避免默认的跨 chapter 大型任务消耗过多请求：

```text
First call find exactly once to list *.py files. Then, in one assistant turn,
call read_file for main.py and agent.py with offset 0 and size 120. Do not read
any additional ranges. Finally summarize only the inspected portions in exactly
3 sentences.
```

命令模板如下；六组只替换 `MODE` 和输出文件名：

```bat
python main.py --no-interactive --mode MODE --model kimi-k2.6 --root-dir . --task "First call find exactly once to list *.py files. Then, in one assistant turn, call read_file for main.py and agent.py with offset 0 and size 120. Do not read any additional ranges. Finally summarize only the inspected portions in exactly 3 sentences." --output "..\experiment\output\2-3_kv-cache\OUTPUT.json"
```

由于现有 `--compare` 不在请求或模式之间加入足够冷却时间，六组按相同配置分别运行，并在组间等待以适配 `3 RPM`。因此它们不是同一个 `--compare` 进程中的连续运行。

## 六组结果

| 模式 | 成功 | 迭代 | 工具调用 | Prompt tokens | Completion tokens | Cached tokens | Cache ratio | 首轮 TTFT | 平均 TTFT | 总时间 |
| --- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `correct` | 是 | 3 | 3 | 4,820 | 763 | 768 | 15.9% | 3.261s | 6.532s | 19.598s |
| `dynamic_system` | 是 | 3 | 3 | 4,875 | 952 | 512 | 10.5% | 3.669s | 9.231s | 27.699s |
| `dynamic_profile` | 是 | 3 | 3 | 4,877 | 1,090 | 512 | 10.5% | 3.508s | 8.925s | 26.784s |
| `shuffled_tools` | 是 | 3 | 3 | 4,874 | 796 | 256 | 5.3% | 4.874s | 9.198s | 27.612s |
| `sliding_window` | 是 | 3 | 3 | 4,956 | 789 | 1,024 | 20.7% | 5.156s | 7.070s | 21.213s |
| `text_format` | 否 | 7 | 6 | 5,690 | 1,117 | 3,072 | 54.0% | 3.617s | 6.499s | 41.427s |

`Avg TTFT` 是成功收到模型响应的迭代平均值。`text_format` 的第 7 轮只有 429 错误，没有 TTFT 和 token usage，因此平均值只覆盖前六次成功响应。

## 工具轨迹与逐轮缓存

前五组都执行了相同工具轨迹并生成最终答案：

```text
Iteration 1 -> find("*.py")
Iteration 2 -> read_file(main.py, 0, 120)
               read_file(agent.py, 0, 120)
Iteration 3 -> final answer（无 tool_calls）
```

终端记录的正 `cached_tokens` 如下。`—` 表示该轮日志没有打印正的缓存 token，不等同于已经证明服务端记录了一次 cache miss。

| 模式 | Iteration 1 | Iteration 2 | Iteration 3 | 后续 |
| --- | ---: | ---: | ---: | --- |
| `correct` | — | 256 | 512 | 最终回答 |
| `dynamic_system` | 256 | — | 256 | 最终回答 |
| `dynamic_profile` | 256 | 256 | — | 最终回答 |
| `shuffled_tools` | — | 256 | — | 最终回答 |
| `sliding_window` | 256 | 256 | 512 | 最终回答 |
| `text_format` | 256 | 256 | 512 | I4=512、I5=512、I6=1024；I7=429 |

`text_format` 的工具轨迹不是预期轨迹，而是：

```text
find -> find -> find -> find -> find -> find -> 429
```

模型没有进入 `read_file`，也没有生成最终答案。第 4 轮曾先收到一次 429，SDK 重试后成功；第 7 轮在重试后仍因 RPM 限制终止。因此本次可证明纯文本历史与重复调用同时出现，但最终终止原因是 429。

## 关键对照

`correct` 与 `shuffled_tools` 的任务成功、迭代数和工具轨迹一致，prompt tokens 只相差 1.1%，但后者的 cached tokens 从 768 降至 256，减少 66.7%；cache ratio 从 15.9% 降至 5.3%。这是本次最清晰的前缀缓存证据。

`dynamic_system` 与 `dynamic_profile` 都保留了 512 cached tokens，说明动态内容不必然让整个前缀缓存归零。缓存通常只能复用到第一个变化点之前；变化位置越靠前，可复用范围越小。

`sliding_window` 的 20.7% cache ratio 不能解释为它优于正确模式。最终回答前，`conversation_history` 只有 5 条消息，而代码窗口保留最近 6 条，因此本任务没有真正裁剪历史，滑动窗口实验变量没有充分激活。

`text_format` 虽然 cache ratio 达到 54.0%，但任务失败且重复调用工具。高缓存比例只说明大量 prompt tokens 来自相同前缀，不说明这些 token 帮助 Agent 有效推进任务。

## 字段解释与证据边界

- `cached_tokens` 是 Moonshot API 上报的跨请求 prompt cache 指标。它能证明服务端复用了部分输入前缀，但不是直接读取 GPU 中 KV Cache 占用量的硬件测量。
- `Cache ratio = cached_tokens / prompt_tokens`，是比 `Hit%` 更有解释力的指标。
- 内置 `Hit%` 使用 `cache_hits / (cache_hits + cache_misses)`。本批 JSON 的 `cache_misses` 都是 0，未上报缓存字段的轮次没有进入分母，所以六组均显示 100%，不能读成每轮全部命中。
- `Bill.Tok` 和 `Save%` 假设 cached token 按正常 token 价格的 10% 计费，只是数学示意，不是 Moonshot 实际账单。
- JSON 保存了 `mode`、成功状态、最终答案、工具调用和聚合指标，但没有保存命令行中的 `model`、`task`，也没有保存 429 错误详情。模型和任务需要由运行命令与终端记录补足。
- 服务端缓存可能跨独立进程继续存在。后运行模式首轮出现 256 cached tokens，说明运行顺序和缓存预热可能影响绝对值。

## 证据能证明什么

本次证据支持以下结论：

1. 在相同短任务中，打乱工具定义顺序与显著更少的 cached tokens 同时出现。
2. 动态 system/profile 仍可保留变化点之前的部分前缀缓存。
3. 把结构化历史压成普通文本时，Agent 出现了连续重复 `find`、没有推进到读取文件的行为退化。
4. 缓存比例高不等于任务成功，必须同时检查成功状态、工具轨迹与最终答案。

本次证据不能证明：

1. 各模式延迟差异具有统计显著性；每个模式只运行一次。
2. `sliding_window` 在真正删除历史后的效果；本任务没有跨过 6 条历史消息窗口。
3. `text_format` 在没有 RPM 限流时必然以失败结束。
4. API 的 `cached_tokens` 等于可直接观测的底层 GPU KV Cache 大小。
