from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

SignalCategory = Literal[
    'market',
    'macro',
    'portfolio',
    'options',
    'stablecoin',
    'flow',
    'supply_chain',
    'trade_policy',
    'risk',
]
SignalState = Literal['bullish', 'bearish', 'neutral', 'unknown']
RegimeState = Literal['RISK_ON', 'RISK_OFF', 'TRANSITIONAL']
FlowDirection = Literal['INFLOW', 'OUTFLOW', 'NEUTRAL']
Verdict = Literal['BUY', 'CASH']
DisruptionLevel = Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
AlertDirection = Literal['BULLISH', 'BEARISH', 'NEUTRAL']
AlertSeverity = Literal['INFO', 'WARNING', 'CRITICAL']


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_alert_id() -> str:
    return str(uuid4())


def parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)
    return float(value)


def parse_float(value: Any, default: float = 0.0) -> float:
    parsed = parse_optional_float(value)
    return parsed if parsed is not None else default


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        return int(float(stripped))
    return int(value)


@dataclass(slots=True)
class Quote:
    symbol: str
    name: str
    price: float
    change: float
    display: str | None = None
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FearGreedIndex:
    value: int
    classification: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RadarSignal:
    value: Any
    bullish: bool
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MarketRadarVerdict:
    verdict: Verdict
    bullish_count: int
    total_known: int
    signals: dict[str, RadarSignal]
    mayer_multiple: float | None
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'verdict': self.verdict,
            'bullish_count': self.bullish_count,
            'total_known': self.total_known,
            'signals': {key: signal.to_dict() for key, signal in self.signals.items()},
            'mayer_multiple': self.mayer_multiple,
            'timestamp': self.timestamp,
        }


@dataclass(slots=True)
class StablecoinStatus:
    symbol: str
    price: float
    peg: float
    peg_deviation_pct: float
    is_depegged: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ETFFlowSummary:
    ticker: str
    flow_direction: FlowDirection
    flow_magnitude: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BISPolicyRate:
    country: str
    rate: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BISExchangeRate:
    country: str
    real_eer: float
    nominal_eer: float
    change: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BISCreditData:
    country: str
    credit_gdp_ratio: float
    previous_ratio: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EnergyPrices:
    wti: float | None
    brent: float | None
    timestamp: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CrudeInventories:
    latest_period: str | None
    weeks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MacroSignals:
    timestamp: str
    verdict: str
    bullish_count: int
    total_count: int
    signals: dict[str, Any]
    meta: dict[str, Any]
    unavailable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ShippingRate:
    route: str
    rate: float
    timestamp: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChokepointStatus:
    name: str
    score: float
    disruption_level: DisruptionLevel
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CriticalMineral:
    mineral: str
    hhi: float
    risk_rating: str
    global_production: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ShippingStress:
    stress_score: float
    stress_level: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TradeRestriction:
    country: str
    restriction_type: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TariffTrend:
    country: str
    partner_country: str
    product_sector: str
    year: int
    tariff_rate: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TradeFlow:
    country: str
    partner_country: str
    year: int
    export_value_usd: float
    import_value_usd: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TradeBarrier:
    country: str
    barrier_type: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NormalizedSignal:
    signal_id: str
    category: SignalCategory
    source: str
    label: str
    state: SignalState
    score: float
    confidence: float
    observed_at: str
    value: Any = None
    symbol: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PositionSnapshot:
    symbol: str
    asset_type: str
    quantity: float
    market_value: float
    average_cost: float | None = None
    unrealized_pnl: float | None = None
    currency: str = 'USD'
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.average_cost in (None, 0):
            return 0.0
        return ((self.market_value / max(self.quantity, 1e-9)) - self.average_cost) / self.average_cost * 100.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['unrealized_pnl_pct'] = self.unrealized_pnl_pct
        return payload


Position = PositionSnapshot


@dataclass(slots=True)
class OptionContract:
    underlying_symbol: str
    option_symbol: str
    expiration: str | None
    option_type: str
    strike: float | None
    bid: float | None
    ask: float | None
    last: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    rho: float | None
    iv: float | None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_payload(cls, underlying_symbol: str, payload: dict[str, Any]) -> 'OptionContract':
        return cls(
            underlying_symbol=underlying_symbol,
            option_symbol=str(payload.get('symbol') or payload.get('osiSymbol') or payload.get('optionSymbol') or 'UNKNOWN'),
            expiration=payload.get('expiration') or payload.get('expirationDate'),
            option_type=str(payload.get('optionType') or payload.get('right') or 'UNKNOWN'),
            strike=parse_optional_float(payload.get('strike')),
            bid=parse_optional_float(payload.get('bid')),
            ask=parse_optional_float(payload.get('ask')),
            last=parse_optional_float(payload.get('last')),
            delta=parse_optional_float(payload.get('delta')),
            gamma=parse_optional_float(payload.get('gamma')),
            theta=parse_optional_float(payload.get('theta')),
            vega=parse_optional_float(payload.get('vega')),
            rho=parse_optional_float(payload.get('rho')),
            iv=parse_optional_float(payload.get('iv') or payload.get('impliedVolatility')),
            metadata=dict(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IVMetrics:
    iv_rank: float | None
    implied_volatility: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OptionsChain:
    symbol: str
    expiration: str | None
    contracts: list[OptionContract] = field(default_factory=list)
    iv_metrics: IVMetrics | None = None

    @property
    def iv_rank(self) -> float | None:
        return self.iv_metrics.iv_rank if self.iv_metrics else None

    def to_dict(self) -> dict[str, Any]:
        return {
            'symbol': self.symbol,
            'expiration': self.expiration,
            'contracts': [contract.to_dict() for contract in self.contracts],
            'iv_metrics': self.iv_metrics.to_dict() if self.iv_metrics else None,
            'iv_rank': self.iv_rank,
        }


@dataclass(slots=True)
class PortfolioSnapshot:
    account_id: str
    generated_at: str
    buying_power: float | None
    cash: float | None
    equity: float | None
    positions: list[PositionSnapshot] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'account_id': self.account_id,
            'generated_at': self.generated_at,
            'buying_power': self.buying_power,
            'cash': self.cash,
            'equity': self.equity,
            'positions': [position.to_dict() for position in self.positions],
            'raw': self.raw,
        }


@dataclass(slots=True)
class AccountSnapshot:
    account_id: str
    buying_power: float | None
    cash: float | None
    equity: float | None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OptionLeg:
    symbol: str
    side: str
    quantity: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OrderRequest:
    symbol: str
    side: str
    quantity: float
    order_type: str
    time_in_force: str | None = None
    limit_price: float | None = None
    legs: list[OptionLeg] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'order_type': self.order_type,
            'time_in_force': self.time_in_force,
            'limit_price': self.limit_price,
            'legs': [leg.to_dict() for leg in self.legs],
        }


@dataclass(slots=True)
class OrderResult:
    ok: bool
    order_id: str | None = None
    status: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Alert:
    alert_id: str
    alert_type: str
    ticker: str | None
    value: float
    threshold: float
    direction: AlertDirection
    severity: AlertSeverity
    message: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FinanceContext:
    account: AccountSnapshot | None
    positions: list[Position]
    quotes: dict[str, Quote]
    options_chains: dict[str, OptionsChain]
    macro: MacroSignals | None
    market_radar: MarketRadarVerdict | None
    fear_greed: FearGreedIndex | None
    stablecoins: list[StablecoinStatus] | None
    etf_flows: list[ETFFlowSummary] | None
    energy: EnergyPrices | None
    chokepoints: list[ChokepointStatus] | None
    trade_restrictions: list[TradeRestriction] | None
    bis_policy_rates: list[BISPolicyRate] | None
    signals: list[NormalizedSignal]
    regime: str
    regime_flags: list[str]
    timestamp: str
    alerts: list[Alert] = field(default_factory=list)
    previous_regime: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> 'FinanceContext':
        return cls(
            account=None,
            positions=[],
            quotes={},
            options_chains={},
            macro=None,
            market_radar=None,
            fear_greed=None,
            stablecoins=None,
            etf_flows=None,
            energy=None,
            chokepoints=None,
            trade_restrictions=None,
            bis_policy_rates=None,
            signals=[],
            regime='TRANSITIONAL',
            regime_flags=[],
            timestamp=utc_now_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            'account': self.account.to_dict() if self.account else None,
            'positions': [position.to_dict() for position in self.positions],
            'quotes': {key: value.to_dict() for key, value in self.quotes.items()},
            'options_chains': {key: value.to_dict() for key, value in self.options_chains.items()},
            'macro': self.macro.to_dict() if self.macro else None,
            'market_radar': self.market_radar.to_dict() if self.market_radar else None,
            'fear_greed': self.fear_greed.to_dict() if self.fear_greed else None,
            'stablecoins': [item.to_dict() for item in self.stablecoins] if self.stablecoins is not None else None,
            'etf_flows': [item.to_dict() for item in self.etf_flows] if self.etf_flows is not None else None,
            'energy': self.energy.to_dict() if self.energy else None,
            'chokepoints': [item.to_dict() for item in self.chokepoints] if self.chokepoints is not None else None,
            'trade_restrictions': [item.to_dict() for item in self.trade_restrictions] if self.trade_restrictions is not None else None,
            'bis_policy_rates': [item.to_dict() for item in self.bis_policy_rates] if self.bis_policy_rates is not None else None,
            'signals': [signal.to_dict() for signal in self.signals],
            'regime': self.regime,
            'regime_flags': self.regime_flags,
            'timestamp': self.timestamp,
            'alerts': [alert.to_dict() for alert in self.alerts],
            'previous_regime': self.previous_regime,
            'metadata': self.metadata,
        }
