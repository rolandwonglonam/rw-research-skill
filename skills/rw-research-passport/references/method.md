# 方法

## 输入

- 用户原问题和研究项目名称。
- 当前阶段、已有材料、已做判断和仍未解决的问题。
- 原始材料路径或稳定标识符。

## 执行

1. 为项目建立唯一 `project_id`。
2. 为材料、判断、未知项和交接分别建立稳定 ID。
3. 只记录当前能确认的状态；推断和未知项分开保存。
4. 交接时列出输入材料 ID、输出位置和接收 Skill。
5. 每次更新写入 `audit_log`，说明动作、对象和原因。
6. 运行脚本验证，再人工核对原始材料指针。

## 状态变化

- 材料：`raw -> extracted -> verified`。
- 不能使用：`raw/extracted -> rejected`。
- 被新版本替代：任意状态 `-> superseded`。
- 判断：`proposed -> confirmed/rejected/superseded`。
- 未知项：`open -> resolved/blocked`。
- 交接：`prepared -> accepted/rejected`。

状态变化不是自动发生的。每次变化都要有审计记录。
