# 06_SCORING_SYSTEM.md — WebPulse Scoring System Specification (v2.0)

## 1. Purpose
This document specifies the mathematical formulas, weighting rules, severity levels, and confidence interval calculations used to generate WebPulse auditing reports. It ensures all scores are reproducible, transparent, and aligned with standard risk assessment frameworks across multi-page crawls and authenticated zones.

---

## 2. Overview
WebPulse generates a numerical score between 0 and 100 for each auditing vector (Security, SEO, Performance, Accessibility), which are then combined to calculate a single **Overall Health Score**. Deductions are applied based on discovered findings, weighted by their severity level, finding confidence, and target page depth.

---

## 3. Severity Levels and Weights
WebPulse assigns a numeric weight to each finding based on its severity:

| Severity Level | Weight ($W_{sev}$) | Description |
|---|---|---|
| **Critical** | 10.0 | High-severity exploits (e.g., exposed config, critical CVEs, expired SSL). |
| **High** | 6.0 | Missing primary security boundaries (e.g., CSP missing, TLS 1.0 enabled). |
| **Medium** | 3.0 | Modern standard recommendations omitted (e.g., CORS mismatch, slow response). |
| **Low** | 1.0 | Minor issues (e.g., Alt tags missing, short SEO meta descriptions). |
| **Info** | 0.0 | Information collection points (e.g., detected tech headers). |

---

## 4. Finding Confidence Metric
Each finding includes a confidence rating ($C$) between 0.0 and 1.0:
* **Certain (1.0):** Direct, verifiable proof (e.g. HTTP header verified).
* **Firm (0.7):** Heuristics matched with high probability.
* **Tentative (0.4):** Indirect correlation or weak signature match.

---

## 5. Scoring Formulas

### 5.1 Single-Page Score
For any individual audited URL (page $p$), the raw category score is:

$$Score_{page, p} = \max\left(0, 100 - \sum_{i=1}^{n} (W_{sev, i} \times C_{i} \times M_{category})\right)$$

Where:
* $W_{sev, i}$ is the severity weight of finding $i$.
* $C_{i}$ is the confidence of finding $i$.
* $M_{category}$ is the category deduction multiplier:
  * **Security Multiplier ($M_{sec}$):** 1.5
  * **Performance Multiplier ($M_{perf}$):** 1.2
  * **Accessibility Multiplier ($M_{a11y}$):** 1.0
  * **SEO Multiplier ($M_{seo}$):** 0.8

### 5.2 Multi-Page Aggregate Category Score
To prevent a site's category score from being disproportionately skewed by a single minor page, WebPulse applies a weighted average between the root page and subpages:

$$Score_{category} = (Score_{root} \times 0.50) + \left(\frac{1}{P_{sub}} \sum_{s=1}^{P_{sub}} Score_{subpage, s} \times 0.50\right)$$

* If no subpages were crawled ($P_{sub} = 0$), then $Score_{category} = Score_{root}$.
* If $P_{sub} > 0$, the subpage scores are averaged and contribute $50\%$ to the final category score.

### 5.3 Authentication Status Modifier
If session authentication was configured in `webpulse.yaml`, but the `AuthCoordinator` failed to log in or received HTTP 401/403 errors during page scans:
* A penalty deduction of **-15 points** is subtracted directly from the final $Score_{sec}$.

### 5.4 Overall Health Score
The Overall Health Score ($HS_{overall}$) is a weighted average of the individual aggregate category scores:

$$HS_{overall} = (Score_{sec} \times 0.40) + (Score_{perf} \times 0.25) + (Score_{a11y} \times 0.20) + (Score_{seo} \times 0.15)$$

### 5.5 Risk Score
The Risk Score represents the target site's vulnerability risk exposure, calculated on a scale of 0 to 10:

$$RiskScore = \min\left(10.0, \frac{100 - HS_{overall}}{10} + \max(0, \text{Critical Count} \times 1.0)\right)$$

---

## 6. Heuristic Confidence Calculations

### 6.1 WAF and Technology Match Confidence
When identifying active Web Application Firewalls or backend frameworks, the engine calculates a match confidence percentage based on signature weight parameters:

$$Confidence_{match} = \frac{\sum(\text{Matched Signature Weights})}{\sum(\text{Total Weights in Tech Signature Map})} \times 100$$

* If a tech match is detected by header ($weight=4$), cookie ($weight=3$), and path response ($weight=3$), the confidence is $100\%$.
* If only a cookie matches, the confidence drops to $30\%$.

---

## 7. Numerical Example Calculation

### 7.1 Scenario
A target site is crawled, yielding 1 root page and 2 subpages ($P_{sub}=2$). Authenticated scan was configured and completed successfully.
* **Root Page Findings:** 1 Critical Security Finding (Confidence 1.0), 1 High Performance Finding (Confidence 0.7).
* **Subpage 1 Findings:** 2 Low SEO Findings (Confidence 1.0).
* **Subpage 2 Findings:** 1 Medium Security Finding (Confidence 1.0).

### 7.2 Math Walkthrough
1. **Security Scores:**
   * **Root Security Score:** $Score_{root\_sec} = 100 - (10.0 \times 1.0 \times 1.5) = 100 - 15.0 = 85$
   * **Subpage 1 Security Score:** $Score_{sub1\_sec} = 100 - 0 = 100$
   * **Subpage 2 Security Score:** $Score_{sub2\_sec} = 100 - (3.0 \times 1.0 \times 1.5) = 100 - 4.5 = 95.5 \approx 96$
   * **Aggregate Security Score:**
     $$Score_{sec} = (85 \times 0.50) + \left(\frac{100 + 96}{2} \times 0.50\right) = 42.5 + (98 \times 0.50) = 42.5 + 49 = 91.5 \approx 92$$

2. **SEO Scores:**
   * **Root SEO Score:** $Score_{root\_seo} = 100$
   * **Subpage 1 SEO Score:** $Score_{sub1\_seo} = 100 - 2 \times (1.0 \times 1.0 \times 0.8) = 100 - 1.6 = 98.4 \approx 98$
   * **Subpage 2 SEO Score:** $Score_{sub2\_seo} = 100$
   * **Aggregate SEO Score:**
     $$Score_{seo} = (100 \times 0.50) + \left(\frac{98 + 100}{2} \times 0.50\right) = 50 + 49.5 = 99.5 \approx 100$$

3. **Performance Scores:**
   * **Root Performance Score:** $Score_{root\_perf} = 100 - (6.0 \times 0.7 \times 1.2) = 100 - 5.04 = 94.96 \approx 95$
   * **Subpage 1 & 2 Performance Score:** $100$
   * **Aggregate Performance Score:**
     $$Score_{perf} = (95 \times 0.50) + (100 \times 0.50) = 47.5 + 50 = 97.5 \approx 98$$

4. **Aggregate Accessibility Score:** $100$ (No findings).

5. **Overall Health Score:**
   $$HS_{overall} = (92 \times 0.40) + (98 \times 0.25) + (100 \times 0.20) + (100 \times 0.15) = 36.8 + 24.5 + 20 + 15 = 96.3 \approx 96\%$$

---

## 8. Design Decisions
* **Decision:** The scoring system uses a fixed multiplier structure ($M_{category}$) for vulnerability scoring deductions.
* **Rationale:** This prioritizes security issues. A single critical security vulnerability has a larger impact on the overall score than multiple minor performance issues.

---

## 9. References
* CVSS (Common Vulnerability Scoring System) v3.1 Specification: https://www.first.org/cvss/specification-document
* Google Lighthouse Scoring Methodology: https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/

---

## 10. Validation Rules
* No individual category score can fall below 0 or exceed 100.
* Overall Health Score must be rounded to the nearest integer.

---

## 11. Engineering Notes
* Scoring logic must reside fully within the `webpulse.reports.reporter` module to prevent analyzer plugins from calculating their own scores dynamically.

---

## 12. AI Notes
* Do not attempt to write custom scoring algorithms inside individual plugins. Plugins only supply `Finding` instances with specified `Severity` and `Confidence`.
