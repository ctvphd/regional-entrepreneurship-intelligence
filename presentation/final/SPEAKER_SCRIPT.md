# Speaker Script

Planned main-deck time: **11:20**. This leaves approximately 40 seconds within a 12-minute slot for transitions, a slow dashboard load, or a brief pause. Backup slides are excluded.

## 1. Regional Entrepreneurship Intelligence — 0:20

**Script:** Economic growth creates opportunity, but opportunity does not automatically translate into entrepreneurship. In this empirical model, opportunity means observable regional and industry conditions, not every possible dimension of economic opportunity. The project asks whether those historical conditions can identify where startup activity may fall below a model-based expectation three years later. The purpose is to focus limited analytical attention, not diagnose a market from a score.

**Cues:** Opening tension; opportunity means observable conditions; three-year horizon; prioritization, not diagnosis.

**Transition:** That tension creates a specific regional-development problem.

## 2. The problem — 0:35

**Script:** A regional industry can grow economically without seeing a proportional entrepreneurial response. That mismatch is the practical problem. In the analysis, the observed response is compared with what similar observable regional-industry conditions would lead the model to expect. This is a predictive association, not a causal claim. The challenge is deciding which of thousands of combinations deserve closer investigation.

**Cues:** Growth and startup response can diverge; call it a mismatch; avoid causality; prioritize from thousands of cases.

**Transition:** The research question turns that mismatch into a testable prediction problem.

## 3. Research question — 0:35

**Script:** With limited time and staff, which markets deserve closer investigation? Technically, the study asks whether information available today can rank the risk of a model-relative entrepreneurial gap three years later. A useful system narrows the field while preserving human judgment. It does not allocate funding, issue an official designation, or explain the cause of a gap.

**Cues:** Limited analyst capacity; future gap risk at t plus three; preserve human judgment; no funding or official designation.

**Transition:** To answer it, we first need a definition of entrepreneurial alignment.

## 4. Conceptual framework — 0:35

**Script:** The framework compares what happened with what the model expected under similar observable conditions. In the empirical model, opportunity is represented by employment, startup history, sector, and regional context; it does not cover every dimension of economic opportunity. Expected and observed startup activity form entrepreneurial alignment. A materially negative difference becomes a potential gap. The benchmark is conditional and model-based, not one national target for every place.

**Cues:** Observed versus context-specific expectation; measured opportunity variables; entrepreneurial alignment; not one national target.

**Transition:** That comparison requires a panel that joins business dynamics with regional context.

## 5. Data and unit — 0:45

**Script:** One observation represents one metropolitan area, one broad industry, and one year. The technical unit is MSA by two-digit NAICS sector by year. The panel contains 63,577 observations across 381 metros, 19 sectors, and 2010 through 2023. BDS supplies startup activity, QCEW employment conditions, ACS regional context, and CBP establishment context. Sources are harmonized to July 2023 CBSA geography and the 2022 NAICS analytical standard.

**Cues:** One metro, broad industry, and year; technical unit; four scope numbers; source roles; harmonization second.

**Transition:** With the unit established, we can define the outcome precisely.

## 6. Defining the gap — 0:50

**Script:** A gap means startup activity falls meaningfully below what the model expected under observable conditions. The technical construct is entrepreneurial alignment: observed minus expected startup rate. The lowest training-fifth becomes the gap definition, formally the p20 residual threshold. That threshold is learned from training data only. The label is model-relative, not a causal diagnosis, regulatory classification, funding rule, or judgment about ecosystem quality.

**Cues:** Meaningful shortfall first; entrepreneurial alignment equation; lowest training 20% = p20; training-only threshold; no official designation.

**Likely question:** Why p20? It defines a stable minority outcome and is relearned inside every training fold; robustness checks examine alternatives.

**Transition:** The same training-only principle governs the prediction design.

## 7. Leakage-safe prediction design — 0:40

**Script:** The design asks what could have been known at the time. Conditions at t predict whether a meaningful shortfall appears at t plus three. The technical approach is leakage-safe temporal validation. Development predictors span 2010 through 2017. Later years the model never trained on use predictors from 2018 through 2020 and targets from 2021 through 2023. The expected model, p20 threshold, and scaling are learned inside training data only. Future information never moves backward.

**Cues:** Available information only; leakage-safe temporal validation; 2018–2020 to 2021–2023; future never moves backward.

**Transition:** Before fitting the prediction models, exploratory analysis shaped what signals to expect.

## 8. EDA lessons — 0:40

**Script:** Three findings matter. Growth has a modest relationship with startup activity: a five-point employment-growth difference corresponds to about 0.175 startup-rate points; the technical coefficient is 3.502 per 1.0 decimal growth. Industry explains much more structure than growth alone. And markets differ from one another more consistently than they change year to year: pooled lag correlation is 0.690 versus 0.077 within the same MSA-industry. The simulated null is about negative 0.085, so 0.077 is small, not zero.

**Cues:** Modest growth association; five points = +0.175; industry matters more; 0.690 pooled vs 0.077 within; do not call zero.

**Transition:** Those findings motivate a two-stage strategy and a serious sector benchmark.

## 9. Two-stage modeling — 0:35

**Script:** First, estimate what startup activity would normally look like under similar observable conditions. Technically, OLS produces the expected-rate benchmark and training-only gap label. Second, predict whether a meaningful shortfall appears three years later. Logistic Regression is primary. HistGradientBoosting tests whether nonlinear structure improves ranking. Logistic was preselected, interpretable, and competitive across development.

**Cues:** Normal response under similar conditions; OLS benchmark; future shortfall prediction; Logistic primary; HGB sensitivity.

**Transition:** First question: does the model rank future risk usefully?

## 10. Main holdout result — 0:50

**Script:** On later years it never trained on, the model ranks the less-common gap outcome substantially better than the natural baseline. Average Precision is 0.404 versus 0.233 prevalence; AP is not accuracy. Its ability to separate higher-risk from lower-risk cases, ROC-AUC, is 0.692. Gaps are concentrated at 1.99 times the overall rate in the top decile. Probability error, measured by the Brier score, is 0.164. This is useful ranking, not perfect classification.

**Cues:** Ranking quality first; AP 0.404 vs 0.233; AP is not accuracy; AUC = separation; lift = concentration; useful, not perfect.

**Likely question:** What about the development threshold? Holdout recall was 70.8% and precision was 32.8% at that frozen threshold; the decision slide uses a capacity-based top-decile rule instead.

**Transition:** Second question: should I have chosen the more complex model?

## 11. Model comparison uncertainty — 0:40

**Script:** The more complex HGB model scored slightly better in the holdout: AP 0.424 versus 0.404 for Logistic. We repeatedly resampled metropolitan areas while keeping each metro’s observations together; technically, this is an MSA-cluster bootstrap. The AP difference is plus 0.020, with a 95 percent interval from plus 0.006 to plus 0.034. But only 48.7 percent of draws cleared the practical threshold, HGB won two of three development folds, and its pooled development advantage was about 0.004. The full switch rule was not met, so Logistic remains primary.

**Cues:** Complexity versus consistency; HGB 0.424 vs Logistic 0.404; cluster bootstrap keeps metros together; +0.020 CI; switch rule not met.

**Transition:** Third question: is the model doing anything more than identifying risky industries?

## 12. Sector benchmark — 0:40

**Script:** If all we knew was industry identity, the sector-only benchmark reaches AP 0.325 versus 0.233 prevalence. Industry clearly matters. The full Logistic model reaches 0.404. Its incremental AP is plus 0.079, with a 95 percent interval from plus 0.061 to plus 0.098, and it beats sector prevalence in all 17 evaluable sectors. Regional and historical conditions still distinguish places within the same industry. The AP difference is not a percent explained.

**Cues:** What industry alone predicts; sector-only 0.325; Logistic 0.404; +0.079; 17 of 17; not percent explained.

**Transition:** Ranking value becomes concrete only when translated into a workload.

## 13. Decision use — 0:50

**Script:** The practical option is a focused queue: review the highest-risk ten percent. That is 1,031 cases, of which 476 became realized gaps. For every 100 priority reviews, about 46 became gaps and 54 did not. That 46.2 percent share is precision. The queue captured 19.9 percent of all gaps, which is recall, and concentrated gaps at 1.99 times the overall rate, which is lift. Each realized gap required 1.17 additional reviews that did not become gaps. This is focused, not comprehensive.

**Cues:** Manageable review queue; 46 of 100 = precision; 19.9% captured = recall; 1.99× = lift; not mandatory policy.

**Transition:** That workload applies only where the data support a score.

## 14. Coverage — 0:40

**Script:** Before performance, ask who can receive a reliable score. Of 12,091 candidate cases, 10,304 have sufficient information, so coverage is 85.2 percent. The remaining 14.8 percent do not receive a forced score; technically, these are insufficient-data model abstentions, not negative predictions. Exclusion is 17.3 percent for small metros, 10.7 percent for the middle group, and 6.6 percent for large metros. AP 0.404 applies only to scoreable cases.

**Cues:** Reliable score for 85.2%; 14.8% insufficient data; model abstention; size gradient; bound performance population.

**Transition:** Coverage is one limitation; temporal shift is another.

## 15. Shift and limitations — 0:40

**Script:** More observations fell below the model’s expected level in later years: gap prevalence rose from 19.1 percent in development to 23.3 percent in the holdout. Raw startup activity also increased, and sector or metro-size composition explains little of the change. Technically, this is a benchmark-relative temporal shift, not a simple decline in entrepreneurship. Limits remain: prediction is not causation, complete-case rules create abstention, sectors are broad, the horizon is three years, and the holdout spans pandemic-era conditions.

**Cues:** More cases below expectation; 19.1% to 23.3%; startup activity increased; benchmark-relative shift; not a simple decline.

**Transition:** The dashboard turns the bounded research result into a concrete analyst workflow.

## 16. Live demonstration — 0:50

**Script:** I select Pittsburgh and Arts, Entertainment, and Recreation. I begin with the 14-year observed history and four years with comparable expected-rate context. For this historical evaluation period, the model assigned the market-industry combination an elevated gap-risk score. That is a retrospective ranking signal, not a 44 percent chance of failure and not a current forecast. I then check data confidence. The appropriate takeaway is to investigate further; the score does not explain why the pattern occurred or what intervention to fund.

**Cues:** Pittsburgh and sector 71; history before score; elevated historical risk ranking; not probability of failure; investigate, do not diagnose.

**Transition:** The demonstration makes the final evidence boundary tangible.

## 17. Conclusion — 0:35

**Script:** Future model-relative gaps contain predictable structure. Sector matters substantially, and regional history adds signal within industries. Risk rankings can create a focused review queue among eligible observations. The evidence does not establish causation, explain why a gap occurs, score every market, or justify automatic funding. Opportunity does not automatically become entrepreneurship. The model identifies where to look—not what intervention to make.

**Cues:** Supported versus unsupported; return to opening tension; end on decision boundary.

**Final line:** Prediction, prioritization, human investigation.

## Timing audit

| Slides | Planned time |
|---|---:|
| 1–5 | 2:50 |
| 6–9 | 2:45 |
| 10–13 | 3:00 |
| 14–17 | 2:45 |
| **Total** | **11:20** |
