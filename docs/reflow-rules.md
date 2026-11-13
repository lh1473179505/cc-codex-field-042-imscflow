# reflow 规则

默认策略见 `fixtures/policy.json`。片源是 25 fps 的 16:9，`ttp:cellResolution` 为 32 15，文档 `tts:extent` 为 1920px 1080px。

## 安全区与 region

- 默认安全区由策略 `safe_area` 给出，百分比相对整幅画面：`{"x": 10, "y": 10, "w": 80, "h": 80}`，即四周各留 10%。
- 输出 cue 的 region 必须完全落在安全区内。输入 region 若超出安全区，要收缩到安全区后再排字，不能把字排到安全区外。
- region 的 `tts:origin` / `tts:extent` 可以用 %、px 或 c（单元格）。输出 IMSC 一律改写成百分比，保留两位小数。
- 默认 `displayAlign` 为 `after`（底部对齐），`writingMode` 为 `lrtb`。不要把竖排写成横排，反之亦然。

## 单元格度量（不要读字体文件）

- 一个单元格的宽 = 画面宽 / 32，高 = 画面高 / 15。
- 西文字符（`U+0020`–`U+007E` 以及常见拉丁扩充）宽度按 0.5 个单元格计，空格同宽。
- CJK 统一表意文字、平假名、片假名、全角标点宽度按 1.0 个单元格计。
- 行高固定为 1.0 个单元格，行距由策略 `line_gap_cells`（默认 0.25）附加。一个 region 里最多 `max_lines` 行（默认 2）。
- 一行放不下时必须在允许的断点处折行：西文在空格处，CJK 在任意两个 CJK 字符之间；不要在西文单词中间断开，除非该单词单独已经超过行宽。标点不得出现在行首（把标点留在上一行末尾，若上一行会因此溢出则把最后一个字连同标点一起移到下一行）。

## 镜头切点

- `fixtures/shots.json` 给出切点时间，单位秒，已按 25 fps 对齐。
- 一条 cue 若跨越切点（begin < shot < end），必须拆成两条：第一条在切点前 `pre_roll_frames`（默认 1 帧）结束，第二条在切点后 `post_roll_frames`（默认 2 帧）开始。拆开后的文本按行盒重新排，允许在切点处把一段话分成前后两截，顺序不得颠倒。
- 若拆完后某段的持续时长小于 `min_cue_frames`（默认 8 帧，即 0.32 s），把这段与相邻的同 region 段合并——但合并后仍不得跨越切点。无法合并时保留短段，并在报告 `reason_codes` 里记录 `short_cue`，这不算 reject。
- 同一 region 里两条 cue 不得时间重叠。若输入重叠，后一条的 begin 推迟到前一条的 end；若因此变空，丢弃后一条并记录 `dropped_overlap`。

## 输出

- `--out-ttml` 必须是合法的 IMSC1 文本档（`ttp:profile` 指向 `http://www.w3.org/ns/ttml/profile/imsc1/text`），时间表达式用 `HH:MM:SS:FF`，帧率与输入相同。
- `--out-vtt` 必须是 WebVTT，时间用 `HH:MM:SS.mmm`，cue 文本与 IMSC 一致（换行用新行，不要用 `<br>` 以外的标记）。不要写 REGION 块以外的内嵌样式。
- 不得丢掉输入里已经能解析的 cue 文本；ruby / span 若存在，按纯文本拼接后重排，但不要擅自翻译或删词。

## 退出码

- 成功写出两份稿件和完整报告：退出 0，`decision` 为 `ok`。
- 输入能解析，但安全区里按度量排不下某条不可分割的单词：写出报告，`decision` 为 `reject`，`reason_codes` 含 `overflow`，退出 1。
- TTML 不是良构 XML、缺时间、时间表达式无法解析：退出 2。
