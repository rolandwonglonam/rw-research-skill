# RW Research Skill v0.7.1 验证记录

日期：2026-07-19。

## 当前证据

- 发布 Skill：19 个。
- License：Apache-2.0。
- 469 条知识原子、149 条公理、115 个案例和反例、116 条行为合同。
- 19 个 Skill 的静态自检通过。
- 仓库版本、manifest、目录、公开计数和 Skill 接续检查通过。
- 公共内容检查覆盖 315 个文件、469 条知识原子、115 个案例和 116 条行为合同，失败项为 0。
- 知识原子不保留原始个人材料字段；案例和行为合同标记为合成输入。
- `rw-citation-audit` 独立结构检查通过。
- 确定性 Python 工具测试见仓库 `tests/` 和 CI 记录。

## 证据边界

- 行为合同保存输入和预期约束，当前构建不会调用模型执行全部合同。
- 静态自检证明文件、结构、数量和独立运行约束符合当前发布要求，不证明模型输出质量。
- v0.7.0 记录的场景结果属于维护者记录。仓库没有同时保存完整模型输出、模型版本、参数、判分和重放日志，因此不作为独立复现证据。
- 当前没有 without-skill 基线、盲评、held-out 路由评测或跨模型效果证据。
- 当前状态：`STATIC-CHECKED`。工具化 Skill 可作为 `TRIAL-CANDIDATE`，不标记 `VERIFIED EFFECTIVE`。

## 发布边界

- 本地硬依赖：0。
- 私人工作区路由：0。
- 真实业务材料：0。
- SkillHub 公共版保留公开来源入口，不包含私人来源摘录和本地研究材料。
- 完整发行包和 SkillHub 公共版共用 `scripts/check_public_privacy.py` 构建门。
- 安装路径使用仓库和 `npx skills add`。GitHub Release 不附带安装 zip。

## 下一步证据

- 为 `rw-claim-audit`、`rw-revision-patch` 和 `rw-research-passport`保存可重放 fixture 和确定性测试。
- 使用真实任务做 project-local paired eval。
- Router 使用未出现在行为合同中的 held-out 任务单独评测。
