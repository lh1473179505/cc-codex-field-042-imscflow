# imscflow

字幕台用的 IMSC1 重排工具。`probe` 已经能把 TTML 里的时间、region 和 cue 列出来，也能读镜头切点列表。`reflow` 还没有实现。

不要引入 Pillow、fonttools、libass 或浏览器引擎，也不要使用 Docker。请复用 `imscflow.ttml` 和 `imscflow.timeexpr`。字体度量按 `docs/reflow-rules.md` 里的单元格模型计算，不要去读系统字体文件。

## 命令

```
python -m imscflow probe --input fixtures/show.ttml --shots fixtures/shots.json
python -m imscflow reflow \
  --input fixtures/show.ttml \
  --shots fixtures/shots.json \
  --policy fixtures/policy.json \
  --out-ttml /tmp/imscflow-out.ttml \
  --out-vtt /tmp/imscflow-out.vtt \
  --report /tmp/imscflow-report.json
```

规则见 `docs/reflow-rules.md`，报告字段见 `docs/report-schema.md`。
