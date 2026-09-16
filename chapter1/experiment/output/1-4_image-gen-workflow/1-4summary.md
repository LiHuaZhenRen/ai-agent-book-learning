# 实验 1-4 Summary

## 文件与命令

本次只跑了 `headphone-poster` 这一句需求的 `workflow` 路线。

成功运行命令：

```bat
python main.py --route workflow --requirement headphone-poster
```

成功运行原始证据：

```text
chapter1/image-gen-workflow/validation/real_20260916T064008Z/evidence.json
```

生成图片：

```text
chapter1/image-gen-workflow/outputs/20260916T064008Z/images/headphone-poster_workflow.png
```

学习记录中复制了一份图片：

```text
chapter1/experiment/images/1-4-headphone-poster-workflow.png
```

运行前还有一次失败记录：

```text
chapter1/image-gen-workflow/validation/real_20260916T063808Z/evidence.json
```

失败原因是 Kimi 改写节点鉴权失败：

```text
401 Invalid Authentication
```

## 运行结果

这些字段来自 `validation/real_20260916T064008Z/evidence.json`：

| 字段 | 值 |
|---|---|
| `schema_version` | `1.0` |
| `created_at` | `2026-09-16T06:40:52.859661+00:00` |
| `requirement_id` | `headphone-poster` |
| `route` | `workflow` |
| `error` | `null` |
| `image.mime` | `image/png` |
| `image.bytes` | 871,085 |
| `image.sha256` | `a04d25ff11d9d97ab58027c2a4784ec6afaf0d396e75059c68c2b68f911d8434` |

原始需求：

```text
帮我做一张新款降噪耳机的产品海报，主打“深夜独处也清净”这句文案，风格简约高级
```

## Workflow 节点

本次 workflow 有两个节点：

| 节点 | Provider | Model | 作用 | 状态 |
|---|---|---|---|---|
| `rewrite` | Moonshot | `kimi-k3` | 把中文口语需求改写为 SD 风格 prompt | ok |
| `image_generate` | DashScope | `wan2.2-t2i-flash` | 根据 prompt / negative prompt 生成图片 | ok |

Kimi 改写节点用量：

| 字段 | 值 |
|---|---:|
| `prompt_tokens` | 295 |
| `completion_tokens` | 589 |
| `reasoning_tokens` | 351 |
| `total_tokens` | 884 |

DashScope 出图节点：

| 字段 | 值 |
|---|---|
| `model` | `wan2.2-t2i-flash` |
| `size` | `1024*1024` |
| `image_count` | 1 |
| `response_bytes` | 871,085 |

## Kimi 改写结果

`prompt`：

```text
masterpiece, best quality, highly detailed, professional product photography, sleek modern wireless noise-canceling headphones, matte black finish, minimalist premium design, floating product shot, centered composition, dark midnight blue gradient background, soft moonlight rim lighting, subtle ambient glow, gentle soft shadows, serene quiet late-night atmosphere, sense of solitude and tranquility, luxury advertising poster aesthetic, clean negative space, copy space at top, studio lighting, sharp focus, 8k
```

`negative_prompt`：

```text
lowres, bad anatomy, blurry, watermark, text, logo, signature, jpeg artifacts, cluttered background, oversaturated colors, distorted shape, low quality, grainy, noise, people, hands, busy scene, harsh lighting
```

`style_notes`：

```text
将“深夜独处也清净”转译为深夜蓝渐变背景+柔和月光轮廓光来营造静谧独处感；用极简悬浮产品构图和大面积留白体现“简约高级”，并预留 copy space 供后期排版文案；因模型生成文字易出错，负面词中排除 text/watermark，建议文案后期手动添加。
```

## DashScope 实际扩写

DashScope 返回的 `actual_prompt`：

```text
Professional product photography, sleek modern wireless noise-canceling headphones in matte black finish, minimalist premium design with smooth curves and brushed metal accents. Floating centered composition against a deep midnight blue gradient background evoking night sky. Soft moonlight rim lighting highlights contours; subtle ambient glow enhances depth. Gentle, precise soft shadows anchor the product. Serene, quiet late-night atmosphere conveys solitude and tranquility. Luxury advertising poster aesthetic—clean negative space, ample copy space at top, studio-perfect sharp focus, 8K resolution, hyper-detailed texture rendering of ear cushions and headband stitching.
```

## 必要说明

- 本 summary 只整理 `workflow` 路线的一次成功运行，不代表完整 1-4 几种路线对照。
- 本次生成图满足“新款降噪耳机、深夜、简约高级”的视觉部分。
- 原始需求中的中文文案“深夜独处也清净”没有进入图片正文；改写节点将它转译为视觉氛围，并在 `negative_prompt` 中排除了 `text`。
