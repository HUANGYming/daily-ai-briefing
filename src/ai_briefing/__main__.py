from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and optionally email the internal AI daily briefing.")
    parser.add_argument("--config", type=Path, default=Path("config/sources.yaml"))
    parser.add_argument("--dry-run", action="store_true", help="Generate only; never send email.")
    args = parser.parse_args()
    run(args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

