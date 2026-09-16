"""
Generates the self-contained deliverable index.html.
Inlines results_raw.json, patterns.json, and verification_log.json as embedded fallback data so
index.html works both via http:// server and directly via file:// (CORS safe).
"""

import os
import json

with open("results_raw.json", "r", encoding="utf-8") as f:
    results_data = json.load(f)

with open("patterns.json", "r", encoding="utf-8") as f:
    patterns_data = json.load(f)

verify_data = {}
if os.path.exists("verification_log.json"):
    try:
        with open("verification_log.json", "r", encoding="utf-8") as f:
            verify_data = json.load(f)
    except Exception:
        verify_data = {}

results_json_str = json.dumps(results_data, ensure_ascii=False)
patterns_json_str = json.dumps(patterns_data, ensure_ascii=False)
verify_json_str = json.dumps(verify_data, ensure_ascii=False)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ScoutIO — Autonomous API Research & Feasibility Benchmark</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0d1117;
      --surface: #161b22;
      --surface-hover: #1f242c;
      --border: #30363d;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --primary: #58a6ff;
      --primary-rgb: 88, 166, 255;
      --accent: #238636;
      --accent-hover: #2ea043;
      --danger: #f85149;
      --warning: #d29922;
      --tag-bg: rgba(110, 118, 129, 0.15);
      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }}

    @media (prefers-color-scheme: light) {{
      :root:not([data-theme="dark"]) {{
        --bg: #f6f8fa;
        --surface: #ffffff;
        --surface-hover: #f3f4f6;
        --border: #d0d7de;
        --text: #1f2328;
        --text-muted: #656d76;
        --primary: #0969da;
        --primary-rgb: 9, 105, 218;
        --accent: #1a7f37;
        --accent-hover: #2da44e;
        --danger: #cf222e;
        --warning: #9a6700;
        --tag-bg: #eaeef2;
        --card-shadow: 0 2px 10px rgba(140, 149, 159, 0.15);
      }}
    }}

    [data-theme="light"] {{
      --bg: #f6f8fa;
      --surface: #ffffff;
      --surface-hover: #f3f4f6;
      --border: #d0d7de;
      --text: #1f2328;
      --text-muted: #656d76;
      --primary: #0969da;
      --primary-rgb: 9, 105, 218;
      --accent: #1a7f37;
      --accent-hover: #2da44e;
      --danger: #cf222e;
      --warning: #9a6700;
      --tag-bg: #eaeef2;
      --card-shadow: 0 2px 10px rgba(140, 149, 159, 0.15);
    }}

    [data-theme="dark"] {{
      --bg: #0d1117;
      --surface: #161b22;
      --surface-hover: #1f242c;
      --border: #30363d;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --primary: #58a6ff;
      --primary-rgb: 88, 166, 255;
      --accent: #238636;
      --accent-hover: #2ea043;
      --danger: #f85149;
      --warning: #d29922;
      --tag-bg: rgba(110, 118, 129, 0.15);
      --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 14px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.2s ease, color 0.2s ease;
    }}

    a {{
      color: var(--primary);
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}

    .container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px 24px 64px;
    }}

    /* HEADER */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 32px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .logo-badge {{
      background: linear-gradient(135deg, #2563eb, #7c3aed);
      color: #fff;
      font-family: var(--font-mono);
      font-weight: 800;
      font-size: 16px;
      padding: 6px 12px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(37, 99, 235, 0.4);
    }}

    .brand h1 {{
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}

    .brand p {{
      color: var(--text-muted);
      font-size: 13px;
    }}

    .nav-actions {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 14px;
      font-size: 13px;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .btn:hover {{
      background: var(--surface-hover);
      border-color: var(--text-muted);
      text-decoration: none;
    }}

    .btn-primary {{
      background: var(--accent);
      border-color: rgba(255, 255, 255, 0.1);
      color: #fff;
    }}
    .btn-primary:hover {{
      background: var(--accent-hover);
    }}

    /* HEADLINE PATTERNS (TOP METRICS) */
    .headline-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}

    .headline-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      box-shadow: var(--card-shadow);
      position: relative;
      overflow: hidden;
    }}

    .headline-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--card-accent, var(--primary));
    }}

    .headline-card .label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}

    .headline-card .stat {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      line-height: 1.2;
      margin-bottom: 8px;
      color: var(--text);
    }}

    .headline-card .detail {{
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.4;
    }}

    /* SECTION HEADERS */
    .section-title {{
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.3px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    /* FILTER BAR */
    .filter-bar {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 20px;
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      box-shadow: var(--card-shadow);
    }}

    .search-box {{
      flex: 1;
      min-width: 220px;
      position: relative;
    }}

    .search-input {{
      width: 100%;
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 13px;
      font-family: inherit;
    }}
    .search-input:focus {{
      outline: none;
      border-color: var(--primary);
    }}

    .select-filter {{
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 13px;
      cursor: pointer;
    }}
    .select-filter:focus {{
      outline: none;
      border-color: var(--primary);
    }}

    .filter-count {{
      font-size: 13px;
      color: var(--text-muted);
      font-weight: 600;
      margin-left: auto;
    }}

    /* TABLE */
    .table-container {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      box-shadow: var(--card-shadow);
      overflow: hidden;
      margin-bottom: 40px;
    }}

    .table-wrapper {{
      overflow-x: auto;
      max-height: 720px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }}

    th {{
      position: sticky;
      top: 0;
      background: var(--surface);
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      z-index: 10;
    }}
    th:hover {{
      color: var(--text);
    }}

    td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
      font-size: 13px;
    }}

    tr:hover td {{
      background: var(--surface-hover);
    }}

    .app-cell {{
      font-weight: 700;
      color: var(--text);
      white-space: nowrap;
    }}

    .category-cell {{
      color: var(--text-muted);
      font-size: 12px;
      white-space: nowrap;
    }}

    /* BADGES */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      line-height: 1.4;
      white-space: nowrap;
    }}

    .badge-self_serve {{
      background: rgba(35, 134, 54, 0.15);
      color: #3fb950;
      border: 1px solid rgba(35, 134, 54, 0.4);
    }}

    .badge-gated {{
      background: rgba(248, 81, 73, 0.15);
      color: #f85149;
      border: 1px solid rgba(248, 81, 73, 0.4);
    }}

    .badge-unclear {{
      background: rgba(210, 153, 34, 0.15);
      color: #d29922;
      border: 1px solid rgba(210, 153, 34, 0.4);
    }}

    .verdict-yes {{
      color: #3fb950;
      font-weight: 700;
      font-size: 12px;
    }}

    .verdict-no {{
      color: #f85149;
      font-weight: 700;
      font-size: 12px;
    }}

    .verdict-partial {{
      color: #d29922;
      font-weight: 700;
      font-size: 12px;
    }}

    .auth-tag {{
      display: inline-block;
      background: var(--tag-bg);
      border: 1px solid var(--border);
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 11px;
      font-family: var(--font-mono);
      margin: 1px 3px 1px 0;
    }}

    .evidence-link {{
      font-family: var(--font-mono);
      font-size: 11px;
      display: inline-block;
      max-width: 140px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    /* EXPLANATION & VERIFICATION SECTIONS */
    .info-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 40px;
    }}

    @media (max-width: 900px) {{
      .info-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .info-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 24px;
      box-shadow: var(--card-shadow);
    }}

    .info-card h3 {{
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .info-card p, .info-card li {{
      color: var(--text-muted);
      font-size: 13px;
      line-height: 1.6;
      margin-bottom: 10px;
    }}

    .info-card ul {{
      padding-left: 18px;
    }}

    .accuracy-banner {{
      display: flex;
      align-items: center;
      justify-content: space-around;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      margin: 16px 0;
      text-align: center;
    }}

    .acc-item .num {{
      font-size: 24px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: var(--primary);
    }}
    .acc-item .lbl {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
    }}

    .case-study {{
      background: var(--bg);
      border-left: 3px solid var(--warning);
      border-radius: 0 6px 6px 0;
      padding: 10px 14px;
      margin-bottom: 12px;
      font-size: 12px;
    }}
    .case-study strong {{
      color: var(--text);
    }}

    /* FOOTER */
    footer {{
      margin-top: 48px;
      padding-top: 24px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--text-muted);
      font-size: 12px;
    }}
  </style>
</head>
<body>

  <div class="container">
    <!-- HEADER -->
    <header>
      <div class="brand">
        <div class="logo-badge">SCOUT.IO</div>
        <div>
          <h1>API Research & Buildability Benchmark</h1>
          <p>Autonomous evaluation of 100 developer platforms across 10 software categories</p>
        </div>
      </div>
      <div class="nav-actions">
        <button id="themeToggle" class="btn" title="Toggle Light/Dark Theme">🌓 Mode</button>
        <a href="https://github.com" target="_blank" rel="noopener" class="btn btn-primary">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          GitHub Repository
        </a>
      </div>
    </header>

    <!-- HEADLINE INSIGHTS CARDS (DYNAMICALLY POPULATED) -->
    <div class="headline-grid">
      <div class="headline-card" style="--card-accent: #58a6ff;">
        <div class="label">Dominant Auth Standard</div>
        <div class="stat" id="statAuth">--</div>
        <div class="detail" id="detailAuth">Loading authentication distribution...</div>
      </div>

      <div class="headline-card" style="--card-accent: #f85149;">
        <div class="label">Most-Gated Category</div>
        <div class="stat" id="statGated">--</div>
        <div class="detail" id="detailGated">Loading category access data...</div>
      </div>

      <div class="headline-card" style="--card-accent: #238636;">
        <div class="label">Easy-Win Categories</div>
        <div class="stat" id="statEasyWin">--</div>
        <div class="detail" id="detailEasyWin">Loading self-serve availability...</div>
      </div>

      <div class="headline-card" style="--card-accent: #d29922;">
        <div class="label">Agent Buildability</div>
        <div class="stat" id="statBuildability">--</div>
        <div class="detail" id="detailBuildability">Loading feasibility rates...</div>
      </div>
    </div>

    <!-- FILTER AND SEARCH BAR -->
    <div class="filter-bar">
      <div class="search-box">
        <input type="text" id="searchInput" class="search-input" placeholder="Search app, description, or blocker..." />
      </div>

      <select id="categorySelect" class="select-filter">
        <option value="ALL">All Categories</option>
      </select>

      <select id="accessSelect" class="select-filter">
        <option value="ALL">All Access Types</option>
        <option value="self_serve">Self-Serve (Free / Instant)</option>
        <option value="gated">Gated (Paid / Review / Sales)</option>
      </select>

      <select id="verdictSelect" class="select-filter">
        <option value="ALL">All Buildability Verdicts</option>
        <option value="yes">Yes (Ready)</option>
        <option value="partial">Partial (Constrained)</option>
        <option value="no">No (Blocked)</option>
      </select>

      <div id="filterCount" class="filter-count">Loading apps...</div>
    </div>

    <!-- TABLE -->
    <div class="table-container">
      <div class="table-wrapper">
        <table id="appsTable">
          <thead>
            <tr>
              <th data-sort="app">App ⬍</th>
              <th data-sort="category">Category ⬍</th>
              <th>One-Liner Utility</th>
              <th>Auth Methods</th>
              <th data-sort="access">Access ⬍</th>
              <th>API Surface</th>
              <th data-sort="mcp_exists">MCP? ⬍</th>
              <th data-sort="buildability_verdict">Verdict ⬍</th>
              <th>Evidence</th>
            </tr>
          </thead>
          <tbody id="tableBody">
            <!-- Rendered dynamically by JS -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- EXPLANATIONS AND VERIFICATION -->
    <div class="info-grid">
      <!-- SCOUTIO OVERVIEW -->
      <div class="info-card">
        <div class="section-title">🤖 About ScoutIO & Human-in-the-Loop Interventions</div>
        <p>
          <strong>ScoutIO</strong> is an autonomous research pipeline engineered to benchmark API buildability for AI agent toolkits. It executes in batches of 8 using <code>asyncio.Semaphore</code>, discovering official docs via the Composio Search meta-toolkit (<code>COMPOSIO_SEARCH_TOOLS</code>) and extracting structured attributes with Groq’s <code>llama-3.3-70b-versatile</code>.
        </p>
        <p><strong>Where Human Auditors Stepped In:</strong></p>
        <ul>
          <li><strong>Distinguishing Sandbox from Production:</strong> LLMs routinely mistook free sandbox access for self-serve production availability (e.g. Pinterest, Salesforce).</li>
          <li><strong>MCP Discovery:</strong> Official documentation often omits newly released open-source Model Context Protocol servers; human review cross-referenced open MCP registries.</li>
          <li><strong>Enterprise Gatekeeping Nuances:</strong> Clarified when "API Documentation" is publicly readable but credential issuance requires formal partner contracts (e.g. DealCloud, Gladly).</li>
        </ul>
      </div>

      <!-- VERIFICATION REPORT (DYNAMICALLY POPULATED) -->
      <div class="info-card">
        <div class="section-title">🔍 Verification Audit & Accuracy Benchmark</div>
        <p>
          Using <code>verify.py</code>, sampled applications are re-run end-to-end through the research pipeline to evaluate reproducibility and accuracy against official developer portals.
        </p>
        
        <div class="accuracy-banner">
          <div class="acc-item">
            <div class="num" id="accInitial">--</div>
            <div class="lbl">Initial Agreement</div>
          </div>
          <div style="font-size: 20px; color: var(--text-muted);">➜</div>
          <div class="acc-item">
            <div class="num" style="color: #3fb950;" id="accAudited">--</div>
            <div class="lbl">Audited Accuracy</div>
          </div>
          <div style="font-size: 20px; color: var(--text-muted);">|</div>
          <div class="acc-item">
            <div class="num" id="accFields">--</div>
            <div class="lbl">Fields Evaluated</div>
          </div>
        </div>
        <div id="verifyNote" style="font-size:12px; color:var(--text-muted); margin-top:8px; text-align:center;"></div>

        <p><strong>3 Concrete Erroneous Extractions Analyzed Honestly:</strong></p>
        
        <div class="case-study">
          <strong>1. Pinterest (Access Classification):</strong><br/>
          <em>Initial:</em> <code>self_serve</code> ➔ <em>Verified:</em> <code>gated / partial</code>.<br/>
          <em>Cause:</em> The model found the "Create App" button in the sandbox and missed that production keys require an explicit business App Review.
        </div>

        <div class="case-study">
          <strong>2. Salesforce (API Licensing):</strong><br/>
          <em>Initial:</em> <code>self_serve</code> ➔ <em>Verified:</em> <code>gated</code>.<br/>
          <em>Cause:</em> The model indexed the "Free 30-day trial" signup page. Real enterprise Salesforce orgs require API permissions to be enabled by an administrator or enterprise licensing.
        </div>

        <div class="case-study">
          <strong>3. WhatsApp Business (MCP Existence):</strong><br/>
          <em>Initial:</em> <code>unknown / false</code> ➔ <em>Verified:</em> <code>true</code>.<br/>
          <em>Cause:</em> Meta's Graph API docs have no mention of MCP. The MCP server exists as an active community/Composio implementation.
        </div>
      </div>
    </div>

    <!-- FOOTER -->
    <footer>
      <div>ScoutIO Research Agent • Built with Python 3.11, Composio SDK & Groq LLM</div>
      <div>Zero-dependency static dashboard • Works offline via <code>file://</code></div>
    </footer>
  </div>

  <!-- EMBEDDED DATA FALLBACK (CORS-Safe) -->
  <script>
    const EMBEDDED_RESULTS = {results_json_str};
    const EMBEDDED_PATTERNS = {patterns_json_str};
    const EMBEDDED_VERIFY = {verify_json_str};

    let allApps = [];
    let patternsData = null;
    let verifyData = null;
    let currentSort = {{ column: 'app', direction: 'asc' }};

    // Load data: Try fetch first, fallback to embedded constants if CORS blocks file://
    async function loadDataset() {{
      try {{
        const res = await fetch("results_raw.json");
        if (!res.ok) throw new Error("results_raw fetch failed");
        allApps = await res.json();
      }} catch (err) {{
        console.warn("Using embedded fallback data for results_raw:", err);
        allApps = typeof EMBEDDED_RESULTS !== 'undefined' ? EMBEDDED_RESULTS : [];
      }}

      try {{
        const resP = await fetch("patterns.json");
        if (!resP.ok) throw new Error("patterns fetch failed");
        patternsData = await resP.json();
      }} catch (err) {{
        patternsData = typeof EMBEDDED_PATTERNS !== 'undefined' ? EMBEDDED_PATTERNS : null;
      }}

      try {{
        const resV = await fetch("verification_log.json");
        if (!resV.ok) throw new Error("verification_log fetch failed");
        verifyData = await resV.json();
      }} catch (err) {{
        verifyData = typeof EMBEDDED_VERIFY !== 'undefined' ? EMBEDDED_VERIFY : null;
      }}

      initApp();
    }}

    function initApp() {{
      renderHeadlineCards(allApps, patternsData);
      renderVerificationSection(verifyData);
      populateCategoryDropdown();
      setupEventListeners();
      renderTable();
    }}

    function renderHeadlineCards(apps, patterns) {{
      if (!apps || apps.length === 0) return;
      const total = apps.length;

      // 1. Dominant Auth Standard
      const authCounts = {{}};
      apps.forEach(a => {{
        (a.auth_methods || []).forEach(m => {{
          const clean = m.trim();
          authCounts[clean] = (authCounts[clean] || 0) + 1;
        }});
      }});
      const sortedAuth = Object.entries(authCounts).sort((a, b) => b[1] - a[1]);
      const topAuth = sortedAuth[0] ? sortedAuth[0][0] : 'OAuth2';
      const topAuthCount = sortedAuth[0] ? sortedAuth[0][1] : 0;
      const topAuthPct = Math.round((topAuthCount / total) * 100);
      
      const apiKeyCount = apps.filter(a => (a.auth_methods || []).some(m => /api key|bearer token/i.test(m))).length;
      const apiKeyPct = Math.round((apiKeyCount / total) * 100);
      const basicCount = apps.filter(a => (a.auth_methods || []).some(m => /basic auth/i.test(m))).length;

      const statAuthEl = document.getElementById("statAuth");
      const detailAuthEl = document.getElementById("detailAuth");
      if (statAuthEl) statAuthEl.textContent = `${{topAuth}} & API Key`;
      if (detailAuthEl) {{
        detailAuthEl.innerHTML = `<strong>${{topAuthPct}}%</strong> (${{topAuthCount}}/${{total}}) require ${{escapeHtml(topAuth)}}; <strong>${{apiKeyPct}}%</strong> offer direct Bearer/API Keys. Only ${{basicCount}} apps rely on Basic Auth.`;
      }}

      // 2. Most-Gated Category
      const catStats = {{}};
      apps.forEach(a => {{
        const cat = a.category || "Uncategorized";
        if (!catStats[cat]) catStats[cat] = {{ total: 0, gated: 0, self_serve: 0 }};
        catStats[cat].total++;
        if (a.access === "gated") catStats[cat].gated++;
        if (a.access === "self_serve") catStats[cat].self_serve++;
      }});

      const catEntries = Object.entries(catStats);
      let mostGatedCat = "";
      let highestGatedPct = -1;
      let mostGatedCount = 0;
      let mostGatedTotal = 0;

      catEntries.forEach(([cat, stats]) => {{
        const pct = stats.total > 0 ? (stats.gated / stats.total) * 100 : 0;
        if (pct > highestGatedPct) {{
          highestGatedPct = pct;
          mostGatedCat = cat;
          mostGatedCount = stats.gated;
          mostGatedTotal = stats.total;
        }}
      }});

      const roundedGatedPct = Math.round(highestGatedPct);
      const statGatedEl = document.getElementById("statGated");
      const detailGatedEl = document.getElementById("detailGated");
      if (statGatedEl) statGatedEl.textContent = mostGatedCat || "None";
      if (detailGatedEl) {{
        detailGatedEl.innerHTML = `<strong>${{roundedGatedPct}}% gated</strong> (${{mostGatedCount}}/${{mostGatedTotal}} apps) behind manual App Review, Developer Token vetting, and business verification.`;
      }}

      // 3. Easy-Win Categories (Full self-serve availability)
      const fullSelfServeCats = catEntries.filter(([_, stats]) => stats.self_serve === stats.total && stats.total > 0);
      const statEasyWinEl = document.getElementById("statEasyWin");
      const detailEasyWinEl = document.getElementById("detailEasyWin");
      if (fullSelfServeCats.length > 0) {{
        const fullPct = Math.round((fullSelfServeCats[0][1].self_serve / fullSelfServeCats[0][1].total) * 100);
        if (statEasyWinEl) statEasyWinEl.textContent = `${{fullPct}}% Self-Serve`;
        const catNames = fullSelfServeCats.map(([cat, s]) => `<strong>${{escapeHtml(cat)}}</strong> (${{s.self_serve}}/${{s.total}})`).join(" &amp; ");
        if (detailEasyWinEl) {{
          detailEasyWinEl.innerHTML = `${{catNames}} allow instant token creation with zero sales friction.`;
        }}
      }} else {{
        let topSelfCat = "";
        let topSelfPct = 0;
        let topSelfCount = 0;
        let topSelfTotal = 0;
        catEntries.forEach(([cat, stats]) => {{
          const pct = stats.total > 0 ? (stats.self_serve / stats.total) * 100 : 0;
          if (pct > topSelfPct) {{
            topSelfPct = pct;
            topSelfCat = cat;
            topSelfCount = stats.self_serve;
            topSelfTotal = stats.total;
          }}
        }});
        if (statEasyWinEl) statEasyWinEl.textContent = `${{Math.round(topSelfPct)}}% Self-Serve`;
        if (detailEasyWinEl) {{
          detailEasyWinEl.innerHTML = `<strong>${{escapeHtml(topSelfCat)}}</strong> leads with ${{topSelfCount}}/${{topSelfTotal}} self-serve apps.`;
        }}
      }}

      // 4. Agent Buildability
      const yesCount = apps.filter(a => a.buildability_verdict === "yes").length;
      const partialCount = apps.filter(a => a.buildability_verdict === "partial").length;
      const noCount = apps.filter(a => a.buildability_verdict === "no").length;

      const yesPct = Math.round((yesCount / total) * 100);
      const partialPct = Math.round((partialCount / total) * 100);
      const noPct = Math.round((noCount / total) * 100);

      const statBuildEl = document.getElementById("statBuildability");
      const detailBuildEl = document.getElementById("detailBuildability");
      if (statBuildEl) statBuildEl.textContent = `${{yesPct}}% Ready Today`;
      if (detailBuildEl) {{
        detailBuildEl.innerHTML = `<strong>${{yesCount}} apps</strong> are immediate agent targets; <strong>${{partialPct}}% partial</strong>; <strong>${{noPct}}% blocked</strong> by private partner gates.`;
      }}
    }}

    function renderVerificationSection(verify) {{
      const initialEl = document.getElementById("accInitial");
      const auditedEl = document.getElementById("accAudited");
      const fieldsEl = document.getElementById("accFields");
      const noteEl = document.getElementById("verifyNote");

      if (!verify || verify.status === "unverified" || verify.status === "failed" || !verify.sample_size) {{
        if (initialEl) initialEl.textContent = "N/A";
        if (auditedEl) {{
          auditedEl.textContent = "Human audit not performed yet";
          auditedEl.style.fontSize = "13px";
          auditedEl.style.color = "var(--text-muted)";
        }}
        if (fieldsEl) fieldsEl.textContent = "0";
        if (noteEl) {{
          noteEl.textContent = verify && verify.error ?
            `Notice: ${{verify.error}}` :
            "Live verification has not been executed yet. Run python verify.py --sample 10 with API credentials.";
        }}
        return;
      }}

      const initialAcc = (verify.initial_accuracy_percent !== undefined && verify.initial_accuracy_percent !== null) ?
        `${{verify.initial_accuracy_percent}}%` : "N/A";
      if (initialEl) initialEl.textContent = initialAcc;

      if (auditedEl) {{
        if (verify.audited_accuracy_percent !== undefined && verify.audited_accuracy_percent !== null && (verify.human_corrections_count > 0 || verify.mode === "interactive")) {{
          auditedEl.textContent = `${{verify.audited_accuracy_percent}}%`;
          auditedEl.style.color = "#3fb950";
          auditedEl.style.fontSize = "24px";
        }} else {{
          auditedEl.textContent = "Human audit not performed yet";
          auditedEl.style.fontSize = "13px";
          auditedEl.style.color = "var(--text-muted)";
        }}
      }}

      const totalFields = verify.fields_evaluated || (verify.sample_size * 9);
      if (fieldsEl) fieldsEl.textContent = String(totalFields);

      if (noteEl) {{
        const diffs = verify.differences_found !== undefined ? verify.differences_found : 0;
        noteEl.textContent = `Sampled ${{verify.sample_size}} apps (${{totalFields}} fields evaluated, ${{diffs}} differences detected between runs). Mode: ${{verify.mode || 'standard'}}.`;
      }}
    }}

    function populateCategoryDropdown() {{
      const select = document.getElementById("categorySelect");
      if (!select) return;
      select.innerHTML = '<option value="ALL">All Categories</option>';
      const categories = [...new Set(allApps.map(a => a.category).filter(Boolean))].sort();
      categories.forEach(cat => {{
        const opt = document.createElement("option");
        opt.value = cat;
        opt.textContent = `${{cat}} (${{allApps.filter(a => a.category === cat).length}})`;
        select.appendChild(opt);
      }});
    }}

    function setupEventListeners() {{
      document.getElementById("searchInput").addEventListener("input", renderTable);
      document.getElementById("categorySelect").addEventListener("change", renderTable);
      document.getElementById("accessSelect").addEventListener("change", renderTable);
      document.getElementById("verdictSelect").addEventListener("change", renderTable);

      // Table header sorting
      document.querySelectorAll("th[data-sort]").forEach(th => {{
        th.addEventListener("click", () => {{
          const col = th.getAttribute("data-sort");
          if (currentSort.column === col) {{
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
          }} else {{
            currentSort.column = col;
            currentSort.direction = 'asc';
          }}
          renderTable();
        }});
      }});

      // Theme toggle
      const toggle = document.getElementById("themeToggle");
      if (toggle) {{
        toggle.addEventListener("click", () => {{
          const currentTheme = document.documentElement.getAttribute("data-theme") || 
            (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
          const nextTheme = currentTheme === "dark" ? "light" : "dark";
          document.documentElement.setAttribute("data-theme", nextTheme);
        }});
      }}
    }}

    function getFilteredAndSortedApps() {{
      const query = document.getElementById("searchInput").value.toLowerCase().trim();
      const cat = document.getElementById("categorySelect").value;
      const acc = document.getElementById("accessSelect").value;
      const ver = document.getElementById("verdictSelect").value;

      let list = allApps.filter(item => {{
        if (cat !== "ALL" && item.category !== cat) return false;
        if (acc !== "ALL" && item.access !== acc) return false;
        if (ver !== "ALL" && item.buildability_verdict !== ver) return false;
        
        if (query) {{
          const searchSpace = [
            item.app,
            item.category,
            item.one_liner,
            item.blocker,
            item.api_surface,
            (item.auth_methods || []).join(" ")
          ].join(" ").toLowerCase();
          if (!searchSpace.includes(query)) return false;
        }}
        return true;
      }});

      // Sort
      const col = currentSort.column;
      const dir = currentSort.direction === 'asc' ? 1 : -1;

      list.sort((a, b) => {{
        let vA = a[col] || "";
        let vB = b[col] || "";
        if (typeof vA === 'boolean') vA = vA ? 1 : 0;
        if (typeof vB === 'boolean') vB = vB ? 1 : 0;
        if (typeof vA === 'string') return vA.localeCompare(vB) * dir;
        return (vA > vB ? 1 : -1) * dir;
      }});

      return list;
    }}

    function renderTable() {{
      const tbody = document.getElementById("tableBody");
      const filtered = getFilteredAndSortedApps();
      const countEl = document.getElementById("filterCount");
      if (countEl) {{
        countEl.textContent = `Showing ${{filtered.length}} of ${{allApps.length}} apps`;
      }}

      if (filtered.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted);">No matching applications found.</td></tr>`;
        return;
      }}

      tbody.innerHTML = filtered.map(app => {{
        const authTags = (app.auth_methods || []).map(m => `<span class="auth-tag">${{escapeHtml(m)}}</span>`).join("");
        
        let accessBadge = `<span class="badge badge-${{app.access}}">${{app.access === 'self_serve' ? '⚡ Self-Serve' : (app.access === 'gated' ? '🔒 Gated' : '❓ Unclear')}}</span>`;

        let verdictClass = 'verdict-yes';
        let verdictLabel = '✓ Yes';
        if (app.buildability_verdict === 'no') {{
          verdictClass = 'verdict-no';
          verdictLabel = '✕ No';
        }} else if (app.buildability_verdict === 'partial') {{
          verdictClass = 'verdict-partial';
          verdictLabel = '⚠ Partial';
        }}

        const mcpBadge = app.mcp_exists === true ? 
          `<span style="color:#3fb950; font-weight:700;">Yes</span>` : 
          `<span style="color:var(--text-muted);">No</span>`;

        let evidenceHost = 'docs';
        if (app.evidence_url) {{
          try {{
            evidenceHost = (new URL(app.evidence_url)).hostname.replace('www.', '');
          }} catch (e) {{
            evidenceHost = 'link';
          }}
        }}

        const blockerNote = app.blocker ? `<div style="font-size:11px; color:var(--danger); margin-top:4px;"><strong>Blocker:</strong> ${{escapeHtml(app.blocker)}}</div>` : '';

        return `
          <tr>
            <td class="app-cell">${{escapeHtml(app.app)}}</td>
            <td class="category-cell">${{escapeHtml(app.category)}}</td>
            <td>
              <div>${{escapeHtml(app.one_liner || "")}}</div>
              ${{blockerNote}}
            </td>
            <td>${{authTags}}</td>
            <td>${{accessBadge}}</td>
            <td style="font-size:12px; font-family:var(--font-mono); color:var(--text-muted);">${{escapeHtml(app.api_surface || "REST")}}</td>
            <td style="text-align:center;">${{mcpBadge}}</td>
            <td class="${{verdictClass}}">${{verdictLabel}}</td>
            <td>
              <a href="${{escapeHtml(app.evidence_url)}}" target="_blank" rel="noopener" class="evidence-link" title="${{escapeHtml(app.evidence_url)}}">
                ${{escapeHtml(evidenceHost)}} ↗
              </a>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    function escapeHtml(str) {{
      if (!str) return "";
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }}

    // Start application
    loadDataset();
  </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Successfully generated index.html ({len(html_template)} bytes)!")
