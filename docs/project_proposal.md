# Predicting Regional Entrepreneurial Growth in Alignment with Growing Industries

## 1. Introduction & Motivation

Regional industries can experience strong economic growth, but that growth does not always produce a proportional increase in entrepreneurial activity. Employment, establishments, payroll, and wages may rise while starting new firms remains low. This creates an important question: Why do some growing regional industries generate more entrepreneurial activity than others.

Entrepreneurship supports regional development through new firm creation, innovation, and entry of new economic actors. However, firm formation is developed and influenced by more than economic growth. Regional economic conditions, reputable institutions, industry structure, politics and historical factors have significant impact on entrepreneurial activity (Dejardin, 2011).

Understanding this difference matters because regions with similar industry growth may produce varying levels of new business formation. Identifying these differences can help researchers and lawmakers to understand when economic growth can translate into more entrepreneurial opportunity and when the opposite occurs. This study examines United States Metropolitan Statistical Areas (MSAs) at the industry level to determine whether entrepreneurial activity is occurring at a rate in relation to local industry growth and regional economic conditions.

**Research Question:** Why do MSAs experiencing similar levels of industry growth produce different levels of entrepreneurial activity?

## 2. Pathway and Target Contribution

- **Pathway:** Research-Oriented Investigation (for now)
- **Intended audience:** Academic researchers in entrepreneurship, economic development and business analytics. Focused on those studying entrepreneurial ecosystems at a regional level
- **Contribution:** This study will create a predictive framework for identifying U.S. regional industries where entrepreneurial activity is lower than expected in relation to industry growth and regional economic conditions.

## 3. Literature Review and Research Gap

- **Prior Work:** U.S. research shows that regional entrepreneurship varies by industry and is influenced by factors such as population density and human capital, history of entrepreneurial activity, university research, and industry composition (Renski, 2014; Qian, 2017; Fritsch et al., 2025). International studies support these findings highlighting that entrepreneurial activity is also shaped by regional ecosystems, industry structure and historical conditions (Bruns et al., 2017; Cosci et al., 2022; Stuetzer et al., 2016; Mazzoni & Innocenti, 2024).
- **Specific gap:** Current studies explain the historical context for higher entrepreneurial activity in certain regions, but has not addressed if the entrepreneurial activity is keeping pace with the economic growth within a specific regional industry. Essentially, there is limited research combining industry growth and regional characteristics to predict where entrepreneurial activity is lower than expected.
- **Method to address it:** This study develops a predictive framework at the U.S. MSA-industry level to identify regional industries where entrepreneurial activity falls below the level expected given regional economic conditions and charted industry growth or decline. This shifts the focus from describing entrepreneurial differences to detecting entrepreneurial gaps.

## 4. Research Questions and Hypotheses

- **Primary RQ:** How accurately can historical industry growth, prior entrepreneurial activity, labor-market conditions, and regional economic characteristics predict future entrepreneurial gaps within MSA-industry combinations?
- **H-1:** Historical industry, entrepreneurial, labor-market and regional economic characteristics will improve prediction of future entrepreneurial gaps compared with a simple baseline model
  - **Null (H-0):** These characteristics will not materially improve predictive performance relative to the baseline model.
  - **Falsification condition:** H1 will be rejected if the full model does not produce meaningfully better predictive performance than the baseline model.
- **H-2:** Stronger historical industry growth will be associated with greater entrepreneurial activity
  - **Falsification condition:** H-2 will be rejected if industry growth has no positive relationship with startup activity
- **H-3:** MSA-industry combinations with stronger prior entrepreneurial activity will be less likely to experience future entrepreneurial gaps
  - **Falsification condition:** H-3 will be rejected if prior entrepreneurial activity does not reduce the likelihood or severity of future gaps
- **H-4:** The relationship between industry growth and entrepreneurial activity will vary across two-digit NAICS sectors
  - **Falsification condition:** H-4 will be rejected if sector effects do not meaningfully differ.

**Operationalization of key constructs**

- Entrepreneurial activity = firm startup rate within each MSA-industry-year
- Industry growth = changes in employment, establishments, payroll, and wages
- Prior entrepreneurial activity = lagged startup rate
- Entrepreneurial alignment = Observed Entrepreneurial Activity - Expected Entrepreneurial Activity
- Entrepreneurial gap = a large negative entrepreneurial alignment value, with the classification threshold established numerically

## 5. Data

| Source | Variables | Frequency | Coverage | Accessibility |
| --- | --- | --- | --- | --- |
| Census Business Dynamics Statistics (BDS) | Firm startups, establishment births/deaths, job creation/destruction | Annual | U.S. regions and industries; BDS time series currently extends through 2023 | Public and free; Census API with API key. (Census.gov) |
| BLS Quarterly Census of Employment and Wages (QCEW) | Employment, establishments, wages, industry employment growth | Quarterly/Annual | U.S. counties/MSAs and NAICS industries | Public and free; downloadable files and CSV/open-data access. (Bureau of Labor Statistics) |
| Census County Business Patterns (CBP) | Establishments, employment, annual payroll, first-quarter payroll | Annual | Counties and MSAs by 2-6 digit NAICS | Public and free; Census API with API key or bulk download. (Census.gov) |
| American Community Survey (ACS) | Population, income, education, unemployment, labor-force characteristics | Annual | U.S. metropolitan areas and other geographic levels | Public and free; Census API with API key. (Census.gov) |

- **Sample construction:** UOA will be MSA x NAICS (2-digit) x Year, studying from 2005-2023. Observations will be included with consistent industry geographic, and entrepreneurial measures. MSA definitions and NAICS classifications will be consistent across years to maintain a longitudinal panel
- **Variables:** DV will be entrepreneurial activity through startup rate. IVs will include prior startup activity, employment growth, establishment growth, payroll growth, wage growth, and industry size. Controls will include population growth, educational attainment, income, labor-market conditions and MSA, industry and year effects.
- **Data quality & sufficiency:** Each source provides geographic, industry and longitudinal detail to test the proposed hypotheses. Only concerns will be disclosure suppression, missing observations, NAICS revisions, MSA boundary changes, etc. Data will require cleaning, geographic and industry alignment, lag construction and merging by MSA x Industry x Year identifiers

## 6. Methods and Identification Strategy

- **Estimator / model:** Two-stage predictive approach.
  - First, panel regression models will estimate expected entrepreneurial activity using prior startup activity, industry growth, and regional economic conditions. Results, Observed Entrepreneurship - Expected Entrepreneurship, measures entrepreneurial alignment.
  - Second, logistic regression, random forest, and gradient boosting/XGBoost models will predict whether an MSA-industry combination will experience a future entrepreneurial gap. These models fit because the goal is prediction.
- **Identification strategy:** The analysis will reduce confounding by including lagged predictors, MSA effects, industry effects and year effects to account foe persistent regional differences, sector differences, and common macroeconomic conditions. Temporal ordering will be maintained by using historical characteristics to predict future outcomes.
- **Validation & robustness:** Performance will be evaluated using temporal out-of-sample testing, with earlier years used for training and later years reserved for testing. Robustness checks will include alternative entrepreneurship measures, gap thresholds, industry-growth measures, model specifications, etc. Where feasible, geographic holdout samples will be used to test whether findings generalize across regions.

## 7. Analysis Plan and Expected Outcomes

- **Pre-specified analyses:** Describe entrepreneurship and industry growth, construct the entrepreneurial-gap measure, estimate expected activity, and compare predictive models using out-of-sample performance
- **Hypothesis supports vs. refutes:** H1 is supported if the predictive models clearly outperform the baseline and remain reasonably stable across validation periods and alternative specifications. H1 is not supported if performance is similar to the baseline, weakens over time, or is highly sensitive to reasonable model changes
- **Reporting commitment:** Null, weak, or negative results will be reported as valid findings because they still show the limits of using regional economic indicators to predict entrepreneurial gaps

## 8. Contribution and Significance

- **Contribution to theory or literature:** Extends regional entrepreneurial research by testing whether industry growth, history, and regional characteristics can predict where entrepreneurial activity falls below expected levels (Renski, 2014; Qian, 2017; Fritsch et al., 2025)
- **Contribution to practice:** Could help economic developers identify growing regional industries where entrepreneurial activity appears unusually weak and where focus may be needed
- **Success metrics:** Producing a replicable, clear entrepreneurial gap measure and demonstrating whether available regional indicators can meaningfully predict future gaps

## 9. Threats to Validity, Limitations and Fallback

- **Internal validity:** lagged predictors, regional, industry, and year controls will help reduce confounding from persistent differences and broader economic shocks
- **External validity / construct validity:** Results will favor urban versus rural economies. Startup rates measure firm formation but do not capture all forms of entrepreneurship (self-employment, innovation or high-growth ventures)
- **Limitations & fallback:** Startup data may be sparse, if so, establishment-entry rates may be used. If the industry-growth index has too much missing data, employment growth will be used.

## 10. Technical Implementation & Reproducibility

- **Database:** Normalized panel database organized by MSA, two-digit NAICS industry, year, entrepreneurship measures, industry metrics and regional controls
- **Analysis:** Python using pandas, NumPy, statsmodels, scikit-learn, and potentially XGBoost. All cleaning, modeling, and validation scripts will be version-controlled and reproducible
- **Dashboard:** Streamlit dashboard showing MSA and industry trends, observed versus expected entrepreneurship, entrepreneurial gaps, and predicted future gap probabilities
- **Deployment:** Streamlit Cloud connected to the project repository so the dashboard and analysis can be updated as new data are added

| Weeks | Milestone / activities | Course anchor |
| --- | --- | --- |
| 1-2 | Collect data, clean sources, build database schema | Before R3 |
| 3-4 | Construct variables and complete exploratory analysis | Before R3 |
| 5-8 | Estimate models, compare predictions, validate results | Before R3 |
| 9-12 | Build dashboard, deploy application, draft findings | Before R3 |
| 13 | Final review, documentation, and submission | R3 |

## 11. References

Bruns, K., Bosma, N., Sanders, M., & Schramm, M. (2017). Searching for the existence of entrepreneurial ecosystems: A regional cross-section growth regression approach. *Small Business Economics, 49*, 31-54.

Cosci, S., Meliciani, V., & Pini, M. (2022). Historical roots of innovative entrepreneurial culture: The case of Italian regions. *Regional Studies, 56*(10), 1683-1697.

Dejardin, M. (2011). Linking net entry to regional economic growth. *Small Business Economics, 36*(4), 443-460.

Fritsch, M., Sorgner, A., Wyrwich, M., & Zazdravnykh, E. (2019). Historical shocks and persistence of economic activity: Evidence on self-employment from a unique natural experiment. *Regional Studies, 53*(6), 790-802.

Fritsch, M., Potter, J., Qian, H., & Fotopoulos, G. (2025). Persistence and change in regional entrepreneurship performance: A three-economy comparison. *Regional Studies, 59*(1), 2474033.

Mazzoni, L., & Innocenti, N. (2024). What conditions favor high-potential entrepreneurship? Unpacking the nexus between the industrial structure and startup typologies. *Small Business Economics, 62*, 1201-1222.

Qian, H. (2017). Skills and knowledge-based entrepreneurship: Evidence from U.S. cities. *Regional Studies, 51*(10), 1469-1482.

Renski, H. (2014). The influence of industry mix on regional new firm formation in the United States. *Regional Studies, 48*(8), 1353-1370.

Stuetzer, M., Obschonka, M., Audretsch, D. B., Wyrwich, M., Rentfrow, P. J., Coombes, M., Shaw-Taylor, L., & Satchell, M. (2016). Industry structure, entrepreneurship, and culture: An empirical analysis using historical coalfields. *European Economic Review, 86*, 52-72.
