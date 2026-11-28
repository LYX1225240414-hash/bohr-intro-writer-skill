---
name: intro-writer
description: 来源约束下的引言与相关工作写作工作流，从真实材料梳理研究背景、按问题或方法路线分组比较相关工作、从已引文献缺口推导研究空白，并让每条贡献与正文方法图表结果一一对应，输出带引用映射和证据的可编辑草稿；内置可离线运行的引用核验脚本（cite_lint.py），把草稿引用与文献库逐条比对，机械检出幻觉引用、元数据不符与无出处的强断言；当用户要求写引言、整理相关工作、推导研究空白、核对贡献表述或补引用覆盖时使用。适用于期刊论文、学位论文、基金申请，支持中英文材料。
---

# 引言与相关工作：立得住、分得清、说得实、对得上

把真实论文材料变成**可直接进入论文的引言与相关工作草稿**，而不是“近年来受到广泛关注”式的空转铺垫。核心是四个可验证的性质：**立得住**（背景指向真实研究脉络与具体未解决问题）、**分得清**（相关工作按同一维度分组比较而非逐篇摘要）、**说得实**（研究空白由已引文献的缺口推出）、**对得上**（贡献与方法图表结果一一对应，引用元数据经得起逐条核对）。

## 何时使用

- 需要起草或重写“引言 / 研究背景 / 相关工作 / 研究空白 / 贡献”章节。
- 需要按问题设定、方法路线、数据与评价方式等维度对相关工作分组比较。
- 需要从已引文献的共同限制推导本文要填补的空白，并核对贡献是否有正文证据。
- 需要检查关键工作覆盖、引用元数据与论断—引用匹配。

不适用：无论文材料、要求凭空编造文献或虚构实验结果、只需一句话大纲的场景。

## 运行环境与输出路径（重要）

- 平台把本 Skill 安装到 `/skills/weekly-skill`，用固定案例运行。先读真实输入 `/input/case.json` 与 `/input/task.md`，`case.json` 中可能有 `case_id`、`output_contract`、论文与文献库路径、目标文体/引用格式；**以实际字段为准，不从标签或文件名推断材料内容**。
- 中间文件写在 `/app/work`，不要污染输入目录；资源从 `/skills/weekly-skill/resources/` 读取。
- 最终产物写到 `/app/output/result.json`（UTF-8 合法 JSON），并同时保存**可编辑草稿** `/app/output/introduction_draft.md` 与**引用证据表** `/app/output/claim_citations.md` 供复核。
- `result.json` 必须原样回填 `case_id`，并完整包含 `output_contract` 的全部字段（不得改名、不得遗漏），再补充本 Skill 的扩展字段；若合同字段与本表同名，以合同为准。
- 预算内**尽早写入诚实的部分结果**再增量完善；3 个案例、每条件 3 次运行由平台安排，参赛者不提供测试案例或白板。
- 禁止提交预制答案、正式案例答案、假造的运行日志或评测成绩；本 Skill 包内不应含任何 `result.json`。

## 输入输出

输入：论文正文/摘要/图表说明或路径、参考文献库或路径、目标文体与引用格式、需突出的研究问题。

输出：`result.json` 字段如下（`output_contract` 优先）：

| 字段 | 要求 |
|---|---|
| case_id | 从 case.json 原样回填；确实没有才填 `N/A` |
| status | `success` / `partial` / `unable` / `refused`；部分完成须说明未完成范围与人工接管位置 |
| introduction_draft | 对象，含 `background` / `related_work` / `gap` / `contributions` 四段**完整可编辑正文**，段落与论断可继续编辑；缺失材料处明确标注而不是编造 |
| related_work_groups | 数组，每项含 `group_id` / `dimension` / `works` / `comparison` / `anchor`；同组按同一比较维度写出取舍与局限 |
| claim_citations | 数组，每项含 `claim_id` / `claim` / `ref_id` / `evidence` / `anchor` / `match_basis` / `confidence`（high/medium/low）；每条论断的支撑可逐句回查 |
| gap_derivation | 数组，每项含 `gap_id` / `premise_refs` / `reasoning` / `anchor`；从已引文献共同限制或未覆盖场景推出，并说明本文如何对应 |
| contribution_map | 数组，每项含 `contribution_id` / `statement` / `evidence_in_paper` / `anchor` / `boundary`；每条贡献在正文方法/图表/结果中有对应证据，并写明适用范围边界 |
| reference_coverage | 数组，每项含 `ref_id` / `authors` / `year` / `venue` / `cited_in` / `metadata_complete` / `verified`；缺失元数据填“原文未述” |
| verification | 对象，逐项给 `result`（pass/fail/na）与 `evidence`（含具体计数或抽查片段）：`background_specificity`、`grouping_consistency`、`claim_ref_match`、`gap_from_sources`、`contribution_evidence`、`coverage`、`no_new_facts` |
| uncertainties | 材料不足、引用查不到原文、空白缺乏依据、目标格式未知等条目及原因 |
| sources | 使用的输入文件与页码/段号范围，界定输入边界 |
| change_log | 自检回修记录：问题、修正、位置 |

**锚点格式**：`p<页>:<段>` / `<章节>:<段>` / `fig<号>` / `tab<号>` / `eq<号>` / `ref:<ref_id>`，必须指向输入材料的真实位置。

## 工作流

### 第 1 步：解析案例与建立证据台账
打开并读取全部输入文件，记录 `sources` 与 `output_contract` 字段，立即写骨架 `result.json`（`status: partial`、`case_id` 已填）。从材料中摘出：研究问题、关键工作、方法与结果、图表证据、文献库字段；缺文件 → `status: unable` 并写明路径。

### 第 2 步：研究背景立得住
按“领域脉络 → 具体问题 → 技术约束 → 为什么现在值得做”组织 `background`，每个关键论断配 `claim_citations`，引用落到具体论断句。禁止“近年来受到广泛关注”式空转；材料中没有的紧迫性判断写入 `uncertainties` 或明确标为作者判断。

### 第 3 步：相关工作按维度分组比较
建立比较维度（问题设定 / 方法路线 / 数据与评价方式 / 适用条件），把文献按维度分组写入 `related_work_groups`，逐组写共同点、差异与取舍，而不是逐篇摘要拼接。转述他人结论须与原文一致，限定条件与否定关系原样保留；`evidence` 短引须能在 `anchor` 找到。

### 第 4 步：从证据推导空白与贡献
`gap_derivation` 每条必须列出 `premise_refs`（哪些已引工作的共同限制、未覆盖场景或相互冲突结论）与推理链，再说明本文工作如何填补。`contribution_map` 每条必须给出正文方法/图表/结果的 `evidence_in_paper`，并写明 `boundary`（不夸大适用范围）。无依据的空白或贡献不得写出，写入 `uncertainties`。

### 第 5 步：引用覆盖与三重自检（关键）

**先跑机械核验，再做人工判断**——引用是否真实存在、元数据是否对得上、断言是否有出处，这三项可以完全机械化：

```bash
C=/skills/weekly-skill/resources/scripts/cite_lint.py
python3 "$C" scan    --materials /app/work/materials --out /app/work/refs.json
python3 "$C" check   --refs-json /app/work/refs.json \
                     --draft /app/output/intro_related_work.md --out /app/work
python3 "$C" contrib --draft /app/output/intro_related_work.md --out /app/work
```

| 输出类别 | 含义 | 必须动作 |
|---|---|---|
| `hallucinated` | 草稿引用了文献库里查不到的条目 | **必须处理**：确认文献真实存在并入库，否则删除该引用（这是最严重的错误） |
| `metadata_mismatches` | 编号/年份/作者与文献库不一致 | 按文献库原值改正 |
| `uncited_assertions` | 含"表明/证明/优于/显著"等强断言但无引用 | 补引用，或改写为作者判断并显式标注 |
| `unused` | 文献库有、草稿未引 | 评估是否属于必须覆盖的关键工作，补进相关工作 |
| `matched` | 可回查且元数据一致 | 直接作为 `claim_citations` 的条目 |

`cite_report.md` 是人读版（按类别分组，带行号）；`cite_report.json.verification_hint` 给出四项计数口径。`contrib` 子命令检查贡献段里的"图 N / 表 N"是否在正文真实存在，防止贡献与图表对不上。

**支持的引用写法**（`check` 会全部识别，漏一种就会把有引用的段落误判成"断言无引用"）：

| 写法 | 例子 | 说明 |
|---|---|---|
| 编号式 | `[1]` `[1,3]` `[2-5]` | 与编号式文献表对齐 |
| LaTeX 式 | `\cite{smith2020}` `\citep{a,b}` | 按 bibitem key 对齐 |
| **键式** | `[smith2020]` `[@smith2020]` `[smith2020; lee2021]` | markdown 草稿最常见的写法 |
| 作者-年份 | `(Smith et al., 2023)` `Smith et al. (2023)` | 走姓氏+年份匹配 |

键式判定有条防误报规则：只有 pandoc 写法 `[@key]`，或键内带四位年份（`19xx`/`20xx`）才算引用，因此 `[GPU]`、`[LiFePO4]` 这类缩写与化学式不会被当成引用标记。

**文献库解析**支持单行与多行 bib、嵌套花括号字段、编号式文献表与 JSON 导出；`scan` 会给出每个文件的 `count` 与 `skipped` 原因（未检出条目时会明说，不会静默返回空库）。

`--out` 既可传目录也可传文件名（`scan --out refs.json` 与 `scan --out /app/work` 都可用）。

脚本测不出的部分仍需人工判断：转述是否忠实于原文结论、分组维度是否统一、空白是否真由已引文献的缺口推出、贡献是否夸大了适用范围。

逐项核对 `resources/checklist.md`，把结果写入 `verification`（**优先用脚本计数**，不要只写“通过”）：
1. **覆盖计数**：关键工作数 / 已引用数、近五年进展是否覆盖、四段草稿是否齐全、引用元数据字段完整数 / 总数。
2. **回查**：抽查每条 `claim_citations`，按 `anchor` 找到 `evidence` 且文献结论确实支撑论断；统计成功数 / 总数，失败即修正或降 confidence 并写入 `uncertainties`。
3. **一致性**：分组维度是否统一、空白是否由已引文献推出、贡献是否与正文证据一一对应、是否新增材料外事实。发现问题回到第 2–4 步修正并记入 `change_log`。
完成后 `status` 才能置 `success`；仍有未解决项则置 `partial` 并列出可人工接管位置。

### 第 6 步：输出可核验产物
写 `/app/output/result.json`、可编辑草稿与引用证据表；确认 `case_id` 已回填、`output_contract` 字段齐全、`verification` 含计数、`uncertainties` 与 `change_log` 如实填写。

## 异常处理

| 情况 | 处理 |
|---|---|
| 论文材料缺失 / 文献库为空 | 写明缺失路径，`status: unable` 或 `partial`，不代写事实 |
| 引用查不到原文 / DOI 无法核验 | `verified: false`，写入 `uncertainties`，保留原始元数据 |
| 目标期刊格式未知 | 按材料中出现的格式处理，并在 `uncertainties` 请求确认 |
| 语言切换 / 中英混排 | 草稿语言随任务要求，专有名词与题名保留原文写法 |
| 空白缺乏文献依据 | 不强行推导，写入 `uncertainties` 并标注为作者判断 |
| 超长输入 / 预算紧张 | 分块处理、save early，标注已完成部分，宁可 `partial` 也不编造 |

## 资源

- `resources/scripts/cite_lint.py`：**执行内核**。`scan` 解析 bib/编号式/JSON 文献库 → `refs.json`；`check` 比对草稿引用，分出幻觉引用/元数据不符/断言无引用/未引用；`contrib` 检查贡献段的图表引用是否可解析。纯标准库，无第三方依赖。
- `environment/resources.yaml`：资源清单、依赖、运行时与产物说明。
- `resources/checklist.md`：自检与计数清单。
- `resources/field_dict.md`：字段字典、锚点格式、分组维度与贡献边界示例。
- `resources/grouping_template.md`：相关工作分组比较与空白推导模板。
- `resources/output_example.json`：输出结构示意（非答案）。
- `examples/README.md`：最小调用示例。

## 最小示例（示意，非真实论文草稿）

```bash
C=/skills/weekly-skill/resources/scripts/cite_lint.py
python3 "$C" scan  --materials /app/work/materials --out /app/work/refs.json
python3 "$C" check --refs-json /app/work/refs.json --draft /app/output/intro_related_work.md --out /app/work
cat /app/work/cite_report.md
```

示意输出（仅结构）：

```json
{"library_size": 18, "citation_marks": 14, "matched_count": 14,
 "hallucinated_count": 0, "metadata_count": 0, "unused_count": 4,
 "uncited_assertion_count": 1, "citation_precision": 1.0, "coverage": 0.778}
```

真正的结果必须来自本次实际运行，示意输出不得冒充正式案例答案。
