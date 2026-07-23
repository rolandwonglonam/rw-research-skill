---
name: rw-paper-extractor
description: |
  从论文 PDF 和补充材料中提取结构化字段、章节、图表、原文位置、缺失项和可支持的判断，并可建立带 hash 的 Paper Case 和分阶段精读报告。 Use when the user asks for “提取这篇论文”、“批量抽论文信息”、“做论文卡片”、“精读 PDF”、“提取图表” or “分阶段精读报告”. Runs without a private local workspace or preset research-lab; use user-provided material and bundled public-source methods.
---

# RW Paper Extractor

从论文和补充材料中提取结构化字段、原文位置、缺失项和可支持的判断。

## 启动

1. 读取 `references/standalone.md`、`references/method.md` 和 `references/standards.md`。
2. 读取用户本轮提供的材料；没有材料时，只完成当前证据允许的部分。
3. 需要规则判断时检索 `references/atoms.jsonl`；遇到相似任务时读取 `references/cases.md`。
4. 需要选择方法或工具时读取 `references/domain-guide.md`，并使用 `assets/worksheet.md` 组织交付。
5. 读取 `references/acceptance.md`。`references/behavior-tests.json` 只用于测试，不作为用户任务事实。
6. 当前文献、API、报告规范和期刊要求可能变化时，打开 `references/source-map.md` 中的官方链接核验并记录日期。
7. 用户需要 PDF 工作区、图表提取或分阶段精读时，读取 `references/paper-case.md`，并使用 `scripts/paper_case.py`。

## 工作阶段

1. 确认提取目的、研究类型、可用全文和补充材料。
2. 为论文建立题名、作者、年份、来源、DOI、PMID 或其他稳定标识。
3. 按研究类型选择字段，并先记录提取 schema 的版本。
4. 提取研究问题、设计、样本、变量、方法、结果、限制和资金披露。
5. 为关键字段保存页码、段落、表、图或补充材料位置。
6. 执行第二遍核对，区分缺失、未报告、不适用和无法判断。

## PDF 精读流程

1. 为原始 PDF 建立 Paper Case，记录来源 hash、配置 hash 和隐私状态。
2. 生成带 page、bbox 和 text unit 的文本证据；章节识别保留判断依据和置信度。
3. 提取图表候选。跨页表格生成拼接图，同时保留每一页的独立 locator。
4. 生成 5 个阶段文件和合并报告脚手架。报告只能使用已有证据单元。
5. 把候选主张交给 `rw-claim-audit`。门禁为 PASS 后，才生成 LitNet 回写预览。
6. LitNet 预览不执行写入；Zotero 或用户原始文件仍是来源正典。

## 运行规则

- 提取 schema 由后续用途决定，不能对所有论文使用同一张空表。
- 标题和摘要只能提供它们实际报告的信息。
- Methods、Results 和 Discussion 的陈述类型要分开。
- 作者解释不能写成测得结果。
- 没有正文时不能推断随机化、盲法、模型设定或缺失数据处理。
- 表图中的分母、单位、时间点和分析集必须一起提取。
- 调整后和未调整结果不能混写。
- 主要、次要、探索性和事后分析要区分。
- 未报告、零事件和不适用不是同一个值。
- 批量提取前先用两篇不同结构的论文试表。
- 机器提取的字段要保留置信度和复核状态。
- 关键字段修改时保留原值、修改值和理由。
- 自动识别的章节和图表都要保留置信度或复核状态。
- 拼接图是阅读产物，不替代原始页码和 bbox。
- 来源、配置或上游阶段 hash 改变时，将下游结果标为 STALE。

## 输出

- 结构化论文卡片或批量表。
- 原文定位、置信度和复核状态。
- 缺失项、冲突和待补材料。
- 可选 Paper Case、分阶段报告、Claim Audit 接续和 LitNet 回写预览。

## 停止条件

- 没有可访问正文时，不填写正文专属字段。
- 无法定位原文的关键字段不能标为已核验。
- 不绕过访问限制获取论文。
- 不把报告规范缺项自动判为研究没有实施。

## 独立运行

- 默认不读取私人工作区、个人语料目录或预设 research-lab。
- 用户提供的文件、文本、链接和数据是当前任务输入，不是安装依赖。
- 网络不可用时，使用 Skill 内的稳定方法继续；需要当前事实的部分标记为待核验。
- 本包内其他科研 Skill 存在时可以接续；单独安装时直接返回下一步说明，不停止当前任务。

## 来源纪律

- 把用户材料、公开来源、当前推断和未知事项分开。
- 报告规范只检查报告透明度，不自动证明设计质量。
- 公开来源摘要保存在 Skill 内；需要版本、费用、政策、API 或期刊现状时回到官方页面。
- 不生成不存在的论文、数据、DOI、工具运行结果或期刊要求。
