"""Scoring and Reporting Engine for WebPulse.

Calculates category scores, overall health and risk scores, and generates
reports in Console, JSON, Markdown, and premium HTML formats.
"""

import json
import logging
from typing import Any, ClassVar
from urllib.parse import parse_qsl, urlencode, urlparse

from webpulse.reports.schemas import Finding, Severity

logger = logging.getLogger("webpulse.reports.reporter")


class ReportGenerator:
    """Calculates audit metrics and exports results to multiple target formats."""

    SEVERITY_WEIGHTS: ClassVar[dict[Severity, float]] = {
        Severity.CRITICAL: 10.0,
        Severity.HIGH: 6.0,
        Severity.MEDIUM: 3.0,
        Severity.LOW: 1.0,
        Severity.INFO: 0.0,
    }

    CATEGORY_MULTIPLIERS: ClassVar[dict[str, float]] = {
        "security": 1.5,
        "performance": 1.2,
        "accessibility": 1.0,
        "seo": 0.8,
    }

    def __init__(
        self,
        target_url: str,
        scan_timestamp: str,
        duration_seconds: float,
        findings: list[Finding],
        auth_enabled: bool,
        auth_status: str,
        max_depth: int,
        max_pages: int,
        pages_discovered: int,
        pages_scanned: int,
        scanned_urls: list[str],
    ) -> None:
        """Initialize the ReportGenerator with scan parameters."""
        self.target_url = target_url
        self.scan_timestamp = scan_timestamp
        self.duration_seconds = round(duration_seconds, 2)
        self.findings = findings
        self.auth_enabled = auth_enabled
        self.auth_status = auth_status
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.pages_discovered = pages_discovered
        self.pages_scanned = pages_scanned
        self.scanned_urls = scanned_urls

        # Compile scores dictionary
        self.scores = self.calculate_scores()

    def _standardize_url(self, url: str) -> str:
        """Helper to standardize URLs for exact matching."""
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = parsed.path
            if path.endswith("/") and len(path) > 1:
                path = path[:-1]

            query_params = parse_qsl(parsed.query)
            query_params.sort()
            query = urlencode(query_params) if query_params else ""

            reconstructed = f"{scheme}://{netloc}{path}"
            if query:
                reconstructed += f"?{query}"
            return reconstructed
        except Exception:
            return url

    def _map_category(self, category: str) -> str:
        """Normalize category tags to match standard core scores."""
        c = category.lower().strip()
        if c in ("security", "waf", "ssl"):
            return "security"
        if c in ("performance", "http"):
            return "performance"
        if c in ("seo",):
            return "seo"
        if c in ("accessibility", "a11y"):
            return "accessibility"
        return "security"

    def calculate_scores(self) -> dict[str, Any]:
        """Apply mathematical formulas to calculate category and overall health scores."""
        std_root = self._standardize_url(self.target_url)

        # Distinguish between root page findings and subpage findings
        root_findings: dict[str, list[Finding]] = {
            "security": [],
            "performance": [],
            "accessibility": [],
            "seo": [],
        }
        subpages_findings: dict[str, dict[str, list[Finding]]] = {
            "security": {},
            "performance": {},
            "accessibility": {},
            "seo": {},
        }

        # Initialize unique subpages crawled list (excluding root)
        subpage_urls = set()
        for url in self.scanned_urls:
            std_url = self._standardize_url(url)
            if std_url != std_root:
                subpage_urls.add(std_url)

        # Group findings
        for f in self.findings:
            cat = self._map_category(f.category)
            std_f_url = self._standardize_url(f.target_url)

            if std_f_url == std_root:
                root_findings[cat].append(f)
            else:
                if std_f_url not in subpages_findings[cat]:
                    subpages_findings[cat][std_f_url] = []
                subpages_findings[cat][std_f_url].append(f)

        category_scores = {}
        for cat in ["security", "performance", "accessibility", "seo"]:
            mult = self.CATEGORY_MULTIPLIERS[cat]

            # Calculate Root Page score for this category
            root_deductions = 0.0
            for f in root_findings[cat]:
                weight = self.SEVERITY_WEIGHTS.get(f.severity, 0.0)
                root_deductions += weight * f.confidence * mult
            score_root = round(max(0.0, 100.0 - root_deductions))

            # Calculate Subpages scores for this category
            if subpage_urls:
                subpage_scores_list = []
                for std_url in subpage_urls:
                    sub_deductions = 0.0
                    sub_f_list = subpages_findings[cat].get(std_url, [])
                    for f in sub_f_list:
                        weight = self.SEVERITY_WEIGHTS.get(f.severity, 0.0)
                        sub_deductions += weight * f.confidence * mult
                    subpage_scores_list.append(round(max(0.0, 100.0 - sub_deductions)))

                avg_subpage_score = sum(subpage_scores_list) / len(subpage_scores_list)
                # Aggregate category score formula: Root * 0.50 + Subpages_avg * 0.50
                score_category = (score_root * 0.50) + (avg_subpage_score * 0.50)
            else:
                score_category = float(score_root)

            category_scores[cat] = round(score_category)

        # Authentication status modifier penalty:
        # Subtract 15 points directly from final security score if Auth failed.
        if self.auth_enabled and self.auth_status == "FAILED":
            category_scores["security"] = max(0, category_scores["security"] - 15)

        # Calculate Overall Health Score
        hs_overall = (
            (category_scores["security"] * 0.40)
            + (category_scores["performance"] * 0.25)
            + (category_scores["accessibility"] * 0.20)
            + (category_scores["seo"] * 0.15)
        )
        overall_health_score = round(hs_overall)

        # Calculate Risk Score
        critical_count = sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
        risk_score = min(
            10.0,
            ((100.0 - overall_health_score) / 10.0) + max(0.0, float(critical_count) * 1.0),
        )
        risk_score = round(risk_score, 2)

        return {
            "overall_health_score": overall_health_score,
            "risk_score": risk_score,
            "categories": category_scores,
        }

    def to_json(self) -> str:
        """Export scan details into JSON format matching the schema."""
        report_data = {
            "metadata": {
                "target_url": self.target_url,
                "scan_timestamp": self.scan_timestamp,
                "engine_version": "2.0.0",
                "duration_seconds": self.duration_seconds,
            },
            "crawler_summary": {
                "max_depth": self.max_depth,
                "max_pages": self.max_pages,
                "pages_discovered": self.pages_discovered,
                "pages_scanned": self.pages_scanned,
                "scanned_urls": self.scanned_urls,
            },
            "auth_summary": {
                "auth_enabled": self.auth_enabled,
                "auth_status": self.auth_status,
            },
            "scores": self.scores,
            "findings": [f.model_dump() for f in self.findings],
        }
        return json.dumps(report_data, indent=2)

    def to_console(self, use_color: bool = True) -> str:
        """Generate human-readable console report with optional ANSI color codes."""
        c_reset = "\033[0m" if use_color else ""
        c_title = "\033[1;94m" if use_color else ""
        c_bold = "\033[1m" if use_color else ""
        c_gold = "\033[1;93m" if use_color else ""

        sev_colors = {
            Severity.CRITICAL: "\033[1;91m" if use_color else "",
            Severity.HIGH: "\033[91m" if use_color else "",
            Severity.MEDIUM: "\033[93m" if use_color else "",
            Severity.LOW: "\033[96m" if use_color else "",
            Severity.INFO: "\033[92m" if use_color else "",
        }

        lines = [
            "=" * 70,
            f" {c_title}WEBPULSE WEBSITE AUDIT REPORT{c_reset}",
            f" Target:       {self.target_url}",
            f" Date:         {self.scan_timestamp}",
            f" Crawler:      BFS Scanned {self.pages_scanned}/{self.pages_discovered} Pages (Max Depth: {self.max_depth})",
            f" Auth Status:  {self.auth_status} (Enabled: {self.auth_enabled})",
            "=" * 70,
            "",
            f" [*] {c_gold}OVERALL HEALTH SCORE:{c_reset} {c_bold}{self.scores['overall_health_score']} / 100{c_reset}",
            f" [!] {c_bold}RISK SCORE:{c_reset}            {self.scores['risk_score']} / 10",
            "",
            " Category Breakdown:",
            f" - [Security]      {self.scores['categories']['security']}/100",
            f" - [SEO]           {self.scores['categories']['seo']}/100",
            f" - [Performance]   {self.scores['categories']['performance']}/100",
            f" - [Accessibility] {self.scores['categories']['accessibility']}/100",
            "",
            "-" * 70,
            " Discovered Findings:",
            "",
        ]

        if not self.findings:
            lines.append(" No findings discovered. Great job!")
        else:
            for f in self.findings:
                c_sev = sev_colors.get(f.severity, "")
                lines.extend(
                    [
                        f" [{c_sev}{f.severity}{c_reset}] (Confidence: {f.confidence}) - {f.title}",
                        f"  - URL:         {f.target_url}",
                        f"  - Description: {f.description}",
                        f"  - Remediation: {f.remediation}",
                    ]
                )
                if f.evidence:
                    lines.append("  - Evidence:")
                    for ev in f.evidence:
                        lines.append(f"    * [{ev.type}] {ev.data}")
                lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Export scan details into collapsible structured Markdown format."""
        lines = [
            f"# WebPulse Scan Report: `{self.target_url}`",
            "",
            f"**Scan Timestamp:** `{self.scan_timestamp}`  ",
            f"**Crawl Stats:** Discovered {self.pages_discovered} pages, scanned {self.pages_scanned} pages (max depth: {self.max_depth}).  ",
            f"**Auth Status:** `{self.auth_status}` (Enabled: {self.auth_enabled})  ",
            f"**Overall Health Score:** **{self.scores['overall_health_score']} / 100**  ",
            f"**Risk Level:** **{self.scores['risk_score']} / 10**",
            "",
            "## Category Scores",
            "| Category | Score | Status |",
            "|---|---|---|",
            f"| Security | {self.scores['categories']['security']} / 100 | {'Pass' if self.scores['categories']['security'] >= 80 else 'Fail'} |",
            f"| Performance | {self.scores['categories']['performance']} / 100 | {'Pass' if self.scores['categories']['performance'] >= 80 else 'Fail'} |",
            f"| Accessibility | {self.scores['categories']['accessibility']} / 100 | {'Pass' if self.scores['categories']['accessibility'] >= 80 else 'Fail'} |",
            f"| SEO | {self.scores['categories']['seo']} / 100 | {'Pass' if self.scores['categories']['seo'] >= 80 else 'Fail'} |",
            "",
            "## Discovered Findings",
            "",
        ]

        if not self.findings:
            lines.append("No findings discovered. All audits clean!")
        else:
            for f in self.findings:
                lines.extend(
                    [
                        f"### [{f.severity}] {f.title}",
                        f"* **URL:** `{f.target_url}`",
                        f"* **Module:** `{f.plugin_name}`",
                        f"* **Confidence:** `{f.confidence}`",
                        f"* **Description:** {f.description}",
                        f"* **Remediation:** {f.remediation}",
                    ]
                )
                if f.evidence:
                    lines.append("* **Evidence:**")
                    lines.append("  <details><summary>Click to view evidence traces</summary>")
                    lines.append("")
                    lines.append("  ```yaml")
                    for ev in f.evidence:
                        lines.append(f"  {ev.type}: {json.dumps(ev.data)}")
                    lines.append("  ```")
                    lines.append("  </details>")
                lines.append("")

        return "\n".join(lines)

    def to_html(self) -> str:
        """Generate a sleek, dark-mode, single-page interactive HTML report."""
        findings_json = json.dumps([f.model_dump() for f in self.findings])
        categories_json = json.dumps(self.scores["categories"])
        json.dumps(self.scanned_urls)

        # SVG Circle circumference constants for gauges
        overall_score = self.scores["overall_health_score"]
        overall_dashoffset = round(251.2 * (1.0 - overall_score / 100.0))

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebPulse Audit Report - {self.target_url}</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --sidebar-bg: #111827;
            --card-bg: #1f2937;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-gold: #fbbf24;
            --border-color: #374151;

            --critical-color: #ef4444;
            --high-color: #f97316;
            --medium-color: #3b82f6;
            --low-color: #06b6d4;
            --info-color: #10b981;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            display: flex;
            min-height: 100vh;
        }}

        /* Sidebar Styling */
        .sidebar {{
            width: 320px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 2.5rem 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
        }}

        .brand {{
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(to right, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.05em;
        }}

        .meta-group {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .meta-item {{
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }}

        .meta-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }}

        .meta-value {{
            font-size: 0.9rem;
            font-weight: 600;
            word-break: break-all;
        }}

        /* Main Panel */
        .main-content {{
            margin-left: 320px;
            flex: 1;
            padding: 3rem;
            max-width: 1200px;
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
        }}

        .header-title h1 {{
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.5rem;
        }}

        .header-title p {{
            color: var(--text-secondary);
        }}

        /* Circular Gauge */
        .gauge-container {{
            position: relative;
            width: 120px;
            height: 120px;
        }}

        .gauge-svg {{
            transform: rotate(-90deg);
        }}

        .gauge-bg {{
            fill: none;
            stroke: #2d3748;
            stroke-width: 8;
        }}

        .gauge-fill {{
            fill: none;
            stroke: var(--accent-gold);
            stroke-width: 8;
            stroke-dasharray: 251.2;
            stroke-dashoffset: {overall_dashoffset};
            stroke-linecap: round;
            transition: stroke-dashoffset 1s ease-out;
        }}

        .gauge-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--text-primary);
        }}

        /* Category Grid */
        .scores-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}

        .score-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
            text-align: center;
        }}

        .score-card-title {{
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}

        .mini-gauge {{
            position: relative;
            width: 80px;
            height: 80px;
        }}

        /* Filters */
        .filter-bar {{
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            align-items: center;
        }}

        .filter-btn {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }}

        .filter-btn.active, .filter-btn:hover {{
            background-color: #3b82f6;
            border-color: #3b82f6;
        }}

        /* Findings List */
        .findings-container {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .finding-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            overflow: hidden;
            transition: border-color 0.2s ease;
        }}

        .finding-header {{
            padding: 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }}

        .finding-meta {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .sev-tag {{
            font-size: 0.7rem;
            font-weight: 800;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
        }}

        .sev-critical {{ background-color: var(--critical-color); }}
        .sev-high {{ background-color: var(--high-color); }}
        .sev-medium {{ background-color: var(--medium-color); }}
        .sev-low {{ background-color: var(--low-color); }}
        .sev-info {{ background-color: var(--info-color); }}

        .finding-title {{
            font-weight: 700;
            font-size: 1.05rem;
        }}

        .finding-url {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .finding-details {{
            display: none;
            padding: 0 1.25rem 1.25rem 1.25rem;
            border-top: 1px solid var(--border-color);
            background-color: rgba(0, 0, 0, 0.15);
            font-size: 0.95rem;
        }}

        .details-section {{
            margin-top: 1rem;
        }}

        .details-label {{
            font-size: 0.75rem;
            font-weight: 800;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}

        .evidence-box {{
            background-color: #111827;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.75rem;
            font-family: monospace;
            white-space: pre-wrap;
            margin-top: 0.5rem;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>

    <!-- SIDEBAR -->
    <div class="sidebar">
        <div class="brand">WEBPULSE AUDIT ENGINE</div>

        <div class="meta-group">
            <div class="meta-item">
                <div class="meta-label">Target URL</div>
                <div class="meta-value">{self.target_url}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Scan Timestamp</div>
                <div class="meta-value">{self.scan_timestamp}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Crawl Stats</div>
                <div class="meta-value">BFS Scanned {self.pages_scanned}/{self.pages_discovered} Pages</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Authentication</div>
                <div class="meta-value">{self.auth_status}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Duration</div>
                <div class="meta-value">{self.duration_seconds}s</div>
            </div>
        </div>
    </div>

    <!-- MAIN WINDOW -->
    <div class="main-content">
        <div class="header">
            <div class="header-title">
                <h1>WebPulse Scan Dashboard</h1>
                <p>Comprehensive security, performance, accessibility, and SEO analysis audit report.</p>
            </div>
            <div class="gauge-container">
                <svg class="gauge-svg" width="120" height="120">
                    <circle class="gauge-bg" cx="60" cy="60" r="40"/>
                    <circle class="gauge-fill" cx="60" cy="60" r="40"/>
                </svg>
                <div class="gauge-text">{overall_score}%</div>
            </div>
        </div>

        <!-- CATEGORIES GRID -->
        <div class="scores-grid" id="categories-grid"></div>

        <!-- FILTER BAR -->
        <div class="filter-bar">
            <span>Filter Findings:</span>
            <button class="filter-btn active" onclick="filterFindings('all')">All</button>
            <button class="filter-btn" onclick="filterFindings('CRITICAL')">Critical</button>
            <button class="filter-btn" onclick="filterFindings('HIGH')">High</button>
            <button class="filter-btn" onclick="filterFindings('MEDIUM')">Medium</button>
            <button class="filter-btn" onclick="filterFindings('LOW')">Low</button>
        </div>

        <!-- FINDINGS LIST -->
        <div class="findings-container" id="findings-wrapper"></div>
    </div>

    <script>
        const findings = {findings_json};
        const categories = {categories_json};

        // Populate Categories Grid
        const grid = document.getElementById("categories-grid");
        Object.keys(categories).forEach(cat => {{
            const score = categories[cat];
            const dashoffset = Math.round(188.4 * (1.0 - score / 100.0));
            const card = document.createElement("div");
            card.className = "score-card";
            card.innerHTML = `
                <div class="score-card-title">${{cat}}</div>
                <div class="mini-gauge">
                    <svg width="80" height="80" style="transform: rotate(-90deg);">
                        <circle cx="40" cy="40" r="30" fill="none" stroke="#2d3748" stroke-width="6"/>
                        <circle cx="40" cy="40" r="30" fill="none" stroke="#60a5fa" stroke-width="6"
                                stroke-dasharray="188.4" stroke-dashoffset="${{dashoffset}}" stroke-linecap="round"/>
                    </svg>
                    <div style="position: absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-weight:700;">${{score}}</div>
                </div>
            `;
            grid.appendChild(card);
        }});

        // Populate Findings list
        function renderFindings(list) {{
            const wrapper = document.getElementById("findings-wrapper");
            wrapper.innerHTML = "";

            if (list.length === 0) {{
                wrapper.innerHTML = `<div style="padding:2rem; text-align:center; background-color:var(--card-bg); border-radius:8px; color:var(--text-secondary);">No matching findings discovered.</div>`;
                return;
            }}

            list.forEach((f, idx) => {{
                const card = document.createElement("div");
                card.className = "finding-card";

                let evHTML = "";
                if (f.evidence && f.evidence.length > 0) {{
                    const evText = f.evidence.map(ev => `[${{ev.type}}] ${{ev.data}}`).join("\\n");
                    evHTML = `
                        <div class="details-section">
                            <div class="details-label">Evidence</div>
                            <div class="evidence-box">${{evText}}</div>
                        </div>
                    `;
                }}

                card.innerHTML = `
                    <div class="finding-header" onclick="toggleDetails(${{idx}})">
                        <div class="finding-meta">
                            <span class="sev-tag sev-${{f.severity.toLowerCase()}}">${{f.severity}}</span>
                            <div>
                                <div class="finding-title">${{f.title}}</div>
                                <div class="finding-url">${{f.target_url}}</div>
                            </div>
                        </div>
                        <div style="font-size: 1.25rem;">▸</div>
                    </div>
                    <div class="finding-details" id="details-${{idx}}">
                        <div class="details-section">
                            <div class="details-label">Description</div>
                            <p>${{f.description}}</p>
                        </div>
                        <div class="details-section">
                            <div class="details-label">Remediation</div>
                            <p style="color: var(--accent-gold); font-weight:600;">${{f.remediation}}</p>
                        </div>
                        ${{evHTML}}
                    </div>
                `;
                wrapper.appendChild(card);
            }});
        }}

        function toggleDetails(idx) {{
            const el = document.getElementById(`details-${{idx}}`);
            if (el.style.display === "block") {{
                el.style.display = "none";
            }} else {{
                el.style.display = "block";
            }}
        }}

        function filterFindings(sev) {{
            // Active button class
            const btns = document.querySelectorAll(".filter-btn");
            btns.forEach(btn => btn.classList.remove("active"));
            event.target.classList.add("active");

            if (sev === "all") {{
                renderFindings(findings);
            }} else {{
                const filtered = findings.filter(f => f.severity === sev);
                renderFindings(filtered);
            }}
        }}

        // Initial render
        renderFindings(findings);
    </script>
</body>
</html>
"""
