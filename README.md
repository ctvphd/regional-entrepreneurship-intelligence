# Regional Entrepreneurship Intelligence

## Project Overview

Regional Entrepreneurship Intelligence is a predictive business analytics initiative examining whether entrepreneurial activity aligns with rapidly growing industries in regional economies.

The framework is intended to support standardized geographic analysis across the United States. Future work may analyze Metropolitan Statistical Areas (MSAs), Micropolitan Statistical Areas, and Counties so the project can be replicated across different regional economies.

This repository currently contains the technical foundation for the project. It does not yet contain research results, data pipelines, exploratory analysis, predictive models, or dashboard code.

## Geographic Framework

The project is being designed around standardized U.S. geographic units rather than a single fixed pilot region. Northern Alabama or the Tennessee Valley may still be useful as a future demonstration case, but they are not the defining analytical geography of the repository.

### Metropolitan Statistical Areas

Metropolitan Statistical Areas are expected to serve as the primary regional analytical unit because they better represent integrated labor and economic markets.

### Micropolitan Statistical Areas

Micropolitan Statistical Areas may be used to represent smaller regional economies that are not included in metropolitan areas.

### Counties

Counties are expected to support more granular drill-down, local diagnostics, and future stakeholder analysis.

Conceptually, the future geographic hierarchy may look like this where applicable:

```text
United States
`-- State
    |-- Metropolitan Statistical Area
    |   `-- County
    `-- Micropolitan Statistical Area
        `-- County
```

The anticipated primary analytical unit is Metropolitan Statistical Area x Industry x Year, with county-level analysis available for more granular investigation and potential inclusion of micropolitan areas. This design is not final; Assignment 3 will formally define the unit of analysis, dependent variable, independent variables, geographic scope, hypotheses, and modeling strategy.

## Research Direction

The eventual project is expected to explore:

- regional industry growth
- firm startup and business dynamics
- entrepreneurial-industry alignment
- entrepreneurial gaps
- differences across metropolitan, micropolitan, and county economies
- predictive modeling for business analytics
- national scalability

The exact formal research question and hypotheses will be finalized in Assignment 3.

## Repository Structure

- `src/`: Python package source code for future project components.
- `tests/`: Test package for future validation and regression checks.
- `docs/`: Project documentation, including AI use disclosure.
- `data/`: Placeholder folders for future raw, interim, processed, and external data.
- `notebooks/`: Jupyter notebooks for future exploration and analysis.

The source package uses an expanded structure in preparation for later assignments:

- `data`: future data access and data-specific utilities
- `etl`: future extract, transform, and load workflows across standardized geographies
- `database`: future database connection and schema logic
- `analysis`: future exploratory and statistical analysis code
- `models`: future predictive modeling code
- `dashboard`: future Streamlit or dashboard-related code

Future data sources may include the BLS Quarterly Census of Employment and Wages (QCEW), Census Business Dynamics Statistics (BDS), Census County Business Patterns (CBP), and American Community Survey (ACS). Later assignments may integrate these sources using standardized geography and industry identifiers such as geographic codes, county FIPS, CBSA codes where appropriate, NAICS, and year.

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
