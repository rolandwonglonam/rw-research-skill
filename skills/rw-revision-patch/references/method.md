# 方法

## 输入门

- 固定的 Markdown 基础文稿。
- 用户批准的修改范围。
- 审稿意见、问题 ID 或其他修改理由。

## 流程

1. `anchor` 创建新副本和 manifest，不覆盖基础文稿。
2. 人或 Agent 只为批准块生成 replace operation。
3. `check` 一次验证全部 operation。
4. `apply` 在所有 precondition 通过后生成新文稿。
5. 人工复核修改块，再用 report 检查保留比例。

## 原子性

任何一个 operation 的 block ID、hash 或格式错误，整批 Patch 失败。脚本不应用已通过的那一部分。

## 结构修改

新增、删除、重排章节不能用第一版 Patch 完成。先向用户说明结构变化，再建立单独任务和验收范围。
