# Verdict 定义

- `VERIFIED`：来源原文在当前人群、时间、变量和强度下支持主张。
- `PARTIAL`：来源支持句子的一部分，或主张范围大于来源范围。
- `DISTORTED`：来源被夸大、反向、错误概括或改变了限定条件。
- `UNSUPPORTED`：来源中没有该信息，或来源设计不能支持该说法。
- `UNVERIFIABLE_ACCESS`：来源存在，但当前无法访问足够原文。
- `NOT_CHECKED`：尚未完成核验。
- `NOT_APPLICABLE`：该记录不是需要外部来源支持的事实性主张。

`VERIFIED`、`PARTIAL` 和 `DISTORTED` 必须保存至少一个来源对象。来源对象包括：

- `id`
- `source_pointer`
- `locator`
- `support_note`

不要把长篇原文复制进 Audit。保存短说明和可回到原文的位置。
