# Patch JSON

```json
{
  "schema_version": "rw-revision-patch/v1",
  "base_document_hash": "manifest 中的 hash",
  "operations": [
    {
      "op": "replace",
      "block_id": "B0002",
      "expected_hash": "旧块 hash",
      "new_text": "替换后的完整块正文",
      "reason": "为什么修改",
      "issue_ids": ["REV-001"]
    }
  ]
}
```

规则：

- `base_document_hash` 必须与 anchored 文稿一致。
- 每个 `block_id` 只能出现一次。
- `expected_hash` 来自 manifest。
- `new_text` 是完整替换块，不是搜索替换片段。
- `reason` 不能为空。
- `issue_ids` 可以为空数组，但处理审稿意见时必须填写。
