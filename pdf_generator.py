from fpdf import FPDF
from datetime import datetime
import re


class LenskartReport(FPDF):
    def __init__(self, store_id, city):
        super().__init__()
        self.store_id = store_id
        self.city = city
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(auto=True, margin=22)

    def header(self):
        # ── Navy gradient bar ──
        self.set_fill_color(0, 0, 48)
        self.rect(0, 0, 210, 14, "F")
        # Gold accent stripe
        self.set_fill_color(253, 232, 0)
        self.rect(0, 14, 210, 1.8, "F")
        # Header text
        self.set_font("Arial", "B", 7.5)
        self.set_text_color(255, 255, 255)
        self.set_y(4)
        self.cell(0, 6, "LENSKART   ZM COPILOT   |   STORE PERFORMANCE REPORT   |   CONFIDENTIAL", 0, 0, "C")
        self.set_text_color(0, 0, 0)
        self.ln(18)

    def footer(self):
        self.set_y(-12)
        self.set_fill_color(8, 12, 22)
        self.rect(0, self.get_y(), 210, 14, "F")
        self.set_font("Arial", "I", 7)
        self.set_text_color(120, 140, 170)
        ts = datetime.now().strftime("%d %b %Y  %H:%M")
        self.cell(0, 6, f"Confidential  -  AI-Generated  -  {ts}  -  Page {self.page_no()}", 0, 0, "C")
        self.set_text_color(0, 0, 0)

    def section_header(self, title, color=(15, 23, 42), icon=""):
        self.ln(4)
        # Left accent stripe
        self.set_fill_color(253, 232, 0)
        self.rect(18, self.get_y(), 2.5, 6, "F")
        # Background
        self.set_fill_color(*color)
        self.rect(21, self.get_y(), 171, 6, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 8)
        self.set_xy(24, self.get_y())
        label = f"{icon}  {title}" if icon else title
        self.cell(0, 6, label, 0, 1, "L")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def metric_box(self, label, value, x, y, w=42, h=18, highlight=False, sub=None, accent_color=None):
        self.set_xy(x, y)
        # Background
        bg = (232, 242, 255) if highlight else (246, 249, 253)
        bd = accent_color if accent_color else ((59, 130, 246) if highlight else (215, 225, 240))
        self.set_fill_color(*bg)
        self.set_draw_color(*bd)
        self.rect(x, y, w, h, "DF")
        # Top accent line
        if accent_color:
            self.set_fill_color(*accent_color)
            self.rect(x, y, w, 1.5, "F")
        # Label
        self.set_xy(x + 2.5, y + 3)
        self.set_font("Arial", "", 6)
        self.set_text_color(100, 120, 145)
        self.cell(w - 5, 3, label.upper(), 0, 2)
        # Value
        self.set_xy(x + 2.5, y + 7)
        self.set_font("Arial", "B", 10)
        self.set_text_color(15, 23, 42)
        self.cell(w - 5, 6, str(value), 0, 0)
        # Sub
        if sub:
            self.set_xy(x + 2.5, y + 13.5)
            self.set_font("Arial", "", 5.5)
            self.set_text_color(140, 160, 180)
            self.cell(w - 5, 3, str(sub), 0, 0)
        self.set_text_color(0, 0, 0)

    def add_store_page(self, store_id, city, metrics, health_score, health_label,
                       signals, trends, report_text, benchmarks=None):
        self.add_page()
        # ─── TITLE BLOCK ───────────────────────────────────────────────────────────
        self.set_font("Arial", "B", 24)
        self.set_text_color(10, 16, 35)
        self.cell(0, 10, f"Store {store_id}", 0, 1)
        self.set_font("Arial", "", 9)
        self.set_text_color(90, 110, 135)
        self.cell(0, 5, f"{city}   -   Store Performance Summary   -   {datetime.now().strftime('%d %b %Y')}", 0, 1)
        self.ln(4)

        # Health badge pill + score bar
        hc = _health_color(health_label)
        # Pill
        self.set_fill_color(*hc)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 9)
        pill_w = 32
        self.cell(pill_w, 7, f"  {health_label}  ", 0, 0, "C", fill=True)

        self.set_text_color(60, 80, 100)
        self.set_font("Arial", "", 9)
        self.cell(8, 7, "")
        self.cell(45, 7, f"Health Score:  {health_score} / 100", 0, 0)

        # Score bar
        bar_x = self.get_x() + 2
        bar_y = self.get_y() + 2.5
        bar_w = 64
        self.set_fill_color(220, 228, 240)
        self.rect(bar_x, bar_y, bar_w, 3.5, "F")
        filled = int(bar_w * health_score / 100)
        self.set_fill_color(*hc)
        self.rect(bar_x, bar_y, filled, 3.5, "F")
        self.ln(11)

        # Divider
        self.set_draw_color(220, 228, 240)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(5)

        # ─── REVENUE AT RISK ALERT (P0/P1 only) ───────────────────────────────────
        if health_label in ("CRITICAL", "EMERGENCY"):
            risk_amt = metrics.get('revenue', 0) * 0.2
            self.set_fill_color(255, 237, 237)
            self.set_draw_color(*hc)
            self.set_line_width(0.6)
            self.rect(18, self.get_y(), 174, 11, "DF")
            self.set_line_width(0.2)
            # Red accent left bar
            self.set_fill_color(*hc)
            self.rect(18, self.get_y(), 3, 11, "F")
            self.set_xy(24, self.get_y() + 2.5)
            self.set_font("Arial", "B", 9)
            self.set_text_color(*hc)
            self.cell(0, 6, f"ALERT - ESTIMATED MONTHLY REVENUE AT RISK:  INR {risk_amt:,.0f}", 0, 1)
            self.ln(4)
            self.set_text_color(0, 0, 0)

        # ─── KPI METRICS GRID ─────────────────────────────────────────────────────
        self.section_header("KEY STORE NUMBERS", color=(10, 16, 35))
        y_grid = self.get_y()
        accent_seq = [
            (0, 48, 160), (0, 48, 160),
            (22, 163, 74), (22, 163, 74),
            (100, 116, 139), (100, 116, 139),
            (100, 116, 139), (100, 116, 139),
        ]
        boxes = [
            ("Footfall",        f"{metrics.get('footfall', 0):,}",              None,           False),
            ("Transactions",    f"{metrics.get('transactions', 0):,}",           None,           False),
            ("Revenue (INR)",   f"{metrics.get('revenue', 0):,.0f}",             None,           True),
            ("Conversion Rate", f"{metrics.get('conversion_rate', 0):.1f}%",    "Target: 15%",  True),
            ("Avg Order Value", f"INR {metrics.get('aov', 0):,.0f}",             None,           False),
            ("Staff Count",     str(metrics.get("staff_count", 0)),               None,           False),
            ("Rev / Visitor",   f"INR {metrics.get('revenue_per_visitor', 0):.0f}", None,        False),
            ("Staff Efficiency",f"{metrics.get('staff_efficiency', 0):.1f} tx/staff", None,     False),
        ]
        cols, w, gap = 4, 42, 2.5
        for i, (label, value, sub, hl) in enumerate(boxes):
            col = i % cols
            row = i // cols
            x   = 18 + col * (w + gap)
            yy  = y_grid + row * 22
            self.metric_box(label, value, x, yy, w=w, h=19, highlight=hl, sub=sub, accent_color=accent_seq[i] if hl else None)
        self.set_y(y_grid + (len(boxes) // cols) * 22 + 7)

        # ─── TREND ANALYSIS ────────────────────────────────────────────────────────
        self.section_header("TRENDS", color=(0, 40, 100))
        trend_label = trends.get("trend_label", "N/A")
        tc = _trend_color(trend_label)

        self.set_fill_color(*tc)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 8)
        self.cell(26, 6, f"  {trend_label}", 0, 0, "C", fill=True)
        self.ln(9)

        trend_items = [
            ("Conversion Rate", trends.get("conversion_change_pct", 0), "%"),
            ("Footfall",        trends.get("footfall_change_pct",   0), "%"),
            ("Revenue",         trends.get("revenue_change_pct",    0), "%"),
            ("Avg Order Value", trends.get("aov_change_pct",        0), "%"),
        ]
        for i, (label, val, unit) in enumerate(trend_items):
            col = i % 2
            if col == 0:
                self.set_x(18)
            else:
                self.set_x(110)
            self.set_font("Arial", "", 8)
            self.set_text_color(80, 100, 125)
            self.cell(48, 5, f"{label}:", 0, 0)
            color = (22, 163, 74) if val >= 0 else (185, 28, 28)
            self.set_text_color(*color)
            self.set_font("Arial", "B", 8)
            arrow = "(+)" if val >= 0 else "(-)"
            self.cell(30, 5, f"{arrow} {abs(val):.1f}{unit}", 0, 0)
            if col == 1:
                self.ln()
        self.set_text_color(0, 0, 0)
        self.ln(4)

        # ─── ACTIVE SIGNALS ────────────────────────────────────────────────────────
        if signals:
            self.section_header("IMPORTANT ALERTS", color=(110, 20, 20))
            for s in signals:
                stype = s.get("type", "INFO")
                is_crit = stype == "CRITICAL"
                if is_crit:
                    self.set_fill_color(255, 240, 240)
                    self.set_draw_color(200, 50, 50)
                    label_rgb = (200, 50, 50)
                else:
                    self.set_fill_color(255, 252, 235)
                    self.set_draw_color(200, 160, 10)
                    label_rgb = (200, 160, 10)

                # Left accent
                self.set_fill_color(*label_rgb)
                row_y = self.get_y()
                self.rect(18, row_y, 2.5, 7, "F")

                # Type label box
                self.set_fill_color(*([255, 240, 240] if is_crit else [255, 252, 235]))
                self.set_draw_color(*label_rgb)
                self.set_xy(21, row_y)
                self.set_font("Arial", "B", 7)
                self.set_text_color(*label_rgb)
                self.cell(16, 7, f" {stype}", 1, 0, "C", fill=True)

                cat = _safe_text(s.get("category", ""))
                msg = _safe_text(s.get("msg", ""))
                full = f"  [{cat}]  {msg}"

                self.set_fill_color(252, 254, 255)
                self.set_draw_color(210, 220, 235)
                self.set_text_color(30, 45, 65)
                self.set_font("Arial", "", 7.5)
                self.cell(0, 7, full[:120], 1, 1, "L", fill=True)
                self.set_text_color(0, 0, 0)
            self.ln(2)

        # ─── BENCHMARKING (NEW) ───────────────────────────────────────────────────
        if benchmarks:
            self.section_header("COMPARED TO OTHER STORES", color=(60, 80, 100))
            pdf_y = self.get_y()
            cols_b = [
                ("Metric", 60), ("Current", 38), ("City Avg", 38), ("Zonal Avg", 38)
            ]
            self.set_font("Arial", "B", 7.5)
            self.set_fill_color(240, 245, 250)
            for label, width in cols_b:
                self.cell(width, 7, f" {label}", 1, 0, "L", fill=True)
            self.ln()
            
            self.set_font("Arial", "", 7.5)
            for m_key, m_label in [("conversion_rate", "Conversion Rate (%)"), ("aov", "Avg Order Value (INR)"), ("revenue_per_visitor", "Rev per Visitor (INR)")]:
                if m_key in benchmarks:
                    b = benchmarks[m_key]
                    self.cell(60, 6, f" {m_label}", 1)
                    self.cell(38, 6, f" {b.get('current', 0):.1f}", 1, 0, "C")
                    self.cell(38, 6, f" {b.get('city_avg', 0):.1f}", 1, 0, "C")
                    self.cell(38, 6, f" {b.get('zone_avg', 0):.1f}", 1, 1, "C")
            self.ln(4)

        # ─── AI DIAGNOSTIC REPORT ─────────────────────────────────────────────────
        if report_text:
            self.section_header("AI RECOMMENDATIONS", color=(4, 30, 10))
            clean = report_text.encode("ascii", "ignore").decode("ascii")
            self.set_font("Arial", "", 8.5)
            self.set_text_color(30, 45, 65)

            section_headers = {
                "STORE HEALTH:", "TREND:", "ROOT CAUSE:", "REVENUE BRIDGE:",
                "CONVERSION DRIVERS:", "PLAYBOOK:", "EXPECTED IMPACT:", "CONFIDENCE:"
            }

            for line in clean.split("\n"):
                line = line.rstrip()
                if not line:
                    self.ln(2)
                    continue

                self.set_x(18)
                is_header = any(line.strip().startswith(h) for h in section_headers)

                if is_header:
                    self.set_font("Arial", "B", 8.5)
                    self.set_text_color(10, 20, 50)
                    self.multi_cell(0, 5, line.strip())
                    self.set_font("Arial", "", 8.5)
                    self.set_text_color(30, 45, 65)
                elif line.strip().startswith("---"):
                    self.set_draw_color(215, 225, 240)
                    self.line(18, self.get_y(), 192, self.get_y())
                    self.ln(2)
                elif re.match(r"^\s*[1-3]\.", line.strip()):
                    # Playbook numbered action
                    self.set_font("Arial", "B", 8.5)
                    self.set_text_color(0, 80, 180)
                    self.multi_cell(0, 5, line.strip())
                    self.set_font("Arial", "", 8.5)
                    self.set_text_color(30, 45, 65)
                elif line.strip().startswith(">") or line.strip().startswith("->"):
                    self.set_font("Arial", "I", 8)
                    self.set_text_color(80, 100, 130)
                    self.set_x(22)
                    self.multi_cell(0, 5, line.strip().lstrip(">-").strip())
                    self.set_font("Arial", "", 8.5)
                    self.set_text_color(30, 45, 65)
                else:
                    self.multi_cell(0, 5, line.strip())


def _safe_text(text):
    """Strip non-ASCII characters for FPDF compatibility."""
    return text.encode("ascii", "replace").decode("ascii").replace("?", "")


def _health_color(label):
    return {
        "HEALTHY":   (22, 163, 74),
        "AT RISK":   (202, 138, 4),
        "CRITICAL":  (194, 65, 12),
        "EMERGENCY": (185, 28, 28),
    }.get(label, (100, 116, 139))


def _trend_color(label):
    return {
        "IMPROVING": (22, 163, 74),
        "DECLINING": (185, 28, 28),
        "STABLE":    (202, 138, 4),
    }.get(label, (100, 116, 139))


def create_pdf_report(store_id, city, metrics, health_score, health_label,
                      signals, trends, report_text, benchmarks=None):
    pdf = LenskartReport(store_id, city)
    pdf.add_store_page(store_id, city, metrics, health_score, health_label,
                       signals, trends, report_text, benchmarks)
    return pdf.output()


def create_fleet_summary_pdf(role, person, decisions, period):
    pdf = LenskartReport("FLEET", "ALL CITIES")
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(10, 16, 35)
    pdf.cell(0, 10, "Zone Summary Report", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(90, 110, 135)
    identity = f" - {person}" if person else ""
    pdf.cell(0, 5, f"Role: {role}{identity}   -   {period} Analysis   -   {datetime.now().strftime('%d %b %Y')}", 0, 1)
    pdf.ln(6)

    # Summary Stats
    total_stores = len(decisions)
    if total_stores == 0:
        pdf.cell(0, 10, "No data available for the selected filters.", 0, 1)
        return pdf.output()

    critical = sum(1 for d in decisions if d["health_label"] in ("CRITICAL", "EMERGENCY"))
    at_risk = sum(1 for d in decisions if d["health_label"] == "AT RISK")
    total_rev = sum(d["metrics"]["revenue"] for d in decisions)
    avg_conv = sum(d["metrics"]["conversion_rate"] for d in decisions) / total_stores if total_stores > 0 else 0

    pdf.section_header("ZONE OVERVIEW", color=(10, 16, 35))
    y = pdf.get_y()
    pdf.metric_box("Total Stores", total_stores, 18, y, w=42, h=19)
    pdf.metric_box("Critical Stores", critical, 62.5, y, w=42, h=19, accent_color=(185, 28, 28) if critical > 0 else None)
    pdf.metric_box("At-Risk Stores", at_risk, 107, y, w=42, h=19, accent_color=(202, 138, 4) if at_risk > 0 else None)
    pdf.metric_box("Avg Fleet Conv%", f"{avg_conv:.1f}%", 151.5, y, w=42, h=19, highlight=True)
    pdf.ln(25)

    # Table of stores
    pdf.section_header("STORE HEALTH LIST", color=(0, 40, 100))
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 245, 250)
    pdf.cell(30, 7, " Store ID", 1, 0, "L", fill=True)
    pdf.cell(35, 7, " City", 1, 0, "L", fill=True)
    pdf.cell(30, 7, " Health", 1, 0, "C", fill=True)
    pdf.cell(20, 7, " Score", 1, 0, "C", fill=True)
    pdf.cell(30, 7, " Conv%", 1, 0, "C", fill=True)
    pdf.cell(29, 7, " Revenue (INR)", 1, 1, "R", fill=True)

    pdf.set_font("Arial", "", 7.5)
    # Sort critical first
    sorted_d = sorted(decisions, key=lambda x: x["health_score"])
    for d in sorted_d[:30]: # Limit to top 30 for summary
        pdf.cell(30, 6, f" {d['store_id']}", 1)
        pdf.cell(35, 6, f" {d['city']}", 1)
        
        hc = _health_color(d["health_label"])
        pdf.set_text_color(*hc)
        pdf.set_font("Arial", "B", 7.5)
        pdf.cell(30, 6, f" {d['health_label']}", 1, 0, "C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 7.5)
        
        pdf.cell(20, 6, f" {d['health_score']}", 1, 0, "C")
        pdf.cell(30, 6, f" {d['metrics']['conversion_rate']:.1f}%", 1, 0, "C")
        pdf.cell(29, 6, f" {d['metrics']['revenue']:,.0f} ", 1, 1, "R")
    
    if len(decisions) > 30:
        pdf.ln(2)
        pdf.set_font("Arial", "I", 7)
        pdf.cell(0, 6, f"... and {len(decisions)-30} more stores in full report", 0, 1, "C")

    return pdf.output()


def create_consolidated_report(role, person, decisions, period, reports_dict):
    pdf = LenskartReport("CONSOLIDATED", "FLEET")
    
    # ─── PREMIUM TITLE PAGE ──────────────────────────────────────────────────
    pdf.add_page()
    # Background for title page
    pdf.set_fill_color(0, 0, 48)
    pdf.rect(0, 0, 210, 297, "F")
    
    # Gold accent
    pdf.set_fill_color(253, 232, 0)
    pdf.rect(0, 140, 210, 2, "F")
    
    # Lenskart Logo / Branding
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 36)
    pdf.set_xy(0, 100)
    pdf.cell(210, 20, "ZM COPILOT", 0, 1, "C")
    
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(253, 232, 0)
    pdf.cell(210, 10, "ALL STORE PERFORMANCE REPORTS", 0, 1, "C")
    
    pdf.set_xy(0, 160)
    pdf.set_text_color(200, 210, 230)
    pdf.set_font("Arial", "B", 16)
    identity = f" | {person}" if person else ""
    pdf.cell(210, 10, f"{role}{identity}", 0, 1, "C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(150, 160, 180)
    pdf.cell(210, 10, f"Analysis Period: {period}   -   Generated: {datetime.now().strftime('%d %b %Y')}", 0, 1, "C")
    
    # ─── SUMMARY PAGE ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_header("ZONE PERFORMANCE SUMMARY", color=(10, 16, 35))
    
    total_stores = len(decisions)
    critical = sum(1 for d in decisions if d["health_label"] in ("CRITICAL", "EMERGENCY"))
    total_rev = sum(d["metrics"]["revenue"] for d in decisions)

    y = pdf.get_y()
    pdf.metric_box("Total Stores", total_stores, 18, y, w=58, h=22)
    pdf.metric_box("Critical Alerts", critical, 78.5, y, w=58, h=22, accent_color=(185, 28, 28))
    pdf.metric_box("Fleet Revenue", f"INR {total_rev:,.0f}", 139, y, w=53, h=22, highlight=True)
    pdf.ln(30)
    
    pdf.section_header("ZONE ANALYSIS", color=(10, 16, 35))
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(40, 50, 70)
    brief = f"This consolidated portfolio report provides a detailed performance diagnostic for the {total_stores} store locations " \
            f"currently under the jurisdiction of {role} {person if person else ''}. \n\n" \
            f"The primary objective of this intelligence report is to identify conversion degrowth drivers and surface " \
            f"actionable playbooks for immediate operational recovery. \n\n" \
            f"KEY FINDINGS:\n" \
            f"- {critical} stores are currently in CRITICAL or EMERGENCY status, requiring P0 intervention.\n" \
            f"- {sum(1 for d in decisions if d['health_label'] == 'AT RISK')} stores are AT RISK and should be monitored.\n" \
            f"- Total portfolio revenue being analyzed stands at INR {total_rev:,.0f} for the selected {period} period.\n\n" \
            f"The following pages contain individual Store Intelligence Reports generated by the ZM Copilot AI Engine."
    pdf.multi_cell(0, 6, brief)
    pdf.ln(10)
    
    # 2. Individual Store Pages
    # Sort so critical stores are at the beginning
    sorted_d = sorted(decisions, key=lambda x: x["health_score"])
    
    for d in sorted_d:
        store_id = d["store_id"]
        report_text = reports_dict.get(store_id, "AI analysis not generated for this store yet.")
        pdf.add_store_page(
            store_id=d["store_id"],
            city=d["city"],
            metrics=d["metrics"],
            health_score=d["health_score"],
            health_label=d["health_label"],
            signals=d["signals"],
            trends=d["trends"],
            report_text=report_text,
            benchmarks=d.get("benchmarks")
        )
        
    return pdf.output()