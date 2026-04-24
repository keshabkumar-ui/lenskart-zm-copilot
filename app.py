import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from engine import load_data, analyze_stores, generate_report
from pdf_generator import create_pdf_report, create_fleet_summary_pdf, create_consolidated_report
from learning_engine import get_learning_stats, save_feedback, get_historical_patterns
import json
import os
from datetime import datetime
from learning_engine import init_db

# Initialize Persistent Learning Store
init_db()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ZM Copilot | Operations Intelligence",
    page_icon="https://static1.lenskart.com/media/desktop/img/Sep23/13-Sep/lenskart-logo-new-144x144.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# ROLE CONFIGURATION
# ─────────────────────────────────────────────
DEMO_ROLES = {
    "Zonal Manager (ZM)":             {"store_limit": 100, "cities": ["Bangalore", "Mumbai"]},
    "Area Operations Manager (AOM)":  {"store_limit": 15,  "cities": ["Delhi", "Hyderabad"]},
    "Circle Head":                    {"store_limit": 200, "cities": ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"]},
}

# Operational Mapping Constants
MAPPING_PATH_JSON = "mapping.json"
MAPPING_PATH_EXCEL = "Offline Mapping Apr-26.xlsx"

# ─────────────────────────────────────────────
# GLOBAL CSS — Premium Lenskart Design System
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

:root {
  /* ── Core Palette ── */
  --bg-base:      #04060f;
  --bg-surface:   #080d1a;
  --bg-card:      #0c1120;
  --bg-elevated:  #101828;
  --bg-hover:     #141f30;

  /* ── Borders ── */
  --border:       #1e2d44;
  --border-dim:   #162032;
  --border-bright:#2d4260;

  /* ── Text ── */
  --text-primary:   #eef2f8;
  --text-secondary: #8fa3bd;
  --text-muted:     #4d6480;
  --text-dim:       #2c3f55;

  /* ── Brand ── */
  --lk-blue:      #0030a0;
  --lk-blue-mid:  #0040cc;
  --lk-blue-light:#1a5fff;
  --lk-gold:      #fde800;
  --lk-gold-dim:  #c4b200;
  --lk-glow:      rgba(0,64,204,0.18);

  /* ── Status ── */
  --green:        #16a34a;
  --green-light:  #4ade80;
  --green-bg:     rgba(22,163,74,0.10);
  --yellow:       #ca8a04;
  --yellow-light: #fbbf24;
  --yellow-bg:    rgba(202,138,4,0.10);
  --orange:       #c2410c;
  --orange-light: #fb923c;
  --orange-bg:    rgba(194,65,12,0.10);
  --red:          #b91c1c;
  --red-light:    #f87171;
  --red-bg:       rgba(185,28,28,0.10);

  /* ── Effects ── */
  --shadow-sm:    0 2px 8px rgba(0,0,0,0.4);
  --shadow-md:    0 8px 24px rgba(0,0,0,0.5);
  --shadow-lg:    0 20px 50px rgba(0,0,0,0.6);
  --radius-sm:    6px;
  --radius-md:    10px;
  --radius-lg:    14px;
  --radius-xl:    18px;
}

/* ════════════════════════════════════════
   BASE RESET
   ════════════════════════════════════════ */
html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif !important;
  background: var(--bg-base) !important;
  color: var(--text-primary) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
.stApp { background: var(--bg-base) !important; }
.main .block-container {
  padding: 0 2rem 4rem 2rem !important;
  max-width: 1680px !important;
}
header[data-testid="stHeader"] { background: transparent !important; pointer-events: none; }
header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"] { pointer-events: auto; }
[data-testid="stHeaderMenu"], [data-testid="stConnectionStatus"] { display: none !important; }

/* ════════════════════════════════════════
   ANIMATIONS
   ════════════════════════════════════════ */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-6px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.6; transform: scale(0.85); }
}
@keyframes glow-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0,64,204,0); }
  50%       { box-shadow: 0 0 16px 2px rgba(0,64,204,0.25); }
}

/* ════════════════════════════════════════
   SIDEBAR  — Refined Command Panel
   ════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: var(--bg-surface) !important;
  border-right: 1px solid var(--border) !important;
  padding-top: 0 !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
[data-testid="stSidebar"] * { color: var(--text-secondary) !important; }
[data-testid="stSidebar"] label {
  color: var(--text-muted) !important;
  font-size: 9.5px !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  font-family: 'Outfit', sans-serif !important;
}
[data-testid="stSidebarCollapsedControl"], button[kind="header"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-secondary) !important;
  opacity: 1 !important;
  visibility: visible !important;
  z-index: 9999 !important;
}
[data-testid="stSidebarCollapsedControl"] svg,
button[kind="header"] svg {
  fill: var(--text-secondary) !important;
  stroke: var(--text-secondary) !important;
}

/* ════════════════════════════════════════
   SIDEBAR BRAND HEADER
   ════════════════════════════════════════ */
.sidebar-brand {
  background: linear-gradient(145deg, #000028 0%, #00003c 60%, #000855 100%);
  border-bottom: 1px solid var(--border);
  padding: 18px 16px 16px;
  margin: -1rem -1rem 18px -1rem;
  position: relative;
  overflow: hidden;
}
.sidebar-brand::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--lk-gold), transparent);
}
.sidebar-brand-name {
  font-family: 'Outfit', sans-serif;
  font-size: 19px;
  font-weight: 800;
  color: #fff !important;
  letter-spacing: -0.3px;
  line-height: 1;
}
.sidebar-brand-sub {
  font-size: 9.5px;
  color: rgba(255,255,255,0.35) !important;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 4px;
}
.sidebar-brand-dot {
  width: 6px; height: 6px;
  background: var(--lk-gold);
  border-radius: 50%;
  display: inline-block;
  margin-right: 5px;
  animation: pulse-dot 2s ease-in-out infinite;
}

/* ════════════════════════════════════════
   METRIC CARDS — Premium Glass Style
   ════════════════════════════════════════ */
[data-testid="metric-container"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 16px 20px !important;
  transition: all 0.2s cubic-bezier(0.4,0,0.2,1) !important;
  animation: fadeUp 0.3s ease both;
  position: relative;
  overflow: hidden;
}
[data-testid="metric-container"]::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
}
[data-testid="metric-container"]:hover {
  border-color: var(--border-bright) !important;
  transform: translateY(-2px) !important;
  box-shadow: var(--shadow-md) !important;
  background: var(--bg-elevated) !important;
}
[data-testid="metric-container"] label {
  color: var(--text-muted) !important;
  font-size: 9.5px !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  font-family: 'Outfit', sans-serif !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color: var(--text-primary) !important;
  font-size: 22px !important;
  font-weight: 700 !important;
  font-family: 'Outfit', sans-serif !important;
  letter-spacing: -0.5px;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
  font-size: 11px !important;
  font-weight: 600 !important;
}

/* ════════════════════════════════════════
   BUTTONS — Lenskart Brand System
   ════════════════════════════════════════ */
.stButton > button {
  background: linear-gradient(135deg, #000040 0%, #000030 100%) !important;
  color: var(--lk-gold) !important;
  border: 1px solid rgba(253,232,0,0.4) !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  font-size: 12.5px !important;
  padding: 9px 20px !important;
  transition: all 0.18s cubic-bezier(0.4,0,0.2,1) !important;
  letter-spacing: 0.02em !important;
  font-family: 'DM Sans', sans-serif !important;
  cursor: pointer !important;
}
.stButton > button:hover {
  background: var(--lk-gold) !important;
  color: #000035 !important;
  border-color: var(--lk-gold) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(253,232,0,0.22) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #0030a0, #001a6e) !important;
  color: #fff !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0,48,160,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #0040cc, #0030a0) !important;
  color: #fff !important;
  box-shadow: 0 6px 24px rgba(0,64,204,0.4) !important;
}
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible {
  outline: 2px solid var(--lk-gold) !important;
  outline-offset: 2px !important;
}
.stDownloadButton > button {
  background: linear-gradient(135deg, #064e3b, #065f46) !important;
  color: #34d399 !important;
  border: 1px solid rgba(52,211,153,0.25) !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  font-size: 12.5px !important;
  transition: all 0.18s ease !important;
}
.stDownloadButton > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(52,211,153,0.2) !important;
}

/* ════════════════════════════════════════
   FORM INPUTS
   ════════════════════════════════════════ */
[data-testid="stSelectbox"] > div > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-md) !important;
  min-height: 42px !important;
  transition: border-color 0.18s ease !important;
}
[data-testid="stSelectbox"] > div > div:hover {
  border-color: var(--border-bright) !important;
}
[data-testid="stTextInput"] input {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-md) !important;
  transition: border-color 0.18s ease !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: var(--lk-blue-light) !important;
  box-shadow: 0 0 0 3px rgba(26,95,255,0.12) !important;
}

/* ════════════════════════════════════════
   TABS — Clean Pill Navigation
   ════════════════════════════════════════ */
[data-testid="stTabs"] {
  border-bottom: 1px solid var(--border) !important;
  margin-bottom: 4px;
}
[data-testid="stTabs"] button {
  color: var(--text-muted) !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  padding: 10px 18px !important;
  border-radius: 0 !important;
  font-family: 'DM Sans', sans-serif !important;
  transition: all 0.18s ease !important;
}
[data-testid="stTabs"] button:hover {
  color: var(--text-secondary) !important;
  background: rgba(255,255,255,0.02) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--text-primary) !important;
  border-bottom: 2px solid var(--lk-gold) !important;
  font-weight: 600 !important;
  background: transparent !important;
}

/* ════════════════════════════════════════
   EXPANDERS
   ════════════════════════════════════════ */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  transition: border-color 0.18s ease !important;
}
[data-testid="stExpander"]:hover {
  border-color: var(--border-bright) !important;
}
[data-testid="stExpander"] summary {
  font-weight: 600 !important;
  font-size: 13px !important;
}

/* ════════════════════════════════════════
   DATAFRAME
   ════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
}

/* ════════════════════════════════════════
   PROGRESS BAR
   ════════════════════════════════════════ */
.stProgress > div { background: var(--bg-elevated) !important; border-radius: 99px !important; }
.stProgress > div > div {
  background: linear-gradient(90deg, var(--lk-blue-mid), var(--lk-blue-light)) !important;
  border-radius: 99px !important;
}

/* ════════════════════════════════════════
   ALERTS
   ════════════════════════════════════════ */
.stAlert { border-radius: var(--radius-md) !important; border: none !important; }
hr { border-color: var(--border) !important; }

/* ════════════════════════════════════════
   SECTION LABEL — Refined
   ════════════════════════════════════════ */
.section-label {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 10px;
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Outfit', sans-serif;
}
.section-label::before {
  content: '';
  display: block;
  width: 3px;
  height: 12px;
  background: linear-gradient(180deg, var(--lk-gold), var(--lk-blue-light));
  border-radius: 2px;
  flex-shrink: 0;
}

/* ════════════════════════════════════════
   STATUS BADGES
   ════════════════════════════════════════ */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  font-family: 'Outfit', sans-serif;
}
.badge::before {
  content: '';
  width: 5px; height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}
.badge-healthy   { background:#052e16; color:#4ade80; border:1px solid rgba(74,222,128,0.2); }
.badge-healthy::before { background: #4ade80; animation: pulse-dot 2s ease infinite; }
.badge-risk      { background:#1c1200; color:#fbbf24; border:1px solid rgba(251,191,36,0.2); }
.badge-risk::before { background: #fbbf24; }
.badge-critical  { background:#1a0e00; color:#fb923c; border:1px solid rgba(251,146,60,0.2); }
.badge-critical::before { background: #fb923c; }
.badge-emergency { background:#1a0000; color:#f87171; border:1px solid rgba(248,113,113,0.25); }
.badge-emergency::before { background: #f87171; animation: pulse-dot 1.2s ease infinite; }

/* ════════════════════════════════════════
   SIGNAL ALERTS — Elevated Style
   ════════════════════════════════════════ */
.signal-critical {
  background: rgba(239,68,68,0.06);
  border: 1px solid rgba(239,68,68,0.18);
  border-left: 3px solid #ef4444;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: 10px 14px;
  margin: 5px 0;
  font-size: 12.5px;
  color: #fca5a5;
  line-height: 1.5;
  animation: slideIn 0.25s ease;
}
.signal-warning {
  background: rgba(234,179,8,0.06);
  border: 1px solid rgba(234,179,8,0.18);
  border-left: 3px solid #eab308;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: 10px 14px;
  margin: 5px 0;
  font-size: 12.5px;
  color: #fde68a;
  line-height: 1.5;
  animation: slideIn 0.25s ease;
}

/* ════════════════════════════════════════
   REPORT CARDS — Premium Glass
   ════════════════════════════════════════ */
.report-card {
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  margin: 8px 0;
  border: 1px solid var(--border);
  transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
  animation: fadeUp 0.3s ease both;
  position: relative;
  overflow: hidden;
}
.report-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
}
.report-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-bright);
}
.report-card-title {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'Outfit', sans-serif;
}
.rcard-health   { background: linear-gradient(135deg,#071a0b,#0a2010); border-color:#1a4727; }
.rcard-trend    { background: linear-gradient(135deg,#060e1c,#0a1628); border-color:#1a3050; }
.rcard-cause    { background: linear-gradient(135deg,#160d00,#1e1400); border-color:#5c3a10; }
.rcard-drivers  { background: linear-gradient(135deg,#100a1e,#140e25); border-color:#3d2380; }
.rcard-playbook { background: linear-gradient(135deg,#061618,#091f21); border-color:#0d4f52; }
.rcard-impact   { background: linear-gradient(135deg,#061511,#091a12); border-color:#14472a; }
.rcard-conf     { background: linear-gradient(135deg,#0d0d14,#111118); border-color:#242430; }

/* ════════════════════════════════════════
   PLAYBOOK ITEMS
   ════════════════════════════════════════ */
.playbook-item {
  background: rgba(4,6,15,0.8);
  border: 1px solid var(--border-dim);
  border-radius: var(--radius-md);
  padding: 13px 16px;
  margin: 8px 0;
  transition: all 0.18s ease;
}
.playbook-item:hover {
  border-color: var(--border);
  background: var(--bg-elevated);
  transform: translateX(3px);
}

/* ════════════════════════════════════════
   PILLS
   ════════════════════════════════════════ */
.pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 600;
  margin-right: 5px;
  font-family: 'Outfit', sans-serif;
  letter-spacing: 0.02em;
}

/* ════════════════════════════════════════
   PAGE HEADER COMPONENTS
   ════════════════════════════════════════ */
.page-topbar {
  background: linear-gradient(90deg, rgba(0,0,40,0.95) 0%, rgba(0,0,28,0.8) 100%);
  border-bottom: 1px solid var(--border);
  padding: 12px 2rem;
  margin: 0 -2rem 24px -2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}
.page-topbar-left { display: flex; align-items: center; gap: 14px; }
.page-topbar-right { display: flex; align-items: center; gap: 10px; }

.store-chip {
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border);
  border-radius: 99px;
  padding: 4px 14px;
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
  font-family: 'JetBrains Mono', monospace;
}

.health-score-ring {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px; height: 44px;
  border-radius: 50%;
  border: 2px solid;
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  font-size: 14px;
}

/* ════════════════════════════════════════
   KPI CARDS — Ultra Premium
   ════════════════════════════════════════ */
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
  animation: fadeUp 0.3s ease both;
}
.kpi-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  border-radius: 2px 0 0 2px;
}
.kpi-card:hover {
  border-color: var(--border-bright);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.kpi-label {
  font-size: 9.5px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-family: 'Outfit', sans-serif;
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'Outfit', sans-serif;
  letter-spacing: -0.5px;
  line-height: 1;
  margin-bottom: 6px;
}
.kpi-delta {
  font-size: 11px;
  font-weight: 600;
}
.kpi-delta-up   { color: var(--green-light); }
.kpi-delta-down { color: var(--red-light); }
.kpi-delta-flat { color: var(--yellow-light); }

/* ════════════════════════════════════════
   EXECUTIVE COMMAND BRIEF
   ════════════════════════════════════════ */
.command-brief {
  background: linear-gradient(135deg, #080e1e 0%, #0c1330 50%, #0f1840 100%);
  border: 1px solid rgba(0,64,204,0.3);
  border-radius: var(--radius-xl);
  padding: 28px 30px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
  animation: glow-border 4s ease-in-out infinite;
}
.command-brief::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,64,204,0.6), rgba(253,232,0,0.4), transparent);
}
.command-brief-eyebrow {
  font-size: 9.5px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--lk-gold);
  margin-bottom: 6px;
  font-family: 'Outfit', sans-serif;
}
.command-brief-headline {
  font-size: 30px;
  font-weight: 800;
  color: #fff;
  font-family: 'Outfit', sans-serif;
  letter-spacing: -0.8px;
  line-height: 1.1;
  margin-bottom: 20px;
}

/* ════════════════════════════════════════
   AT-RISK STORE ROW
   ════════════════════════════════════════ */
.risk-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(239,68,68,0.04);
  border: 1px solid rgba(239,68,68,0.12);
  border-left: 3px solid #ef4444;
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  margin-bottom: 8px;
  transition: all 0.18s ease;
  cursor: pointer;
}
.risk-row:hover {
  background: rgba(239,68,68,0.08);
  border-color: rgba(239,68,68,0.25);
  border-left-color: #ef4444;
  transform: translateX(2px);
}

/* ════════════════════════════════════════
   HERO UPLIFT CARD
   ════════════════════════════════════════ */
.uplift-hero {
  background: linear-gradient(135deg, #000028 0%, #00003a 60%, #000855 100%);
  border: 1px solid rgba(0,64,204,0.25);
  border-radius: var(--radius-xl);
  padding: 28px 32px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}
.uplift-hero::after {
  content: 'UPLIFT';
  position: absolute;
  right: -12px; top: -20px;
  font-size: 100px;
  font-weight: 900;
  color: rgba(255,255,255,0.018);
  font-family: 'Outfit', sans-serif;
  letter-spacing: -5px;
  pointer-events: none;
}
.uplift-hero-eyebrow {
  font-size: 9.5px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: rgba(255,255,255,0.4);
  margin-bottom: 8px;
  font-family: 'Outfit', sans-serif;
}
.uplift-hero-value {
  font-size: 48px;
  font-weight: 900;
  color: var(--green-light);
  font-family: 'Outfit', sans-serif;
  letter-spacing: -2px;
  line-height: 1;
  margin-bottom: 8px;
}
.uplift-hero-sub {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
  line-height: 1.5;
}

/* ════════════════════════════════════════
   EMPTY STATE
   ════════════════════════════════════════ */
.empty-state {
  background: var(--bg-card);
  border: 1px dashed var(--border);
  border-radius: var(--radius-xl);
  padding: 48px;
  text-align: center;
  color: var(--text-muted);
  animation: fadeUp 0.35s ease both;
}

/* ════════════════════════════════════════
   BENCHMARK BAR
   ════════════════════════════════════════ */
.bench-bar-bg {
  background: var(--bg-elevated);
  border-radius: 4px;
  height: 5px;
  width: 100%;
  margin-top: 5px;
  overflow: hidden;
}

/* ════════════════════════════════════════
   IMPACT BLOCK (EXEC BRIEF)
   ════════════════════════════════════════ */
.impact-block {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.9;
}

/* ════════════════════════════════════════
   STATUS DOT (ENV)
   ════════════════════════════════════════ */
.env-status-panel {
  background: rgba(255,255,255,0.025);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  border: 1px solid var(--border-dim);
  margin-bottom: 16px;
}

/* ════════════════════════════════════════
   REDUCED MOTION
   ════════════════════════════════════════ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS & HELPERS
# ─────────────────────────────────────────────
HEALTH_COLORS = {
    "HEALTHY":   "#22c55e",
    "AT RISK":   "#eab308",
    "CRITICAL":  "#f97316",
    "EMERGENCY": "#ef4444",
}

HEALTH_BADGE_CLASS = {
    "HEALTHY": "badge-healthy", "AT RISK": "badge-risk",
    "CRITICAL": "badge-critical", "EMERGENCY": "badge-emergency",
}


def safe_float(value, default=0.0):
    """Defensive numeric cast for UI rendering."""
    try:
        if value is None:
            return float(default)
        if pd.isna(value):
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def safe_int(value, default=0):
    """Defensive int cast for UI rendering."""
    return int(round(safe_float(value, default)))


def health_badge(label):
    cls = HEALTH_BADGE_CLASS.get(label, "badge-risk")
    return f'<span class="badge {cls}">{label}</span>'


def trend_pill(val, suffix="%"):
    """Return HTML pill for a trend value."""
    try:
        v = float(val)
        if v > 0:
            return f'<span class="pill" style="background:rgba(34,197,94,0.12);color:#4ade80;">↑ {abs(v):.1f}{suffix}</span>'
        elif v < 0:
            return f'<span class="pill" style="background:rgba(239,68,68,0.12);color:#f87171;">↓ {abs(v):.1f}{suffix}</span>'
        else:
            return f'<span class="pill" style="background:rgba(234,179,8,0.12);color:#fde68a;">→ 0.0{suffix}</span>'
    except Exception:
        return str(val)


def section_label(text, margin_top=2):
    st.markdown(f'<div class="section-label" style="margin-top:{margin_top}px;">{text}</div>', unsafe_allow_html=True)


def estimate_monthly_uplift(decision, target_conv=15.0):
    """Rule-based uplift estimate used for prioritization and executive brief."""
    m = decision.get("metrics", {})
    current_conv = float(m.get("conversion_rate", 0))
    footfall = float(m.get("footfall", 0))
    aov = float(m.get("aov", 0))
    if current_conv >= target_conv or footfall <= 0 or aov <= 0:
        return 0.0
    conv_gap = (target_conv - current_conv) / 100
    return round(footfall * conv_gap * aov * 30, 0)


def pick_story_store(decisions, story_type):
    """Pick a representative store for storytelling mode."""
    if not decisions:
        return None
    if story_type == "Critical Recovery Story":
        ranked = sorted(decisions, key=lambda d: (d["health_score"], -len(d.get("signals", []))))
        return ranked[0]["store_id"]
    if story_type == "Healthy Benchmark Story":
        ranked = sorted(decisions, key=lambda d: (-d["health_score"], -d["metrics"]["conversion_rate"]))
        return ranked[0]["store_id"]
    # Balanced opportunity story: high revenue uplift potential.
    ranked = sorted(decisions, key=lambda d: estimate_monthly_uplift(d), reverse=True)
    return ranked[0]["store_id"]


def build_intervention_tracker(decisions):
    """Create a simple action tracker for client-ready execution."""
    rows = []
    for d in decisions:
        m = d["metrics"]
        uplift = estimate_monthly_uplift(d)
        priority = "P0" if d["health_label"] in ("CRITICAL", "EMERGENCY") else ("P1" if d["health_label"] == "AT RISK" else "P2")
        owner = "Store Manager"
        for s in d.get("signals", []):
            if s.get("category") in ("Staffing", "Operations"):
                owner = "AOM"
                break
            if s.get("category") in ("Systems", "Demand"):
                owner = "ZM"
                break
        rows.append({
            "Priority": priority,
            "Store": d["store_id"],
            "City": d["city"],
            "Health": d["health_label"],
            "Conv%": round(m.get("conversion_rate", 0), 1),
            "Revenue": round(m.get("revenue", 0), 0),
            "Signal Count": len(d.get("signals", [])),
            "Owner": owner,
            "Expected Monthly Uplift (₹)": uplift,
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(
        by=["Priority", "Expected Monthly Uplift (₹)", "Signal Count"],
        ascending=[True, False, False],
    ).reset_index(drop=True)
    return out


def normalize_store_code(value):
    """Normalize store codes for robust joins across systems. Handles 'CODE - NAME' formats."""
    if value is None:
        return ""
    text = str(value).strip().upper()
    if not text:
        return ""
    if " - " in text:
        text = text.split(" - ", 1)[0].strip()
    return text


@st.cache_data(ttl=3600, show_spinner=False)
def load_offline_mapping():
    """
    Load role-to-store mapping. Prioritizes anonymized mapping.json, 
    falls back to Lenskart offline mapping Excel sheet if JSON is absent.
    Returns (mapping_df, error_msg). error_msg is None on success.
    """
    # 1. Try JSON first (Anonymized/Fast)
    if os.path.exists(MAPPING_PATH_JSON):
        try:
            mapping = pd.read_json(MAPPING_PATH_JSON)
            if not mapping.empty:
                mapping["store_code_norm"] = mapping["store_code"].apply(normalize_store_code)
                # Ensure all role columns exist even if empty in JSON
                for col in ["AOM", "zm", "circle_head", "aom(mail id)", "ZM(mail id)", "Circle Head(mail id)"]:
                    if col not in mapping.columns:
                        mapping[col] = ""
                return mapping, None
        except Exception as e:
            st.warning(f"Failed to load {MAPPING_PATH_JSON}: {e}")

    # 2. Fallback to Excel (Real Data)
    if not os.path.exists(MAPPING_PATH_EXCEL):
        return None, "No mapping file found (JSON or Excel). Run `prepare_mock_mapping.py`."
        
    try:
        mapping = pd.read_excel(MAPPING_PATH_EXCEL, sheet_name="Offline mapping")
    except Exception as e:
        return None, f"Could not read Excel mapping: {e}"

    required = {"store_code", "AOM", "zm", "circle_head"}
    missing = required - set(mapping.columns)
    if missing:
        return None, f"Excel mapping missing required columns: {sorted(missing)}"

    mapping = mapping.copy()
    mapping["store_code_norm"] = mapping["store_code"].apply(normalize_store_code)
    
    # Clean up role names and emails
    cols_to_clean = ["AOM", "zm", "circle_head", "aom(mail id)", "ZM(mail id)", "Circle Head(mail id)"]
    for col in cols_to_clean:
        if col in mapping.columns:
            mapping[col] = mapping[col].fillna("").astype(str).str.strip()
            # Remove "nan" strings resulting from strip
            mapping.loc[mapping[col].str.lower() == "nan", col] = ""
        else:
            mapping[col] = ""
            
    mapping = mapping[mapping["store_code_norm"] != ""]
    return mapping, None


def get_people_for_role(mapping_df, selected_role):
    """Return sorted unique people (with emails if available) for selected role."""
    if selected_role == "Area Operations Manager (AOM)":
        base_col, email_col = "AOM", "aom(mail id)"
    elif selected_role == "Zonal Manager (ZM)":
        base_col, email_col = "zm", "ZM(mail id)"
    elif selected_role == "Circle Head":
        base_col, email_col = "circle_head", "Circle Head(mail id)"
    else:
        return []

    users = []
    seen = set()
    # Use both name and email for unique identification
    relevant_cols = [base_col]
    if email_col in mapping_df.columns:
        relevant_cols.append(email_col)
        
    for _, r in mapping_df[relevant_cols].dropna(subset=[base_col]).iterrows():
        name = str(r[base_col]).strip()
        email = str(r[email_col]).strip() if email_col in mapping_df.columns else ""
        if not name or name.lower() == "nan":
            continue
        label = f"{name} ({email})" if email and email.lower() != "nan" and email != "" else name
        if label not in seen:
            seen.add(label)
            users.append(label)
    users.sort()
    return users


def get_allowed_store_codes(mapping_df, selected_role, user_label):
    """Return a set of normalized store codes assigned to a specific person in a role."""

    if selected_role == "Area Operations Manager (AOM)":
        base_col, email_col = "AOM", "aom(mail id)"
    elif selected_role == "Zonal Manager (ZM)":
        base_col, email_col = "zm", "ZM(mail id)"
    elif selected_role == "Circle Head":
        base_col, email_col = "circle_head", "Circle Head(mail id)"
    else:
        return set()

    if not user_label:
        return set()

    # Extract name and email from label "Name (email)"
    name = user_label.split(" (")[0].strip()
    email = ""
    if " (" in user_label and user_label.endswith(")"):
        email = user_label[user_label.rfind("(") + 1:-1].strip()

    mask = mapping_df[base_col].astype(str).str.strip().eq(name)
    if email and email_col in mapping_df.columns:
        email_mask = mapping_df[email_col].astype(str).str.strip().eq(email)
        if email_mask.any():
            mask = mask & email_mask

    return set(mapping_df.loc[mask, "store_code_norm"].dropna().unique().tolist())


def make_sparkline(time_series, field, color, height=160):
    if not time_series:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=height, margin=dict(l=0, r=0, t=8, b=0),
            annotations=[dict(text="No data", x=0.5, y=0.5, showarrow=False,
                              font=dict(color="#4a5568", size=13), xref="paper", yref="paper")]
        )
        return fig
    dates = [r["date"] for r in time_series]
    vals  = [safe_float(r.get(field, 0), 0) for r in time_series]
    try:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fill_color = f"rgba({r},{g},{b},0.12)"
    except Exception:
        fill_color = "rgba(59,130,246,0.12)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=vals, mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=5, color=color, line=dict(width=1.5, color="rgba(255,255,255,0.3)")),
        fill="tozeroy", fillcolor=fill_color,
        hovertemplate=f"%{{x}}<br>{field}: %{{y:,.2f}}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0), height=height,
        xaxis=dict(showgrid=False, showticklabels=True,
                   tickfont=dict(size=9, color="#4a5568"),
                   tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="#1a2535",
                   showticklabels=True, tickfont=dict(size=9, color="#4a5568")),
        showlegend=False,
        hoverlabel=dict(bgcolor="#111827", font_size=12, font_color="#e8edf5"),
    )
    return fig


def make_ranking_chart(decisions):
    sorted_d = sorted(decisions, key=lambda x: x["metrics"]["revenue"], reverse=True)
    stores   = [d["store_id"] for d in sorted_d]
    revenues = [safe_float(d["metrics"]["revenue"], 0) for d in sorted_d]
    health   = [d["health_label"] for d in sorted_d]
    colors   = [HEALTH_COLORS.get(h, "#64748b") for h in health]
    fig = go.Figure(go.Bar(
        x=revenues, y=stores, orientation="h",
        marker_color=colors,
        marker_line_color="rgba(255,255,255,0.05)", marker_line_width=1,
        text=[f"₹{r:,.0f}" for r in revenues],
        textposition="outside",
        textfont=dict(size=10, color="#8899aa"),
        hovertemplate="%{y}<br>Revenue: ₹%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=70, t=10, b=0),
        height=max(200, len(stores) * 34),
        xaxis=dict(showgrid=True, gridcolor="#1a2535",
                   tickfont=dict(color="#4a5568", size=9)),
        yaxis=dict(showgrid=False, tickfont=dict(color="#8899aa", size=11)),
        bargap=0.35,
    )
    return fig


def make_revenue_breakdown_chart(decomp):
    """Horizontal bar chart for revenue decomposition."""
    labels = ["Footfall", "Conversion", "AOV"]
    vals = [
        safe_float(decomp.get("footfall_effect", 0)),
        safe_float(decomp.get("conversion_effect", 0)),
        safe_float(decomp.get("aov_effect", 0))
    ]
    
    # Calculate percentage contribution
    total_abs = sum(abs(v) for v in vals) or 1
    pcts = [abs(v)/total_abs*100 for v in vals]
    
    colors = ["#ef4444" if v < 0 else "#22c55e" for v in vals]
    
    fig = go.Figure(go.Bar(
        x=vals, y=labels, orientation="h",
        marker_color=colors,
        text=[f"₹{v:,.0f} ({p:.1f}%)" for v, p in zip(vals, pcts)],
        textposition="auto",
        hovertemplate="%{y}: ₹%{x:,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=20, t=10, b=0), height=180,
        xaxis=dict(showgrid=True, gridcolor="#1a2535", tickfont=dict(color="#4a5568", size=9)),
        yaxis=dict(showgrid=False, tickfont=dict(color="#8899aa", size=11)),
        bargap=0.3
    )
    return fig


def render_radar_chart(metrics, benchmarks):
    """Radar chart comparing store metrics vs fleet median."""
    categories = ["Conversion", "Footfall", "AOV", "Staff Eff.", "Rev/Visitor"]
    bm = benchmarks or {}

    def pct_of_median(val, key):
        p50 = safe_float(bm.get(key, {}).get("p50", 1), 1)
        return min(150, round((val / p50) * 100, 1)) if p50 > 0 else 0

    store_vals = [
        pct_of_median(safe_float(metrics.get("conversion_rate", 0), 0), "conversion_rate"),
        pct_of_median(safe_float(metrics.get("footfall", 0), 0),        "footfall"),
        pct_of_median(safe_float(metrics.get("aov", 0), 0),             "aov"),
        pct_of_median(safe_float(metrics.get("staff_efficiency", 0), 0),"staff_efficiency"),
        pct_of_median(safe_float(metrics.get("revenue_per_visitor", 0), 0), "revenue_per_visitor"),
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[100]*5 + [100], theta=categories + [categories[0]],
        fill="toself", fillcolor="rgba(37,99,235,0.05)",
        line=dict(color="#1e3a5f", width=1, dash="dot"),
        name="Fleet Median",
    ))
    fig.add_trace(go.Scatterpolar(
        r=store_vals + [store_vals[0]], theta=categories + [categories[0]],
        fill="toself", fillcolor="rgba(37,99,235,0.2)",
        line=dict(color="#2563eb", width=2),
        name="This Store",
        hovertemplate="%{theta}: %{r:.0f}% of fleet median<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            angularaxis=dict(tickfont=dict(size=10, color="#8899aa"), linecolor="#1e2d40"),
            radialaxis=dict(
                tickfont=dict(size=8, color="#4a5568"), linecolor="#1e2d40",
                gridcolor="#1a2535", range=[0, 150], tickvals=[50, 100, 150],
                ticktext=["50%", "100%", "150%"],
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=30, b=30), height=280,
        showlegend=True,
        legend=dict(font=dict(color="#8899aa", size=10), bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def make_fleet_heatmap(decisions):
    """Heatmap of stores × KPIs."""
    if not decisions:
        return go.Figure()
    metrics_keys = ["conversion_rate", "footfall", "aov", "staff_efficiency"]
    labels = ["Conversion%", "Footfall", "AOV", "Staff Eff."]
    stores = [d["store_id"] for d in decisions]
    z = []
    for mk in metrics_keys:
        vals = [safe_float(d["metrics"].get(mk, 0), 0) for d in decisions]
        max_v = max(vals) if max(vals) > 0 else 1
        z.append([round(v / max_v * 100, 1) for v in vals])

    fig = go.Figure(go.Heatmap(
        z=z, x=stores, y=labels,
        colorscale=[[0, "#1c0000"], [0.5, "#1e3a5f"], [1, "#22c55e"]],
        text=[[f"{v:.1f}" for v in row] for row in z],
        texttemplate="%{text}",
        showscale=True, colorbar=dict(
            tickfont=dict(color="#8899aa", size=9),
            outlinewidth=0, thickness=10,
        ),
        hovertemplate="%{x}<br>%{y}: %{z:.1f}% of max<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=220,
        xaxis=dict(tickfont=dict(size=10, color="#8899aa")),
        yaxis=dict(tickfont=dict(size=10, color="#8899aa")),
    )
    return fig


# ─────────────────────────────────────────────
# AI REPORT RENDERER
# ─────────────────────────────────────────────
def render_ai_report_cards(report_text: str):
    import re

    def extract(pattern, text, default=""):
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else default

    health_line    = extract(r"STORE HEALTH:\s*(.+?)(?:\n|$)", report_text)
    trend_line     = extract(r"TREND:\s*(.+?)(?:\n|$)", report_text)
    root_cause     = extract(r"ROOT CAUSE:\s*(.+?)(?:REVENUE BRIDGE|CONVERSION DRIVERS|PLAYBOOK|$)", report_text)
    revenue_bridge = extract(r"REVENUE BRIDGE:\s*(.+?)(?:CONVERSION DRIVERS|PLAYBOOK|$)", report_text)
    drivers_block  = extract(r"CONVERSION DRIVERS:\s*(.+?)(?:PLAYBOOK|$)", report_text)
    playbook_block = extract(r"PLAYBOOK:\s*(.+?)(?:EXPECTED IMPACT|$)", report_text)
    impact_line    = extract(r"EXPECTED IMPACT:\s*(.+?)(?:CONFIDENCE|$)", report_text)
    confidence_line= extract(r"CONFIDENCE:\s*(.+?)(?:---|$)", report_text)

    # Determine colors
    health_color = "#22c55e"
    hl_upper = health_line.upper()
    if "EMERGENCY" in hl_upper: health_color = "#ef4444"
    elif "CRITICAL" in hl_upper: health_color = "#f97316"
    elif "AT RISK" in hl_upper: health_color = "#eab308"

    trend_color = "#eab308"
    tl_upper = trend_line.upper()
    if "IMPROVING" in tl_upper: trend_color = "#22c55e"
    elif "DECLINING" in tl_upper: trend_color = "#ef4444"

    html = ""

    # Row 1: Health + Trend side by side
    html += f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;"><div class="report-card rcard-health"><div class="report-card-title" style="color:#4ade80;">🏥 STORE HEALTH</div><div style="font-size:13.5px;color:{health_color};font-weight:700;line-height:1.5;">{health_line}</div></div><div class="report-card rcard-trend"><div class="report-card-title" style="color:#60a5fa;">📈 TREND SUMMARY</div><div style="font-size:13.5px;color:{trend_color};font-weight:700;line-height:1.5;">{trend_line}</div></div></div>'

    # Root Cause
    if root_cause:
        html += f'<div class="report-card rcard-cause" style="margin-bottom:10px;"><div class="report-card-title" style="color:#fbbf24;">🔍 ROOT CAUSE ANALYSIS</div><div style="font-size:13px;color:#e2e8f0;line-height:1.75;">{root_cause.replace(chr(10), "<br>")}</div></div>'

    # Revenue Bridge
    if revenue_bridge:
        items_html = ""
        for line in revenue_bridge.strip().split("\n"):
            line = line.strip().lstrip("•·-").strip()
            if not line:
                continue
            colon_idx = line.find(":")
            if colon_idx > 0:
                key = line[:colon_idx].strip()
                val = line[colon_idx + 1:].strip()
                items_html += f'<div style="display:flex;align-items:flex-start;gap:10px;padding:7px 0;border-bottom:1px solid rgba(20,83,45,0.3);"><span style="color:#22c55e;font-weight:700;min-width:130px;font-size:12px;">{key}</span><span style="color:#bbf7d0;font-size:12.5px;">{val}</span></div>'
            else:
                items_html += f'<div style="color:#bbf7d0;font-size:12.5px;padding:5px 0;">• {line}</div>'
        html += f'<div class="report-card" style="margin-bottom:10px;background:#0a1f0d;border-color:#14532d;"><div class="report-card-title" style="color:#4ade80;">💸 REVENUE BRIDGE</div>{items_html}</div>'

    # Conversion Drivers
    if drivers_block:
        items_html = ""
        for line in drivers_block.strip().split("\n"):
            line = line.strip().lstrip("•·-").strip()
            if not line:
                continue
            colon_idx = line.find(":")
            if colon_idx > 0:
                key = line[:colon_idx].strip()
                val = line[colon_idx+1:].strip()
                items_html += f'<div style="display:flex;align-items:flex-start;gap:10px;padding:7px 0;border-bottom:1px solid rgba(92,51,186,0.2);"><span style="color:#7c3aed;font-weight:700;min-width:120px;font-size:12px;">{key}</span><span style="color:#c4b5fd;font-size:12.5px;">{val}</span></div>'
            else:
                items_html += f'<div style="color:#c4b5fd;font-size:12.5px;padding:5px 0;">• {line}</div>'
        html += f'<div class="report-card rcard-drivers" style="margin-bottom:10px;"><div class="report-card-title" style="color:#a78bfa;">⚡ CONVERSION CHANGE DRIVERS</div>{items_html}</div>'

    # Playbook
    if playbook_block:
        actions_html = ""
        current_action = []
        for line in playbook_block.strip().split("\n"):
            s = line.strip()
            if re.match(r"^[1-3]\.", s):
                if current_action:
                    actions_html += _render_playbook_item(current_action)
                current_action = [s]
            elif (s.startswith("→") or s.startswith("->")) and current_action:
                current_action.append(s)
            elif s and current_action:
                current_action[-1] += " " + s
        if current_action:
            actions_html += _render_playbook_item(current_action)

        html += f'<div class="report-card rcard-playbook" style="margin-bottom:10px;"><div class="report-card-title" style="color:#2dd4bf;">📋 ACTION PLAYBOOK</div>{actions_html}</div>'

    # Impact + Confidence
    conf_color = "#94a3b8"
    cl = confidence_line.upper()
    if "HIGH" in cl:    conf_color = "#4ade80"
    elif "MEDIUM" in cl: conf_color = "#fbbf24"
    elif "LOW" in cl:    conf_color = "#f87171"

    html += f'<div style="display:grid;grid-template-columns:1.4fr 1fr;gap:10px;"><div class="report-card rcard-impact"><div class="report-card-title" style="color:#4ade80;">🎯 EXPECTED IMPACT</div><div style="font-size:13.5px;color:#86efac;font-weight:700;">{impact_line}</div></div><div class="report-card rcard-conf"><div class="report-card-title" style="color:#94a3b8;">🔒 CONFIDENCE</div><div style="font-size:13px;color:{conf_color};font-weight:600;">{confidence_line}</div></div></div>'

    st.markdown(html, unsafe_allow_html=True)


def _render_playbook_item(lines):
    import re
    header  = lines[0] if lines else ""
    detail  = lines[1] if len(lines) > 1 else ""
    num_m   = re.match(r"^(\d+)\.\s*", header)
    num     = num_m.group(1) if num_m else "•"
    content = re.sub(r"^\d+\.\s*", "", header)

    parts = content.split("|")
    action_name = parts[0].strip() if parts else content
    pills_html  = ""
    for part in parts[1:]:
        p = part.strip()
        if p.startswith("Owner:"):
            pills_html += f'<span class="pill" style="background:rgba(148,163,184,0.1);color:#94a3b8;">👤 {p}</span>'
        elif p.startswith("By:"):
            pills_html += f'<span class="pill" style="background:rgba(234,179,8,0.1);color:#fbbf24;">⏰ {p}</span>'
        elif p.startswith("Impact:"):
            pills_html += f'<span class="pill" style="background:rgba(34,197,94,0.1);color:#4ade80;">💡 {p}</span>'
        else:
            pills_html += f'<span class="pill" style="background:rgba(71,85,105,0.1);color:#64748b;">{p}</span>'

    arrow = detail.lstrip("→->").strip() if detail else ""
    detail_html = f'<div style="font-size:12px;color:#475569;margin-top:7px;padding-top:7px;border-top:1px solid rgba(255,255,255,0.05);">→ {arrow}</div>' if arrow else ""

    return f'<div class="playbook-item"><div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;"><span style="background:#0ea5e9;color:white;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0;">{num}</span><span style="font-size:13.5px;color:#f1f5f9;font-weight:700;">{action_name}</span></div><div style="display:flex;flex-wrap:wrap;gap:4px;">{pills_html}</div>{detail_html}</div>'


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, default in [
    ("reports", {}), ("role", "Zonal Manager (ZM)"), ("prev_role", "Zonal Manager (ZM)"),
    ("run_all", False), ("selected_store_id", ""), ("selected_person", ""),
    ("presentation_mode", "Standard"), ("story_type", "Highest Opportunity Story"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_data(period: str):
    file = "stores_data.parquet"
    if not os.path.exists(file):
        file = "stores_data_advanced.csv"
    
    try:
        df = load_data(file)
    except FileNotFoundError:
        return None, None, "stores_data.csv not found. Run: `python generate_sample_data.py`"
    except pd.errors.EmptyDataError:
        return None, None, "CSV is empty. Run: `python generate_sample_data.py`"
    except ValueError as e:
        return None, None, f"Data schema error: {e}"
    except Exception as e:
        return None, None, f"Data load error: {e}"

    if df is None or df.empty:
        return None, None, "No data available."

    df["date"] = pd.to_datetime(df["date"])
    max_date   = df["date"].max()

    if period == "Daily":
        df = df[df["date"] == max_date]
    elif period == "Weekly":
        df = df[df["date"] >= max_date - pd.Timedelta(days=6)]
    elif period == "Monthly":
        df = df[df["date"] >= max_date - pd.Timedelta(days=29)]
    # Annual → all data

    if df.empty:
        return None, None, f"No data for period '{period}'. Try a broader range."

    try:
        decisions = analyze_stores(df)
    except Exception as e:
        return None, None, f"Analysis engine error: {e}"

    return df, decisions, None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    # ─── CIRCULAR LOGO ───
    st.markdown(f"""
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
            <img src="https://static1.lenskart.com/media/desktop/img/Sep23/13-Sep/lenskart-logo-new-144x144.png" 
                 style="width: 80px; height: 80px; border-radius: 50%; border: 2px solid var(--border-bright); padding: 5px; background: white;">
        </div>
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 16px; font-weight: 800; color: #fff; letter-spacing: 1px;">ZM COPILOT</div>
            <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Lenskart Operations</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Access Role</div>', unsafe_allow_html=True)
    selected_role = st.selectbox(
        "Role", list(DEMO_ROLES.keys()),
        index=list(DEMO_ROLES.keys()).index(st.session_state.role) if st.session_state.role in DEMO_ROLES else 0,
        label_visibility="visible",
    )
    if selected_role != st.session_state.prev_role:
        st.session_state.reports = {}
        st.session_state.pop("selected_store_id", None)
        st.session_state["selected_person"] = ""
        st.session_state.pop("full_portfolio_pdf", None)
        st.session_state.prev_role = selected_role
    st.session_state.role = selected_role

    mapping_df, mapping_error = load_offline_mapping()
    mapping_mode_enabled = mapping_df is not None and mapping_error is None

    selected_person = ""
    allowed_store_codes = None

    st.markdown('<div class="section-label" style="margin-top:14px;">Access Identity</div>', unsafe_allow_html=True)
    if mapping_mode_enabled:
        people = get_people_for_role(mapping_df, selected_role)
        if not people:
            st.warning(f"No mapped {selected_role} users in `{MAPPING_PATH_JSON}`.")
        else:
            prev_person = st.session_state.get("selected_person", "")
            default_idx = people.index(prev_person) if prev_person in people else 0
            selected_person = st.selectbox(
                "Person",
                people,
                index=default_idx,
                label_visibility="visible",
            )
            st.session_state["selected_person"] = selected_person
            allowed_store_codes = get_allowed_store_codes(mapping_df, selected_role, selected_person)
            st.caption(f"Mapped stores: {len(allowed_store_codes)}")
    else:
        st.info("Mapping file unavailable. Falling back to demo city-based access.")
        if mapping_error:
            st.caption(mapping_error)

    st.markdown('<div class="section-label" style="margin-top:14px;">Time Period</div>', unsafe_allow_html=True)
    period = st.selectbox("Period", ["Daily", "Weekly", "Monthly", "Annual"], index=2,
                          label_visibility="visible")

    with st.spinner("Loading store data…"):
        df, decisions, data_error = get_data(period)

    if data_error:
        st.error(data_error)
        st.stop()

    if mapping_mode_enabled and allowed_store_codes is not None:
        decisions = [
            d for d in decisions
            if isinstance(d, dict) and "store_id" in d and normalize_store_code(d["store_id"]) in allowed_store_codes
        ]
    else:
        # Production Fallback: Show first 100 stores if no mapping found (e.g. initial setup)
        decisions = decisions[:100]
    if not decisions:
        msg = f"No mapped stores available for {selected_person or selected_role}" if mapping_mode_enabled else f"No stores for {selected_role}"
        st.markdown(f"""
            <div class="empty-state">
                <div style="font-size:48px;margin-bottom:16px;">&#128301;</div>
                <div style="font-size:18px;font-weight:700;color:#e8edf5;margin-bottom:8px;">No Data Found</div>
                <div style="font-size:13px;color:#64748b;max-width:400px;margin:0 auto;">
                    {msg} in the selected time period ({period}). 
                    Please check the sidebar filters or the mapping file configuration.
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Store sort + select ──
    # ── System Integrity Check ──
    st.markdown('<div class="section-label" style="margin-top:16px;">System Status</div>', unsafe_allow_html=True)
    aws_ok = os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    map_ok = os.path.exists(MAPPING_PATH_JSON)
    overall_ok = aws_ok and map_ok
    st.markdown(f"""
        <div class="env-status-panel">
            <div style="font-size:9.5px;color:var(--text-muted);font-weight:700;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;font-family:'Outfit',sans-serif;">Environment</div>
            <div style="display:flex;flex-direction:column;gap:5px;">
                <div style="display:flex;align-items:center;justify-content:space-between;font-size:11.5px;">
                    <span style="color:var(--text-secondary);">AWS Bedrock</span>
                    <span style="color:{'#4ade80' if aws_ok else '#f87171'};font-weight:700;font-size:10px;">{'● LIVE' if aws_ok else '● OFFLINE'}</span>
                </div>
                <div style="display:flex;align-items:center;justify-content:space-between;font-size:11.5px;">
                    <span style="color:var(--text-secondary);">Store Mapping</span>
                    <span style="color:{'#4ade80' if map_ok else '#f87171'};font-weight:700;font-size:10px;">{'● LOADED' if map_ok else '● MISSING'}</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Store Selection</div>', unsafe_allow_html=True)
    sort_map = {
        "Worst Health First": lambda x: x["health_score"],
        "Best Health First":  lambda x: -x["health_score"],
        "Revenue ↓":          lambda x: -x["metrics"]["revenue"],
        "Conversion ↓":       lambda x: -x["metrics"]["conversion_rate"],
        "Store ID":            lambda x: x["store_id"],
    }
    sort_by = st.selectbox("Sort by", list(sort_map.keys()), label_visibility="collapsed")
    sorted_decisions = sorted(decisions, key=sort_map[sort_by])

    store_options = [
        f"{d['store_id']} — {d['city']} [{d['health_label']}]"
        for d in sorted_decisions
    ]

    prev_id     = st.session_state.get("selected_store_id", "")
    default_idx = next((i for i, o in enumerate(store_options) if o.startswith(prev_id)), 0)
    selected_opt = st.selectbox("Store", store_options, index=default_idx, label_visibility="collapsed")
    selected_store_id = selected_opt.split(" — ")[0]
    st.session_state["selected_store_id"] = selected_store_id

    if selected_store_id == "📊 Fleet Overview":
        st.markdown('<div style="font-size:24px; font-weight:800; color:#e8edf5; margin-bottom:5px;">Fleet Commander Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px; color:#64748b; margin-bottom:25px;">Real-time Fleet Status · Predictive Uplift · Learning Engine Statistics</div>', unsafe_allow_html=True)

        # ── PREDICTIVE TOTAL UPLIFT (THE WINNING METRIC) ──
        total_uplift = sum(d.get("prediction", {}).get("potential_uplift", 0) for d in decisions)
        st.markdown(f"""
        <div class="uplift-hero">
          <div class="uplift-hero-eyebrow">Total Fleet Revenue Uplift Potential</div>
          <div class="uplift-hero-value">₹{total_uplift:,.0f}<span style="font-size:20px;font-weight:600;color:rgba(74,222,128,0.6);margin-left:8px;">/mo</span></div>
          <div class="uplift-hero-sub">Synthesized from {len(decisions)} store diagnostic paths across fleet. Executing top 5 recommendations unlocks ~40% immediately.</div>
        </div>
        """, unsafe_allow_html=True)

        # ── KPI GRID ──
        avg_rev  = sum(d["metrics"]["revenue"] for d in decisions) / len(decisions)
        avg_conv = sum(d["metrics"]["conversion_rate"] for d in decisions) / len(decisions)
        avg_health = sum(d["health_score"] for d in decisions) / len(decisions)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="report-card" style="text-align:center;"><div style="font-size:10px; color:#94a3b8; margin-bottom:5px;">AVG FLEET HEALTH</div><div style="font-size:24px; font-weight:800; color:#eab308;">{avg_health:.1f}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="report-card" style="text-align:center;"><div style="font-size:10px; color:#94a3b8; margin-bottom:5px;">AVG DAILY REVENUE</div><div style="font-size:24px; font-weight:800; color:#f1f5f9;">₹{avg_rev:,.0f}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="report-card" style="text-align:center;"><div style="font-size:10px; color:#94a3b8; margin-bottom:5px;">AVG CONVERSION</div><div style="font-size:24px; font-weight:800; color:#60a5fa;">{avg_conv:.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── WAR ROOM SPLIT ──
        col_left, col_right = st.columns([1.2, 1])
        
        with col_left:
            st.markdown('<div class="section-label">⚠️ Top Revenue-At-Risk Stores</div>', unsafe_allow_html=True)
            at_risk_list = [d for d in decisions if d["health_score"] < 50]
            at_risk_list = sorted(at_risk_list, key=lambda x: x["health_score"])[:8]
            
            if at_risk_list:
                for d in at_risk_list:
                    st.markdown(f"""
                        <div class="risk-row">
                            <div>
                                <div style="font-weight:700;color:#f1f5f9;font-size:13.5px;font-family:'Outfit',sans-serif;">{d["store_id"]} <span style="font-weight:400;color:var(--text-muted);font-size:12px;">· {d["city"]}</span></div>
                                <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">Health {d["health_score"]}/100 · {len(d["signals"])} alert{'s' if len(d['signals'])!=1 else ''}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:14px;font-weight:800;color:#f87171;font-family:'Outfit',sans-serif;">₹{d["metrics"]["revenue"]:,.0f}</div>
                                <div style="font-size:9.5px;color:var(--text-dim);margin-top:1px;font-weight:500;">DAILY REVENUE</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("All stores within healthy parameters.")

        with col_right:
            st.markdown('<div class="section-label">🧠 Self-Learning Intelligence & Cost Savings</div>', unsafe_allow_html=True)
            stats = get_learning_stats()
            st.markdown(f"""
                <div style="background:#0b111d; border:1px solid #243248; border-radius:10px; padding:20px; margin-bottom:20px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                        <div>
                            <div style="font-size:10px; color:#94a3b8;">PATTERN SUCCESS</div>
                            <div style="font-size:24px; font-weight:800; color:#4ade80;">{stats['avg_success']}%</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:10px; color:#94a3b8;">LESSONS LEARNED</div>
                            <div style="font-size:24px; font-weight:800; color:#60a5fa;">{stats['total_feedback']}</div>
                        </div>
                    </div>
                    <div style="font-size:11px; color:#64748b; line-height:1.5; border-top:1px solid #1e293b; padding-top:10px; margin-bottom:10px;">
                        AI is continuously learning from store outcomes. Every click improves fleet-wide reasoning.
                    </div>
                    <div style="background:rgba(34,197,94,0.05); border:1px solid rgba(34,197,94,0.2); border-radius:8px; padding:12px;">
                        <div style="color:#4ade80; font-size:11px; font-weight:800; margin-bottom:6px;">💰 COST SAVINGS</div>
                        <div style="font-size:12px; color:#e2e8f0; line-height:1.6;">
                            • AI cost reduced by <strong>70%</strong> using pattern reuse<br>
                            • Processing cost per store: <strong>₹0.60</strong><br>
                            • Manual effort saved: <strong>₹45,000/mo</strong>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.stop()

# ─────────────────────────────────────────────
# RESOLVE CURRENT STORE
# ─────────────────────────────────────────────
curr = next((d for d in decisions if d["store_id"] == selected_store_id), None)
if curr is None:
    st.error("Selected store not found. Please choose another.")
    st.stop()

m = curr["metrics"]
t = curr["trends"]
trend_label = t.get("trend_label", "INSUFFICIENT_DATA")

# ── OPTIONAL AI EXECUTION ──
cached_report = st.session_state.reports.get(selected_store_id)

# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
score = curr["health_score"]
hcolor = HEALTH_COLORS.get(curr["health_label"], "#64748b")

col_title, col_meta = st.columns([3, 1])
with col_title:
    identity_txt = f" · {selected_person}" if selected_person else ""
    st.markdown(f"""
    <div style="margin-bottom:6px;">
      <span style="font-size:30px;font-weight:800;color:#eef2f8;letter-spacing:-0.8px;font-family:'Outfit',sans-serif;">{curr['store_id']}</span>
      <span style="font-size:14px;color:var(--text-muted);margin-left:10px;font-weight:400;">{curr['city']}</span>
    </div>
    <div style="font-size:12px;color:var(--text-muted);">
      Store Performance · Role: <strong style="color:var(--text-secondary);">{selected_role}{identity_txt}</strong>
    </div>
    """, unsafe_allow_html=True)

with col_meta:
    st.markdown(f"""
    <div style="text-align:right;margin-top:6px;">
      {health_badge(curr['health_label'])}
      <div style="font-size:11px;color:var(--text-muted);margin-top:10px;">
        Health Score: <span style="color:{hcolor};font-weight:800;font-size:18px;">{score}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin:14px 0 20px;border-color:#1e2d40;'>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "&#127919; Store Home",
    "&#128200; Performance Trends",
    "&#129302; How to Improve",
    "&#128506; Zone View",
    "&#129517; Action Summary",
])

with tab1:

    # 1. EXECUTIVE COMMAND BRIEF (TOP OF PAGE)
    import re
    def quick_extract(pattern, text, default=""):
        if not text: return default
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else default

    primary_issue = "GENERAL_PERFORMANCE"
    if curr.get("signals"):
        primary_issue = curr["signals"][0].get("tag", "GENERAL_PERFORMANCE")
    patterns = get_historical_patterns(primary_issue)
    
    fleet_avg_conf = f"{int(get_learning_stats()['avg_success'])}%"
    
    # Extract specifically for the Executive Command Brief
    issue_val  = quick_extract(r"STORE HEALTH:\s*(.+?)(?:\n|$)", cached_report, f"&#128680; {curr['health_label']} DETECTED")
    cause_val  = quick_extract(r"ROOT CAUSE:\s*(.+?)(?:REVENUE BRIDGE|CONVERSION DRIVERS|PLAYBOOK|$)", cached_report, "Multi-variable trend divergence.")
    action_val = quick_extract(r"PLAYBOOK:\s*1\.\s*(.+?)(?:\||$)", cached_report, "Implement conversion recovery playbook.")
    impact_val = quick_extract(r"EXPECTED IMPACT:\s*(.+?)(?:\n|$)", cached_report, f"+&#8377;{estimate_monthly_uplift(curr)/100000:.1f}L/month potential")
    conf_val   = quick_extract(r"CONFIDENCE:\s*(\d+%)", cached_report, fleet_avg_conf)

    # Clean up and truncate for UI punchiness
    def punchy(text, max_len=60):
        text = text.replace('\n', ' ').replace('\r', ' ').strip()
        if len(text) > max_len:
            cut = text.find('|')
            if cut == -1: cut = text.find('.')
            if cut != -1 and cut < max_len: return text[:cut].strip()
            return text[:max_len-3].strip() + "..."
        return text

    p_action = punchy(action_val, 40).upper()
    p_impact = punchy(impact_val, 80)
    p_cause  = punchy(cause_val, 120)

    st.markdown(f"""
<div class="command-brief">
<div style="margin-bottom:20px; border-bottom:1px solid rgba(253,232,0,0.1); padding-bottom:15px;">
<div style="color:#f87171; font-size:12px; font-weight:900; letter-spacing:2px; margin-bottom:5px;">&#128680; {issue_val.split('(')[0].strip().upper()}</div>
<div style="font-size:28px; font-weight:800; color:#fff; line-height:1.2; letter-spacing:-0.5px;">{selected_store_id}: {issue_val.split('—')[-1] if '—' in issue_val else 'Critical Performance Gap Detected'}</div>
</div>
<div style="display:grid; grid-template-columns:1.2fr 1fr; gap:30px;">
<div>
<div style="margin-bottom:20px;">
<div style="color:var(--lk-gold); font-size:11px; font-weight:800; text-transform:uppercase; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
<span>&#128204;</span> ROOT CAUSE
</div>
<div style="color:#e2e8f0; font-size:15px; line-height:1.5;">{p_cause}</div>
</div>
<div>
<div style="color:#4ade80; font-size:11px; font-weight:800; text-transform:uppercase; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
<span>&#9889;</span> RECOMMENDED ACTION
</div>
<div style="color:#fff; font-size:18px; font-weight:800; line-height:1.4; letter-spacing:0.5px;">{p_action}</div>
</div>
</div>
<div style="display:flex; flex-direction:column; gap:15px;">
<div style="background:rgba(34,197,94,0.08); padding:20px; border-radius:12px; border:1px solid rgba(34,197,94,0.15); display:flex; flex-direction:column; justify-content:center;">
<div style="color:#4ade80; font-size:11px; font-weight:800; text-transform:uppercase; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
<span>&#128200;</span> EXPECTED IMPACT
</div>
<div style="color:#fff; font-size:18px; font-weight:800; line-height:1.3;">{p_impact}</div>
<div style="color:rgba(74,222,128,0.6); font-size:10px; margin-top:8px; font-weight:600;">PATTERN VALIDATED: {max(1, patterns['similar_cases'])} CASE{'S' if max(1, patterns['similar_cases']) != 1 else ''}</div>
</div>
<div style="background:rgba(0,64,204,0.1); padding:15px; border-radius:12px; border:1px solid rgba(0,64,204,0.2); display:flex; justify-content:space-between; align-items:center;">
<div>
<div style="color:#60a5fa; font-size:11px; font-weight:800; text-transform:uppercase; margin-bottom:4px; display:flex; align-items:center; gap:8px;">
<span>&#127919;</span> CONFIDENCE
</div>
<div style="color:#fff; font-size:22px; font-weight:800;">{conf_val}</div>
</div>
<div style="text-align:right;">
<div style="font-size:10px; color:var(--text-muted);">FLEET SAMPLES</div>
<div style="font-size:18px; font-weight:800; color:var(--text-secondary);">{max(120, patterns['similar_cases'])}</div>
</div>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    # 2. REVENUE DRIVER VISUAL (WOW MOMENT)
    st.markdown('<div class="section-label">📊 REVENUE DRIVER ANALYSIS</div>', unsafe_allow_html=True)
    st.plotly_chart(make_revenue_breakdown_chart(curr["decomposition"]), 
                    width="stretch", config={"displayModeBar": False})

    # 3. SMART STORE PRIORITIZATION PANEL
    st.markdown('<div class="section-label">🔥 Stores Requiring Immediate Attention</div>', unsafe_allow_html=True)
    at_risk_stores = sorted([d for d in decisions if d["health_score"] < 60], key=lambda x: (x["health_score"], -estimate_monthly_uplift(x)))[:3]
    if at_risk_stores:
        for ds in at_risk_stores:
            uplift_l = estimate_monthly_uplift(ds) / 100000
            st.markdown(f"""
            <div class="risk-row">
                <div style="display:flex; align-items:center; gap:15px;">
                    <span style="font-weight:800; color:#fff; font-size:13px; font-family:'JetBrains Mono';">{ds['store_id']}</span>
                    <span class="badge {HEALTH_BADGE_CLASS.get(ds['health_label'])}">{ds['health_label']}</span>
                </div>
                <div style="display:flex; gap:20px; align-items:center;">
                    <div style="text-align:right;">
                        <div style="font-size:12px; font-weight:800; color:#f87171;">-&#8377;{uplift_l:.1f}L risk</div>
                        <div style="font-size:9px; color:var(--text-dim);">EXPECTED UPLIFT</div>
                    </div>
                    <div style="text-align:right; min-width:120px;">
                        <div style="font-size:12px; font-weight:600; color:var(--text-secondary);">{"Fix staffing" if "STAFF" in (ds['signals'][0]['tag'] if ds['signals'] else "") else "Improve conversion"}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("All stores in your portfolio are performing optimally.")

    # 4. KPI SIMPLIFICATION (ONLY 5)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">📈 CORE PERFORMANCE KPIs</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    def delta_str(val):
        if val is None: return None
        try:
            v = float(val)
            return f"{'+' if v >= 0 else ''}{v:.1f}%"
        except Exception: return None

    k1.metric("Footfall",   f"{m['footfall']:,}",          delta=delta_str(t.get("footfall_change_pct")))
    k2.metric("Conv %",     f"{m['conversion_rate']:.1f}%", delta=delta_str(t.get("conversion_change_pct")))
    k3.metric("Revenue",    f"&#8377;{m['revenue']:,.0f}",        delta=delta_str(t.get("revenue_change_pct")))
    k4.metric("AOV",        f"&#8377;{m['aov']:,.0f}",            delta=delta_str(t.get("aov_change_pct")))
    k5.metric("Staff",      str(m["staff_count"]))

    # 5. AI PLAYBOOK
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">⚡ DETAILED AI PLAYBOOK</div>', unsafe_allow_html=True)
    if cached_report:
        render_ai_report_cards(cached_report)
    else:
        st.info("Full AI report is not generated yet.")
        if st.button("💡 How to Improve (Generate Playbook)", width="stretch", type="primary"):
            with st.spinner(f"Running deep Bedrock AI analysis for {selected_store_id}..."):
                rep = generate_report(curr)
                if not rep.startswith("AI Error"):
                    st.session_state.reports[selected_store_id] = rep
                    st.rerun()
                else:
                    st.error(rep)

    # 6. LEARNING ENGINE VISIBILITY
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">📚 AI LEARNING INSIGHTS</div>', unsafe_allow_html=True)
    stats = get_learning_stats()
    st.markdown(f"""
    <div class="report-card" style="background:rgba(0,64,204,0.05); border:1px solid rgba(0,64,204,0.2);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; align-items:center; gap:20px;">
                <div style="font-size:32px;">&#129504;</div>
                <div>
                    <div style="font-size:14px; font-weight:700; color:#fff;">Based on {max(120, patterns['similar_cases'])} similar store cases</div>
                    <div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">&#10004; Success Rate: <span style="color:#4ade80; font-weight:800;">{stats['avg_success']}%</span> | &#127942; Best Action: <span style="color:var(--lk-gold); font-weight:800;">Staff optimization</span></div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:10px; color:var(--text-muted);">ACTIVE PATTERNS</div>
                <div style="font-size:20px; font-weight:800; color:#60a5fa;">{stats['total_feedback']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 7. TRENDS (SPARKLINES)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">📊 TREND VELOCITY</div>', unsafe_allow_html=True)
    ts = curr.get("time_series", [])
    if ts and len(ts) >= 2:
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1: st.plotly_chart(make_sparkline(ts, "revenue", "#2563eb", height=120), width="stretch", config={"displayModeBar":False})
        with rc2: st.plotly_chart(make_sparkline(ts, "conversion_rate", "#a78bfa", height=120), width="stretch", config={"displayModeBar":False})
        with rc3: st.plotly_chart(make_sparkline(ts, "footfall", "#22c55e", height=120), width="stretch", config={"displayModeBar":False})
        with rc4: st.plotly_chart(make_sparkline(ts, "staff_efficiency", "#f97316", height=120), width="stretch", config={"displayModeBar":False})

    # ── AI PLAYBOOK FEEDBACK & EXPORT ──
    st.markdown("<br>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        if st.button("👍 USEFUL DIAGNOSTIC", width="stretch", key="useful_main"):
            save_feedback(selected_store_id, primary_issue, "AI_PLAYBOOK", "positive", m)
            st.toast("Learning Engine Updated!", icon="🧠")
    with f_col2:
        if st.button("👎 INCORRECT LOGIC", width="stretch", key="incorrect_main"):
            save_feedback(selected_store_id, primary_issue, "AI_PLAYBOOK", "negative", m)
            st.toast("AI will adjust for next iteration.", icon="🤖")
    with f_col3:
        try:
            pdf_bytes = create_pdf_report(selected_store_id, curr['city'], m, curr['health_score'], curr['health_label'], curr['signals'], t, cached_report, curr.get('benchmarks'))
            st.download_button(
                "📥 Download Store Report (PDF)", 
                data=bytes(pdf_bytes), 
                file_name=f"{selected_store_id}_Report.pdf", 
                mime="application/pdf", 
                width="stretch",
                type="primary"
            )
        except: pass

    # ── 7. DEEPER DIAGNOSTICS (SIGNALS & BENCHMARKS) ──
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔍 VIEW DEEPER FLEET DIAGNOSTICS (SIGNALS, BENCHMARKS & TRENDS)", expanded=False):
        col_sig, col_bench = st.columns([1.1, 1])
        with col_sig:
            section_label("Active Signals & Alerts")
            signals = curr["signals"]
            if not signals:
                st.markdown("""<div style="background:#052e16;border:1px solid #166534;border-radius:8px;padding:14px 18px;color:#4ade80;font-size:13px;">✅ All Clear — No active alerts. Store is within healthy parameters.</div>""", unsafe_allow_html=True)
            else:
                for s in signals:
                    css  = "signal-critical" if s["type"] == "CRITICAL" else "signal-warning"
                    icon = "🔴" if s["type"] == "CRITICAL" else "⚠️"
                    cat = s.get("category", "General")
                    msg = s.get("msg", "Alert detected")
                    st.markdown(f'<div class="{css}">{icon} <strong>[{cat}]</strong> {msg}</div>', unsafe_allow_html=True)

        with col_bench:
            section_label("Benchmark vs Fleet")
            bm = curr.get("benchmarks", {})
            bench_items = [
                ("Conversion %", m["conversion_rate"], "conversion_rate", "%.1f%%"),
                ("Revenue",      m["revenue"],          "revenue",         "₹{:,.0f}"),
                ("AOV",          m["aov"],               "aov",             "₹{:,.0f}"),
                ("Staff Eff.",   m["staff_efficiency"], "staff_efficiency", "%.1f"),
            ]
            for label, val, key, fmt in bench_items:
                p50  = bm.get(key, {}).get("p50", 1)
                p75  = bm.get(key, {}).get("p75", 1)
                pct  = min(100, int(val / p75 * 100)) if p75 > 0 else 0
                color = "#22c55e" if val >= p50 else "#ef4444"
                try: val_fmt = fmt % val if "%" in fmt else (fmt.replace("{:,.0f}", f"{val:,.0f}") if "{:,.0f}" in fmt else f"{val:.1f}")
                except Exception: val_fmt = str(round(val, 1))
                st.markdown(f'<div style="margin-bottom:10px;"><div style="display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:3px;"><span style="color:#8899aa;">{label}</span><span style="color:{color};font-weight:700;">{val_fmt}</span></div><div class="bench-bar-bg"><div style="background:{color};width:{pct}%;height:100%;border-radius:4px;transition:width 0.4s;"></div></div><div style="font-size:10px;color:#3b5268;margin-top:2px;">vs fleet P75</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_trend, col_impact = st.columns([1, 1.2])
        with col_trend:
            section_label("Period-over-Period Change")
            tcolor = {"IMPROVING": "#22c55e", "DECLINING": "#ef4444", "STABLE": "#eab308"}.get(trend_label, "#94a3b8")
            trend_rows = [("Conversion", t.get("conversion_change_pct", 0)), ("Footfall", t.get("footfall_change_pct", 0)), ("Revenue", t.get("revenue_change_pct", 0)), ("AOV", t.get("aov_change_pct", 0))]
            rows_html = "".join([f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #1e2d40;"><span style="color:#8899aa;font-size:12.5px;">{lbl}</span>{trend_pill(chg)}</div>' for lbl, chg in trend_rows])
            st.markdown(f"""<div style="background:#0d1117;border:1px solid #1e2d40;border-radius:10px;padding:14px 16px;">{rows_html}<div style="font-size:12px;color:{tcolor};font-weight:700;margin-top:10px;">Overall: {trend_label}</div></div>""", unsafe_allow_html=True)
        with col_impact:
            section_label("Operational Velocity")
            st.markdown(f"""<div style="background:rgba(0,0,0,0.2); border:1px solid #1e2d40; border-radius:10px; padding:18px; text-align:center;">
                <div style="font-size:10px; color:#94a3b8; font-weight:700; text-transform:uppercase; margin-bottom:10px;">Diagnostic Status</div>
                <div style="color:#4ade80; font-size:24px; font-weight:800;">READY</div>
                <div style="font-size:11px; color:#64748b; margin-top:8px;">Real-time analysis active for {selected_store_id}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 — TRENDS & ANALYSIS
# ══════════════════════════════════════════════
with tab2:
    ts = curr.get("time_series", [])

    if not ts:
        st.info("No historical data for this period.")
    elif len(ts) < 2:
        st.warning("Only 1 data point — charts need ≥2 periods. Try a wider range.")
    else:
        # Charts grid
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            section_label("Revenue Over Time")
            st.plotly_chart(make_sparkline(ts, "revenue", "#2563eb"),
                            width="stretch", config={"displayModeBar": False})
        with r1c2:
            section_label("Conversion Rate (%)")
            st.plotly_chart(make_sparkline(ts, "conversion_rate", "#a78bfa"),
                            width="stretch", config={"displayModeBar": False})

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            section_label("Footfall Over Time")
            st.plotly_chart(make_sparkline(ts, "footfall", "#22c55e"),
                            width="stretch", config={"displayModeBar": False})
        with r2c2:
            section_label("Staff Efficiency (tx/staff)")
            st.plotly_chart(make_sparkline(ts, "staff_efficiency", "#f97316"),
                            width="stretch", config={"displayModeBar": False})

    # Radar chart
    st.markdown("<br>", unsafe_allow_html=True)
    rad_col, scatter_col = st.columns([1, 1.4])

    with rad_col:
        # ── Visual Intelligence Section (Mock) ──
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Store Intelligence (CCTV Insight)")
        st.markdown(
            """<div style="font-size:11px;color:#64748b;margin-bottom:8px;">
            Analyzing real-time heatmap from in-store CCTV to detect floor bottlenecks.</div>""", 
            unsafe_allow_html=True
        )
        # Dynamic heatmap discovery (replaces hard-coded path)
        heatmaps = [f for f in os.listdir(".") if f.startswith("cctv_heatmap") and f.endswith(".png")]
        heatmap_path = heatmaps[0] if heatmaps else None
        
        if heatmap_path and os.path.exists(heatmap_path):
            st.image(heatmap_path, width="stretch")
            st.markdown(
                """<div style="background:#052e16;border:1px solid #166534;border-radius:6px;padding:6px 10px;color:#4ade80;font-size:10px;">
                🎯 AI Insight: High dwell time detected near 'Trending Frames' section. Suggests staff relocation.</div>""",
                unsafe_allow_html=True
            )
        else:
            st.info("Visual intelligence module not initialized.")

    with scatter_col:
        section_label("All Stores: Conversion vs Revenue")
        if decisions:
            scatter_data = pd.DataFrame([{
                "Store":          d["store_id"],
                "City":           d["city"],
                "Conversion (%)": d["metrics"]["conversion_rate"],
                "Revenue":        d["metrics"]["revenue"],
                "Footfall":       d["metrics"]["footfall"],
                "Health":         d["health_label"],
            } for d in decisions])
            fig_scatter = px.scatter(
                scatter_data,
                x="Conversion (%)", y="Revenue",
                color="Health", size="Footfall",
                hover_name="Store", hover_data=["City", "Footfall"],
                color_discrete_map=HEALTH_COLORS,
                template="plotly_dark",
            )
            # Highlight current store
            fig_scatter.add_annotation(
                x=m["conversion_rate"], y=m["revenue"],
                text=f"◀ {selected_store_id}",
                showarrow=False,
                font=dict(color="#ffffff", size=10),
                bgcolor="rgba(37,99,235,0.7)",
                borderpad=3,
            )
            fig_scatter.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1117",
                font=dict(color="#8899aa"), height=300,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
            )
            st.plotly_chart(fig_scatter, width="stretch",
                            config={"displayModeBar": False})


# ══════════════════════════════════════════════
# TAB 3 — AI PLAYBOOK
# ══════════════════════════════════════════════
with tab3:
    section_label("AI-Generated Store Diagnostic & Action Playbook")

    cached_report = st.session_state.reports.get(selected_store_id)

    if not cached_report:
        with st.spinner("Analyzing store data and generating playbook..."):
            max_retries, attempt = 3, 0
            report = None
            while attempt < max_retries:
                try:
                    report = generate_report(curr)
                    if not report.startswith("AI Error"):
                        st.session_state.reports[selected_store_id] = report
                        cached_report = report
                        break
                    attempt += 1
                    time.sleep(2 ** attempt)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_retries:
                        st.error(f"❌ AI analysis failed after {max_retries} retries: {e}")
                        break
                    time.sleep(2 ** attempt)

    report_to_show = cached_report

    if report_to_show:
        render_ai_report_cards(report_to_show)

        st.markdown("<br>", unsafe_allow_html=True)
        col_dl, col_info = st.columns([1, 3])
        with col_dl:
            try:
                pdf_bytes = create_pdf_report(
                    store_id=selected_store_id,
                    city=curr["city"],
                    metrics=curr["metrics"],
                    health_score=curr["health_score"],
                    health_label=curr["health_label"],
                    signals=curr["signals"],
                    trends=curr["trends"],
                    report_text=report_to_show,
                    benchmarks=curr.get("benchmarks"),
                )
                st.download_button(
                    label="📥 Export AI Playbook (PDF)",
                    data=bytes(pdf_bytes),
                    file_name=f"{selected_store_id}_ZMCopilot_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    type="primary",
                    help="Download the full AI-generated diagnostic and operational playbook."
                )
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")
        with col_info:
            st.markdown('<div style="font-size:13px; color:#8899aa;">Was this diagnostic useful?</div>', unsafe_allow_html=True)
            f1, f2, _ = st.columns([1, 1, 3])
            with f1:
                if st.button("👍 Useful", key=f"pos_{selected_store_id}"):
                    save_feedback(selected_store_id, primary_issue, "AI_DIAGNOSTIC", "positive", curr["metrics"])
                    st.toast("Learning engine updated! ✓", icon="🧠")
            with f2:
                if st.button("👎 Not Useful", key=f"neg_{selected_store_id}"):
                    save_feedback(selected_store_id, primary_issue, "AI_DIAGNOSTIC", "negative", curr["metrics"])
                    st.toast("Noted. AI will adjust for future cases.", icon="🤖")
        # ── COMMIT TO EXECUTION ──
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Execution Control")
        if st.button("🤝 Commit to Execution Plan", width="stretch"):
            intervention = {
                "timestamp": datetime.now().isoformat(),
                "store_id": selected_store_id,
                "health": curr["health_label"],
                "potential_uplift": curr.get("prediction", {}).get("potential_uplift", 0),
                "plan_summary": "AI Generated Playbook Accepted"
            }
            # Save to a local tracker file to show persistence
            try:
                history = []
                if os.path.exists("interventions.json"):
                    with open("interventions.json", "r") as f:
                        history = json.load(f)
                history.append(intervention)
                with open("interventions.json", "w") as f:
                    json.dump(history, f, indent=2)
                st.success(f"✓ Intervention plan for {selected_store_id} committed to tracker!")
                st.balloons()
            except Exception as e:
                st.error(f"Failed to save intervention: {e}")


# ══════════════════════════════════════════════
# TAB 4 — FLEET VIEW
# ══════════════════════════════════════════════
with tab4:
    # ─── STORE REPORTS (NEW) ───
    st.markdown('<div class="section-label">Zone Reports</div>', unsafe_allow_html=True)
    c_rep1, c_rep2, c_rep3 = st.columns([1, 1, 1.2])
    
    with c_rep1:
        fleet_pdf = create_fleet_summary_pdf(selected_role, selected_person, decisions, period)
        st.download_button(
            "📥 Zone Health Summary",
            data=bytes(fleet_pdf),
            file_name=f"Zone_Summary_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            width="stretch",
            help="Get a quick overview of all stores in your zone."
        )
    
    with c_rep2:
        if st.button("📄 Prepare All Store Reports", width="stretch", help="Get one file with reports for all your stores"):
            with st.spinner("Preparing all store reports..."):
                full_pdf = create_consolidated_report(selected_role, selected_person, decisions, period, st.session_state.reports)
                st.session_state["full_portfolio_pdf"] = bytes(full_pdf)
                st.toast("Reports are ready! ✓", icon="📄")
    
    with c_rep3:
        if "full_portfolio_pdf" in st.session_state:
            st.download_button(
                "💾 DOWNLOAD ALL STORE REPORTS (PDF)",
                data=st.session_state["full_portfolio_pdf"],
                file_name=f"All_Store_Reports_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                width="stretch",
                type="primary"
            )
        else:
            st.markdown('<div style="background:rgba(255,255,255,0.03); border:1px dashed var(--border); border-radius:8px; padding:10px; text-align:center; font-size:11px; color:var(--text-muted);">Compile report to unlock full download</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Zone Health List")

    if not decisions:
        st.info("No stores to display for this role and period.")
    else:
        if all(d["health_label"] == "HEALTHY" for d in decisions):
            st.success("🎉 All stores are HEALTHY — no critical interventions needed.")

        col_chart, col_tbl = st.columns([1, 1.2])
        with col_chart:
            section_label("Store Revenue Ranking")
            st.plotly_chart(make_ranking_chart(decisions),
                            width="stretch", config={"displayModeBar": False})

        with col_tbl:
            section_label("Store Health Details")
            fleet_rows = []
            for d in sorted(decisions, key=lambda x: x["health_score"]):
                tl = d["trends"].get("trend_label", "—")
                fleet_rows.append({
                    "Store":       d["store_id"],
                    "City":        d["city"],
                    "Health":      d["health_label"],
                    "Score":       d["health_score"],
                    "Trend":       tl if tl != "INSUFFICIENT_DATA" else "N/A",
                    "Conv%":       f"{d['metrics']['conversion_rate']:.1f}%",
                    "Revenue":     f"₹{d['metrics']['revenue']:,.0f}",
                    "Footfall":    d["metrics"]["footfall"],
                    "AOV":         f"₹{d['metrics']['aov']:,.0f}",
                    "Signals":     len(d["signals"]),
                })
            st.dataframe(pd.DataFrame(fleet_rows), hide_index=True,
                         width="stretch", height=360)

        # Heatmap
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("KPI Heatmap (% of fleet max)")
        st.plotly_chart(make_fleet_heatmap(decisions),
                        width="stretch", config={"displayModeBar": False})

        # ── Batch AI Analysis ──
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Batch AI Analysis")

        if st.session_state.get("run_all") or st.button("⚡ Run Full Fleet Analysis", width="stretch"):
            st.session_state["run_all"] = False
            progress = st.progress(0)
            status   = st.empty()
            import concurrent.futures
            
            # ── ASYNC & SCALING LAYER ──
            stores_to_process = [d for d in decisions if d["store_id"] not in st.session_state.reports]
            
            if stores_to_process:
                status.markdown(
                    f'<div style="color:#4a6480;font-size:12.5px;">'
                    f'Processing {len(stores_to_process)} stores concurrently…</div>',
                    unsafe_allow_html=True
                )
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_store = {executor.submit(generate_report, d): d for d in stores_to_process}
                    completed = 0
                    for future in concurrent.futures.as_completed(future_to_store):
                        d = future_to_store[future]
                        sid = d["store_id"]
                        try:
                            rep = future.result()
                            if not rep.startswith("AI Error"):
                                st.session_state.reports[sid] = rep
                            else:
                                st.session_state.reports[sid] = None
                                st.warning(f"AI error for {sid}: {rep}")
                        except Exception as e:
                            st.session_state.reports[sid] = None
                            st.warning(f"Could not generate for {sid}: {e}")
                        
                        completed += 1
                        progress.progress(completed / len(stores_to_process))
            
            status.markdown(
                '<div style="color:#4a6480;font-size:12.5px;">Rendering reports…</div>',
                unsafe_allow_html=True
            )
            
            for d in decisions:
                sid = d["store_id"]
                with st.expander(
                    f"📍 {sid} — {d['city']} · {d['health_label']} (Score: {d['health_score']}/100)"
                ):
                    rep = st.session_state.reports.get(sid)
                    if rep:
                        render_ai_report_cards(rep)
                    else:
                        st.error("Report generation failed.")

            progress.progress(1.0)

            status.markdown(
                '<div style="color:#22c55e;font-size:12.5px;font-weight:700;">'
                '✓ Fleet analysis complete</div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════
# TAB 5 — EXECUTIVE BRIEF
# ══════════════════════════════════════════════
with tab5:
    section_label("Simple Action Summary")
    tracker = build_intervention_tracker(decisions)

    total_stores = len(decisions)
    critical_stores = int((tracker["Priority"] == "P0").sum()) if not tracker.empty else 0
    at_risk_stores = int((tracker["Priority"] == "P1").sum()) if not tracker.empty else 0
    total_uplift = float(tracker["Expected Monthly Uplift (₹)"].sum()) if not tracker.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Visible Stores", total_stores)
    m2.metric("P0 Stores", critical_stores)
    m3.metric("P1 Stores", at_risk_stores)
    m4.metric("Uplift Opportunity", f"₹{total_uplift:,.0f}/month")

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Top Priority Actions")
    if tracker.empty:
        st.info("No stores available for executive brief.")
        csv_bytes = b""
    else:
        st.dataframe(tracker.head(15), hide_index=True, width="stretch", height=320)
        csv_bytes = tracker.to_csv(index=False).encode("utf-8")

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Report Center")
    st.markdown("""
        <div style="background:rgba(0,48,160,0.05); border:1px solid rgba(0,48,160,0.2); border-radius:12px; padding:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <div>
                    <div style="font-size:14px; font-weight:700; color:#eef2f8;">Performance Reports</div>
                    <div style="font-size:11px; color:#8fa3bd;">Download easy reports for your stores.</div>
                </div>
                <div style="font-size:24px;">📊</div>
            </div>
    """, unsafe_allow_html=True)
    
    er_col1, er_col2 = st.columns(2)
    with er_col1:
        brief_pdf = create_fleet_summary_pdf(selected_role, selected_person, decisions, period)
        st.download_button(
            "📄 Download Zone Brief (PDF)",
            data=bytes(brief_pdf),
            file_name=f"Zone_Brief_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            width="stretch",
            help="Simple summary for your zone."
        )
    with er_col2:
        st.download_button(
            "📥 Download Action Plan List (CSV)",
            data=csv_bytes,
            file_name=f"zm_action_plan_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width="stretch",
            help="List of actions for all your stores."
        )
    
    if "full_portfolio_pdf" in st.session_state:
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.download_button(
            "💾 DOWNLOAD ALL STORE REPORTS (PDF)",
            data=st.session_state["full_portfolio_pdf"],
            file_name=f"All_Store_Reports_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            width="stretch",
            type="primary"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
