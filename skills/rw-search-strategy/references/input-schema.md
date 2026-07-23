# 输入结构

使用 `assets/search-strategy-template.json` 作为起点。

## 顶层字段

- `question`：保留原研究问题。必填。
- `language`：`Chinese`、`English`、`mixed` 或用户指定值。
- `framework`：`PICO`、`PCC`、`PEO`、`SPIDER` 或 `open`。
- `concepts`：概念块列表。至少 1 个。
- `targets`：需要生成的数据库平台。
- `validation`：种子文献、第二人复核和备注。

## 概念块

每个概念块包含：

- `id`：稳定且不重复的标识。
- `label`：原语言概念。
- `english_label`：英文规范表达。
- `free_text`：自由词、缩写、拼写变体和截词形式。
- `headings.mesh`：MeSH 记录。
- `headings.emtree`：Emtree 记录。
- `headings.cinahl`：CINAHL Headings 记录。
- `headings.apa`：APA Thesaurus 记录。

## 受控词记录

```json
{
  "label": "Depressive Disorder",
  "identifier": "D003866",
  "status": "verified_by_public_api",
  "source": "NLM MeSH RDF API",
  "verified_at": "2026-07-23",
  "explode": true,
  "focus": false
}
```

状态含义：

- `verified_by_public_api`：由公开官方接口核验。只适用于 MeSH。
- `verified_in_subscribed_platform`：在有权访问的订阅平台核验。
- `user_confirmed`：用户提供了可追溯的核验记录。
- `candidate`：候选词，尚未核验。
- `unverified`：当前无法核验。
- `rejected`：已经检查并排除。

只有前 3 种状态进入默认可执行检索式。运行 `render --include-candidates` 时，候选词会进入草案，但仍保留待平台核验说明。

## 订阅词表导入

导入文件可以是记录列表，也可以使用：

```json
{
  "records": [
    {
      "concept_id": "population_condition",
      "vocabulary": "emtree",
      "label": "depression",
      "identifier": "platform-record-id",
      "status": "verified_in_subscribed_platform",
      "source": "Embase.com thesaurus",
      "verified_at": "2026-07-23",
      "explode": true,
      "focus": false
    }
  ]
}
```

已核验记录必须有 `source` 和 `verified_at`。专有词表记录不能使用 `verified_by_public_api`。
