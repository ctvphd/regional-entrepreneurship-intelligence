# Assignment 6 Completion Checklist

- [x] Freeze target, features, model specifications, common eligibility, metrics, and threshold policies in the committed final model lock.
- [x] Commit the development-only numeric residual threshold before querying final holdout targets.
- [x] Preserve exact same-CBSA/same-sector three-year pairing and target-year feature isolation.
- [x] Evaluate the locked logistic reference and frozen HGB sensitivity on 2021–2023 outcomes.
- [x] Produce performance, prediction, calibration, lift, year, sector, MSA-size, sample-flow, and research-question outputs.
- [x] Document predictive evidence, limitations, AI assistance, and leakage controls.
- [x] Verify repeat-run output hashes and source-database integrity.
- [x] Run the complete test suite and review whitespace/diff checks.
- [x] Commit the completed A6.7 analytics engine.
- [ ] Push `main` (one attempt failed because the environment could not connect to `github.com:443`; retry with `git push origin main`).
- [x] Keep Assignment 7/dashboard work out of scope.

## Final Evidence

- Holdout: 10,304 eligible MSA-sector pairs, 365 MSAs, 19 sectors; prevalence 0.233.
- Logistic: AP 0.404, ROC-AUC 0.692, Brier 0.164, top-decile lift 1.985.
- Frozen HGB sensitivity: AP 0.424, ROC-AUC 0.708, Brier 0.161, top-decile lift 2.090.
- Interpretation: useful above-prevalence ranking with calibration, subgroup, complete-case, and temporal-generalization caveats; no causal claims.
