"""Minimal IMSC1 / TTML parser. Probe uses this; please reuse it."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from . import timeexpr

TTML = "http://www.w3.org/ns/ttml"
TTS = "http://www.w3.org/ns/ttml#styling"
TTP = "http://www.w3.org/ns/ttml#parameter"
ITTP = "http://www.w3.org/ns/ttml/profile/imsc1#parameter"
ITTS = "http://www.w3.org/ns/ttml/profile/imsc1#styling"


class TtmlError(ValueError):
    pass


def _q(ns: str, name: str) -> str:
    return f"{{{ns}}}{name}"


def _attr(el: ET.Element, ns: str | None, name: str, default=None):
    if ns:
        return el.attrib.get(_q(ns, name), el.attrib.get(name, default))
    return el.attrib.get(name, default)


@dataclass
class Region:
    xml_id: str
    origin: str | None
    extent: str | None
    display_align: str | None
    writing_mode: str | None
    style: dict[str, str] = field(default_factory=dict)


@dataclass
class Cue:
    xml_id: str | None
    begin: float
    end: float
    region: str | None
    text: str
    raw_begin: str
    raw_end: str
    style: dict[str, str] = field(default_factory=dict)


@dataclass
class Document:
    path: str
    frame_rate: float
    frame_rate_multiplier: tuple[int, int] | None
    tick_rate: float | None
    cell_resolution: tuple[int, int]
    extent: str | None
    regions: dict[str, Region]
    cues: list[Cue]
    languages: list[str]


def _effective_fps(frame_rate: float, multiplier: tuple[int, int] | None) -> float:
    if not multiplier:
        return frame_rate
    return frame_rate * multiplier[0] / multiplier[1]


def _text_of(el: ET.Element) -> str:
    parts: list[str] = []

    def walk(node: ET.Element, skip_self=False):
        if not skip_self and node.text:
            parts.append(node.text)
        for child in list(node):
            tag = child.tag
            if tag == _q(TTML, "br") or tag.endswith("}br") or tag == "br":
                parts.append("\n")
                if child.tail:
                    parts.append(child.tail)
                continue
            walk(child)
            if child.tail:
                parts.append(child.tail)

    walk(el, skip_self=False)
    # el.text already included; but walk started with node.text of el — good
    return "".join(parts)


def parse_ttml(path: str) -> Document:
    tree = ET.parse(path)
    root = tree.getroot()
    if not root.tag.endswith("tt"):
        raise TtmlError(f"root is not tt: {root.tag}")
    fr = _attr(root, TTP, "frameRate") or root.attrib.get(_q(TTP, "frameRate"))
    # xml.etree uses Clark notation
    fr = root.attrib.get(_q(TTP, "frameRate")) or root.attrib.get("frameRate") or "25"
    try:
        frame_rate = float(fr)
    except ValueError as e:
        raise TtmlError(f"bad frameRate {fr}") from e
    mul_raw = root.attrib.get(_q(TTP, "frameRateMultiplier")) or root.attrib.get("frameRateMultiplier")
    multiplier = None
    if mul_raw:
        bits = mul_raw.split()
        if len(bits) != 2:
            raise TtmlError(f"bad frameRateMultiplier {mul_raw}")
        multiplier = (int(bits[0]), int(bits[1]))
    tick_raw = root.attrib.get(_q(TTP, "tickRate")) or root.attrib.get("tickRate")
    tick_rate = float(tick_raw) if tick_raw else None
    cell_raw = root.attrib.get(_q(TTP, "cellResolution")) or root.attrib.get("cellResolution") or "32 15"
    cw, ch = cell_raw.split()
    cell = (int(cw), int(ch))
    extent = None
    lang = root.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") or root.attrib.get("xml:lang") or ""
    head = root.find(_q(TTML, "head"))
    body = root.find(_q(TTML, "body"))
    regions: dict[str, Region] = {}
    if head is not None:
        layout = head.find(_q(TTML, "layout"))
        styling = head.find(_q(TTML, "styling"))
        styles = {}
        if styling is not None:
            for st in styling.findall(_q(TTML, "style")):
                sid = st.attrib.get("{http://www.w3.org/XML/1998/namespace}id") or st.attrib.get("id")
                if not sid:
                    continue
                styles[sid] = {k.split("}")[-1]: v for k, v in st.attrib.items()}
        if layout is not None:
            for rg in layout.findall(_q(TTML, "region")):
                rid = rg.attrib.get("{http://www.w3.org/XML/1998/namespace}id") or rg.attrib.get("id")
                if not rid:
                    continue
                style = {}
                sid = rg.attrib.get(_q(TTML, "style")[len(TTML)+2:] if False else "style") or rg.attrib.get(_q(TTML, "style"))
                # style attribute may be in default xmlns or un-namespaced
                sid = rg.attrib.get("style")
                if sid and sid in styles:
                    style.update(styles[sid])
                style.update({k.split("}")[-1]: v for k, v in rg.attrib.items()})
                regions[rid] = Region(
                    xml_id=rid,
                    origin=rg.attrib.get(_q(TTS, "origin")) or style.get("origin"),
                    extent=rg.attrib.get(_q(TTS, "extent")) or style.get("extent"),
                    display_align=rg.attrib.get(_q(TTS, "displayAlign")) or style.get("displayAlign"),
                    writing_mode=rg.attrib.get(_q(TTS, "writingMode")) or style.get("writingMode"),
                    style=style,
                )
        # document extent sometimes lives on tt or on a region
    extent = root.attrib.get(_q(TTS, "extent"))
    fps = _effective_fps(frame_rate, multiplier)
    cues: list[Cue] = []
    if body is None:
        raise TtmlError("missing body")
    default_region = body.attrib.get("region")
    default_begin = body.attrib.get("begin")
    default_end = body.attrib.get("end")

    def add_p(el: ET.Element, inherited_region: str | None):
        begin = el.attrib.get("begin") or default_begin
        end = el.attrib.get("end") or default_end
        if begin is None or end is None:
            # skip undated content
            return
        region = el.attrib.get("region") or inherited_region
        xml_id = el.attrib.get("{http://www.w3.org/XML/1998/namespace}id") or el.attrib.get("id")
        text = _text_of(el)
        style = {k.split("}")[-1]: v for k, v in el.attrib.items()}
        cues.append(
            Cue(
                xml_id=xml_id,
                begin=timeexpr.parse_time(begin, fps, tick_rate),
                end=timeexpr.parse_time(end, fps, tick_rate),
                region=region,
                text=text,
                raw_begin=begin,
                raw_end=end,
                style=style,
            )
        )

    def walk(el: ET.Element, region: str | None):
        region = el.attrib.get("region") or region
        if el.tag == _q(TTML, "p") or el.tag.endswith("}p") or el.tag == "p":
            add_p(el, region)
            return
        for child in list(el):
            walk(child, region)

    walk(body, default_region)
    return Document(
        path=str(Path(path)),
        frame_rate=frame_rate,
        frame_rate_multiplier=multiplier,
        tick_rate=tick_rate,
        cell_resolution=cell,
        extent=extent,
        regions=regions,
        cues=cues,
        languages=[lang] if lang else [],
    )
