# RW Research Skill

把研究问题、文献、证据、研究设计、论文草稿和投稿材料，变成当前可以核验和继续推进的一步。

RW Research Skill 由 Roland Wayne 创建。当前包含 19 个科研 Skill、469 条知识原子、149 条公理、115 个案例和反例，以及 116 条行为合同。

适用于手上有研究想法、论文、数据、研究方案、章节草稿或审稿意见，需要判断下一步的人。你可以直接提交材料，也可以只说现在卡在哪里。系统会选择一个主 Skill，每次处理当前一步。

当前版本：`v0.7.1`

[新手从这里开始](#新手从这里开始) · [安装](#安装) · [常见场景](#常见场景与当前入口) · [全部 Skill](#直接调用的-skill) · [项目状态](#项目状态与接续) · [本地构建](#本地构建)

## 你可以用它做什么

| 你交付的内容 | RW Research Skill 会处理什么 |
| --- | --- |
| 一个还没定下来的研究兴趣 | 界定对象、构念、边界和可证伪条件，形成研究问题 |
| 一组需要查找或整理的文献 | 设计检索、核验来源、提取字段，并组织证据关系 |
| 文献中的冲突、空白或异常 | 区分缺证据和真冲突，生成并筛选候选创新点 |
| 一个研究方案或方法选择 | 检查设计、样本、测量、分析和替代解释 |
| 一组数据、代码、协议或材料链接 | 核对版本、标识符、访问路径、限制和数据声明 |
| 一篇带统计结果的文稿 | 核对分析单位、重复层级、方法和报告数字 |
| 一篇论文或章节草稿 | 根据已有材料组织论证，检查语气、来源支持和修改范围 |
| 一组审稿意见 | 拆分修改任务，只改批准的内容，并保留核验记录 |
| 一个持续推进的研究项目 | 保存材料、判断、未知项、阶段、交接和变更记录 |
| 一个需要选择工具的科研任务 | 根据任务、数据和环境选择工具，不把工具当成研究判断 |

## 新手从这里开始

安装后，在 Codex 中输入：

```text
$rw-research-router 新手入门
```

在其他支持 Agent Skills 的 Agent 中，直接说：

```text
请用 rw-research-router 带我新手入门。
```

新手入口不会先展示全部 Skill。它会一次问一个问题，先确认你手上有什么，再确认这次想得到什么结果，然后选择一个主 Skill。

你也可以直接提交任务：

```text
我只有一个研究想法，还没有形成研究问题：……
我有一批文献，需要判断应该先提取什么：……
这些研究的结果互相冲突，我想找能继续验证的方向：……
这是我的研究设计，请在执行前找出漏洞：……
这段论文引用了 3 篇文献，帮我检查来源是否支持这些说法：……
这是审稿意见和原稿，只修改指定段落：……
```

完成当前一步后，再次使用 `rw-research-router`。它会根据刚得到的结果选择下一步，不预先排出一条固定流程。

## 安装

### 按需安装

先查看仓库中可以安装的 Skill：

```bash
npx -y skills add rolandwonglonam/rw-research-skill --list
```

只安装研究入口：

```bash
npx -y skills add rolandwonglonam/rw-research-skill -g --skill rw-research-router
```

安装一个当前需要的 Skill：

```bash
npx -y skills add rolandwonglonam/rw-research-skill -g --skill rw-claim-audit
```

`npx -y` 会下载并执行 `skills` CLI，`-g` 会写入全局 Skill 目录。先确认仓库地址、目标目录和安装范围。

### 安装全部 Skill

需要整套科研路由时，可以安装全部 19 个 Skill：

```bash
npx -y skills add rolandwonglonam/rw-research-skill -g --all
```

如果已经有科研路由、审计或写作系统，先按需安装，避免增加重复入口。

安装后没有立即出现新入口时，新建一次对话再使用。

### 更新

已经通过 `skills` CLI 安装时，可以让 Agent 执行：

```bash
npx -y skills update
```

更新前可以检查已安装 Skill 是否有新版本：

```bash
npx -y skills check
```

## 常见场景与当前入口

RW Research Skill 每次选择一个主流程。下面使用 `$skill-name` 表示 Codex 入口；在其他 Agent 中可以直接说“使用 skill-name”。

### 不知道从哪里开始

```text
$rw-research-router 新手入门
```

入口会判断当前瓶颈属于研究问题、文献、提取、证据、创新、设计、研究材料、统计报告、项目状态、主张核验、写作、局部修订、投稿还是工具选择。

### 从研究兴趣形成问题

```text
$rw-research-question 我想研究……，帮我把它变成可检索、可证伪的问题。
```

先确认对象、构念、边界和可能推翻结论的证据，再决定是否进入文献发现或研究设计。

### 查找并整理文献

```text
$rw-literature-discovery 为这个判断寻找并核验文献：……
$rw-paper-extractor 从这些论文中提取研究设计、样本、测量和结果。
$rw-evidence-map 把这些研究的支持、冲突、偏倚和缺口连起来。
```

文献存在、字段提取和证据关系分开处理。找到论文不等于论文支持当前主张。

### 从证据空白形成研究方向

```text
$rw-research-novelty 根据这组证据冲突，生成可以继续验证的候选创新点。
```

候选方向需要标出证据来源、贡献、可行性和证伪条件。没有完成检索时，不使用“首次”或“从未研究”等表述。

### 设计研究或投稿前找漏洞

```text
$rw-research-design 把这个研究问题转成设计、样本、测量和分析计划。
$rw-research-referee 在执行前检查偏倚、替代解释和结论边界。
```

研究设计负责形成方案；研究审查负责攻击方案。两者不在同一步混用。

### 检查研究材料和统计报告

```text
$rw-research-data 检查这篇论文的数据、代码和补充材料能否取得，并整理数据声明。
$rw-statistics-audit 核对这篇文稿的分析单位、重复层级、统计方法和报告数字。
```

研究材料审查处理对象、版本、访问路径和限制。统计审查处理报告是否对得上；没有原始数据和代码时，不声称已经重新分析。

### 写作、核验和局部修改

```text
$rw-phd-write 判断当前部分的写作功能，连接证据、解释和研究问题，不补造来源。
$rw-phd-tone 保留我的学术语气，只改影响理解的部分。
$rw-citation-audit 核对文内引用、参考文献、作者、年份和 DOI。
$rw-claim-audit 检查每个事实主张是否被指定来源原文支持。
$rw-revision-patch 只修改我批准的 Markdown 段落，其他内容保持不动。
```

写作、语气、来源核验和局部修改各自保留边界。需要改稿时，先确认问题属于哪一层。

### 准备投稿

```text
$rw-journal-submission 核验目标期刊要求，并整理投稿文件和审稿回复。
```

期刊要求、费用、政策和投稿入口可能变化。执行时回到期刊官方页面核验日期和版本。

### 管理项目状态或选择科研工具

```text
$rw-research-passport 为这个研究项目建立可以交接的状态档案。
$rw-research-lab-router 根据任务、数据和当前环境选择工具。
```

项目状态保存研究材料和判断；工具路由只负责执行环境，不代替研究设计。

## 直接调用的 Skill

| 目标 | Skill |
| --- | --- |
| 判断当前研究阶段和下一步 | `rw-research-router` |
| 把研究兴趣变成问题 | `rw-research-question` |
| 发现并核验文献 | `rw-literature-discovery` |
| 从论文和补充材料提取字段 | `rw-paper-extractor` |
| 整理证据关系、冲突、偏倚和缺口 | `rw-evidence-map` |
| 生成并筛选候选创新点 | `rw-research-novelty` |
| 设计系统综述、范围综述和证据综合流程 | `rw-review-methods` |
| 建立研究设计、样本、测量和分析计划 | `rw-research-design` |
| 审查数据、代码和材料的访问与声明 | `rw-research-data` |
| 审查分析单位、重复层级和统计报告 | `rw-statistics-audit` |
| 在执行或投稿前检查研究漏洞 | `rw-research-referee` |
| 保存单个研究项目的状态和交接记录 | `rw-research-passport` |
| 核对文内引用、参考文献、作者、年份和 DOI | `rw-citation-audit` |
| 核验主张是否被指定来源支持 | `rw-claim-audit` |
| 对批准的 Markdown 块执行局部修改 | `rw-revision-patch` |
| 判断科研文本的写作功能，组织证据、解释和研究问题连接 | `rw-phd-write` |
| 提取并保持作者的学术语气 | `rw-phd-tone` |
| 核验期刊并准备投稿和审稿回复 | `rw-journal-submission` |
| 根据任务和环境选择科研工具 | `rw-research-lab-router` |

完整的前后关系见 [Skill 关系图](docs/skill-link-map.md)。

## 项目状态与接续

对话中的上下文不等于研究项目档案。需要跨对话、跨 Agent 或跨阶段继续时，使用 `rw-research-passport` 保存 JSON 状态。

状态文件记录：

- 当前研究阶段和原问题。
- 已有材料及其处理状态。
- 已确认事实、当前判断和未知事项。
- 已否定方向、停止条件和下一步。
- Skill 交接和变更记录。

主张核验使用 `rw-claim-audit` 保存来源位置、原文定位和 `PASS`、`REVIEW`、`BLOCK` 判断。局部改稿使用 `rw-revision-patch` 保存块 ID、hash、修改原因和未修改内容的保留比例。

## 知识与验收

公开包当前包含：

- 469 条结构化知识原子。
- 149 条运行公理。
- 115 个案例和反例。
- 116 条行为合同。
- 19 个独立运行静态自检脚本。

行为合同保存提示词、应做事项、不应做事项和下一步，用于后续模型评测。静态自检只检查文件、结构、数量和独立运行约束，不代表模型已经执行全部行为合同，也不证明真实任务提效。

公开内容不包含个人论文、数据、评审记录、研究项目状态或个人来源标签。案例和行为合同使用合成或占位输入。规则见 [`docs/public-content-policy.md`](docs/public-content-policy.md)。

每个 Skill 自带适用方法、来源入口、停止条件、案例、反例、工作表和自检。需要当前文献、API、期刊政策或报告规范时，仍需核验官方来源。

发布检查结果见 [v0.7.1 验证记录](docs/validation.md)。

## v0.7.1 更新

- 将行为条目标记为行为合同，不再把静态自检写成模型行为测试。
- 增加 `rw-citation-audit`，分开检查引用身份、格式和主张支持。
- 默认展示按需安装，整包全局安装改为可选路径。
- SkillHub 保留公开来源入口和原有来源标识。
- 增加仓库检查、确定性工具测试和 push／PR CI。

## v0.7.0 更新

- 修复了一些已知问题。
- 增加 SkillHub 公共版构建，合并参考资料并限制为最多 200 个文件。
- 清除公共版中的本地来源标签、个人研究材料和内部来源说明。
- 增加 `rw-research-data`，检查研究对象、版本、访问路径、限制和声明。
- 增加 `rw-statistics-audit`，检查分析单位、重复层级、统计方法和报告数字。
- 文献发现增加可取得层级、版本关系和失败来源记录。
- 审稿回复增加稳定意见编号、状态和修改位置。

## v0.6.0 更新

- 新增 `rw-research-passport`，保存研究项目的材料、判断、未知项、阶段和交接状态。
- 新增 `rw-claim-audit`，区分来源存在、引用格式和来源是否支持具体主张。
- 新增 `rw-revision-patch`，按稳定 Markdown 块和 hash 执行局部替换，并报告保留比例。
- 更新 `rw-research-router`，加入“新手入门”和 3 个新流程的路由。
- 更新 `rw-phd-write`，按写作功能判断解释义务，不按章节编号套用模式。
- 公开包增加到 16 个科研 Skill。

## 本地构建

公开仓库中的 Skill 是发布副本。维护者从工作区源码同步后运行：

```bash
python3 scripts/sync_from_workspace.py
python3 scripts/build_release.py
```

发布包生成在：

```text
dist/rw-research-skill-0.7.1.zip
```

构建过程检查版本一致性、Skill 结构和 19 个独立运行静态自检。

## License

本项目采用 [Apache License 2.0](LICENSE)。

公共仓库：[rolandwonglonam/rw-research-skill](https://github.com/rolandwonglonam/rw-research-skill)
