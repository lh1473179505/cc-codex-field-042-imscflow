"""Read-only inventory of an IMSC1 document and a shot-change list."""

from __future__ import annotations

import json
from pathlib import Path

from . import ttml


def load_shots(path: str | None) -> list[float]:
    if not path:
        return []
    doc = json.loads(Path(path).read_text())
    shots = doc.get("shots") if isinstance(doc, dict) else doc
    return [float(x) for x in shots]


def probe_path(ttml_path: str, shots_path: str | None = None) -> dict:
    doc = ttml.parse_ttml(ttml_path)
    shots = load_shots(shots_path)
    return {
        "ttml": ttml_path,
        "shots": shots_path,
        "frame_rate": doc.frame_rate,
        "frame_rate_multiplier": list(doc.frame_rate_multiplier) if doc.frame_rate_multiplier else None,
        "cell_resolution": list(doc.cell_resolution),
        "extent": doc.extent,
        "languages": doc.languages,
        "regions": {
            rid: {
                "origin": r.origin,
                "extent": r.extent,
                "display_align": r.display_align,
                "writing_mode": r.writing_mode,
            }
            for rid, r in doc.regions.items()
        },
        "cues": [
            {
                "id": c.xml_id,
                "begin": c.begin,
                "end": c.end,
                "raw_begin": c.raw_begin,
                "raw_end": c.raw_end,
                "region": c.region,
                "text": c.text,
            }
            for c in doc.cues
        ],
        "shot_times": shots,
    }


def format_probe(info: dict) -> str:
    return json.dumps(info, ensure_ascii=False, indent=2)
