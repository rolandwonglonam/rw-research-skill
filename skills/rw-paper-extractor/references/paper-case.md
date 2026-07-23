# Paper Case 精读流程

需要处理本地 PDF、提取图表或生成分阶段报告时使用本流程。

## 依赖

- Python 3。
- PyMuPDF。
- Pillow。只用于把跨页表格渲染为一张拼接图。

依赖缺失时明确报告，不改用外部模型上传 PDF。

## 1．建立工作区

```bash
python3 scripts/paper_case.py build \
  --pdf paper.pdf \
  --output paper-case \
  --title "Paper title" \
  --doi "10.xxxx/example"
```

Zotero 标识是可选字段：

```bash
python3 scripts/paper_case.py build \
  --pdf paper.pdf \
  --output paper-case \
  --title "Paper title" \
  --zotero-library-id 1 \
  --zotero-key ITEMKEY \
  --zotero-attachment-key ATTACHMENTKEY
```

脚本不复制 PDF，不调用外部模型。

## 2．检查证据

重点检查：

- `evidence/section-map.json`：章节、识别依据和置信度。
- `evidence/text-units.jsonl`：page、bbox、原文和 text unit locator。
- `evidence/visual-evidence.jsonl`：图表候选、复核状态、分段 locator 和图片 hash。
- `visuals/`：单页图表或跨页拼接图。

跨页拼接图用灰线表示换页。`segments` 中的各页 bbox 才是来源定位。

## 3．建立分阶段报告

```bash
python3 scripts/paper_case.py scaffold --output paper-case
```

生成：

1. `stages/01-question.md`
2. `stages/02-methods.md`
3. `stages/03-results-and-visuals.md`
4. `stages/04-limits.md`
5. `stages/05-conclusion.md`
6. `report.md`

每个事实都填写 text unit、page、table、figure 或 supplement locator。视觉候选在复核前不作为已确认依据。

## 4．记录阶段 hash

阶段完成后记录自身产物和上游文件：

```bash
python3 scripts/paper_case.py mark-stage \
  --output paper-case \
  --stage report_assembled \
  --artifact report.md \
  --upstream stages/01-question.md \
  --upstream stages/02-methods.md \
  --upstream stages/03-results-and-visuals.md \
  --upstream stages/04-limits.md \
  --upstream stages/05-conclusion.md
```

来源、配置、阶段产物或上游文件改变后，`validate` 返回 STALE。

## 5．Claim Audit

把 `evidence/claim-candidates.jsonl` 中的候选主张写入 `rw-claim-audit`。每条主张保存来源指针和 locator。

```bash
python3 scripts/paper_case.py validate --output paper-case
```

Claim Audit 的 BLOCK 不能进入 LitNet。REVIEW 只能保存为待核。PASS 才能进入回写预览。

## 6．LitNet 回写预览

```bash
python3 scripts/paper_case.py litnet-preview \
  --output paper-case \
  --claim-audit paper-case/audit/claim-audit.json \
  --litnet-work w_example \
  --zotero-record zotero_example
```

输出 `litnet-writeback-preview.json`，其中 `write_performed` 固定为 `false`。预览只提供 Paper Case、报告、视觉证据和主张门禁状态，不修改 LitNet。
