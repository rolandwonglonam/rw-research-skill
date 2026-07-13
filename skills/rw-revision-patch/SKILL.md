---
name: rw-revision-patch
description: |
  将 Markdown 文稿切成带稳定 ID 和 hash 的段落块，只对用户批准的块执行替换，并输出保留比例、修改理由和问题追踪报告。Use when the user asks for“只改这几段”“按审稿意见局部修改”“保留其他内容不动”“生成可复核修改 patch”,or requests the rw-revision-patch workflow.
---

# RW Revision Patch

限制修改范围。第一版只替换已有 Markdown 块，不静默增加、删除或重排章节。

## 启动

1. 读取 `references/method.md` 和 `references/patch-format.md`。
2. 保留原始文稿，运行 `scripts/revision_patch.py anchor` 生成带块 ID 的副本和 manifest。
3. 根据已批准的修改范围建立 Patch JSON。
4. 运行 `check`，确认 hash、块 ID、修改比例和问题 ID。
5. 运行 `apply` 生成新文稿和报告。
6. 对修改块复核内容，对未修改块核对 preserved ratio。

## 命令

```bash
python3 scripts/revision_patch.py anchor draft.md --output draft.anchored.md --manifest draft.manifest.json
python3 scripts/revision_patch.py check draft.anchored.md --manifest draft.manifest.json --patch revision.patch.json
python3 scripts/revision_patch.py apply draft.anchored.md --manifest draft.manifest.json --patch revision.patch.json --output draft.revised.md --report revision.report.json
```

修改块超过全文 60% 时停止。只有用户明确同意大范围修改后才能加入 `--allow-large-patch`。

## 工作阶段

1. 固定基础文稿和版本 hash。
2. 把标题、段落、列表或代码块按空行边界编号。
3. 将每项修改连接到块 ID、旧 hash、理由和 issue ID。
4. 先验证所有操作；任意一项失败时不生成部分结果。
5. 生成新文件，不覆盖原文件。
6. 输出修改块、保留块、保留比例和新 hash。

## 运行规则

- 原文件不被修改。
- Patch 第一版只支持 `replace`。
- 一个块在一次 Patch 中只能修改一次。
- `expected_hash` 必须与 manifest 一致。
- `new_text` 不能包含 RW block marker。
- 任意 precondition 失败时整批停止。
- 未涉及块的正文保持原样。
- 新增、删除、重排章节进入结构修改，不伪装成局部替换。
- Patch 只能限制改动范围，不能证明修改内容正确。

## 输出

- Anchored Markdown 副本。
- Block manifest JSON。
- Patch JSON。
- Revised Markdown 新文件。
- Apply report JSON，包含 preserved ratio 和修改追踪。

## 停止条件

- 输入文稿没有稳定版本时，不生成 Patch。
- hash、块 ID 或基础文稿不匹配时停止。
- 修改比例超过 60% 且用户没有明确批准时停止。
- 需要新增、删除或重排章节时，改走结构修订流程。

## 接续

- 学术写作：`rw-phd-write`。
- 作者语气：`rw-phd-tone`。
- 审稿回复：`rw-journal-submission`。
- 主张复核：`rw-claim-audit`。
