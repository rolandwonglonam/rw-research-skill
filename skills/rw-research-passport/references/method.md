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

## 原始材料版本变化

材料有已记录的 `content_sha256`，且当前内容 hash 不同时：

1. 不覆盖旧材料记录。把旧材料标为 `superseded`。
2. 用新 ID 登记新版本，并在 `supersedes_id` 指向旧材料。
3. 把只依赖旧材料的 `confirmed` 判断标为 `superseded`；复核结果另建 `proposed` 判断。
4. 把仍引用旧材料的 `prepared` 交接标为 `rejected`。
5. 在 `audit_log` 分别记录材料、判断和交接的变化原因。
6. 新材料完成核验、依赖判断重新确认并建立新交接前，不接受交接。

`superseded` 和 `rejected` 表示旧版本不能继续使用，不表示新版本内容错误。
