# Regional Entrepreneurship Intelligence

## Project Overview

Regional Entrepreneurship Intelligence is a predictive business analytics initiative examining whether entrepreneurial activity aligns with rapidly growing industries in regional economies.

The Northern Alabama-Tennessee Valley will serve as the initial pilot region. The technical framework is being designed so future assignments can support replication across other U.S. regions.

This repository currently contains the technical foundation for the project. It does not yet contain research results, data pipelines, exploratory analysis, predictive models, or dashboard code.

## Research Direction

The eventual project is expected to explore:

- regional industry growth
- entrepreneurship and business dynamics
- entrepreneurial alignment with growing industries
- potential entrepreneurial opportunity gaps
- predictive modeling for business analytics

The exact formal research question and hypotheses will be finalized in Assignment 3.

## Repository Structure

- `src/`: Python package source code for future project components.
- `tests/`: Test package for future validation and regression checks.
- `docs/`: Project documentation, including AI use disclosure.
- `data/`: Placeholder folders for future raw, interim, processed, and external data.
- `notebooks/`: Jupyter notebooks for future exploration and analysis.

The source package uses an expanded structure in preparation for later assignments:

- `data`: future data access and data-specific utilities
- `etl`: future extract, transform, and load workflows
- `database`: future database connection and schema logic
- `analysis`: future exploratory and statistical analysis code
- `models`: future predictive modeling code
- `dashboard`: future Streamlit or dashboard-related code

## Requirements

- Python 3.10 or newer
- Git
- UV

## Environment Setup

Clone the repository:

```powershell
git clone https://github.com/<your-github-username>/regional-entrepreneurship-intelligence.git
```

Change into the project directory:

```powershell
cd regional-entrepreneurship-intelligence
```

Check that UV is installed:

```powershell
uv --version
```

Install and sync the project dependencies:

```powershell
uv sync
```

Confirm the Python version managed by the project:

```powershell
uv run python --version
```

Run commands inside the UV-managed environment:

```powershell
uv run python
```

Start Jupyter:

```powershell
uv run jupyter notebook
```

## Dependency Management

New Python packages should be added with UV:

```powershell
uv add package-name
```

Avoid manually editing dependency lock files. Assignment 2 intentionally includes only the core dependencies required for setup: `pandas`, `numpy`, and `jupyter`.

## Git Workflow

A concise Git workflow for project updates:

```powershell
git status
git add .
git commit -m "Meaningful commit message"
git push
```

## Project Status

The project is currently in:

**Assignment 2 - Environment Setup & Repository Creation**

## AI Use

AI-assisted development is documented in [docs/AI_USE.md](docs/AI_USE.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
