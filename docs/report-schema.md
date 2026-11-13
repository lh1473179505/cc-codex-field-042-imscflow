# 报告 schema

| 字段 | 类型 | 含义 |
|---|---|---|
| input | string | 输入 TTML 路径 |
| decision | string | `ok` 或 `reject` |
| reason_codes | string[] | 见规则 |
| cues_in | integer | 输入 cue 数 |
| cues_out | integer | 输出 cue 数（拆分后） |
| split_on_shots | integer | 因切点拆开的次数 |
| dropped_overlap | integer | 因重叠丢弃的条数 |
| overflow_cues | string[] | 无法排下的 cue id |
| out_ttml | string | 输出 TTML 路径 |
| out_vtt | string | 输出 WebVTT 路径 |
