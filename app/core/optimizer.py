"""PDF 최적화 및 압축."""

from __future__ import annotations

import fitz


_PRESETS = {
    "web": {"garbage": 4, "deflate": True, "clean": True},
    "print": {"garbage": 4, "deflate": True, "clean": True},
    "custom": {"garbage": 4, "deflate": True},
}


def optimize_pdf(
    input_path: str,
    output_path: str,
    *,
    preset: str = "web",
) -> None:
    """PDF 파일 최적화.

    Parameters
    ----------
    preset : str
        "web" (작은 크기), "print" (높은 품질), "custom".
    """
    opts = _PRESETS.get(preset, _PRESETS["web"])

    doc = fitz.open(input_path)

    save_kwargs = {
        "garbage": opts.get("garbage", 4),
        "deflate": opts.get("deflate", True),
        "clean": opts.get("clean", False),
    }

    doc.save(output_path, **save_kwargs)
    doc.close()
