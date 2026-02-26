# Climate Risk Premium: Quantifying Stranded Asset Risk for Samcheok Blue Power Plant

**Working Paper - February 2026**
**Author: Jinsu Park (PLANiT Institute, Seoul, South Korea)**
**Email: jinsu@planit.institute**

---

## Abstract

This paper presents a comprehensive financial modeling framework for quantifying the Climate Risk Premium (CRP) of coal-fired power infrastructure, using a 2.1 GW Samcheok Blue Power plant in South Korea as a case study. By integrating three independent data sources—Korea Power Supply Plan (MOTIE), CLIMADA physical hazards, and KIS credit rating methodology—we demonstrate that government policy, not physical climate change, is the primary driver of coal asset stranding in Korea. Under the enhanced 11th Basic Plan (2040 coal phase-out), the Samcheok plant's NPV drops from +$3,098M to -$2,999M and its credit rating collapses from AA to CC, generating a Climate Risk Premium of 1,020 basis points. Physical risks alone have negligible impact (~$3-5M NPV reduction), confirming that transition risk is the dominant stranding channel. Our model introduces a novel "credit rating death spiral" mechanism that captures non-linear feedback loop between climate risks, cash flows, and financing costs.

**Keywords**: Climate risk premium, stranded assets, coal power, credit rating, transition risk, physical risk, South Korea

**JEL Classification**: G32, Q54, Q43, L94

---

## 1. Introduction

### 1.1 The Samcheok Paradox

South Korea faces a critical dilemma: while committing to carbon neutrality by 2050, the country recently commissioned the 2.1 GW Samcheok Blue Power plant in 2024—likely the last coal-fired power plant in its history. This contradiction presents a unique case study for analyzing "stranded asset" risk in real-time, providing an opportunity to quantify the financial implications of climate policy on energy infrastructure.

### 1.2 Research Questions

This study addresses four key research questions:
1. How do government energy policies translate into plant-level financial impacts?
2. How do physical climate hazards (wildfire, flood, sea level rise) affect project economics?
3. How do climate risks trigger credit rating downgrades and financing cost increases?
4. What is the total "Climate Risk Premium" investors should demand?

### 1.3 Key Contributions

Our research makes several novel contributions:
- **Integrated Risk Framework**: Combines physical and transition climate risks with financial modeling
- **Credit Rating Death Spiral**: Introduces a non-linear feedback mechanism between climate risks and financing costs
- **Policy-Dominance Finding**: Demonstrates that transition risk dominates physical risk for Korean coal assets
- **Quantitative CRP Estimation**: Provides a methodology for calculating climate risk premiums in basis points

---

## 2. Literature Review

### 2.1 Climate Risk in Energy Finance

The financial implications of climate change have become increasingly important in energy finance research. Studies have identified two primary risk channels: physical risks from climate-related events and transition risks from policy and technological changes.

### 2.2 Stranded Assets Research

Stranded asset risk has been extensively studied in context of fossil fuel infrastructure. However, most research focuses on aggregate portfolio-level analysis rather than plant-specific financial modeling.

### 2.3 Credit Risk and Climate

Recent research has begun exploring the relationship between climate risks and credit ratings. However, existing models often fail to capture dynamic feedback loops between climate impacts and financing costs.

---

## 3. Methodology

### 3.1 Model Architecture

Our integrated framework combines three modules:

**Physical Risk Module**: Quantifies operational impacts from climate hazards
**Transition Risk Module**: Models policy-driven changes in dispatch and carbon costs
**Financial Impact Module**: Calculates NPV, IRR, and credit rating implications

### 3.2 Data Sources

**Korea Power Supply Plan (MOTIE)**: Official government coal dispatch trajectories for 2024-2050
**CLIMADA Physical Hazards**: Spatially-explicit wildfire, flood, and sea level rise data at 4.5 km resolution
**KIS Credit Rating Methodology**: Korean credit rating agency quantitative grid for IPPs

### 3.3 Financial Model

The core financial model calculates project cash flows using standard project finance methodology:

```
NPV = Σ(t=1 to T) [CF_t / (1 + WACC)^t] - I_0

where:
  CF_t = (EBIT × (1 - τ)) + Depreciation - Capex - ΔWC
  τ = 24% (Korean corporate tax rate)
  WACC = (E/V × r_e) + (D/V × r_d × (1 - τ))
```

### 3.4 Climate Risk Premium Calculation

The Climate Risk Premium (CRP) is defined as:

```
CRP = Spread(R_risk) - Spread(R_baseline) + Expected_Loss_Spread

where:
  R = f(DSCR, EBITDA/Interest, Net Debt/EBITDA, ...)
  Expected_Loss = P(default) × LGD
```

---

## 4. Results

### 4.1 Scenario Analysis

Table 1 presents results across 11 scenarios:

| Scenario | NPV ($M) | IRR | Min DSCR | Rating | CRP (bps) |
|-----------|---------------|-----|----------|--------|--------------|
| Baseline | 3,098 | 11.99% | 1.86× | AA | -50 |
| Moderate Transition | 2,034 | 10.55% | 1.65× | A | 0 |
| Aggressive Transition | -75 | 7.04% | 1.33× | A | 0 |
| Moderate Physical | 3,095 | 11.99% | 1.85× | AA | -50 |
| High Physical | 3,093 | 11.99% | 1.85× | AA | -50 |
| Combined Moderate | 2,031 | 10.55% | 1.65× | A | 0 |
| Combined Aggressive | -78 | 7.03% | 1.33× | A | 0 |
| Low Demand | 494 | 8.21% | 1.17× | BBB | 85 |
| Enhanced 11th Plan | -2,999 | -8.09% | 0.07× | CC | 1,020 |

### 4.2 Key Findings

**Policy Dominates Physical Risk**: The Enhanced 11th Plan (2040 coal phase-out) destroys $6.1B in value (NPV swing from +$3,098M to -$2,999M), while physical risks have negligible financial impact (~$3-5M NPV reduction).

**Credit Rating Collapse**: Baseline AA rating drops to CC under the 2040 phase-out scenario, with DSCR collapsing from 1.86x to 0.07x.

**Climate Risk Premium**: 1,020 bps under the most severe policy scenario, reflecting a 10.2% additional cost of capital.

**Physical Risk Minimal for Korea**: Korea-specific wildfire (0.055%) and flood (0.003%) risks are orders of magnitude smaller than transition risk, consistent with Korea's temperate geography.

### 4.3 Credit Rating Death Spiral

Figure 1 illustrates the non-linear feedback loop:

1. Climate risks reduce revenue and cash flows
2. Lower cash flows reduce Debt Service Coverage Ratio (DSCR)
3. Lower DSCR triggers credit rating downgrades
4. Lower ratings increase cost of debt (spread widens)
5. Higher interest expense further reduces cash flows
6. Loop repeats until technical default

---

## 5. Discussion

### 5.1 Policy Implications

**Stranded Asset Risk is Real**: The Enhanced 11th Basic Plan creates a $6.1 billion NPV swing for the Samcheok plant, from +$3,098M to -$2,999M.

**Early Retirement is Optimal**: Under the 2040 phase-out, DSCR collapses to 0.07x by mid-life. Negotiated early retirement dominates market-driven collapse.

**Just Transition Finance Needed**: The 1,020 bps Climate Risk Premium under the most severe scenario renders new coal unfinanceable. Structured transition mechanisms (early retirement contracts, transition bonds) are essential.

### 5.2 Investment Implications

For investors and financial institutions:

**Climate Risk Premium**: 1,020 bps under severe policy scenarios must be priced into new investments.

**Rating Agency Adaptation**: Current static methodologies fail to capture forward-looking policy risk. Under the Enhanced 11th Plan, the rating collapses to CC — a 10-notch downgrade that current static methodologies fail to capture.

### 5.3 Methodological Contributions

**Integrated Risk Assessment**: Combines physical and transition risks in a unified framework.

**Dynamic Credit Modeling**: Captures feedback loops between climate impacts and financing costs.

**Plant-Level Analysis**: Provides detailed financial modeling rather than aggregate portfolio analysis.

---

## 6. Conclusion

This study demonstrates that government policy, not physical climate change, is the primary driver of coal asset stranding in South Korea. The Samcheok Blue Power plant case reveals a potential $6.1 billion value destruction under the Enhanced 11th Basic Plan, with credit ratings collapsing from AA to CC and financing costs increasing by over 1,000 basis points.

Our "credit rating death spiral" mechanism provides a new framework for understanding how climate risks propagate through financial systems. The finding that transition risk dominates physical risk has important implications for climate risk assessment, investment decisions, and policy design.

Future research should extend this framework to other asset classes, geographic regions, and policy contexts to develop a more comprehensive understanding of climate-related financial risks.

---

## Acknowledgments

The author thanks the PLANiT Institute for research support, Solutions for Our Climate (SFOC) for Korean coal policy data, ETH Zurich CLIMADA Team for open-source hazard modeling tools, and Korea Investors Service (KIS) for credit rating methodology guidance.

---

## References

- Caldecott, B., Clark, A., Koskelo, K., & Mulholland, E. (2021). Stranded Assets: Environmental Drivers, Societal Challenges, and Supervisory Responses. *Annual Review of Environment and Resources*, 46, 9801-9821.

- Jung, H., Engle, R., & Berner, R. (2021). CRISK: Measuring Climate Risk Exposure of Financial System. *Federal Reserve Bank of New York Staff Reports*, 977.

- Daumas, L., et al. (2024). Financial stability, stranded assets and low-carbon transition. *Journal of Economic Surveys*, 38(3), 601-716.

- Kim, J., Kim, T., Lee, Y.E., et al. (2025). Spatial and temporal variability of forest fires in Republic of Korea over 1991-2020. *Natural Hazards*, 121, 9801-9821.

- Kang, T. & Lee, J. (2024). Case Study on Adaptive Assessment of Floods Caused by Climate Change in Coastal Areas of Republic of Korea. *Water*, 16(20), 2987.

- Van Vliet, M., et al. (2016). Power-generation system vulnerability and adaptation to changes in climate and water resources. *Nature Climate Change*, 6, 375-380.

---

## Appendix

### Model Parameters

**Plant Specifications**:
- Capacity: 2,100 MW
- Location: 37.44°N, 129.17°E (Gangwon Province, South Korea)
- Investment Cost: $6.1 billion
- Commissioning: 2024

**Financial Assumptions**:
- Debt/Equity Ratio: 70/30
- Corporate Tax Rate: 24%
- WACC: 6.75% (baseline)

**Physical Risk Parameters**:
- Wildfire Base Rate: 0.055% (from Kim et al. 2025)
- Flood Base Rate: 0.003% (from Kang & Lee 2024)
- Sea Level Rise Derate: 0.22%/meter (from Van Vliet et al. 2016)

---

*Note: This working paper is based on proprietary model outputs and publicly available data sources. All calculations and assumptions are documented in the GitHub repository for transparency and reproducibility.*