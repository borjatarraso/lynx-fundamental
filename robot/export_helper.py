"""Helper script for Robot Framework export tests.

Loads cached analysis from data_test and exports to the specified format,
avoiding redundant network calls.

Usage: python robot/export_helper.py <ticker> <format> <output_path>
"""

import json
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lynx.core.storage import set_mode, get_company_dir
from lynx.core.analyzer import _dict_to_report
from lynx.export import ExportFormat, export_report


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <ticker> <format> <output_path>", file=sys.stderr)
        sys.exit(1)

    ticker, fmt, output = sys.argv[1], sys.argv[2], sys.argv[3]

    set_mode("testing")

    # Load the latest analysis directly (bypass the is_testing() guard)
    latest = get_company_dir(ticker) / "analysis_latest.json"
    if not latest.exists():
        print(f"No cached analysis for {ticker} at {latest}", file=sys.stderr)
        sys.exit(1)

    with open(latest, encoding="utf-8") as f:
        data = json.load(f)

    report = _dict_to_report(data)
    path = export_report(report, ExportFormat(fmt), Path(output))
    print(f"Exported to: {path}")


if __name__ == "__main__":
    main()
