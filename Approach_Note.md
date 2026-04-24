# 1-Pager Approach Note

## Problem Statement
**Chosen Problem:** #26 Store Performance Diagnostic Agent (Base Points: 35 ⭐⭐⭐⭐⭐)
**Pain Point:** Manual store diagnosis requires 2-3 hours of manual data interpretation per store, leading to inconsistent root-cause tracing and delayed interventions for degrowing stores.
**Baseline Metric:** Diagnostic turnaround time of 2-3 hours per store.

## My Solution
I built ZM Copilot, an enterprise-grade Autonomous Intelligence Agent designed to identify store performance drivers, generate causal root-cause diagnostics, and produce actionable operational playbooks for Zonal Managers.
**Workflow:**
*   **Vectorized KPI Ingestion:** Automatically ingests and normalizes Parquet store data mapping over 15 operational metrics.
*   **Revenue Bridge Calculation:** Decomposes revenue shifts mathematically into Footfall, Conversion, and AOV drivers to identify primary operational leaks.
*   **Signal Detection:** Triggers based on 50+ pre-defined operational anomalies (e.g., QMS drop-offs, Staff inefficiency).
*   **Causal LLM Reasoning:** Passes the KPI vector and detected signals to Claude 3.7 to generate first-principles operational narratives.
*   **Learning Engine Feedback Loop:** Persists ZM feedback in a local SQLite database to refine playbook recommendations dynamically.

**AI/LLM Technique:** I used **Reasoning-on-Data** via AWS Bedrock (Claude 3.7) to analyze interactions between multiple metrics. Instead of a standard chatbot, I designed an advanced system prompt to construct causal chains and determine structural issues in-store without hallucinations. 

## Tech Stack
*   **Frontend UI:** Streamlit (Python), Plotly for visual dashboarding.
*   **Data Processing Engine:** Pandas, PyArrow (Parquet ingestion).
*   **AI/LLM Layer:** AWS Bedrock, Claude 3.7 (Anthropic Claude 3.5 Sonnet as fallback), Boto3.
*   **Learning Engine:** SQLite (local persistence).
*   **Document Generation:** FPDF2 for exporting branded diagnostic reports.

## Business Impact
*   **Metric Moved:** Diagnostic Turnaround Time.
*   **Impact Before/After:** Before: 2-3 hours of manual analysis per store. After: under 30 seconds for structured diagnostics + prioritized action plan. Delta: ~95% faster diagnostic turnaround.
*   **Quantified Savings:** Saves approximately 300 hours/month per ZM (150 stores × ~2 hours saved), representing ~$50k ops cost avoidance at scale.

## Assumptions & Limitations
*   **Assumptions:** The underlying Parquet data schema matches the exact Lenskart metrics alias mappings defined in `mapping.json`. It assumes timely AWS Bedrock API availability.
*   **Limitations & Production Needs:** Currently relies on a local SQLite database for the learning engine. For enterprise-wide deployment, this needs migration to a distributed database (e.g., PostgreSQL or DynamoDB). Real-time KPI streams (e.g., Kafka) should replace static Parquet ingestion for live insights.
