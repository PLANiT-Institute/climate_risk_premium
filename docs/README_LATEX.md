# Mathematical Framework for Climate Risk Premium

This directory contains the rigorous mathematical derivation and proofs for the Climate Risk Premium model.

## Document Overview

**File**: `mathematical_framework.tex`

### Contents

1. **Introduction** (Section 1)
   - Motivation and problem statement
   - Contributions

2. **Model Setup** (Section 2)
   - Notation and definitions
   - Cash flow equations
   - State variables

3. **Climate Risk Integration** (Section 3)
   - Transition risk mathematical formulation
   - Physical risk modeling
   - Combined risk scenarios

4. **Financial Metrics** (Section 4)
   - NPV and IRR definitions
   - DSCR and LLCR formulas
   - Debt amortization

5. **Expected Loss Framework** (Section 5)
   - Formal definition of expected loss
   - **Theorem**: Monotonicity of expected loss
   - Statistical extensions

6. **Climate Risk Premium** (Section 6)
   - WACC formulation
   - Spread mapping assumptions
   - **Main Theorem**: CRP existence and bounds
   - **Corollary**: CRP scaling properties

7. **Comparative Statics** (Section 7)
   - Sensitivity to carbon pricing
   - Sensitivity to physical risk
   - **Theorem**: Subadditivity of combined risks

8. **Empirical Calibration** (Section 8)
   - Parameter estimates
   - Samcheok case study results
   - Key findings

9. **Discussion** (Section 9)
   - Policy implications
   - Model limitations
   - Extensions

10. **Appendices**
    - Technical proofs
    - Numerical algorithms
    - Convergence properties

## Key Mathematical Results

### Theorem 1: Monotonicity of Expected Loss
Climate risks with stricter constraints always produce higher expected losses.

### Theorem 2: CRP Existence and Bounds
- **Existence**: Climate risks always increase cost of capital when EL > 0
- **Upper Bound**: CRP is bounded by a linear function of expected loss percentage

### Theorem 3: Subadditivity of Combined Risks
Physical risks partially offset carbon cost impacts, creating subadditive interactions.

## Compilation Instructions

### Prerequisites

Install a LaTeX distribution:
- **macOS**: MacTeX (`brew install --cask mactex`)
- **Linux**: TeX Live (`sudo apt-get install texlive-full`)
- **Windows**: MiKTeX or TeX Live

### Compile the PDF

#### Option 1: Using Make (Recommended)
```bash
cd docs/
make              # Compile with bibliography
make view         # Compile and open PDF (macOS)
make clean        # Remove auxiliary files
```

#### Option 2: Manual Compilation
```bash
cd docs/
pdflatex mathematical_framework.tex
bibtex mathematical_framework
pdflatex mathematical_framework.tex
pdflatex mathematical_framework.tex
```

The output will be: **`mathematical_framework.pdf`**

## Document Features

### Mathematical Rigor
- **8 Definitions**: Formal definitions of all key concepts
- **3 Assumptions**: Explicit modeling assumptions
- **3 Theorems**: Main results with proofs
- **4 Propositions**: Supporting results
- **2 Lemmas**: Technical results in appendix

### Equations
- 60+ numbered equations
- Consistent notation throughout
- Clear variable definitions

### Tables
- Parameter calibration table
- Empirical results from Samcheok case study

### References
- 8 key papers in climate finance
- TCFD recommendations
- Climate stress-testing literature

## Using the Document

### For Academic Papers
Cite as:
```
Climate Risk Analysis Team (2025). Mathematical Framework for Quantifying
Climate Risk Premium in Infrastructure Finance. Plan It Institute Technical Report.
```

### For Presentations
Key slides to extract:
- Definition of CRP (Equation 24)
- Main theorem (Theorem 2)
- Empirical results table (Table 2)
- Policy implications (Section 9.1)

### For Extensions
The framework is modular:
- **Monte Carlo**: Replace Section 3 assumptions with stochastic processes
- **Real Options**: Add Section 7.4 on flexibility value
- **Portfolio**: Extend Section 5.2 to correlated risks

## Notation Summary

| Symbol | Meaning |
|--------|---------|
| $T$ | Design lifetime |
| $T^*$ | Actual operating lifetime under climate risk |
| $C$ | Installed capacity (MW) |
| $\rho_t$ | Capacity factor |
| $\tau_t$ | Carbon price ($/tCO₂) |
| $\lambda$ | Outage rate |
| $\delta$ | Capacity derating |
| $\text{EL}\%$ | Expected loss percentage |
| $\text{CRP}$ | Climate Risk Premium |
| $w_d, w_e$ | Debt and equity fractions |
| $\beta_d, \beta_e$ | Spread sensitivities |

## Theoretical Contributions

1. **First formal definition of CRP** in project finance context
2. **Proof of monotonicity** linking climate policy stringency to losses
3. **Analytical bounds on CRP** as function of expected loss
4. **Subadditivity result** showing interaction effects between risk types
5. **Transparent calibration** to empirical financing parameters

## Contact

For questions about the mathematical framework:
- Technical: jinsu@planit.institute
- Methodological: sanghyun@planit.institute

## License

This document is released under Creative Commons CC-BY 4.0. You are free to:
- Share and adapt the material
- With proper attribution

---

**Document Status**: Complete and ready for publication
**Last Updated**: November 2025
**Version**: 1.0
