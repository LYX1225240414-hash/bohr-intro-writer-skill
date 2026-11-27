# 相关工作分组、空白推导与贡献对照模板

> 以下均为结构模板，不含任何真实案例答案。

## 相关工作分组模板

```text
group_id: G1
dimension: 方法路线
comparison:
  common: [组内工作共同的前提/目标]
  differences:
    - ref_id: [文献号]
      approach: [路线概述，忠实转述]
      data_metric: [数据与评价方式]
      limitation: [原文明确给出的限制或适用条件]
      anchor: [原文位置]
  takeaway: [按同一维度比较后的取舍结论，不新增事实]
```

写法要求：
- 先写比较维度，再选文献；不要先堆文献再找维度。
- 每条 limitation 必须来自原文或明确标为本文判断。
- 同组工作数量 > 1 时必须有可比较的维度描述，否则拆组。

## 研究空白推导模板

```text
gap_id: GAP1
premise_refs: [ref:A, ref:B]
reasoning:
  - [A 在场景 X 下的限制（引原文锚点）]
  - [B 在场景 Y 下的限制（引原文锚点）]
  - [两者共同未覆盖的场景 Z / 相互冲突的结论]
  => [空白：需要解决的具体问题，而非笼统的“研究不足”]
anchor: [支撑上述前提的原文位置]
response: [本文工作如何对应这一空白]
```

判定：任一 premise 缺少原文锚点则不得写出空白，写入 `uncertainties`。

## 贡献对照模板

```text
contribution_id: C1
statement: [一条可核对的贡献，限定到具体任务/条件]
evidence_in_paper:
  - anchor: fig3 / p6:2 / [方法章节位置]
    excerpt: [原文或图表中的具体证据]
boundary: [成立条件与未验证的推广范围]
```

常见失败模式：
- 贡献与实验结果无对应图表 → 删除或降级为“作者判断”。
- 把“性能更好”写成贡献但不写数据与条件 → 补 `evidence_in_paper` 与 `boundary`。
- 贡献之间重复 → 合并为一条，保留全部证据锚点。
