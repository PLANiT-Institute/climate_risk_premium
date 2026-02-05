"""
Asset-Level Financial Exposure Module.

Following Bressan et al. (2024) methodology from Nature Communications:
"Asset-level assessment of climate physical risk matters for adaptation finance"

Key insight: Without asset-level data, investor losses are underestimated by up to 70%.

This module provides:
1. Detailed asset-level financial exposure profiles
2. Ownership chain tracking
3. Insurance coverage modeling
4. Debt profile for credit risk analysis

Sources:
- Bressan et al. (2024) Nature Communications
- KEPCO Annual Reports
- Korean DART financial disclosures
- Korea Electric Power Statistics
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import date


class AssetType(Enum):
    """Power plant asset types."""
    COAL_SUBCRITICAL = "coal_subcritical"
    COAL_SUPERCRITICAL = "coal_supercritical"
    COAL_USC = "coal_usc"
    GAS_CCGT = "gas_ccgt"
    GAS_OCGT = "gas_ocgt"
    NUCLEAR = "nuclear"
    HYDRO = "hydro"
    SOLAR = "solar"
    WIND_ONSHORE = "wind_onshore"
    WIND_OFFSHORE = "wind_offshore"


class CreditRating(Enum):
    """Credit rating categories."""
    AAA = "AAA"
    AA_PLUS = "AA+"
    AA = "AA"
    AA_MINUS = "AA-"
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    BBB_PLUS = "BBB+"
    BBB = "BBB"
    BBB_MINUS = "BBB-"
    BB_PLUS = "BB+"
    BB = "BB"
    UNRATED = "NR"


@dataclass
class OwnershipChain:
    """
    Ownership chain for asset-level tracking.

    Following Bressan et al. (2024) methodology for
    tracing physical risk to ultimate beneficial owners.
    """
    direct_owner: str                    # Operating company
    parent_company: str                  # Parent holding
    ultimate_owner: str                  # Ultimate beneficial owner
    ownership_percentage: float          # % owned by parent
    listed_exchange: Optional[str]       # Stock exchange if public
    ticker: Optional[str]                # Stock ticker if public
    government_owned_pct: float = 0.0    # Government ownership %

    def is_public(self) -> bool:
        """Check if ultimate owner is publicly traded."""
        return self.listed_exchange is not None


@dataclass
class InsuranceCoverage:
    """
    Insurance coverage details.

    Critical for understanding residual risk after insurance.
    """
    property_coverage_usd: float         # Property damage coverage
    business_interruption_days: int      # BI coverage period
    bi_daily_value_usd: float            # Daily BI coverage value
    deductible_usd: float                # Deductible amount
    annual_premium_usd: float            # Annual premium
    coverage_ratio: float                # Coverage / Replacement cost
    insurer: str                         # Primary insurer
    reinsurance_pct: float = 0.0         # % reinsured

    @property
    def max_bi_coverage_usd(self) -> float:
        """Maximum business interruption coverage."""
        return self.business_interruption_days * self.bi_daily_value_usd

    @property
    def total_coverage_usd(self) -> float:
        """Total coverage amount."""
        return self.property_coverage_usd + self.max_bi_coverage_usd


@dataclass
class DebtProfile:
    """
    Debt profile for credit risk analysis.

    Used to calculate DSCR impact from physical risk.
    """
    total_debt_usd: float                # Total outstanding debt
    senior_debt_usd: float               # Senior secured debt
    subordinated_debt_usd: float         # Subordinated debt
    weighted_avg_maturity_years: float   # WAM of debt
    weighted_avg_interest_rate: float    # WAIR
    annual_debt_service_usd: float       # Annual P&I payments
    credit_rating: CreditRating          # Current rating
    rating_agency: str                   # Rating agency
    last_rating_date: str                # Date of last rating

    # Covenants
    min_dscr_covenant: float = 1.20      # Minimum DSCR covenant
    max_leverage_covenant: float = 0.70  # Maximum leverage covenant

    @property
    def leverage_ratio(self) -> float:
        """Calculate leverage ratio (placeholder - needs equity)."""
        return 0.0  # Needs total capitalization


@dataclass
class AssetLevelExposure:
    """
    Complete asset-level financial exposure profile.

    Following Bressan et al. (2024) 5-step methodology:
    1. Asset database with detailed attributes
    2. Physical risk assessment
    3. Macroeconomic linkage
    4. Corporate performance connection
    5. Security value adjustment

    This dataclass captures Step 1 comprehensively.
    """
    # Required fields (no defaults) - must come first
    asset_id: str
    asset_name: str
    asset_type: AssetType
    latitude: float
    longitude: float
    capacity_mw: float

    # Optional fields with defaults
    country: str = "KOR"
    region: str = ""
    address: str = ""
    capacity_factor: float = 0.85
    annual_generation_gwh: float = 0.0
    efficiency: float = 0.40             # Thermal efficiency
    commissioning_year: int = 2000
    expected_retirement_year: int = 2050
    remaining_life_years: int = 25

    # Financial values
    replacement_cost_usd: float = 0.0    # Full replacement cost
    book_value_usd: float = 0.0          # Accounting book value
    fair_value_usd: float = 0.0          # Mark-to-market value
    annual_revenue_usd: float = 0.0      # Annual revenue
    annual_ebitda_usd: float = 0.0       # EBITDA
    annual_opex_usd: float = 0.0         # Operating expenses

    # Revenue breakdown
    capacity_payment_usd: float = 0.0    # Capacity market revenue
    energy_payment_usd: float = 0.0      # Energy sales revenue
    ancillary_payment_usd: float = 0.0   # Ancillary services

    # Ownership and financing
    ownership: Optional[OwnershipChain] = None
    insurance: Optional[InsuranceCoverage] = None
    debt: Optional[DebtProfile] = None

    # Data quality
    data_source: str = ""
    last_updated: str = ""
    data_quality_score: float = 1.0      # 0-1 quality score

    def __post_init__(self):
        """Calculate derived values."""
        if self.annual_generation_gwh == 0 and self.capacity_mw > 0:
            self.annual_generation_gwh = (
                self.capacity_mw * 8760 * self.capacity_factor / 1000
            )
        if self.remaining_life_years == 25:
            self.remaining_life_years = max(0,
                self.expected_retirement_year - date.today().year
            )

    @property
    def value_per_mw(self) -> float:
        """Calculate value per MW of capacity."""
        if self.capacity_mw > 0:
            return self.replacement_cost_usd / self.capacity_mw
        return 0.0

    @property
    def revenue_per_mwh(self) -> float:
        """Calculate revenue per MWh."""
        if self.annual_generation_gwh > 0:
            return self.annual_revenue_usd / (self.annual_generation_gwh * 1000)
        return 0.0

    @property
    def ebitda_margin(self) -> float:
        """Calculate EBITDA margin."""
        if self.annual_revenue_usd > 0:
            return self.annual_ebitda_usd / self.annual_revenue_usd
        return 0.0

    def calculate_dscr(self) -> float:
        """Calculate Debt Service Coverage Ratio."""
        if self.debt and self.debt.annual_debt_service_usd > 0:
            return self.annual_ebitda_usd / self.debt.annual_debt_service_usd
        return 0.0

    def calculate_uninsured_exposure(self) -> float:
        """Calculate exposure not covered by insurance."""
        if self.insurance:
            return max(0, self.replacement_cost_usd - self.insurance.total_coverage_usd)
        return self.replacement_cost_usd

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type.value,
            "capacity_mw": self.capacity_mw,
            "replacement_cost_usd": self.replacement_cost_usd,
            "annual_revenue_usd": self.annual_revenue_usd,
            "annual_ebitda_usd": self.annual_ebitda_usd,
            "dscr": self.calculate_dscr(),
            "uninsured_exposure_usd": self.calculate_uninsured_exposure(),
        }


# =============================================================================
# KOREAN COAL FLEET DATA
# =============================================================================

# Based on KEPCO Annual Report 2023 and Korea Electric Power Statistics

KOREAN_COAL_FLEET: Dict[str, AssetLevelExposure] = {
    "samcheok": AssetLevelExposure(
        asset_id="KR-KOSPO-CBP",
        asset_name="Samcheok Blue Power",
        asset_type=AssetType.COAL_USC,
        latitude=37.4404,
        longitude=129.1671,
        region="Gangwon",
        capacity_mw=2100.0,
        capacity_factor=0.85,
        efficiency=0.44,
        commissioning_year=2017,
        expected_retirement_year=2057,
        replacement_cost_usd=4_500_000_000,
        book_value_usd=3_800_000_000,
        annual_revenue_usd=850_000_000,
        annual_ebitda_usd=180_000_000,
        annual_opex_usd=670_000_000,
        ownership=OwnershipChain(
            direct_owner="Samcheok Blue Power Co.",
            parent_company="Korea Southern Power Co. (KOSPO)",
            ultimate_owner="Korea Electric Power Corporation (KEPCO)",
            ownership_percentage=100.0,
            listed_exchange="KRX",
            ticker="015760.KS",
            government_owned_pct=51.1,
        ),
        insurance=InsuranceCoverage(
            property_coverage_usd=3_000_000_000,
            business_interruption_days=365,
            bi_daily_value_usd=2_300_000,
            deductible_usd=50_000_000,
            annual_premium_usd=15_000_000,
            coverage_ratio=0.67,
            insurer="Korean Re + Munich Re",
            reinsurance_pct=60.0,
        ),
        debt=DebtProfile(
            total_debt_usd=2_500_000_000,
            senior_debt_usd=2_000_000_000,
            subordinated_debt_usd=500_000_000,
            weighted_avg_maturity_years=12.0,
            weighted_avg_interest_rate=0.045,
            annual_debt_service_usd=280_000_000,
            credit_rating=CreditRating.AA,
            rating_agency="Korea Investors Service",
            last_rating_date="2024-06-30",
        ),
        data_source="KEPCO Annual Report 2023, DART filings",
        last_updated="2024-01-01",
    ),

    "dangjin": AssetLevelExposure(
        asset_id="KR-EWP-DJN",
        asset_name="Dangjin Thermal Power",
        asset_type=AssetType.COAL_SUPERCRITICAL,
        latitude=36.9310,
        longitude=126.6325,
        region="Chungnam",
        capacity_mw=6040.0,
        capacity_factor=0.82,
        efficiency=0.42,
        commissioning_year=1999,
        expected_retirement_year=2039,
        replacement_cost_usd=8_000_000_000,
        book_value_usd=3_200_000_000,
        annual_revenue_usd=2_100_000_000,
        annual_ebitda_usd=420_000_000,
        annual_opex_usd=1_680_000_000,
        ownership=OwnershipChain(
            direct_owner="Korea East-West Power Co. (EWP)",
            parent_company="Korea Electric Power Corporation (KEPCO)",
            ultimate_owner="Korea Electric Power Corporation (KEPCO)",
            ownership_percentage=100.0,
            listed_exchange="KRX",
            ticker="015760.KS",
            government_owned_pct=51.1,
        ),
        debt=DebtProfile(
            total_debt_usd=3_500_000_000,
            senior_debt_usd=3_000_000_000,
            subordinated_debt_usd=500_000_000,
            weighted_avg_maturity_years=8.0,
            weighted_avg_interest_rate=0.042,
            annual_debt_service_usd=520_000_000,
            credit_rating=CreditRating.AA,
            rating_agency="Korea Investors Service",
            last_rating_date="2024-06-30",
        ),
        data_source="KEPCO Annual Report 2023",
        last_updated="2024-01-01",
    ),

    "taean": AssetLevelExposure(
        asset_id="KR-WP-TAN",
        asset_name="Taean Thermal Power",
        asset_type=AssetType.COAL_SUPERCRITICAL,
        latitude=36.7536,
        longitude=126.2642,
        region="Chungnam",
        capacity_mw=6100.0,
        capacity_factor=0.80,
        efficiency=0.41,
        commissioning_year=1995,
        expected_retirement_year=2035,
        replacement_cost_usd=7_500_000_000,
        book_value_usd=2_500_000_000,
        annual_revenue_usd=2_000_000_000,
        annual_ebitda_usd=380_000_000,
        annual_opex_usd=1_620_000_000,
        ownership=OwnershipChain(
            direct_owner="Korea Western Power Co. (WP)",
            parent_company="Korea Electric Power Corporation (KEPCO)",
            ultimate_owner="Korea Electric Power Corporation (KEPCO)",
            ownership_percentage=100.0,
            listed_exchange="KRX",
            ticker="015760.KS",
            government_owned_pct=51.1,
        ),
        data_source="KEPCO Annual Report 2023",
        last_updated="2024-01-01",
    ),

    "hadong": AssetLevelExposure(
        asset_id="KR-KOSPO-HDG",
        asset_name="Hadong Thermal Power",
        asset_type=AssetType.COAL_SUPERCRITICAL,
        latitude=34.9344,
        longitude=127.8819,
        region="Gyeongnam",
        capacity_mw=4000.0,
        capacity_factor=0.78,
        efficiency=0.40,
        commissioning_year=1997,
        expected_retirement_year=2037,
        replacement_cost_usd=5_500_000_000,
        book_value_usd=2_000_000_000,
        annual_revenue_usd=1_300_000_000,
        annual_ebitda_usd=260_000_000,
        annual_opex_usd=1_040_000_000,
        ownership=OwnershipChain(
            direct_owner="Korea Southern Power Co. (KOSPO)",
            parent_company="Korea Electric Power Corporation (KEPCO)",
            ultimate_owner="Korea Electric Power Corporation (KEPCO)",
            ownership_percentage=100.0,
            listed_exchange="KRX",
            ticker="015760.KS",
            government_owned_pct=51.1,
        ),
        data_source="KEPCO Annual Report 2023",
        last_updated="2024-01-01",
    ),

    "boryeong": AssetLevelExposure(
        asset_id="KR-KOMIPO-BRY",
        asset_name="Boryeong Thermal Power",
        asset_type=AssetType.COAL_SUBCRITICAL,
        latitude=36.3588,
        longitude=126.4921,
        region="Chungnam",
        capacity_mw=4000.0,
        capacity_factor=0.72,
        efficiency=0.38,
        commissioning_year=1983,
        expected_retirement_year=2033,
        replacement_cost_usd=5_000_000_000,
        book_value_usd=800_000_000,
        annual_revenue_usd=1_100_000_000,
        annual_ebitda_usd=180_000_000,
        annual_opex_usd=920_000_000,
        ownership=OwnershipChain(
            direct_owner="Korea Midland Power Co. (KOMIPO)",
            parent_company="Korea Electric Power Corporation (KEPCO)",
            ultimate_owner="Korea Electric Power Corporation (KEPCO)",
            ownership_percentage=100.0,
            listed_exchange="KRX",
            ticker="015760.KS",
            government_owned_pct=51.1,
        ),
        data_source="KEPCO Annual Report 2023",
        last_updated="2024-01-01",
    ),

    "yeongheung": AssetLevelExposure(
        asset_id="KR-KOSEP-YGH",
        asset_name="Yeongheung Thermal Power",
        asset_type=AssetType.COAL_SUPERCRITICAL,
        latitude=37.2417,
        longitude=126.4456,
        region="Incheon",
        capacity_mw=5080.0,
        capacity_factor=0.83,
        efficiency=0.42,
        commissioning_year=2004,
        expected_retirement_year=2044,
        replacement_cost_usd=7_000_000_000,
        book_value_usd=4_200_000_000,
        annual_revenue_usd=1_800_000_000,
        annual_ebitda_usd=400_000_000,
        annual_opex_usd=1_400_000_000,
        ownership=OwnershipChain(
            direct_owner="Korea South-East Power Co. (KOSEP)",
            parent_company="Korea Electric Power Corporation (KEPCO)",
            ultimate_owner="Korea Electric Power Corporation (KEPCO)",
            ownership_percentage=100.0,
            listed_exchange="KRX",
            ticker="015760.KS",
            government_owned_pct=51.1,
        ),
        data_source="KEPCO Annual Report 2023",
        last_updated="2024-01-01",
    ),

    "sinseocheon": AssetLevelExposure(
        asset_id="KR-KOMIPO-SSC",
        asset_name="Sinseocheon Thermal Power",
        asset_type=AssetType.COAL_SUPERCRITICAL,
        latitude=36.4583,
        longitude=126.5167,
        region="Chungnam",
        capacity_mw=2000.0,
        capacity_factor=0.85,
        efficiency=0.43,
        commissioning_year=2016,
        expected_retirement_year=2056,
        replacement_cost_usd=3_500_000_000,
        book_value_usd=3_000_000_000,
        annual_revenue_usd=700_000_000,
        annual_ebitda_usd=150_000_000,
        annual_opex_usd=550_000_000,
        ownership=OwnershipChain(
            direct_owner="Korea Midland Power Co. (KOMIPO)",
            parent_company="Korea Electric Power Corporation (KEPCO)",
            ultimate_owner="Korea Electric Power Corporation (KEPCO)",
            ownership_percentage=100.0,
            listed_exchange="KRX",
            ticker="015760.KS",
            government_owned_pct=51.1,
        ),
        data_source="KEPCO Annual Report 2023",
        last_updated="2024-01-01",
    ),
}


def get_korean_coal_exposure() -> Dict[str, Any]:
    """
    Get summary of Korean coal fleet exposure.

    Returns portfolio-level aggregates.
    """
    total_capacity = sum(p.capacity_mw for p in KOREAN_COAL_FLEET.values())
    total_replacement = sum(p.replacement_cost_usd for p in KOREAN_COAL_FLEET.values())
    total_revenue = sum(p.annual_revenue_usd for p in KOREAN_COAL_FLEET.values())
    total_ebitda = sum(p.annual_ebitda_usd for p in KOREAN_COAL_FLEET.values())

    return {
        "num_plants": len(KOREAN_COAL_FLEET),
        "total_capacity_mw": total_capacity,
        "total_replacement_cost_usd": total_replacement,
        "total_annual_revenue_usd": total_revenue,
        "total_annual_ebitda_usd": total_ebitda,
        "avg_capacity_factor": sum(p.capacity_factor for p in KOREAN_COAL_FLEET.values()) / len(KOREAN_COAL_FLEET),
        "avg_plant_age_years": sum(
            2024 - p.commissioning_year for p in KOREAN_COAL_FLEET.values()
        ) / len(KOREAN_COAL_FLEET),
        "avg_remaining_life_years": sum(
            p.expected_retirement_year - 2024 for p in KOREAN_COAL_FLEET.values()
        ) / len(KOREAN_COAL_FLEET),
        "government_ownership_pct": 51.1,
        "ultimate_owner": "KEPCO",
    }


def get_portfolio_by_region() -> Dict[str, List[AssetLevelExposure]]:
    """Group assets by region."""
    result: Dict[str, List[AssetLevelExposure]] = {}
    for asset in KOREAN_COAL_FLEET.values():
        if asset.region not in result:
            result[asset.region] = []
        result[asset.region].append(asset)
    return result


def get_portfolio_by_genco() -> Dict[str, List[AssetLevelExposure]]:
    """Group assets by generation company."""
    result: Dict[str, List[AssetLevelExposure]] = {}
    for asset in KOREAN_COAL_FLEET.values():
        if asset.ownership:
            owner = asset.ownership.direct_owner
            if owner not in result:
                result[owner] = []
            result[owner].append(asset)
    return result
