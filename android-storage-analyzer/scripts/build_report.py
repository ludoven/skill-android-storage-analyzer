#!/usr/bin/env python3
"""Inject analysis JSON into the HTML template -> a standalone Android report."""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "report_template.html")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: build_report.py <analysis.json> [output.html]")
        return 1

    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser(
        "~/Desktop/android-storage-report.html"
    )

    with open(src, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    with open(TEMPLATE, "r", encoding="utf-8") as handle:
        template = handle.read()

    html = (
        template
        .replace("__REPORT_DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__DELETE_CONFIG__", "null")
    )
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(html)

    print(f"报告已生成: {out}")
    print(f"打开: open '{out}'")
    print("这是静态模式，无一键执行按钮。要启用交互执行，请改用 scripts/server.py。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
