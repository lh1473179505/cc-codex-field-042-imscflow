"""IMSC1 caption reflow. Not implemented in the initial snapshot."""

from __future__ import annotations


class NotImplementedReflow(NotImplementedError):
    pass


def reflow(ttml_path: str, shots_path: str, policy_path: str, out_ttml: str, out_vtt: str, report_path: str) -> int:
    raise NotImplementedReflow(
        "imscflow.reflow.reflow is not implemented yet; TTML probe already works"
    )
