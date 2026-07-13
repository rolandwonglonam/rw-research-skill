# 验收

- `SKILL.md` 前置字段只有 `name` 和 `description`。
- 至少 10 条知识原子、5 条公理和 3 个行为测试。
- 每条 claim 有稳定 ID、文稿位置、类型和 verdict。
- `VERIFIED` 必须有来源、locator 和 support note。
- `validate` 能发现重复 ID、无效 verdict 和缺失定位。
- `gate` 对 PASS、REVIEW 和 BLOCK 使用不同退出码。
- 脚本不自动把来源存在写成主张已验证。
