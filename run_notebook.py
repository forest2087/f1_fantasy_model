#!/usr/bin/env python3
"""Run the F1 Fantasy notebook using papermill.

Usage:
    python run_notebook.py                          # Normal run (scrapes odds)
    python run_notebook.py --skip-scraper           # Skip Oddschecker scraper
    python run_notebook.py --output out.ipynb       # Custom output path
    python run_notebook.py -q                       # Quiet (no progress bar)
"""

import argparse
import os
import shutil
import sys
import papermill as pm


SCRAPER_CELL_INDEX = 7


def run(skip_scraper=False, output=None, quiet=False):
    input_path = "f1-2026.ipynb"
    output_path = output or "f1-2026.ipynb"

    # When skipping scraper: work on a disposable copy, never touch the original
    if skip_scraper:
        tmp_input = "_tmp_run.ipynb"
        shutil.copy2(input_path, tmp_input)

        import nbformat
        nb = nbformat.read(tmp_input, as_version=4)
        nb.cells[SCRAPER_CELL_INDEX]["source"] = 'print("Scraper skipped (--skip-scraper)")'
        with open(tmp_input, "w") as f:
            nbformat.write(nb, f)
    else:
        tmp_input = input_path

    try:
        # Execute into a temp output to avoid corrupting the source
        tmp_output = "_tmp_out.ipynb"
        result = pm.execute_notebook(
            tmp_input,
            tmp_output,
            kernel_name="python3",
            progress_bar=not quiet,
            log_output=not quiet,
            cwd=".",
            start_timeout=120,
        )
        print("\nSUCCESS: Notebook executed")

        # Restore original scraper cell in the output before finalizing
        if skip_scraper:
            import nbformat
            orig_nb = nbformat.read(input_path, as_version=4)
            out_nb = nbformat.read(tmp_output, as_version=4)
            out_nb.cells[SCRAPER_CELL_INDEX]["source"] = orig_nb.cells[SCRAPER_CELL_INDEX]["source"]
            with open(tmp_output, "w") as f:
                nbformat.write(out_nb, f)

        # Only now move the clean output to the final path
        shutil.move(tmp_output, output_path)

        # Print warnings for any cell errors
        for i, cell in enumerate(result.cells):
            if cell.cell_type != "code":
                continue
            for out in cell.get("outputs", []):
                if out.get("output_type") == "error":
                    print(f"WARNING: Cell {i} had error: {out['ename']}: {out['evalue']}")

    except pm.PapermillExecutionError as e:
        print(f"\nFAILED at cell {e.cell_index}: {e.ename}: {e.evalue}", file=sys.stderr)
        print(f"Source:\n{e.source[:200]}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temp files
        for tmp in ["_tmp_run.ipynb", "_tmp_out.ipynb"]:
            if os.path.exists(tmp):
                os.remove(tmp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run F1 Fantasy notebook")
    parser.add_argument("--skip-scraper", action="store_true",
                        help="Skip Oddschecker odds scraper (use existing odds_2026.csv)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output notebook path (default: overwrite input)")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress progress bar and cell output")
    args = parser.parse_args()
    run(skip_scraper=args.skip_scraper, output=args.output, quiet=args.quiet)
