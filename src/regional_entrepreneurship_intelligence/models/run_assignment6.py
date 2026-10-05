"""Reproduce the locked A6.7 evaluation from committed A6.1-A6.6 artifacts.

Earlier Assignment 6 stages are intentionally not rerun: their design and
selection outputs are frozen inputs. The final runner refuses to proceed until
the model lock and development-only p20 threshold have been committed.
"""

from __future__ import annotations

from regional_entrepreneurship_intelligence.models.final_holdout import (
    evaluate_final,
    output_hashes,
    validate_locked_design,
)


def run_assignment6():
    validate_locked_design(require_threshold=True)
    result = evaluate_final()
    result["output_hashes"] = output_hashes()
    return result


if __name__ == "__main__":
    result = run_assignment6()
    print(result["performance"].to_string(index=False))
    print("Final CSV hashes:")
    for name, digest in result["output_hashes"].items():
        print(f"{digest}  {name}")
