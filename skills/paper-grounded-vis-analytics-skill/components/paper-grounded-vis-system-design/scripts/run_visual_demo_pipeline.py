#!/usr/bin/env python3
"""Run the full paper-grounded VIS pipeline through a runnable frontend app."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_frontend_demo  # noqa: E402
import prepare_vis_design_run  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Paper meta/dir/md, dataset file/dir, or free-text idea.")
    parser.add_argument("--description", default="")
    parser.add_argument("--papers-dir", required=True)
    parser.add_argument("--paper-db", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--keyword-count", type=int, default=18)
    parser.add_argument("--embedding-api-base", default=os.getenv("PAPER_EMBED_API_BASE"))
    parser.add_argument("--embedding-api-key", default=None)
    parser.add_argument("--embedding-model", default=os.getenv("PAPER_EMBED_MODEL", prepare_vis_design_run.DEFAULT_EMBED_MODEL))
    parser.add_argument("--embedding-timeout", type=int, default=180)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    prepare_vis_design_run.run(args)
    payload = build_frontend_demo.build_demo(Path(args.run_dir).resolve())
    print(
        json.dumps(
            {
                "run_dir": str(Path(args.run_dir).resolve()),
                "app": str(Path(args.run_dir).resolve() / "app" / "index.html"),
                "domain_id": payload.get("domain_id"),
                "references": len(payload.get("references") or []),
                "keywords": len(payload.get("keywords") or []),
                "status": "frontend_demo_ready",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
