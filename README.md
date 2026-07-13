# RW Research Skill

Roland Wayne 提供的科研工作流 Skill。

## v0.6.0 包含什么

本包包含 16 个独立 Skill：

- `rw-research-router`、`rw-research-question`。
- `rw-literature-discovery`、`rw-paper-extractor`、`rw-evidence-map`、`rw-research-novelty`。
- `rw-review-methods`、`rw-research-design`、`rw-research-referee`。
- `rw-research-passport`、`rw-claim-audit`、`rw-revision-patch`。
- `rw-phd-write`、`rw-phd-tone`、`rw-journal-submission`。
- `rw-research-lab-router`。

这些 Skill 处理研究问题、文献发现、论文提取、证据整理、候选创新点生成与筛选、综述方法、研究设计、研究状态、主张核验、局部修订、研究审查、学术写作、作者语气、期刊投稿和科研工具选择。

## v0.6.0 更新

- 新增 `rw-research-passport`：保存单个研究项目的材料、判断、未知项、阶段和交接状态。
- 新增 `rw-claim-audit`：区分来源存在、引用格式和来源是否支持具体主张。
- 新增 `rw-revision-patch`：按稳定 Markdown 块执行 hash 校验后的局部替换，并报告未修改内容的保留比例。
- 更新 `rw-research-router` 和 Skill 关系图，使 3 个新流程进入科研路由。

## License

本项目使用 [Apache License 2.0](LICENSE)。

## 使用方式

不知道从哪里开始时，使用 `rw-research-router`。研究阶段明确时，可以直接调用对应 Skill。

每个 Skill 自带适用的方法、规则、案例、反例、模板或工作表和自检脚本。它们不要求私人工作区、个人语料目录或预设 research-lab。

## 本地同步

发布目录中的 Skill 是工作区源码的生成副本。更新源码后运行：

```bash
python3 scripts/sync_from_workspace.py
python3 scripts/build_release.py
```

发布包输出到 `dist/rw-research-skill-版本号.zip`。

## 发布前检查

- `VERSION`、`manifest.json` 和 `plugin.json` 版本一致。
- `LICENSE` 使用 Apache-2.0。
- 16 个 Skill 通过结构检查和独立运行自检。
- 发布包没有私人工作区路径、真实业务材料、本地状态或报告。

公共仓库：[rolandwonglonam/rw-research-skill](https://github.com/rolandwonglonam/rw-research-skill)。
