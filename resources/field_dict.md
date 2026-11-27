# 字段字典与判定规则

## 输出字段
- `case_id`：从 `/input/case.json` 原样回填；缺失填 `N/A`。
- `status`：`success` / `partial` / `unable` / `refused`。
- `introduction_draft`：含 `background` / `related_work` / `gap` / `contributions` 四段完整可编辑正文。
- `related_work_groups[]`：`group_id`、`dimension`、`works`、`comparison`、`anchor`。
- `claim_citations[]`：`claim_id`、`claim`、`ref_id`、`evidence`、`anchor`、`match_basis`、`confidence`。
- `gap_derivation[]`：`gap_id`、`premise_refs`、`reasoning`、`anchor`。
- `contribution_map[]`：`contribution_id`、`statement`、`evidence_in_paper`、`anchor`、`boundary`。
- `reference_coverage[]`：`ref_id`、`authors`、`year`、`venue`、`cited_in`、`metadata_complete`、`verified`。
- `verification`：每个键含 `result`（pass/fail/na）与 `evidence`（带计数或抽查短引）。
- `uncertainties` / `sources` / `change_log`：均为数组，逐条写明位置与原因。

## 锚点格式
`p<页>:<段>`、` <章节>:<段>`、`fig<号>`、`tab<号>`、`eq<号>`、`ref:<ref_id>`。
每条 `claim_citations` 必须能在其 `anchor` 位置找到 `evidence` 短引，找不到即判 fail 并回修。

## 分组维度（related_work_groups.dimension）
| 维度 | 比较内容 | 典型错误 |
|---|---|---|
| 问题设定 | 输入、目标、评价方式是否相同 | 把不同任务的工作混为一组 |
| 方法路线 | 模型/算法/假设与适用条件 | 按年份排序逐篇摘要 |
| 数据与评价 | 数据集、指标、实验设置 | 只说“效果更好”不写条件 |
| 局限与边界 | 已知限制、失败场景 | 忽略他人工作的适用条件 |

## 贡献边界（contribution_map.boundary）
- 写明成立条件（数据集、任务、指标范围），未验证的推广写“本文未验证”。
- 每条贡献须在正文方法/图表/结果中有对应证据；无证据者写入 `uncertainties`。

## confidence
- `high`：直接原文短引 + 可回查锚点 + 文献主题结论明确匹配。
- `medium`：有锚点但需结合上下文判断，或元数据轻微缺失。
- `low`：材料不足、推断或存在冲突；必须同步写入 `uncertainties`。
