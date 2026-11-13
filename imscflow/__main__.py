from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import probe, reflow


def cmd_probe(args: argparse.Namespace) -> int:
    info = probe.probe_path(args.input, args.shots)
    text = probe.format_probe(info)
    if args.out:
        Path(args.out).write_text(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    return 0


def cmd_reflow(args: argparse.Namespace) -> int:
    try:
        return reflow.reflow(args.input, args.shots, args.policy, args.out_ttml, args.out_vtt, args.report)
    except reflow.NotImplementedReflow as e:
        sys.stderr.write(str(e) + "\n")
        return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="imscflow")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("probe", help="inventory an IMSC1 document")
    sp.add_argument("--input", required=True)
    sp.add_argument("--shots", default=None)
    sp.add_argument("--out", default=None)
    sp.set_defaults(func=cmd_probe)
    sr = sub.add_parser("reflow", help="reflow captions into safe area and shot cuts")
    sr.add_argument("--input", required=True)
    sr.add_argument("--shots", required=True)
    sr.add_argument("--policy", required=True)
    sr.add_argument("--out-ttml", required=True)
    sr.add_argument("--out-vtt", required=True)
    sr.add_argument("--report", required=True)
    sr.set_defaults(func=cmd_reflow)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
