"""
Solar PV Techno-Economic Assessment Tool
========================================
Author  : Mohammad Nafea
Date    : June 2026
Location: Egypt (Benban Solar Park Reference Data)
Purpose : Assess technical and economic viability of utility-scale Solar PV projects
          across multiple capacity scenarios using real engineering parameters.

Key Outputs:
  - Monthly energy yield based on GHI irradiance data
  - LCOE, NPV, IRR, Payback Period per scenario
  - 25-year cash flow projections
  - Sensitivity analysis (tariff vs capacity factor)
  - CO2 emissions avoided
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. SITE & RESOURCE DATA
# =============================================================================
LOCATION = "Egypt — Benban Solar Region (Aswan)"

# Monthly Global Horizontal Irradiance (GHI) — kWh/m²/day
# Source: NASA POWER / PVGIS validated against Benban operational data
MONTHLY_GHI = {
    'Jan': 4.2, 'Feb': 5.1, 'Mar': 6.3, 'Apr': 7.4,
    'May': 8.1, 'Jun': 8.5, 'Jul': 8.2, 'Aug': 7.8,
    'Sep': 7.0, 'Oct': 5.8, 'Nov': 4.5, 'Dec': 3.9
}
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# =============================================================================
# 2. TECHNICAL PARAMETERS
# =============================================================================
PANEL_EFFICIENCY    = 0.20    # 20% — monocrystalline silicon
PERFORMANCE_RATIO   = 0.80    # PR: accounts for inverter, wiring, soiling, shading losses
DEGRADATION_RATE    = 0.005   # 0.5%/yr — industry standard for mono-Si
PROJECT_LIFE_YRS    = 25      # Standard solar PPA / project lifetime

# =============================================================================
# 3. FINANCIAL PARAMETERS
# =============================================================================
DISCOUNT_RATE        = 0.08   # 8% WACC
ELECTRICITY_TARIFF   = 0.07   # $0.07/kWh — Egypt Feed-in Tariff (Round 2 reference)
INFLATION_RATE       = 0.02   # 2% annual OPEX inflation
GRID_EMISSION_FACTOR = 0.47   # tCO2/MWh — Egypt national grid (IEA 2023)

# =============================================================================
# 4. PROJECT SCENARIOS
# =============================================================================
SCENARIOS = {
    'Small (1 MW)':    {'capacity_mw': 1,  'capex_per_mw': 750_000, 'opex_per_mw_yr': 15_000},
    'Medium (5 MW)':   {'capacity_mw': 5,  'capex_per_mw': 680_000, 'opex_per_mw_yr': 13_000},
    'Large (20 MW)':   {'capacity_mw': 20, 'capex_per_mw': 620_000, 'opex_per_mw_yr': 11_500},
    'Utility (50 MW)': {'capacity_mw': 50, 'capex_per_mw': 580_000, 'opex_per_mw_yr': 10_500},
}


# =============================================================================
# 5. HELPER FUNCTIONS
# =============================================================================

def compute_annual_ghi():
    """Return total annual GHI in kWh/m²/year."""
    return sum(ghi * days for ghi, days in zip(MONTHLY_GHI.values(), DAYS_IN_MONTH))


def compute_monthly_energy(capacity_mw):
    """Return DataFrame with monthly energy yield for a given capacity."""
    rows = []
    for (month, ghi), days in zip(MONTHLY_GHI.items(), DAYS_IN_MONTH):
        energy_mwh = capacity_mw * ghi * days * PERFORMANCE_RATIO
        rows.append({'Month': month, 'GHI_kWh_m2_day': ghi,
                     'Days': days, 'Energy_MWh': round(energy_mwh, 1)})
    return pd.DataFrame(rows)


def compute_lcoe(capex, opex_yr1, annual_energy_mwh_yr1):
    """Compute Levelised Cost of Energy ($/kWh)."""
    pv_costs = capex + sum(
        opex_yr1 * (1 + INFLATION_RATE)**(yr-1) / (1 + DISCOUNT_RATE)**yr
        for yr in range(1, PROJECT_LIFE_YRS + 1)
    )
    pv_energy = sum(
        annual_energy_mwh_yr1 * 1000 * (1 - DEGRADATION_RATE)**(yr-1) / (1 + DISCOUNT_RATE)**yr
        for yr in range(1, PROJECT_LIFE_YRS + 1)
    )
    return pv_costs / pv_energy


def compute_irr(cash_flows, guess=0.10, iterations=200):
    """Compute Internal Rate of Return using Newton-Raphson method."""
    r = guess
    for _ in range(iterations):
        f  = sum(cf / (1 + r)**t for t, cf in enumerate(cash_flows))
        df = sum(-t * cf / (1 + r)**(t+1) for t, cf in enumerate(cash_flows))
        if abs(df) < 1e-12:
            break
        r -= f / df
    return r


def build_cashflow(capacity_mw, capex, opex_yr1, annual_energy_yr1_mwh):
    """Build 25-year cash flow table."""
    rows = []
    cumulative = -capex
    payback_yr = None
    for yr in range(1, PROJECT_LIFE_YRS + 1):
        energy   = annual_energy_yr1_mwh * (1 - DEGRADATION_RATE)**(yr-1)
        tariff   = ELECTRICITY_TARIFF * (1 + INFLATION_RATE)**(yr-1)
        revenue  = energy * 1000 * tariff                          # kWh × $/kWh
        opex     = opex_yr1 * (1 + INFLATION_RATE)**(yr-1)
        net_cf   = revenue - opex
        cumulative += net_cf
        if cumulative >= 0 and payback_yr is None:
            payback_yr = yr
        rows.append({
            'Year': yr, 'Energy_MWh': round(energy, 1),
            'Revenue_USD': round(revenue), 'OPEX_USD': round(opex),
            'Net_CF_USD': round(net_cf), 'Cumulative_CF_USD': round(cumulative)
        })
    return pd.DataFrame(rows), payback_yr


# =============================================================================
# 6. MAIN ANALYSIS LOOP
# =============================================================================

annual_ghi = compute_annual_ghi()
results = []

for name, params in SCENARIOS.items():
    cap   = params['capacity_mw']
    capex = params['capex_per_mw'] * cap
    opex1 = params['opex_per_mw_yr'] * cap

    # Energy yield year 1
    energy_yr1 = cap * annual_ghi * PERFORMANCE_RATIO   # MWh

    # Cash flows
    cf_df, payback = build_cashflow(cap, capex, opex1, energy_yr1)

    # Financial metrics
    lcoe = compute_lcoe(capex, opex1, energy_yr1)
    raw_cfs = [-capex] + list(cf_df['Net_CF_USD'])
    irr  = compute_irr(raw_cfs)
    npv  = sum(cf / (1 + DISCOUNT_RATE)**t for t, cf in enumerate(raw_cfs))

    total_energy_mwh = cf_df['Energy_MWh'].sum()
    co2_avoided      = total_energy_mwh * GRID_EMISSION_FACTOR   # tonnes

    results.append({
        'Scenario'              : name,
        'Capacity_MW'           : cap,
        'CAPEX_MUSD'            : round(capex / 1e6, 2),
        'OPEX_annual_kUSD'      : round(opex1 / 1e3, 1),
        'Annual_Energy_GWh_Yr1' : round(energy_yr1 / 1000, 2),
        'Capacity_Factor_pct'   : round(energy_yr1 / (cap * 8760) * 100, 1),
        'LCOE_USD_per_kWh'      : round(lcoe, 4),
        'NPV_MUSD'              : round(npv / 1e6, 2),
        'IRR_pct'               : round(irr * 100, 2),
        'Payback_Years'         : payback,
        'Total_Energy_25yr_GWh' : round(total_energy_mwh / 1000, 1),
        'CO2_Avoided_25yr_kt'   : round(co2_avoided / 1000, 1),
    })

    # Save individual cash flow
    cf_df.to_csv(f'cashflow_{cap}MW.csv', index=False)

summary_df = pd.DataFrame(results)
monthly_df = compute_monthly_energy(5)   # reference 5 MW for monthly chart

# Save outputs
summary_df.to_csv('scenario_results.csv', index=False)
monthly_df.to_csv('monthly_irradiance.csv', index=False)

# =============================================================================
# 7. PRINT SUMMARY TABLE
# =============================================================================
print("\n" + "="*80)
print(f"SOLAR PV TECHNO-ECONOMIC ASSESSMENT — {LOCATION}")
print("="*80)
display_cols = ['Scenario','Capacity_MW','CAPEX_MUSD','Annual_Energy_GWh_Yr1',
                'Capacity_Factor_pct','LCOE_USD_per_kWh','NPV_MUSD','IRR_pct','Payback_Years']
print(summary_df[display_cols].to_string(index=False))
print(f"\nKey Assumptions: PR={PERFORMANCE_RATIO}, Degradation={DEGRADATION_RATE*100}%/yr, "
      f"Discount={DISCOUNT_RATE*100}%, Tariff=${ELECTRICITY_TARIFF}/kWh, Life={PROJECT_LIFE_YRS}yrs")
print("="*80)


# =============================================================================
# 8. DATA VISUALIZATION
# =============================================================================
# Design goals for this revision:
#   - Light, neutral chart background throughout (no dark chrome to fight contrast on)
#   - Every title/axis label uses a single near-black ink color -> guaranteed readable
#   - A perceptually-uniform, colorblind-safe colormap (viridis) for the heatmap,
#     with a clearly labelled, fully-visible scale
#   - One chart per file, generously sized, with consistent typography

INK       = '#1C2530'   # near-black text — used for ALL titles, labels, ticks
SUBTLE    = '#5B6B79'   # secondary text (subtitles, captions)
BG        = '#FFFFFF'   # figure + axes background — plain white, max contrast
PANEL     = '#F4F6F8'   # very light panel tint for plot area
GRID      = '#D8DEE4'   # gridlines

GOLD, TEAL, SLATE, CORAL = '#E8A33D', '#1B9C85', '#3E6E9E', '#D9544D'
COLORS       = [GOLD, TEAL, SLATE, CORAL]
SHORT_LABELS = ['1 MW', '5 MW', '20 MW', '50 MW']

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'figure.facecolor': BG,
    'axes.facecolor': PANEL,
    'axes.edgecolor': GRID,
    'axes.labelcolor': INK,
    'axes.titlecolor': INK,
    'xtick.color': INK,
    'ytick.color': INK,
    'text.color': INK,
    'grid.color': GRID,
    'grid.alpha': 1.0,
    'axes.grid': True,
    'axes.labelsize': 12,
    'axes.labelweight': 'bold',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.labelcolor': INK,
    'legend.edgecolor': GRID,
})


def style_title(fig, title, subtitle=None):
    """Consistent, high-contrast title block for every chart."""
    fig.suptitle(title, fontsize=15, color=INK, fontweight='bold', y=0.985)
    if subtitle:
        fig.text(0.5, 0.925, subtitle, ha='center', fontsize=10.5, color=SUBTLE)


def plot_resource_analysis(monthly_df, save_path='fig1_irradiance.png'):
    """Fig 1 — Monthly GHI bar chart."""
    fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'Solar Resource Analysis — Egypt (Benban Region)',
                'Monthly average irradiance through the year')

    bars = ax.bar(monthly_df['Month'], monthly_df['GHI_kWh_m2_day'],
                   color=[GOLD if v >= 7 else TEAL for v in monthly_df['GHI_kWh_m2_day']],
                   edgecolor='white', linewidth=0.8, zorder=3)
    ax.set_xlabel('Month', labelpad=10)
    ax.set_ylabel('GHI  (kWh / m² / day)', labelpad=10)
    ax.set_ylim(0, 10.5)
    avg_ghi = monthly_df['GHI_kWh_m2_day'].mean()
    ax.axhline(avg_ghi, color=CORAL, linestyle='--', lw=2,
               label=f'Annual avg: {avg_ghi:.1f} kWh/m²/day', zorder=4)
    ax.legend(fontsize=10, facecolor='white', loc='upper right')
    for bar, val in zip(bars, monthly_df['GHI_kWh_m2_day']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                 f'{val:.1f}', ha='center', va='bottom', fontsize=9, color=INK, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_monthly_energy(monthly_df, save_path='fig1b_monthly_energy.png'):
    """Fig 1b — Monthly energy yield for a 5 MW reference plant."""
    fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'Monthly Energy Yield — 5 MW Reference Plant',
                'Output mirrors the seasonal solar resource shown in Fig. 1')

    energy_5mw = monthly_df['GHI_kWh_m2_day'] * monthly_df['Days'] * 5 * PERFORMANCE_RATIO
    ax.fill_between(range(12), energy_5mw, alpha=0.25, color=TEAL)
    ax.plot(range(12), energy_5mw, 'o-', color=TEAL, lw=3, ms=7, zorder=4,
            markeredgecolor='white', markeredgewidth=1.2)
    ax.set_xticks(range(12))
    ax.set_xticklabels(monthly_df['Month'])
    ax.set_xlabel('Month', labelpad=10)
    ax.set_ylabel('Energy Output  (MWh / month)', labelpad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    for i, val in enumerate(energy_5mw):
        ax.annotate(f'{val:,.0f}', (i, val), textcoords='offset points',
                     xytext=(0, 10), ha='center', fontsize=8.5, color=INK, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_lcoe(summary_df, save_path='fig2a_lcoe.png'):
    """LCOE (Levelised Cost of Energy) — standalone chart."""
    fig, ax = plt.subplots(figsize=(8.5, 6.5), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'LCOE — Levelised Cost of Energy',
                'Lower is better: cost to produce one kWh over the project life')

    lcoe_vals = summary_df['LCOE_USD_per_kWh'] * 100
    bars = ax.bar(SHORT_LABELS, lcoe_vals, color=COLORS, edgecolor='white', lw=1, width=0.55, zorder=3)
    ax.set_xlabel('Project Scenario', labelpad=10)
    ax.set_ylabel('LCOE  (¢ / kWh)', labelpad=10)
    ax.set_ylim(0, 8.5)
    ax.axhline(ELECTRICITY_TARIFF * 100, color=CORAL, linestyle='--', lw=2,
               label=f'Tariff ({ELECTRICITY_TARIFF*100:.1f} ¢/kWh)', zorder=4)
    ax.legend(fontsize=10, facecolor='white', loc='upper right')
    for bar, val in zip(bars, lcoe_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                f'{val:.2f}¢', ha='center', fontsize=11, fontweight='bold', color=INK)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_npv(summary_df, save_path='fig2b_npv.png'):
    """Net Present Value — standalone chart."""
    fig, ax = plt.subplots(figsize=(8.5, 6.5), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'NPV — Net Present Value',
                f'Discounted at {DISCOUNT_RATE*100:.0f}% WACC over {PROJECT_LIFE_YRS} years')

    npv_vals = summary_df['NPV_MUSD']
    bars = ax.bar(SHORT_LABELS, npv_vals, color=COLORS, edgecolor='white', lw=1, width=0.55, zorder=3)
    ax.set_xlabel('Project Scenario', labelpad=10)
    ax.set_ylabel('NPV  (USD Million)', labelpad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}M'))
    for bar, val in zip(bars, npv_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.6,
                f'${val:.1f}M', ha='center', fontsize=11, fontweight='bold', color=INK)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_irr(summary_df, save_path='fig2c_irr.png'):
    """Internal Rate of Return — standalone chart."""
    fig, ax = plt.subplots(figsize=(8.5, 6.5), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'IRR — Internal Rate of Return',
                'Higher is better: the project\'s effective annual return')

    irr_vals = summary_df['IRR_pct']
    bars = ax.bar(SHORT_LABELS, irr_vals, color=COLORS, edgecolor='white', lw=1, width=0.55, zorder=3)
    ax.set_xlabel('Project Scenario', labelpad=10)
    ax.set_ylabel('IRR  (%)', labelpad=10)
    ax.set_ylim(0, 26)
    ax.axhline(DISCOUNT_RATE * 100, color=CORAL, linestyle='--', lw=2,
               label=f'Discount Rate ({DISCOUNT_RATE*100:.0f}%)', zorder=4)
    ax.legend(fontsize=10, facecolor='white', loc='upper right')
    for bar, val in zip(bars, irr_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4,
                f'{val:.1f}%', ha='center', fontsize=11, fontweight='bold', color=INK)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_payback(summary_df, save_path='fig2d_payback.png'):
    """Simple Payback Period — standalone chart."""
    fig, ax = plt.subplots(figsize=(8.5, 6.5), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'Simple Payback Period',
                f'Years to recover CAPEX, out of a {PROJECT_LIFE_YRS}-year project life')

    payback_vals = summary_df['Payback_Years']
    bars = ax.bar(SHORT_LABELS, payback_vals, color=COLORS, edgecolor='white', lw=1, width=0.55, zorder=3)
    ax.set_xlabel('Project Scenario', labelpad=10)
    ax.set_ylabel('Payback  (Years)', labelpad=10)
    ax.set_ylim(0, 12)
    for bar, val in zip(bars, payback_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.25,
                f'{val} yrs', ha='center', fontsize=11, fontweight='bold', color=INK)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_cashflow(cashflow_tables, save_path='fig3_cashflow.png'):
    """Fig 3 — Cumulative cash flow over 25 years for every scenario."""
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'Cumulative Cash Flow Over 25 Years',
                'All four scenarios, from initial investment to year 25')

    for (label, cf_df), color in zip(cashflow_tables.items(), COLORS):
        norm = cf_df['Cumulative_CF_USD'] / 1e6
        ax.plot(cf_df['Year'], norm, lw=3, color=color, label=label, zorder=4)
        ax.fill_between(cf_df['Year'], norm, alpha=0.10, color=color)

    ax.axhline(0, color=INK, linestyle='--', lw=1.5, alpha=0.6, zorder=5, label='Break-even (0)')
    ax.set_xlabel('Project Year', labelpad=10)
    ax.set_ylabel('Cumulative Cash Flow  (USD Million)', labelpad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}M'))
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
    ax.legend(fontsize=10.5, facecolor='white', framealpha=1, title='Scenario',
              title_fontsize=10, loc='upper left')
    ax.set_xlim(1, PROJECT_LIFE_YRS)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_irr_sensitivity(summary_df, save_path='fig4a_sensitivity_heatmap.png'):
    """IRR sensitivity heatmap (tariff x capacity factor) — 20 MW scenario.

    Uses a perceptually-uniform, colorblind-safe colormap (viridis) so the
    gradient is unambiguous, with a clearly labelled, evenly-ticked scale.
    """
    fig, ax = plt.subplots(figsize=(9.5, 7.5), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'IRR Sensitivity — 20 MW Scenario',
                f'Dark = below {DISCOUNT_RATE*100:.0f}% discount rate   ·   Bright = strong return')

    row_20mw    = summary_df[summary_df['Capacity_MW'] == 20].iloc[0]
    capex_20    = row_20mw['CAPEX_MUSD'] * 1e6
    opex_20     = row_20mw['OPEX_annual_kUSD'] * 1e3
    base_cf     = row_20mw['Capacity_Factor_pct'] / 100
    energy_base = row_20mw['Annual_Energy_GWh_Yr1'] * 1000   # MWh

    tariffs     = np.linspace(0.04, 0.12, 9)
    cap_factors = np.linspace(0.17, 0.26, 9)
    irr_matrix  = np.zeros((9, 9))

    for i, cf_t in enumerate(cap_factors):
        for j, tariff in enumerate(tariffs):
            adj_energy = energy_base * (cf_t / base_cf)
            cash_flows = [-capex_20] + [
                adj_energy * (1 - DEGRADATION_RATE)**(yr-1) * 1000 * tariff
                - opex_20 * (1 + INFLATION_RATE)**(yr-1)
                for yr in range(1, PROJECT_LIFE_YRS + 1)
            ]
            irr_matrix[i, j] = compute_irr(cash_flows) * 100

    vmin, vmax = 0, 40
    im = ax.imshow(irr_matrix, cmap='viridis', aspect='auto', vmin=vmin, vmax=vmax)
    ax.set_xticks(range(9))
    ax.set_xticklabels([f'{t*100:.1f}¢' for t in tariffs], fontsize=10)
    ax.set_yticks(range(9))
    ax.set_yticklabels([f'{cf*100:.0f}%' for cf in cap_factors], fontsize=10)
    ax.set_xlabel('Electricity Tariff  (¢ / kWh)', labelpad=10)
    ax.set_ylabel('Capacity Factor  (%)', labelpad=10)
    for i in range(9):
        for j in range(9):
            v = irr_matrix[i, j]
            ax.text(j, i, f'{v:.0f}%', ha='center', va='center', fontsize=9.5,
                     color='white' if v < 20 else 'black', fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, ticks=np.arange(vmin, vmax + 1, 5))
    cbar.set_label('IRR (%)', fontsize=11, color=INK, fontweight='bold')
    cbar.ax.yaxis.set_tick_params(color=INK, labelsize=10)
    cbar.ax.set_yticklabels([f'{v}%' for v in np.arange(vmin, vmax + 1, 5)], color=INK)
    cbar.outline.set_edgecolor(GRID)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


def plot_co2_avoided(summary_df, save_path='fig4b_co2_avoided.png'):
    """CO2 emissions avoided over 25 years — standalone chart."""
    fig, ax = plt.subplots(figsize=(8.5, 6.5), facecolor=BG)
    ax.set_facecolor(PANEL)
    style_title(fig, 'CO₂ Emissions Avoided',
                f'Cumulative impact over a {PROJECT_LIFE_YRS}-year project life')

    co2_vals = summary_df['CO2_Avoided_25yr_kt']
    bars = ax.barh(SHORT_LABELS, co2_vals, color=COLORS, edgecolor='white', lw=1, height=0.5, zorder=3)
    ax.set_xlabel('CO₂ Avoided  (kt, thousand tonnes)', labelpad=10)
    ax.set_ylabel('Project Scenario', labelpad=10)
    for bar, val in zip(bars, co2_vals):
        ax.text(bar.get_width() + 8, bar.get_y() + bar.get_height()/2,
                f'{val:.0f} kt', va='center', fontsize=11, fontweight='bold', color=INK)
    ax.set_xlim(0, co2_vals.max() * 1.20)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)


# --- Generate and save all charts (one chart per file) ---
cashflow_tables = {
    label: pd.read_csv(f'cashflow_{cap}MW.csv')
    for label, cap in zip(SHORT_LABELS, [1, 5, 20, 50])
}

plot_resource_analysis(monthly_df,   save_path='fig1_irradiance.png')
plot_monthly_energy(monthly_df,      save_path='fig1b_monthly_energy.png')
plot_lcoe(summary_df,                save_path='fig2a_lcoe.png')
plot_npv(summary_df,                 save_path='fig2b_npv.png')
plot_irr(summary_df,                 save_path='fig2c_irr.png')
plot_payback(summary_df,             save_path='fig2d_payback.png')
plot_cashflow(cashflow_tables,       save_path='fig3_cashflow.png')
plot_irr_sensitivity(summary_df,     save_path='fig4a_sensitivity_heatmap.png')
plot_co2_avoided(summary_df,         save_path='fig4b_co2_avoided.png')

print("✅ Analysis complete. 9 charts (one chart per file) and CSV files saved.")
