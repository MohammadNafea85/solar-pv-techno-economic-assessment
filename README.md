# ☀️ Solar PV Techno-Economic Assessment — Egypt

**Author:** Mohammad Nafea — Senior Power Plant Operation Engineer | Energy Analyst  
**Location Reference:** Benban Solar Park Region, Aswan, Egypt  
**Tools:** Python · Pandas · NumPy · Matplotlib  
**Date:** June 2026

---

## 📌 Project Overview

This project delivers a full **techno-economic feasibility assessment** for utility-scale Solar PV investments in Egypt, evaluating four capacity scenarios from 1 MW to 50 MW.

Drawing on real solar resource data from Egypt's Benban region — one of the world's largest solar parks — the analysis integrates engineering performance modelling with financial evaluation to support investment decision-making.

This work complements my [Gas Turbine Performance & Emissions Analysis](https://github.com/MohammadNafea85/gas-turbine-performance-analysis), extending my energy analytics expertise from conventional CCGT plants into renewable energy systems.

---

## 🎯 Objectives

- Quantify monthly and annual solar energy yield using GHI irradiance data
- Calculate key financial metrics: **LCOE, NPV, IRR, Payback Period**
- Compare four project capacity scenarios to identify economies of scale
- Perform sensitivity analysis on tariff and capacity factor assumptions
- Estimate CO₂ emissions avoided over a 25-year project life

---

## ⚙️ Technical Methodology

### Solar Resource
| Parameter | Value | Source |
|---|---|---|
| Location | Benban, Aswan, Egypt | NASA POWER / PVGIS |
| Annual GHI | ~2,337 kWh/m²/yr | Validated against Benban operational data |
| Peak month | June (8.5 kWh/m²/day) | — |
| Lowest month | December (3.9 kWh/m²/day) | — |

### System Parameters
| Parameter | Value | Rationale |
|---|---|---|
| Panel Technology | Monocrystalline Silicon | Industry standard for utility-scale |
| Panel Efficiency | 20% | Typical mono-Si at STC |
| Performance Ratio (PR) | 0.80 | Accounts for inverter, wiring, soiling, shading |
| Annual Degradation | 0.5%/yr | Standard for mono-Si (IEC 61215) |
| Project Lifetime | 25 years | Standard PPA / project financing horizon |

**Energy Yield Formula:**
```
E (MWh/yr) = Capacity (MW) × GHI (kWh/m²/yr) × Performance Ratio
```

---

## 💰 Financial Parameters

| Parameter | Value | Notes |
|---|---|---|
| Electricity Tariff | $0.07/kWh | Egypt Feed-in Tariff Round 2 reference |
| Discount Rate (WACC) | 8% | Reflects Egypt renewable energy project risk |
| OPEX Inflation | 2%/yr | Annual cost escalation |
| Grid Emission Factor | 0.47 tCO₂/MWh | Egypt national grid (IEA 2023) |

### LCOE Calculation
```
LCOE = Σ (Costs_t / (1+r)^t) / Σ (Energy_t / (1+r)^t)
```
Where costs include CAPEX + inflated OPEX over 25 years, and energy accounts for 0.5%/yr degradation.

### IRR Calculation
Solved using the Newton-Raphson iterative method on the full 25-year cash flow stream:
```
NPV(IRR) = Σ CF_t / (1 + IRR)^t = 0
```

---

## 📊 Scenario Results

| Scenario | CAPEX ($M) | Energy Yr1 (GWh) | Capacity Factor | LCOE (¢/kWh) | NPV ($M) | IRR | Payback |
|---|---|---|---|---|---|---|---|
| Small (1 MW) | $0.75M | 1.87 GWh | 21.4% | 4.90¢ | $0.65M | 16.4% | 7 yrs |
| Medium (5 MW) | $3.40M | 9.35 GWh | 21.4% | 4.41¢ | $3.71M | 18.4% | 6 yrs |
| Large (20 MW) | $12.4M | 37.4 GWh | 21.4% | 3.99¢ | $16.4M | 20.4% | 6 yrs |
| Utility (50 MW) | $29.0M | 93.5 GWh | 21.4% | 3.72¢ | $43.7M | 22.0% | 5 yrs |

**Key finding:** All scenarios are financially viable (IRR > 16%, well above the 8% discount rate). Larger projects show significantly better economics due to CAPEX and OPEX economies of scale — LCOE drops from 4.90¢ to 3.72¢/kWh as scale increases from 1 MW to 50 MW.

---

## 📁 Repository Structure

```
solar-pv-techno-economic-assessment/
│
├── solar_pv_assessment.py          # Main analysis + visualization script (self-contained)
├── README.md                       # This file
│
├── data/
│   ├── monthly_irradiance.csv      # GHI data + monthly energy yield
│   ├── scenario_results.csv        # Summary of all scenario metrics
│   ├── cashflow_1MW.csv            # 25-yr cash flow — 1 MW scenario
│   ├── cashflow_5MW.csv            # 25-yr cash flow — 5 MW scenario
│   ├── cashflow_20MW.csv           # 25-yr cash flow — 20 MW scenario
│   └── cashflow_50MW.csv           # 25-yr cash flow — 50 MW scenario
│
└── charts/
    ├── fig1_irradiance.png            # Monthly solar resource (GHI)
    ├── fig1b_monthly_energy.png       # Monthly energy yield — 5 MW reference plant
    ├── fig2a_lcoe.png                 # LCOE comparison across scenarios
    ├── fig2b_npv.png                  # NPV comparison across scenarios
    ├── fig2c_irr.png                  # IRR comparison across scenarios
    ├── fig2d_payback.png              # Payback period comparison
    ├── fig3_cashflow.png              # 25-yr cumulative cash flow — all scenarios
    ├── fig4a_sensitivity_heatmap.png  # IRR sensitivity heatmap (tariff × capacity factor)
    └── fig4b_co2_avoided.png          # CO₂ avoided per scenario
```

### Chart design notes
All charts share one consistent, high-contrast visual style:
- White background with a light panel tint for the plot area — no dark chrome competing with text
- Near-black ink color for every title, axis label, and tick — guaranteed readability
- The sensitivity heatmap uses **viridis**, a perceptually-uniform, colorblind-safe colormap, with an evenly-ticked 0–40% scale
- One chart per file, so each metric can be dropped individually into a report or slide

---

## 🔑 Key Insights

**1. Egypt's Solar Resource is Exceptional**  
Annual GHI of ~2,337 kWh/m²/yr places Egypt among the world's best solar resources, yielding a capacity factor of 21.4% — well above the global average of 15–18%.

**2. All Scenarios Deliver Strong Returns**  
Every scenario generates IRR above 16%, significantly exceeding the 8% discount rate. Even the smallest 1 MW project achieves a 7-year payback — well within the 25-year project life.

**3. Scale Dramatically Improves Economics**  
Moving from 1 MW to 50 MW reduces LCOE by 24% (4.90¢ → 3.72¢/kWh) and improves IRR by 5.6 percentage points, driven by CAPEX economies of scale ($750k/MW → $580k/MW).

**4. LCOE Well Below Tariff Across All Scenarios**  
At a tariff of 7.0¢/kWh, all scenarios generate positive spread above LCOE, confirming robust profitability under current Egyptian FiT framework.

**5. Significant Environmental Impact**  
A 50 MW utility-scale plant avoids ~1,103 kt of CO₂ over 25 years — equivalent to taking ~240,000 cars off the road annually.

---

## 🔗 Related Work

- 🔧 [Gas Turbine Performance & Emissions Analysis (CCGT)](https://github.com/MohammadNafea85/gas-turbine-performance-analysis) — ML-based performance monitoring of a 750 MW CCGT plant, applying ISO 2314 ambient correction and NOx emissions analysis.

---

## 👤 About the Author

Mohammad Nafea is a Senior Power Plant Operation Engineer with 13+ years of experience operating large-scale CCGT plants (1,300+ MW) with GE, MHI, and ANSALDO turbines. He combines deep operational engineering expertise with data analytics skills (Python, Power BI, SQL) to bridge the gap between plant operations and strategic energy advisory.

📧 nafeamohammad1@gmail.com  
🔗 [LinkedIn](https://www.linkedin.com/in/mohammed-nafea-7086b072)  
💻 [GitHub](https://github.com/MohammadNafea85)
