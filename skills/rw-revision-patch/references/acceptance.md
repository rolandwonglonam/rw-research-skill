# 验收

- `SKILL.md` 前置字段只有 `name` 和 `description`。
- 至少 10 条知识原子、5 条公理和 3 个行为测试。
- `anchor` 不修改原始文件。
- manifest 包含文稿 hash、块 ID 和块 hash。
- `check` 能发现基础 hash、块 hash和重复块错误。
- `apply` 先验证全部操作，再生成新文件。
- report 包含修改块、保留块、保留比例和新文稿 hash。
- 修改比例超过 60% 时默认停止。
