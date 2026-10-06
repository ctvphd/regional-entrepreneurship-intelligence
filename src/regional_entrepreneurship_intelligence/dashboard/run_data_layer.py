"""Build and validate the frozen A7.2 dashboard data artifacts."""

from __future__ import annotations

from .data_layer import OUTPUT_DIR, output_hashes, write_dashboard_data


def main() -> None:
    result = write_dashboard_data()
    print("Dashboard datasets:")
    print(result["inventory"].to_string(index=False))
    print(f"Quality checks passed: {len(result['quality_checks'])}")
    print("Output SHA-256:")
    for name, digest in output_hashes(OUTPUT_DIR).items():
        print(f"{digest}  {name}")


if __name__ == "__main__":
    main()
