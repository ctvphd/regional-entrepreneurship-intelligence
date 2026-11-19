# Speaker Script

Planned main-deck time: **11:20**. This leaves approximately 40 seconds within a 12-minute slot for transitions, a slow dashboard load, or a brief pause. Backup slides are excluded.

## 1. Regional Entrepreneurship Intelligence — 0:20

**Script:** Economic growth creates opportunity, but opportunity does not automatically translate into entrepreneurship. This project asks whether historical regional and industry conditions can help identify where startup activity is most likely to fall behind a model-based expectation three years later. The goal is not to diagnose a market from a score. It is to focus limited analytical attention.

**Cues:** Opening tension; three-year horizon; prioritization, not diagnosis.

**Transition:** That tension creates a specific regional-development problem.

## 2. The problem — 0:35

**Script:** A regional industry may add jobs or economic activity without producing the entrepreneurial response we might expect under similar historical conditions. That is a predictive association, not a causal claim. The practical challenge is deciding which of thousands of regional-industry combinations deserve closer investigation.

**Cues:** Describe mismatch; avoid causal language; thousands of cases.

**Transition:** The research question turns that mismatch into a testable prediction problem.

## 3. Research question — 0:35

**Script:** Can information available today rank the risk that a model-relative entrepreneurial gap appears three years later? Economic-development organizations cannot investigate every market equally. A useful system would narrow the field while preserving human judgment. It would not automatically allocate funding, label a place as failing, or explain the cause of a gap.

**Cues:** Prediction at t plus three; capacity constraint; no automated funding decisions.

**Transition:** To answer it, we first need a definition of entrepreneurial alignment.

## 4. Conceptual framework — 0:35

**Script:** Historical opportunity and context generate an expected entrepreneurial response. Actual startup activity supplies the observed response. Their difference is entrepreneurial alignment. A materially negative difference becomes a potential gap. This avoids assuming that every industry or metro should produce the same startup rate. The benchmark is conditional and model-based.

**Cues:** Walk both paths; define alignment; context-specific expectation.

**Transition:** That comparison requires a panel that joins business dynamics with regional context.

## 5. Data and unit — 0:45

**Script:** One row is a metropolitan area, two-digit NAICS industry, and year. The production panel contains 63,577 observations across 381 metropolitan areas, 19 sectors, and 2010 through 2023. Business Dynamics Statistics provide startup activity; QCEW captures industry employment conditions; ACS adds regional demographic and labor context; and County Business Patterns adds establishment context. Sources are harmonized to July 2023 CBSA geography and the 2022 NAICS analytical standard.

**Cues:** Define the row; give four scope numbers; name source roles; harmonization is secondary.

**Transition:** With the unit established, we can define the outcome precisely.

## 6. Defining the gap — 0:50

**Script:** Entrepreneurial alignment is observed startup activity minus expected startup activity. Positive or near-zero values approximately meet or exceed expectation. A potential gap is materially negative: below the twentieth percentile of residuals learned only from the training fold. In plain English, it is the lowest training-fifth of the model-relative differences. The label is not a causal diagnosis, administrative designation, or judgment about ecosystem quality.

**Cues:** Say the equation; explain p20; stress model-relative; avoid stigmatizing labels.

**Likely question:** Why p20? It defines a stable minority outcome and is relearned inside every training fold; robustness checks examine alternatives.

**Transition:** The same training-only principle governs the prediction design.

## 7. Leakage-safe prediction design — 0:40

**Script:** Every prediction uses conditions at time t to evaluate a gap three years later. Development predictor years run from 2010 through 2017. The reserved final holdout uses predictor years 2018 through 2020 and target years 2021 through 2023. Within each fold, the expected model, residual threshold, and scaling are learned from training rows only. Future benchmark covariates are excluded. Future information never moves backward.

**Cues:** Trace t to t plus three; development versus holdout; translate leakage plainly.

**Transition:** Before fitting the prediction models, exploratory analysis shaped what signals to expect.

## 8. EDA lessons — 0:40

**Script:** Three findings matter. A five-percentage-point employment-growth difference corresponds to only about 0.175 startup-rate points, so growth is related but weak. Sector controls explain much more structure. Finally, pooled startup persistence is 0.690, but within the same MSA-industry it is only 0.077. Stable differences between markets dominate year-to-year persistence. I do not call 0.077 zero; the simulated null was approximately negative 0.085.

**Cues:** Translate 3.502; sector matters; pooled versus within; null only if needed.

**Transition:** Those findings motivate a two-stage strategy and a serious sector benchmark.

## 9. Two-stage modeling — 0:35

**Script:** OLS first estimates expected startup activity and creates the leakage-safe gap label from training residuals. Logistic Regression then predicts whether that gap appears three years later. HistGradientBoosting, or HGB, tests whether nonlinear structure improves ranking. Logistic remains primary because it was preselected, interpretable, and competitive across development. Random Forest was evaluated earlier but is not central to the final decision.

**Cues:** Expectation then prediction; Logistic primary; HGB sensitivity.

**Transition:** The reserved holdout gives the main test.

## 10. Main holdout result — 0:50

**Script:** Logistic reached Average Precision of 0.404 against a 23.3 percent prevalence baseline. That means it ranked the minority outcome substantially better than the natural benchmark; AP is not accuracy. ROC-AUC of 0.692 indicates moderate separation. The highest-risk decile contained gaps at 1.99 times the overall rate. Probability error remained moderate, with a Brier score of 0.164. The model is useful for ranking, not perfect classification.

**Cues:** AP versus prevalence; AP is not accuracy; translate AUC, lift, Brier; useful ranking.

**Likely question:** What about the development threshold? Holdout recall was 70.8% and precision was 32.8% at that frozen threshold; the decision slide uses a capacity-based top-decile rule instead.

**Transition:** A nonlinear model scored slightly higher, so the next question is whether that should change the primary model.

## 11. Model comparison uncertainty — 0:40

**Script:** HGB reached AP of 0.424 versus Logistic at 0.404. The paired MSA-cluster bootstrap difference is positive, with a 95 percent interval from 0.006 to 0.034. But only 48.7 percent of draws exceeded the practical plus-0.02 threshold, HGB won two of three development folds, and its pooled development advantage was about 0.004. The full predeclared switch rule was not met, so Logistic remains primary.

**Cues:** Positive holdout difference; practical versus statistical; follow the switch rule.

**Transition:** We then benchmarked the harder question: how much signal is more than industry identity?

## 12. Sector benchmark — 0:40

**Script:** Sector-only AP is 0.325, well above the 0.233 natural prevalence. Industry identity clearly matters. Logistic reaches 0.404, an incremental 0.079 with a bootstrap interval from 0.061 to 0.098. It also beats sector prevalence in all 17 evaluable sectors. Regional and historical features add meaningful ranking among places within the same industry. I do not interpret the AP difference as a percent explained.

**Cues:** Give sector credit; +0.079; 17 of 17; no additive decomposition.

**Transition:** Ranking value becomes concrete only when translated into a workload.

## 13. Decision use — 0:50

**Script:** Review the highest-risk ten percent. That creates 1,031 cases, including 476 realized gaps. Of every 100 priority cases reviewed, about 46 meet the eventual gap definition and 54 do not. Precision is 46.2 percent, lift is 1.99 times, and there are 1.17 additional-review cases per true gap. Recall is 19.9 percent, so the queue captures only about one-fifth of all gaps. It is focused, not comprehensive.

**Cues:** 100-case translation; define precision and recall; focused queue; capacity rule, not policy mandate.

**Transition:** That workload applies only where the data support a score.

## 14. Coverage — 0:40

**Script:** Of 12,091 candidate holdout cells, 10,304 are scoreable: 85.2 percent. The remaining 14.8 percent are insufficient-data model abstentions, not negative predictions. Exclusion is uneven: 17.3 percent for small metros, 10.7 percent for the middle group, and 6.6 percent for large metros. AP 0.404 therefore applies only to the population the model can actually score.

**Cues:** 85.2% coverage; abstention language; size gradient; bound the performance population.

**Transition:** Coverage is one limitation; temporal shift is another.

## 15. Shift and limitations — 0:40

**Script:** Gap prevalence rose from 19.1 percent in development to 23.3 percent in the holdout. Yet observed startup activity also increased, and sector or metro-size composition explains very little of the increase. This is a benchmark-relative temporal shift, not a simple decline in entrepreneurship. Other limits include the predictive rather than causal design, complete-case abstention, two-digit sector aggregation, a fixed three-year horizon, and pandemic-era evaluation conditions.

**Cues:** Pair prevalence and startup increase; reject simple decline; concise limitations.

**Transition:** The dashboard turns the bounded research result into a concrete analyst workflow.

## 16. Live demonstration — 0:50

**Script:** I select Pittsburgh and Arts, Entertainment, and Recreation. First, I show the 14-year observed startup history and the four years with comparable expected-rate context. Second, I show the fixed three-year evaluation score, making clear that it is retrospective, not a live forecast. Third, I check data availability and confidence. The appropriate takeaway is whether this market merits deeper review—not why the pattern occurred or what intervention to fund. If the app is unavailable, the screenshot preserves this path.

**Cues:** Pittsburgh; sector 71; history; fixed holdout score; coverage; investigate, do not diagnose.

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
