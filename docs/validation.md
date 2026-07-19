# RW Research Skill v0.7.1 验证记录

日期：2026-07-20。

## 当前证据

- 发布 Skill：19 个。
- License：Apache-2.0。
- 469 条知识原子、149 条公理、115 个案例和反例、116 条行为合同。
- 19 个 Skill 的静态自检通过。
- 仓库版本、manifest、目录、公开计数和 Skill 接续检查通过。
- 公共内容检查覆盖 Skill、文档和跨模型评测记录。469 条知识原子、115 个案例和 116 条行为合同的隐私检查失败项为 0。
- 知识原子不保留原始个人材料字段；案例和行为合同标记为合成输入。
- `rw-citation-audit` 独立结构检查通过。
- 确定性 Python 工具测试见仓库 `tests/` 和 CI 记录。

## 跨模型配对验证

运行 `2026-07-20-cross-model-v2` 使用 2 家提供方的 4 个模型入口：

- OpenAI `gpt-5.6-sol`；
- OpenAI `gpt-5.6-terra`；
- Anthropic `sonnet`，提供方用量记录包含 `claude-sonnet-4-6` 和辅助 `claude-haiku-4-5-20251001`；
- Anthropic `opus`，提供方用量记录包含 `claude-opus-4-8` 和辅助 `claude-haiku-4-5-20251001`。

评测包含 8 个合成任务，覆盖 `rw-claim-audit`、`rw-revision-patch`、`rw-research-passport` 和 `rw-research-router`。每个任务分别运行带 Skill 和不带 Skill 条件，共 64 次调用。模型工具和网络工具关闭，输出按固定 JSON Schema 解析，再用确定性规则判分。

结果：

- 带 Skill：32／32，100%；
- 不带 Skill：19／32，59.375%；
- 配对通过率差：+40.625 个百分点；
- 每个任务的带 Skill 跨模型通过率：4／4；
- 带 Skill 条件的执行或解析错误：0。

评测协议、任务、模型配置、完整输出、检查结果、CLI 版本、prompt hash 和 Skill-context hash 保存在 [`evals/cross-model/`](../evals/cross-model/)。本次 [结果摘要](../evals/cross-model/results/2026-07-20-cross-model-v2/summary.md) 标记为 `CROSS_MODEL_VERIFIED`。

第一次完整运行 `2026-07-20-cross-model-v1` 为 `CROSS_MODEL_NOT_VERIFIED`：带 Skill 26／32，路由表缺少引用核验映射，Passport 测试状态与正式 Schema 不一致。该记录保留为开发证据，没有改分后覆盖。修复定义后另建并固定第 2 组任务。

## 证据边界

- 116 条行为合同没有被全部调用执行。跨模型矩阵执行的是另存的 8 个合成任务。
- 静态自检证明文件、结构、数量和独立运行约束符合当前发布要求，不证明模型输出质量。
- v0.7.0 记录的场景结果属于维护者记录。仓库没有同时保存完整模型输出、模型版本、参数、判分和重放日志，因此不作为独立复现证据。
- 当前已有合成任务的 without-Skill 基线和跨模型执行记录。判分是字段和值的确定性检查，不使用被评模型或另一个模型做 Judge。
- 第 2 组任务在首次调用前固定，但它由仓库维护者编写，不是外部独立 benchmark。
- 运行开始时工作树含未提交变更。记录保存了 source revision、任务文件 hash、prompt hash 和 Skill-context hash；这不等同于干净 commit 上的独立复现。
- 当前状态：`CROSS_MODEL_VERIFIED` 只适用于已记录的合成任务、模型入口和版本。整包仍不标记 `VERIFIED EFFECTIVE`。

## 发布边界

- 本地硬依赖：0。
- 私人工作区路由：0。
- 真实业务材料：0。
- SkillHub 公共版保留公开来源入口，不包含私人来源摘录和本地研究材料。
- 完整发行包和 SkillHub 公共版共用 `scripts/check_public_privacy.py` 构建门。
- 安装路径使用仓库和 `npx skills add`。GitHub Release 不附带安装 zip。

## 下一步证据

- 在干净 commit 上重放第 2 组任务，确认结果文件和输入 hash 可以复核。
- 使用 3 至 5 个去标识真实任务做 project-local paired eval。
- 增加第 2 次重复运行，检查同一模型的波动。
- 由未参与 Skill 和 fixture 编写的人复核任务、预期值和结果。
