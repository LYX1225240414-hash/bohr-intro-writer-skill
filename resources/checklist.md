# 引言写作自检清单（带计数，写入 verification）

## A. 输入与规则
- [ ] 已打开论文材料与文献库的实际文件并记录 `sources`，未从标签/文件名推断内容
- [ ] 目标文体、引用格式、需突出的研究问题已写入规则表，并在第 2–5 步重读
- [ ] 已写骨架 `result.json`（`status: partial`、`case_id` 已填）

## B. 立得住（background_specificity）
- [ ] 背景按“脉络 → 具体问题 → 技术约束 → 现在值得做”组织，无空转铺垫
- [ ] 每个关键背景论断有 `claim_citations` 与 `match_basis`
- [ ] 材料中没有的紧迫性判断已标注为作者判断或写入 uncertainties

## C. 分得清（grouping_consistency）
- [ ] 相关工作按同一比较维度分组（问题设定/方法路线/数据与评价/适用条件）
- [ ] 每组写出共同点、差异与取舍，而非逐篇摘要拼接
- [ ] 转述的限定条件、否定关系与原文一致；抽查 `evidence` 可回查 ___ / ___ 条

## D. 说得实（gap_from_sources）
- [ ] 每条空白都有 `premise_refs` 指向已引文献的共同限制/未覆盖场景/冲突结论
- [ ] 推理链完整，并说明本文工作如何对应；无依据的空白写入 uncertainties

## E. 对得上（contribution_evidence / claim_ref_match）
- [ ] 每条贡献有正文方法/图表/结果的 `evidence_in_paper` 与 `anchor`
- [ ] 每条贡献写明 `boundary`，不夸大适用范围
- [ ] 论断—文献主题与结论匹配 ___ / ___ 条；失败项已修正或降 confidence

## F. 覆盖与诚实性（coverage / no_new_facts）
- [ ] 四段草稿（background / related_work / gap / contributions）齐全且彼此承接
- [ ] 关键工作 ___ / ___ 已覆盖；近五年进展 ___ / ___ 已覆盖
- [ ] 引用元数据完整 ___ / ___ 条；未新增材料外事实、数字或引用
- [ ] `status` 与实际一致，未完成范围写明；uncertainties / change_log 逐条可读

## 判定
- 全部通过 → `status: success`
- 任一计数失败且已标注人工接管位置 → `status: partial`
- 材料缺失不可执行 → `status: unable`
