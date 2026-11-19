"""Reproduce the locked A6.7 evaluation from committed A6.1-A6.6 artifacts.

Earlier Assignment 6 stages are intentionally not rerun: their design and
selection outputs are frozen inputs. The final runner refuses to proceed until
the model lock and development-only p20 threshold have been committed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from regional_entrepreneurship_intelligence.models.final_holdout import (
    evaluate_final,
    output_hashes,
    validate_locked_design,
)


def run_assignment6(
    *,
    source: str = "production",
    reviewer_database: Path | None = None,
    reviewer_output: Path | None = None,
    reviewer_sources: Path | None = None,
):
    if source == "reviewer":
        from regional_entrepreneurship_intelligence.models.reviewer import (
            DEFAULT_DATABASE,
            DEFAULT_OUTPUT_DIR,
            run_reviewer_assignment6,
        )

        return run_reviewer_assignment6(
            database_path=reviewer_database or DEFAULT_DATABASE,
            output_dir=reviewer_output or DEFAULT_OUTPUT_DIR,
            source_dir=reviewer_sources,
        )
    if source != "production":
        raise ValueError(f"Unknown Assignment 6 source: {source}")
    if reviewer_database is not None or reviewer_output is not None or reviewer_sources is not None:
        raise ValueError("Reviewer paths require --source reviewer")
    validate_locked_design(require_threshold=True)
    result = evaluate_final()
    result["output_hashes"] = output_hashes()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("production", "reviewer"), default="production")
    parser.add_argument("--reviewer-database", type=Path)
    parser.add_argument("--reviewer-output", type=Path)
    parser.add_argument("--reviewer-sources", type=Path)
    args = parser.parse_args()
    result = run_assignment6(
        source=args.source,
        reviewer_database=args.reviewer_database,
        reviewer_output=args.reviewer_output,
        reviewer_sources=args.reviewer_sources,
    )
    if args.source == "reviewer":
        print(result["warning"])
        print(json.dumps(result, indent=2))
    else:
        print(result["performance"].to_string(index=False))
        print("Final CSV hashes:")
        for name, digest in result["output_hashes"].items():
            print(f"{digest}  {name}")


if __name__ == "__main__":
    main()
