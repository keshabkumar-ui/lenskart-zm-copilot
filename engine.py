import pandas as pd
import boto3
import json
import os
import time
import logging
import numpy as np
from dotenv import load_dotenv

from learning_engine import get_historical_patterns, save_feedback, init_db

load_dotenv()

# ── Structured logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("zm_copilot")

# Primary Inference Profile (Must be set in .env)
MODEL_ID_PRIMARY = os.getenv("BEDROCK_MODEL_ID_PRIMARY")
MODEL_ID_FALLBACK = os.getenv("BEDROCK_MODEL_ID_FALLBACK")
REGION = os.getenv("AWS_REGION", "ap-south-1")

# ─────────────────────────────────────────────
# ENVIRONMENT VALIDATION on startup
# ─────────────────────────────────────────────
def _validate_environment():
    """Validate required environment variables."""
    required = {
        "AWS_ACCESS_KEY_ID": "AWS access key",
        "AWS_SECRET_ACCESS_KEY": "AWS secret key",
    }
    missing = [k for k in required.keys() if not os.getenv(k)]
    if missing:
        log.warning(
            f"Missing AWS credentials: {missing}. "
            f"Configure in .env file. See .env.example for format."
        )
        return False
    return True

AWS_CONFIGURED = _validate_environment()

client = None
def get_bedrock_client():
    """Get or create AWS Bedrock client with validation."""
    global client
    if client:
        return client
    
    # Validate credentials exist
    ak = os.getenv("AWS_ACCESS_KEY_ID")
    sk = os.getenv("AWS_SECRET_ACCESS_KEY")
    if not ak or not sk:
        raise ValueError("❌ AWS credentials required. Check .env file.")
    
    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name=REGION,
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
        )
        log.info(f"Bedrock client initialized for region {REGION}")
        return client
    except Exception as e:
        log.error(f"Failed to initialize Bedrock client: {e}")
        return None

import json

# ─────────────────────────────────────────────
# CONFIG-DRIVEN THRESHOLDS (Loaded from config.json or environment)
# ─────────────────────────────────────────────
def load_config():
    default_config = {
        "THRESHOLDS": {
            "conversion": {"critical": 8.0, "warning": 12.0, "target": 15.0},
            "footfall":   {"critical": 150, "warning": 250},
            "aov":        {"critical": 1500, "warning": 2000, "discounting_risk": 1800},
            "nps":        {"critical": 30, "warning": 45, "high_traffic_cap": 40},
            "downtime":   {"critical": 8.0, "warning": 4.0, "impact_threshold": 5.0},
            "staff_eff":  {"warning": 5.0, "target": 8.0},
            "qms_conv":   {"warning": 45.0, "target": 55.0},
            "et_conv":    {"critical": 35.0, "target": 45.0, "bottleneck_trigger": 30.0},
            "apt_conv":   {"warning": 35.0, "target": 45.0},
            "bottleneck_footfall": 350,
            "high_traffic_nps":    300,
            "understaffed_foot":   500,
            "understaffed_staff":  5,
            "assortment_et_min":   45.0,
            "assortment_conv_max": 10.0,
            "discount_conv_min":   15.0,
            "system_conv_max":     12.0,
        },
        "COLUMN_ALIASES": {
            "date": ["date", "Date-Parameter", "date_parameter"],
            "store_id": ["store_id", "Store", "Store Code - Name", "store_code"],
            "city": ["city", "City"],
            "footfall": ["footfall", "Footfall", "avg_footfall_per_store", "Avg FF per Store"],
            "transactions": ["transactions", "net_orders", "Net Orders", "gross_orders", "Gross order"],
            "revenue": ["revenue", "net_sales", "Net Sales", "gross_revenue", "Gross Revenue"],
            "staff_count": ["staff_count", "staff_per_day", "# Staff /Day", "staff_per_store_per_day", "# Staff /Day/Store"],
            "nps": ["nps", "NPS"],
            "response_rate": ["response_rate", "Response Rate", "response rate"],
            "qms_entries": ["qms_entries", "QMS Entries (#)"],
            "qms_conversion_percent": ["qms_conversion_percent", "QMS Conv%"],
            "eye_test": ["eye_test", "Eye Test"],
            "et_conversion_percent": ["et_conversion_percent", "ET Conversion%"],
            "appointments": ["appointments", "Apt (#)", "Appointments"],
            "appointment_conversion_percent": ["appointment_conversion_percent", "Apt Conversion%"],
            "tango_downtime_percent": ["tango_downtime_percent", "Tango Downtime%"],
            "net_atv": ["net_atv", "Net ATV", "asp", "Net ASP"],
            "return_revenue": ["return_revenue", "Return Revenue"],
            "gross_revenue": ["gross_revenue", "Gross Revenue"],
            "total_responses": ["total_responses", "Total Responses"],
            "proto": ["proto", "sales prediction"],
        }
    }
    config_path = os.getenv("ZM_CONFIG_PATH", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                log.info(f"Loaded configuration from {config_path}")
                return user_config.get("THRESHOLDS", default_config["THRESHOLDS"]), user_config.get("COLUMN_ALIASES", default_config["COLUMN_ALIASES"])
        except Exception as e:
            log.error(f"Failed to load {config_path}: {e}. Falling back to default configuration.")
    
    return default_config["THRESHOLDS"], default_config["COLUMN_ALIASES"]

THRESHOLDS, COLUMN_ALIASES = load_config()



def _first_available(df, candidates):
    """Return first column name from candidates found in df."""
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _normalize_schema(df):
    """Map heterogeneous business column names into canonical fields."""
    normalized = pd.DataFrame(index=df.index)

    # Resolve and map known aliases
    resolved = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        source = _first_available(df, aliases)
        if source:
            normalized[canonical] = df[source]
            resolved[canonical] = source

    # Required fields with fallback defaults where possible
    required = {"date", "store_id", "footfall", "transactions", "revenue", "staff_count"}
    missing = [c for c in required if c not in normalized.columns]
    if missing:
        raise ValueError(
            f"CSV missing required logical fields: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    # City is optional in raw files; fill with Unknown if absent
    if "city" not in normalized.columns:
        normalized["city"] = "Unknown"

    # Keep raw columns for downstream advanced analysis where useful
    passthrough_candidates = [
        "gross_revenue", "net_sales", "return_revenue", "gross_orders", "net_orders",
        "spnd", "omni_revenue", "ratings_trend", "reviews_trend", "qms_to_footfall_ratio",
        "et_to_footfall_ratio", "staff_per_store_per_day", "optom_per_day",
        "bogo_orders", "bogo_net_revenue_percent", "blue_orders", "blue_net_revenue_percent",
        "sv_net_orders", "sv_net_revenue_percent", "vc_net_orders", "vc_net_revenue_percent",
        "eye_net_orders", "eye_net_revenue_percent", "sun_net_orders", "sun_net_revenue_percent",
        "kids_net_orders", "kids_net_revenue_percent", "jj_net_orders", "jj_net_revenue_percent",
        "cl_net_orders", "cl_net_revenue_percent", "total_customers", "new_customers_percent",
        "gold_overall_percent", "gold_new_members_percent", "insurance_orders",
        "insurance_attach_rate",
    ]
    for col in passthrough_candidates:
        if col in df.columns and col not in normalized.columns:
            normalized[col] = df[col]

    return normalized


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
def load_data(file_path="stores_data.parquet"):
    """Load Parquet/CSV with auto-conversion and optimized typing."""
    parquet_path = os.getenv("ZM_DATA_PATH", "stores_data.parquet")
    
    df = pd.DataFrame()
    try:
        # 1. Load raw data
        if os.path.exists(parquet_path):
            df = pd.read_parquet(parquet_path)
        else:
            # Fallback to file_path (could be CSV or advanced CSV)
            if not os.path.exists(file_path):
                # If default doesn't exist, try common alternatives
                alt_path = "stores_data_advanced.csv" if "parquet" in file_path else "stores_data.csv"
                if os.path.exists(alt_path):
                    file_path = alt_path
                else:
                    raise FileNotFoundError(f"Data file '{file_path}' and default parquet not found.")
                    
            if file_path.endswith(".parquet"):
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)
                
            if df.empty: 
                raise pd.errors.EmptyDataError("File is empty.")

        # 2. ALWAYS Normalize schema (robustness against heterogeneous parquet/CSV sources)
        df = _normalize_schema(df)
        
        # 3. Clean and coerce types
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        num_cols = [c for c in df.columns if c not in ("date", "store_id", "city")]
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # 4. Persistence for performance (refresh parquet if it was non-canonical)
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception as e: 
            log.warning(f"Could not persist to parquet: {e}")

    except FileNotFoundError as fnf:
        log.error(f"File loading error: {fnf}")
        raise
    except pd.errors.EmptyDataError as ede:
        log.error(f"Data loading error: {ede}")
        raise
    except Exception as e:
        log.error(f"Unexpected error loading data: {e}")
        raise

    return df


# ─────────────────────────────────────────────
# KPI ENGINE — safe division throughout
# ─────────────────────────────────────────────
def _safe_div(numerator, denominator):
    """Return element-wise division; 0 where denominator is zero."""
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(denominator != 0, numerator / denominator, 0.0)
    return result


def compute_kpis(df):
    df = df.copy()
    df["conversion_rate"]     = _safe_div(df["transactions"].values, df["footfall"].values) * 100
    df["aov"]                 = _safe_div(df["revenue"].values,      df["transactions"].values)
    if "net_atv" in df.columns:
        # Prefer business-defined ATV when provided by source systems
        df["aov"] = np.where(df["net_atv"].values > 0, df["net_atv"].values, df["aov"].values)
    df["revenue_per_visitor"] = _safe_div(df["revenue"].values,      df["footfall"].values)
    df["staff_efficiency"]    = _safe_div(df["transactions"].values, df["staff_count"].values)
    df["revenue_per_staff"]   = _safe_div(df["revenue"].values,      df["staff_count"].values)
    if "gross_revenue" in df.columns and "return_revenue" in df.columns:
        df["return_revenue_pct"] = _safe_div(df["return_revenue"].values, df["gross_revenue"].values) * 100
    return df


# ─────────────────────────────────────────────
# TREND ENGINE — requires ≥ 2 data points
# ─────────────────────────────────────────────
def compute_trends(df):
    # Ensure KPIs are calculated first
    df = compute_kpis(df)
    
    # Optimization: Pre-sort the whole dataframe once
    df = df.sort_values(["store_id", "date"])
    trends = {}

    # Use a faster groupby loop
    for store, group in df.groupby("store_id", sort=False):
        n = len(group)
        if n < 2:
            trends[store] = {"trend_label": "INSUFFICIENT_DATA"}
            continue

        split = max(1, n // 2)
        recent = group.tail(split)
        prior  = group.head(split)

        def pct_change(new_val, old_val):
            if old_val == 0:
                return 0.0
            return round(((new_val - old_val) / old_val) * 100, 1)

        r_conv = recent["conversion_rate"].mean()
        p_conv = prior["conversion_rate"].mean()
        r_foot = recent["footfall"].mean()
        p_foot = prior["footfall"].mean()
        r_rev  = recent["revenue"].mean()
        p_rev  = prior["revenue"].mean()
        r_aov  = recent["aov"].mean()
        p_aov  = prior["aov"].mean()
        r_eff  = recent["staff_efficiency"].mean()
        p_eff  = prior["staff_efficiency"].mean()

        # Revenue decomposition: ΔRevenue ~= footfall + conversion + AOV effects
        revenue_delta = r_rev - p_rev
        footfall_effect = (r_foot - p_foot) * (p_conv / 100) * p_aov
        conversion_effect = r_foot * ((r_conv - p_conv) / 100) * p_aov
        aov_effect = r_foot * (r_conv / 100) * (r_aov - p_aov)
        residual_effect = revenue_delta - (footfall_effect + conversion_effect + aov_effect)

        # Composite trend score: weighted signals
        rev_delta  = pct_change(r_rev, p_rev)
        conv_delta = r_conv - p_conv

        if conv_delta < -2 or rev_delta < -10:
            trend_label = "DECLINING"
        elif conv_delta > 2 or rev_delta > 10:
            trend_label = "IMPROVING"
        else:
            trend_label = "STABLE"

        trends[store] = {
            "trend_label":            trend_label,
            "conversion_change_pct":  pct_change(r_conv, p_conv),
            "footfall_change_pct":    pct_change(r_foot, p_foot),
            "revenue_change_pct":     rev_delta,
            "aov_change_pct":         pct_change(r_aov,  p_aov),
            "efficiency_change_pct":  pct_change(r_eff,  p_eff),
            "conversion_change_abs":  round(r_conv - p_conv, 2),
            "footfall_change_abs":    int(r_foot - p_foot),
            "revenue_change_abs":     int(r_rev  - p_rev),
            "recent_avg_conversion":  round(r_conv, 2),
            "prior_avg_conversion":   round(p_conv, 2),
            "recent_avg_revenue":     round(r_rev,  2),
            "prior_avg_revenue":      round(p_rev,  2),
            "recent_avg_footfall":    round(r_foot, 1),
            "prior_avg_footfall":     round(p_foot, 1),
            "revenue_bridge": {
                "delta_revenue": round(revenue_delta, 1),
                "footfall_effect": round(footfall_effect, 1),
                "conversion_effect": round(conversion_effect, 1),
                "aov_effect": round(aov_effect, 1),
                "residual_effect": round(residual_effect, 1),
            },
        }

    return trends


# ─────────────────────────────────────────────
# BENCHMARKS — city/fleet level comparisons
# ─────────────────────────────────────────────
def compute_benchmarks(df):
    """Compute fleet-wide percentile benchmarks per KPI."""
    df = compute_kpis(df)
    latest = df.sort_values("date").groupby("store_id").last().reset_index()
    benchmarks = {}
    for col in ["conversion_rate", "revenue", "footfall", "aov", "staff_efficiency"]:
        if col in latest.columns:
            benchmarks[col] = {
                "p25": float(latest[col].quantile(0.25)),
                "p50": float(latest[col].quantile(0.50)),
                "p75": float(latest[col].quantile(0.75)),
                "mean": float(latest[col].mean()),
            }
    return benchmarks


# ─────────────────────────────────────────────
# SIGNAL ENGINE
# ─────────────────────────────────────────────
def detect_signals(row, trends, benchmarks=None):
    vector = []
    T = THRESHOLDS
    conv = row.get("conversion_rate", 0)
    foot = row.get("footfall", 0)
    eff  = row.get("staff_efficiency", 0)
    aov  = row.get("aov", 0)
    downtime = row.get("tango_downtime_percent", 0)
    nps = row.get("nps", 0)

    def add_sig(sig_type, category, tag, val, msg):
        vector.append({"type": sig_type, "category": category, "tag": tag, "val": val, "msg": msg})

    if foot == 0:
        add_sig("CRITICAL", "Demand", "ZERO_FOOTFALL", 0, "Zero footfall — store may be closed.")
        return vector

    if foot > T["bottleneck_footfall"]: add_sig("WARNING", "Demand", "HIGH_FOOTFALL", foot, "High traffic surge detected.")
    if foot < T["footfall"]["critical"]: add_sig("CRITICAL", "Demand", "CRITICAL_LOW_FOOTFALL", foot, "Critical low footfall.")
    if conv < T["conversion"]["warning"]: add_sig("WARNING", "Performance", "CONVERSION_LOW", conv, "Conversion rate drop.")
    if eff < T["staff_eff"]["warning"]: add_sig("WARNING", "Operations", "STAFF_EFFICIENCY_LOW", eff, "Low staff efficiency.")
    
    qms_conv = row.get("qms_conversion_percent", 0)
    et_conv  = row.get("et_conversion_percent", 0)
    if qms_conv > T["qms_conv"]["warning"]: add_sig("WARNING", "Funnel", "QMS_ENGAGEMENT_HIGH", qms_conv, "High QMS engagement.")
    if qms_conv < 40: add_sig("WARNING", "Funnel", "QMS_ENGAGEMENT_LOW", qms_conv, "Low QMS engagement.")
    if et_conv < T["et_conv"]["bottleneck_trigger"]: add_sig("CRITICAL", "Funnel", "EYE_TEST_CONVERSION_LOW", et_conv, "Low Eye-Test conversion.")
    
    if nps > 0 and nps < T["nps"]["critical"]: add_sig("CRITICAL", "Experience", "NPS_CRITICAL", nps, "Critical NPS drop.")
    if downtime > T["downtime"]["impact_threshold"]: add_sig("CRITICAL", "Systems", "DOWNTIME_HIGH", downtime, "High system downtime.")
    if aov < T["aov"]["discounting_risk"]: add_sig("WARNING", "Value", "AOV_LOW", aov, "Low AOV detected.")
    if et_conv > T["assortment_et_min"] and conv < T["assortment_conv_max"]: add_sig("CRITICAL", "Merchandising", "EYE_TEST_PASSED_BUT_NO_SALE", conv, "High ET pass but low sales.")

    if benchmarks:
        p25_conv = benchmarks.get("conversion_rate", {}).get("p25", 0)
        if conv < p25_conv and conv > 0:
            add_sig("WARNING", "Fleet", "BOTTOM_QUARTILE_FLEET", conv, "Bottom quartile conversion.")

    return vector



# ─────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────
def analyze_stores(df):
    df        = compute_kpis(df)
    trends    = compute_trends(df)
    benchmarks = compute_benchmarks(df)
    latest    = df.sort_values("date").groupby("store_id").last().reset_index()
    
    # Optimization: Pre-group history to avoid O(N^2) filtering in loop
    history_groups = {sid: group for sid, group in df.groupby("store_id")}
    results   = []

    for _, row in latest.iterrows():
        store_id    = row["store_id"]
        signals     = detect_signals(row, trends, benchmarks)
        store_trend = trends.get(store_id, {"trend_label": "INSUFFICIENT_DATA"})

        # Health score (0–100), weighted by signal severity
        health_score = 100
        for s in signals:
            if s["type"] == "CRITICAL":
                health_score -= 20
            elif s["type"] == "WARNING":
                health_score -= 10
        health_score = max(0, health_score)

        if   health_score >= 75: health_label = "HEALTHY"
        elif health_score >= 50: health_label = "AT RISK"
        elif health_score >= 25: health_label = "CRITICAL"
        else:                    health_label = "EMERGENCY"

        # Optimization: Use pre-formatted dates if possible
        store_history = history_groups.get(store_id, pd.DataFrame())
        if store_history.empty:
            time_series_records = []
        else:
            # Vectorized extraction of relevant columns
            time_series_records = store_history[[
                "date", "revenue", "footfall", "conversion_rate",
                "transactions", "aov", "staff_efficiency"
            ]].to_dict(orient="records")

        # Compute fleet rank for this store
        fleet_conv_rank = int(
            (latest["conversion_rate"] < row["conversion_rate"]).sum()
        ) + 1

        # Explicit revenue decomposition for UI and AI
        bridge = store_trend.get("revenue_bridge", {})
        
        results.append({
            "store_id":     store_id,
            "city":         row["city"],
            "health_score": health_score,
            "health_label": health_label,
            "metrics": {
                "footfall":            int(row["footfall"]),
                "transactions":        int(row["transactions"]),
                "revenue":             float(round(row["revenue"], 2)),
                "conversion_rate":     round(row["conversion_rate"], 2),
                "aov":                 round(row.get("aov", 0), 2),
                "staff_count":         int(row["staff_count"]),
                "revenue_per_visitor": round(row.get("revenue_per_visitor", 0), 2),
                "staff_efficiency":    round(row.get("staff_efficiency", 0), 2),
                "nps":                 round(row.get("nps", 0), 2),
            },
            "decomposition": {
                "footfall_effect":   bridge.get("footfall_effect", 0),
                "conversion_effect": bridge.get("conversion_effect", 0),
                "aov_effect":        bridge.get("aov_effect", 0),
                "total_delta":       bridge.get("delta_revenue", 0)
            },
            "signals":         signals,
            "trends":          store_trend,
            "benchmarks":      benchmarks,
            "fleet_conv_rank": fleet_conv_rank,
            "fleet_size":      len(latest),
            "time_series":     time_series_records,
            "prediction": {
                "forecast_revenue": round(row["revenue"] * (1 + (store_trend.get("revenue_change_pct", 0) / 100)), 2),
                "potential_uplift": round(
                    max(0, benchmarks.get("conversion_rate", {}).get("p50", 0) - row.get("conversion_rate", 0))
                    * row.get("revenue_per_visitor", 0)
                    * row.get("footfall", 0)
                    / 100,
                    2
                ),
            }
        })

    results.sort(key=lambda x: x["health_score"])
    return results

# ─────────────────────────────────────────────
# AI ENGINE — Production-grade prompt
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Senior Zonal Manager AI Copilot at Lenskart. You are a First-Principles Operational Reasoning Engine.

Your task is to observe a "Store Environment" through its raw metric deltas and construct a causal narrative that explains the financial performance.

CORE REASONING RULES:
1. Construct Causal Chains: Do not describe metrics. Explain how they interact. 
   - (e.g., "The 20% surge in traffic (Footfall Delta) overwhelmed the 2 staff on floor (Staff Count), causing a 5pp drop in Conversion.")
2. Identify the Financial Anchor: Use the Revenue Bridge math to pinpoint exactly which driver (Footfall/Conversion/AOV) is the primary leak.
3. Be Decisive: Eliminate all hedge words (perhaps, might, seems). You are the expert.

STRICT CONSTRAINTS FOR UI COMPATIBILITY:
- EXPECTED IMPACT: MUST be under 10 words. Format as "[Metric Change] | [Financial Uplift]".
- PLAYBOOK TITLES: Action titles (Step 1, 2, 3) MUST be under 6 words.
- ROOT CAUSE: Be direct. Maximum 2 sentences.

REQUIRED OUTPUT FORMAT (Use these EXACT labels for parsing):
---
STORE HEALTH: [HEALTH_LABEL] ([SCORE]/100) — [1-sentence verdict]

TREND: [Overall Trend Label] — [Summary of movement in Revenue/Conversion]

ROOT CAUSE: [Direct 1-2 sentence explanation of causal link]

REVENUE BRIDGE:
• Footfall Effect: Rs[X]
• Conversion Effect: Rs[Y]
• AOV Effect: Rs[Z]
→ PRIMARY LEAK: [Driver Name]

CONVERSION DRIVERS:
• [Factor 1]: [Impact]
• [Factor 2]: [Impact]

PLAYBOOK:
1. [CONCISE ACTION TITLE] | Owner: [role] | By: Day [N] | Expected: [Outcome]
   -> [Exact directive]
2. [CONCISE ACTION TITLE] | Owner: [role] | By: Day [N] | Expected: [Outcome]
   -> [Exact directive]
3. [CONCISE ACTION TITLE] | Owner: [role] | By: Day [N] | Expected: [Outcome]
   -> [Exact directive]

EXPECTED IMPACT: [Punchy Label (e.g. +8% Conv | Rs 2L Monthly Uplift)]

CONFIDENCE: [Verdict (High/Medium/Low)] — [Reasoning]
---"""


# ─────────────────────────────────────────────
# AI ENGINE CACHE LAYER
# ─────────────────────────────────────────────
REPORT_CACHE = {}

def generate_report(data, max_retries: int = 3):
    """
    Call AWS Bedrock (Claude) to generate a production-grade diagnostic report.
    Returns the report string, or an 'AI Error: ...' string on failure.
    Uses exponential back-off on retries and integrates historical patterns.
    """
    store_id    = data.get("store_id", "UNKNOWN")
    health      = data.get("health_label", "UNKNOWN")
    score       = data.get("health_score", 0)
    signals     = data.get("signals", []) 
    trends_data = data.get("trends", {})
    bridge      = trends_data.get("revenue_bridge", {})

    # Check if AWS is configured
    if not AWS_CONFIGURED:
        log.warning("Bedrock not configured; returning fallback diagnostic")
        return "⚠️ AI service not configured. Showing metrics-only analysis. Configure AWS credentials in .env to enable AI diagnostics."

    # Identify Primary Issue Type for Pattern Learning
    primary_issue = "GENERAL_PERFORMANCE"
    if signals:
        primary_issue = signals[0].get("tag", "GENERAL_PERFORMANCE")

    # Fetch Historical Patterns
    patterns = get_historical_patterns(primary_issue)
    sim_cases = patterns["similar_cases"]
    success_rate = patterns["success_rate"]
    
    # Adaptive Confidence & Pattern Caching
    base_confidence = min(95, 50 + (success_rate * 50))
    
    # If we have very high confidence in a previous pattern, we could skip AI
    # (Disabled by default for demo, but architecturally present)
    # if sim_cases > 50 and success_rate > 0.9: return patterns["cached_report"]

    # AI CALL REDUCTION LOGIC & CACHE LAYER
    if sim_cases > 50 and success_rate > 0.9:
        if store_id in REPORT_CACHE:
            log.info("Cache hit! Skipping AI call for %s. Pattern exists and confidence high.", store_id)
            return REPORT_CACHE[store_id]

    log.info("Generating AI report for %s. Historical patterns: %d cases, %.2f success", 
             store_id, sim_cases, success_rate)

    # Pre-compute driver attribution % from revenue bridge
    total_delta = abs(bridge.get("delta_revenue", 0)) or 1
    def _pct(val):
        return round(abs(val / total_delta) * 100, 1)

    driver_context = (
        f"Pre-computed Revenue Bridge:\n"
        f"  Delta Revenue: Rs{bridge.get('delta_revenue', 0):,.0f}\n"
        f"  Footfall Effect: Rs{bridge.get('footfall_effect', 0):,.0f}"
        f" ({_pct(bridge.get('footfall_effect', 0))}% of delta)\n"
        f"  Conversion Effect: Rs{bridge.get('conversion_effect', 0):,.0f}"
        f" ({_pct(bridge.get('conversion_effect', 0))}% of delta)\n"
        f"  AOV Effect: Rs{bridge.get('aov_effect', 0):,.0f}"
        f" ({_pct(bridge.get('aov_effect', 0))}% of delta)\n"
    )

    signal_summary = "\n".join(
        f"  - [{s['type']}] {s['tag']}: {s['val']}" for s in signals
    ) or "  - No critical anomalies detected in signal vector."

    learning_context = (
        f"LEARNING ENGINE CONTEXT:\n"
        f"  - Similar Historical Cases: {sim_cases}\n"
        f"  - Historical Success Rate: {success_rate * 100:.1f}%\n"
        f"  - Base Adaptive Confidence: {base_confidence}%\n"
    )

    # Strip time_series to reduce tokens
    data_for_ai = {k: v for k, v in data.items() if k != "time_series"}

    prompt = (
        f"Generate the complete diagnostic report for this Lenskart store.\n\n"
        f"STORE: {store_id} | CITY: {data.get('city')} | "
        f"HEALTH: {health} ({score}/100)\n\n"
        f"{learning_context}\n"
        f"{driver_context}\n"
        f"PRE-IDENTIFIED SIGNALS:\n{signal_summary}\n\n"
        f"FULL STORE DATA:\n{json.dumps(data_for_ai, indent=2)}"
    )

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1400,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    })

    last_error = None
    for attempt in range(1, max_retries + 1):
        current_model = MODEL_ID_PRIMARY if attempt == 1 else MODEL_ID_FALLBACK
        
        if not current_model:
            log.warning("AI Model ID not configured in .env.")
            return "AI Error: BEDROCK_MODEL_ID_PRIMARY or BEDROCK_MODEL_ID_FALLBACK not set in .env."

        try:
            c = get_bedrock_client()
            if not c:
                return "AI Error: AWS Credentials not configured in .env."
        except ValueError as e:
            log.warning(str(e))
            return f"AI Error: {str(e)}"

        try:
            log.info("AI call attempt %d/%d for %s", attempt, max_retries, store_id)
            response = c.invoke_model(
                modelId=current_model,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            text = json.loads(response["body"].read())["content"][0]["text"]
            log.info("AI report ready for %s (%d chars)", store_id, len(text))
            REPORT_CACHE[store_id] = text
            return text
        except Exception as e:
            last_error = e
            log.warning("AI attempt %d failed for %s: %s", attempt, store_id, str(e))
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    log.error("All %d AI attempts exhausted for %s", max_retries, store_id)
    return f"AI Diagnostic Error after {max_retries} attempts: {str(last_error)}"

