# Passport JSON 结构

必需顶层字段：

- `schema_version`：固定为 `rw-research-passport/v1`。
- `project_id`：项目稳定 ID。
- `title`：项目名称。
- `stage`：`question`、`discovery`、`extraction`、`synthesis`、`design`、`analysis`、`writing`、`review`、`submission` 或 `closed`。
- `updated_at`：UTC ISO 8601 时间。
- `materials`：材料数组。
- `decisions`：判断数组。
- `unknowns`：未知项数组。
- `handoffs`：交接数组。
- `audit_log`：变更记录数组。

## Material

必需字段：`id`、`type`、`title`、`source_pointer`、`status`、`added_at`。

`status`：`raw`、`extracted`、`verified`、`rejected` 或 `superseded`。

可选字段：

- `content_sha256`：当前登记版本的 SHA-256。
- `supersedes_id`：当前材料替代的旧材料 ID。

## Decision

必需字段：`id`、`statement`、`status`、`evidence_ids`、`recorded_at`。

`status`：`proposed`、`confirmed`、`rejected` 或 `superseded`。

## Unknown

必需字段：`id`、`question`、`status`。

`status`：`open`、`resolved` 或 `blocked`。

## Handoff

必需字段：`id`、`from_stage`、`to_stage`、`material_ids`、`status`、`recorded_at`。

`status`：`prepared`、`accepted` 或 `rejected`。

材料 hash 变化时，不创造新的状态枚举。旧材料和依赖判断使用 `superseded`，仍引用旧材料的待交接记录使用 `rejected`。复核后的材料、判断和交接使用新记录和新 ID。

脚本检查结构、枚举、ID 唯一性和引用材料是否存在。脚本不检查论文内容是否真实。
