/* ============================================================
   HEER — Intelligence That Executes
   Command Center UI Logic (vanilla JS, no deps)
   ============================================================ */

"use strict";

/* ------------------------------------------------------------------
   State
   ------------------------------------------------------------------ */

const state = {
  view: "command",
  graph: null,
  graphPositions: {},
  graphDrag: null,
  graphScale: 1,
  graphOffset: { x: 0, y: 0 },
  businesses: [],
  currentBusiness: null,
  lastReply: "",
  recording: false,
  audioCtx: null,
  pcmStream: null,
  pcmProcessor: null,
  pcmSource: null,
  pcmSamples: [],
  pcmSampleRate: 44100,
  activityTimer: null,
  activityIndex: 0,
  autoSpeak: true,
  webSpeechRec: null,
  webSpeechActive: false,
};

/* ------------------------------------------------------------------
   Helpers
   ------------------------------------------------------------------ */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  return node;
}

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

function fmtMoney(n) {
  if (n == null) return "—";
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return "$" + (n / 1e3).toFixed(0) + "K";
  return "$" + n;
}

function fmtPct(n) {
  if (n == null) return "—";
  return Math.round(n * 100) + "%";
}

function timeGreeting() {
  const h = new Date().getHours();
  if (h < 5) return "Good night";
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || res.statusText || "Request failed");
  }
  const ct = res.headers.get("Content-Type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

/* ------------------------------------------------------------------
   Business Switcher
   ------------------------------------------------------------------ */

async function loadBusinesses() {
  try {
    const data = await api("/api/businesses");
    state.businesses = data.businesses || [];
    state.currentBusiness = data.current || null;
    renderBusinessSwitcher();
    return data;
  } catch (e) {
    return { businesses: [], current: null };
  }
}

function renderBusinessSwitcher() {
  const btn = $("#business-switcher-btn");
  const list = $("#business-list");
  if (!btn || !list) return;
  const cur = state.currentBusiness;
  if (cur) {
    const icon = $("#business-icon");
    const name = $("#business-name");
    if (icon) icon.textContent = cur.icon || "🏢";
    if (name) name.textContent = cur.name || "Business";
    btn.style.setProperty("--business-color", cur.color || "#4d9fff");
  }
  list.innerHTML = "";
  (state.businesses || []).forEach((b) => {
    const item = el("div", "business-item" + (cur && cur.id === b.id ? " active" : ""));
    item.append(
      el("span", "business-item-icon", b.icon || "🏢"),
      el("span", "business-item-name", b.name || b.id),
      el("span", "business-item-type", b.type || "")
    );
    item.addEventListener("click", () => {
      if (cur && cur.id === b.id) {
        closeBusinessDropdown();
        return;
      }
      switchBusiness(b.id);
    });
    list.appendChild(item);
  });
}

function openBusinessDropdown() {
  const dd = $("#business-dropdown");
  if (dd) dd.classList.add("open");
}

function closeBusinessDropdown() {
  const dd = $("#business-dropdown");
  if (dd) dd.classList.remove("open");
}

async function switchBusiness(id) {
  try {
    const data = await api("/api/business/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ business_id: id }),
    });
    state.currentBusiness = data.business || null;
    closeBusinessDropdown();
    renderBusinessSwitcher();
    renderHero();
    refreshAllData();
    addMsg("Switched to " + (data.business ? data.business.name : id) + ".", "heer");
  } catch (err) {
    addMsg("Could not switch business — " + err.message, "heer");
  }
}

function refreshAllData() {
  // Reset graph positions so the new business's graph lays out fresh
  state.graphPositions = {};
  state.graphOffset = { x: 0, y: 0 };
  loadGraph();
  api("/api/agents").then((data) => {
    renderConstellation(data.agents || []);
  }).catch(() => {});
  api("/api/activity").then((data) => {
    renderActivity(data.items || []);
  }).catch(() => {});
  api("/api/learning").then((data) => {
    renderLearning(data);
  }).catch(() => {});
  api("/api/status").then((data) => {
    renderMemory(data);
  }).catch(() => {});
  api("/api/briefing").then((data) => {
    renderHeroInsights(data);
  }).catch(() => {});
  api("/api/business").then((data) => {
    renderHeroKPIs(data);
  }).catch(() => {});
  api("/api/opportunities").then((data) => {
    renderHeroOpportunities(data);
  }).catch(() => {});
  api("/api/system").then((data) => {
    if (data.nodes != null) {
      const label = $("#agent-count-label");
      if (label) label.textContent = data.nodes;
    }
  }).catch(() => {});
  // Refresh view-specific data if currently visible
  if (state.view === "intelligence") loadIntelligence();
  if (state.view === "projects") loadProjects();
  if (state.view === "clients") loadClients();
  if (state.view === "agents") loadAgents();
  if (state.view === "skills") loadSkills();
  if (state.view === "automation") loadAutomations();
  if (state.view === "missions") loadMissions();
}

/* ------------------------------------------------------------------
   Navigation
   ------------------------------------------------------------------ */

function switchView(name) {
  state.view = name;
  $$(".nav-link").forEach((a) => a.classList.toggle("active", a.dataset.view === name));
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + name));
  if (name === "knowledge") renderGraph();
  if (name === "agents") loadAgents();
  if (name === "skills") loadSkills();
  if (name === "intelligence") loadIntelligence();
  if (name === "projects") loadProjects();
  if (name === "clients") loadClients();
  if (name === "automation") loadAutomations();
  if (name === "missions") loadMissions();
  if (name === "governance") renderGovernance();
  if (name === "analytics") renderAnalytics();
  if (name === "settings") renderSettings();
}

/* ------------------------------------------------------------------
   Command Center — Hero, Priorities, Activity
   ------------------------------------------------------------------ */

function renderHero() {
  const biz = state.currentBusiness;
  const bizName = biz ? biz.name : "the agency";
  $("#hero-greeting").textContent = timeGreeting() + ", Pankaj.";
  const sub = document.querySelector(".hero-sub");
  if (sub) sub.textContent = "HEER has analyzed your " + bizName + " environment.";
}

function renderActivity(items) {
  const feed = $("#activity-feed");
  if (!feed) return;
  feed.innerHTML = "";
  items.forEach((item) => {
    const row = el("div", "activity-item");
    const time = el("span", "activity-time", item.time || "");
    const text = el("span", "activity-text");
    text.innerHTML = item.html || esc(item.text || "");
    row.append(time, text);
    feed.appendChild(row);
  });
}

function startActivityLoop() {
  if (state.activityTimer) return;
  const tick = async () => {
    try {
      const data = await api("/api/activity");
      if (data && data.items) renderActivity(data.items);
    } catch (e) {
      /* silent */
    }
  };
  tick();
  state.activityTimer = setInterval(tick, 15000);
}

/* ------------------------------------------------------------------
   Agent Constellation
   ------------------------------------------------------------------ */

function renderConstellation(agents) {
  const container = $("#constellation-nodes");
  if (!container) return;
  container.innerHTML = "";
  const active = agents.filter((a) => a.status === "active" || a.status === "working");
  $("#active-agents-count").textContent = active.length + " active";

  const radius = 120;
  const count = Math.min(agents.length, 15);
  agents.slice(0, count).forEach((agent, i) => {
    const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
    const x = 50 + (radius / 2.6) * Math.cos(angle);
    const y = 50 + (radius / 2.6) * Math.sin(angle);
    const node = el("div", "constellation-node" + (agent.status === "active" ? " active" : ""));
    node.style.left = x + "%";
    node.style.top = y + "%";
    node.style.color = agent.color || "#4d9fff";
    const dot = el("div", "node-dot");
    dot.style.background = agent.color || "#4d9fff";
    dot.style.borderColor = agent.color || "#4d9fff";
    const label = el("span", "node-label", agent.name);
    node.append(dot, label);
    node.title = agent.mission || agent.role || agent.name;
    node.addEventListener("click", () => {
      switchView("agents");
    });
    container.appendChild(node);
  });
}

/* ------------------------------------------------------------------
   Agents
   ------------------------------------------------------------------ */

async function loadAgents() {
  const grid = $("#agent-grid");
  if (!grid) return;
  try {
    const data = await api("/api/agents");
    const agents = data.agents || [];
    grid.innerHTML = "";
    agents.forEach((agent) => {
      const card = el("div", "agent-card");
      card.style.setProperty("--agent-color", agent.color || "#4d9fff");

      const head = el("div", "agent-head");
      const icon = el("div", "agent-icon", (agent.name || "?").charAt(0));
      const title = el("div", "agent-title");
      title.append(
        el("div", "agent-name-text", agent.name),
        el("div", "agent-role", agent.role || "Agent")
      );
      const status = el("span", "agent-status " + (agent.status || "idle"), agent.status || "idle");
      head.append(icon, title, status);

      const mission = el("div", "agent-mission", agent.mission || "Monitoring business environment.");

      const details = el("div", "agent-details");
      const rows = [
        ["Current Task", agent.current_task || "—"],
        ["Tools", (agent.tools || []).join(", ") || "—"],
        ["Skills", (agent.skills || []).join(", ") || "—"],
        ["Last Action", agent.last_action || "—"],
        ["Next Action", agent.next_action || "—"],
        ["Business Impact", agent.business_impact || "—"],
      ];
      rows.forEach(([label, value]) => {
        const row = el("div", "agent-detail-row");
        row.append(el("span", "label", label), el("span", "value", value));
        details.appendChild(row);
      });

      // Confidence
      const conf = el("div", "agent-detail-row");
      conf.append(el("span", "label", "Confidence"));
      const confWrap = el("div", "agent-confidence");
      const bar = el("div", "confidence-bar");
      const fill = el("i");
      fill.style.width = Math.round((agent.confidence || 0.8) * 100) + "%";
      bar.appendChild(fill);
      confWrap.append(bar, el("span", "value", Math.round((agent.confidence || 0.8) * 100) + "%"));
      conf.appendChild(confWrap);
      details.appendChild(conf);

      // Autonomy
      const foot = el("div", "agent-detail-row");
      foot.append(el("span", "label", "Autonomy"));
      foot.append(el("span", "agent-autonomy", "L" + (agent.autonomy_level ?? 2) + " · " + (agent.autonomy || "Assisted")));
      details.appendChild(foot);

      card.append(head, mission, details);
      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = '<div class="panel" style="grid-column:1/-1">Unable to load agents: ' + esc(e.message) + "</div>";
  }
}

/* ------------------------------------------------------------------
   Skills
   ------------------------------------------------------------------ */

async function loadSkills() {
  const grid = $("#skill-grid");
  if (!grid) return;
  try {
    const data = await api("/api/skills");
    const skills = data.skills || [];
    grid.innerHTML = "";
    skills.forEach((skill) => {
      const card = el("div", "skill-card");

      const head = el("div", "skill-head");
      const nameWrap = el("div");
      nameWrap.append(
        el("div", "skill-name", skill.name),
        el("div", "skill-version", "v" + (skill.version || "1.0"))
      );
      head.append(nameWrap);
      card.appendChild(head);

      card.appendChild(el("div", "skill-purpose", skill.purpose || skill.description || ""));

      const stats = el("div", "skill-stats");
      const statDefs = [
        ["Success Rate", (skill.success_rate != null ? Math.round(skill.success_rate * 100) : 0) + "%", "green"],
        ["Executions", skill.executions || 0, ""],
        ["Last Validated", skill.last_validated || "—", ""],
        ["Risk", skill.risk_level || "Low", ""],
      ];
      statDefs.forEach(([label, value, cls]) => {
        const stat = el("div", "skill-stat");
        stat.append(el("span", "stat-label", label), el("span", "stat-value " + cls, value));
        stats.appendChild(stat);
      });
      card.appendChild(stats);

      const foot = el("div", "skill-foot");
      const autonomyName = String(skill.autonomy || "assisted");
      const autonomy = el("span", "skill-autonomy " + autonomyName.toLowerCase(), autonomyName.charAt(0).toUpperCase() + autonomyName.slice(1).toLowerCase());
      const validated = el("span", "skill-validated");
      validated.append(el("span", "check", "✓"), document.createTextNode(" Validated"));
      foot.append(autonomy, validated);
      card.appendChild(foot);

      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = '<div class="panel" style="grid-column:1/-1">Unable to load skills: ' + esc(e.message) + "</div>";
  }
}

/* ------------------------------------------------------------------
   Intelligence (Briefing + KPIs + Opportunities)
   ------------------------------------------------------------------ */

async function loadIntelligence() {
  try {
    const briefing = await api("/api/briefing");
    renderBriefing(briefing);
  } catch (e) { /* silent */ }

  try {
    const business = await api("/api/business");
    renderKPIs(business);
  } catch (e) { /* silent */ }

  try {
    const opps = await api("/api/opportunities");
    renderOpportunities(opps);
  } catch (e) { /* silent */ }
}

function briefingText(value) {
  // Normalize any briefing field shape into display text.
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map((v) => {
      if (typeof v === "string") return v;
      if (v && typeof v === "object") {
        // Decision / risk / opportunity objects
        const parts = [];
        if (v.title) parts.push(v.title);
        if (v.detail) parts.push(v.detail);
        if (v.impact) parts.push(v.impact);
        if (v.due) parts.push("Due: " + v.due);
        if (v.severity) parts.push("Severity: " + v.severity);
        if (v.value) parts.push("Value: " + v.value);
        if (v.confidence != null) parts.push("Confidence: " + Math.round(v.confidence * 100) + "%");
        return parts.join(" — ");
      }
      return String(v);
    }).join("\n");
  }
  if (typeof value === "object") {
    const parts = [];
    if (value.title) parts.push(value.title);
    if (value.reason) parts.push(value.reason);
    if (value.action) parts.push(value.action);
    if (value.revenue) parts.push("Revenue: " + value.revenue);
    if (value.pipeline) parts.push("Pipeline: " + value.pipeline);
    if (value.gross_margin) parts.push("Gross Margin: " + value.gross_margin);
    if (value.utilization) parts.push("Utilization: " + value.utilization);
    if (value.delivery) parts.push("Delivery: " + value.delivery);
    return parts.join("\n");
  }
  return String(value);
}

function renderBriefing(data) {
  const body = $("#briefing-body");
  if (!body) return;
  body.innerHTML = "";
  const sections = [
    ["Today", data.today],
    ["This Week", data.this_week],
    ["Decisions", data.decisions],
    ["Risks", data.risks],
    ["Opportunities", data.opportunities],
    ["Performance", data.performance],
    ["AI Ecosystem", data.ai],
    ["Recommendation", data.recommendation],
  ];
  sections.forEach(([title, value]) => {
    const text = briefingText(value);
    if (!text) return;
    const sec = el("div", "briefing-section");
    sec.append(el("h4", null, title));
    const lines = text.split("\n");
    lines.forEach((line) => {
      if (!line) return;
      const p = el("p", null, line);
      sec.appendChild(p);
    });
    body.appendChild(sec);
  });
}

function renderKPIs(data) {
  const grid = $("#kpi-grid");
  if (!grid) return;
  grid.innerHTML = "";
  const kpis = [
    ["Revenue", data.revenue, "gold", data.revenue_delta],
    ["Pipeline", data.pipeline, "blue", data.pipeline_delta],
    ["MRR", data.mrr, "green", data.mrr_delta],
    ["Gross Margin", data.gross_margin, "green", data.gross_margin_delta],
    ["Client Acquisition", data.client_acquisition, "", data.client_acquisition_delta],
    ["Conversion", data.conversion, "blue", data.conversion_delta],
    ["Project Profitability", data.project_profitability, "gold", data.project_profitability_delta],
    ["Automation Savings", data.automation_savings, "green", data.automation_savings_delta],
  ];
  kpis.forEach(([label, value, cls, delta]) => {
    if (value == null) return;
    const card = el("div", "kpi-card");
    card.append(el("span", "kpi-label", label), el("span", "kpi-value " + cls, value));
    if (delta != null) {
      const d = el("span", "kpi-delta " + (delta >= 0 ? "up" : "down"), (delta >= 0 ? "▲ " : "▼ ") + Math.abs(delta) + "%");
      card.appendChild(d);
    }
    grid.appendChild(card);
  });
}

function renderOpportunities(data) {
  const list = $("#opportunity-list");
  if (!list) return;
  list.innerHTML = "";
  const opps = data.opportunities || [];
  opps.forEach((opp, i) => {
    const item = el("div", "opportunity-item");
    item.append(el("span", "opportunity-rank", String(i + 1).padStart(2, "0")));

    const score = Math.round((opp.score || 0) * 100);
    const ring = el("div", "score-ring " + (score >= 75 ? "high" : score >= 50 ? "med" : "low"));
    ring.append(el("span", null, score));
    item.appendChild(ring);

    const body = el("div", "opportunity-body");
    body.append(el("div", "opportunity-name", opp.title || opp.name), el("div", "opportunity-desc", opp.summary || opp.description || ""));
    item.appendChild(body);

    const meta = el("div", "opportunity-meta");
    if (opp.impact) meta.append(el("span", null, "Impact " + opp.impact));
    if (opp.feasibility) meta.append(el("span", null, "Feasibility " + opp.feasibility));
    if (opp.urgency) meta.append(el("span", null, "Urgency " + opp.urgency));
    if (opp.category) meta.append(el("span", null, opp.category));
    item.appendChild(meta);

    list.appendChild(item);
  });
}

/* ------------------------------------------------------------------
   Projects
   ------------------------------------------------------------------ */

async function loadProjects() {
  const grid = $("#project-grid");
  if (!grid) return;
  try {
    const data = await api("/api/projects");
    const projects = data.projects || [];
    grid.innerHTML = "";
    projects.forEach((p) => {
      const card = el("div", "project-card");
      const head = el("div", "card-head");
      const titleWrap = el("div");
      titleWrap.append(el("div", "card-title", p.name), el("div", "card-sub", p.type || "Project"));
      head.append(titleWrap, el("span", "health-badge " + (p.health || "healthy"), p.health || "Healthy"));
      card.appendChild(head);

      const stats = el("div", "card-stats");
      const statDefs = [
        ["Progress", p.progress != null ? p.progress + "%" : "—", ""],
        ["Budget", fmtMoney(p.budget), ""],
        ["Margin", p.margin != null ? p.margin + "%" : "—", p.margin != null && p.margin < 20 ? "red" : "green"],
        ["Milestones", p.milestones || "—", ""],
      ];
      statDefs.forEach(([label, value, cls]) => {
        const stat = el("div", "card-stat");
        stat.append(el("span", "cs-label", label), el("span", "cs-value " + cls, value));
        stats.appendChild(stat);
      });
      card.appendChild(stats);

      const notes = el("div", "card-notes");
      (p.notes || []).forEach((n) => {
        const note = el("div", "card-note" + (n.startsWith("Risk") || n.startsWith("Block") ? " risk" : ""), n);
        notes.appendChild(note);
      });
      card.appendChild(notes);

      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = '<div class="panel" style="grid-column:1/-1">Unable to load projects: ' + esc(e.message) + "</div>";
  }
}

/* ------------------------------------------------------------------
   Clients
   ------------------------------------------------------------------ */

async function loadClients() {
  const grid = $("#client-grid");
  if (!grid) return;
  try {
    const data = await api("/api/clients");
    const clients = data.clients || [];
    grid.innerHTML = "";
    clients.forEach((c) => {
      const card = el("div", "client-card");
      const head = el("div", "card-head");
      const titleWrap = el("div");
      titleWrap.append(el("div", "card-title", c.name), el("div", "card-sub", c.industry || ""));
      head.append(titleWrap, el("span", "health-badge " + (c.health || "active"), c.health || "Active"));
      card.appendChild(head);

      const stats = el("div", "card-stats");
      const statDefs = [
        ["Revenue", fmtMoney(c.revenue), "gold"],
        ["Pipeline", fmtMoney(c.pipeline), "blue"],
        ["Projects", c.projects || "—", ""],
        ["Status", c.status || "—", ""],
      ];
      statDefs.forEach(([label, value, cls]) => {
        const stat = el("div", "card-stat");
        stat.append(el("span", "cs-label", label), el("span", "cs-value " + cls, value));
        stats.appendChild(stat);
      });
      card.appendChild(stats);

      const notes = el("div", "card-notes");
      (c.notes || []).forEach((n) => {
        const note = el("div", "card-note", n);
        notes.appendChild(note);
      });
      card.appendChild(notes);

      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = '<div class="panel" style="grid-column:1/-1">Unable to load clients: ' + esc(e.message) + "</div>";
  }
}

/* ------------------------------------------------------------------
   Automations
   ------------------------------------------------------------------ */

async function loadAutomations() {
  const map = $("#automation-map");
  if (!map) return;
  try {
    const data = await api("/api/automations");
    const flows = data.automations || [];
    map.innerHTML = "";
    flows.forEach((flow) => {
      const row = el("div", "automation-flow");
      const steps = [
        ["trigger", "⚡", flow.trigger || "Schedule"],
        ["agent", "◈", flow.agent || "Agent"],
        ["skill", "◆", flow.skill || "Skill"],
        ["tool", "⚙", flow.tool || "Tool"],
        ["action", "→", flow.action || "Action"],
        ["validation", "✓", flow.validation || "Validation"],
        ["outcome", "★", flow.outcome || "Outcome"],
      ];
      steps.forEach(([cls, icon, label], i) => {
        if (i > 0) row.append(el("span", "flow-arrow", "→"));
        const step = el("span", "flow-step " + cls);
        step.append(el("span", "step-icon", icon), document.createTextNode(label));
        row.appendChild(step);
      });
      const meta = el("span", "flow-meta");
      meta.append(el("span", "status", flow.status || "Active"));
      if (flow.autonomy) meta.append(el("span", null, flow.autonomy));
      row.appendChild(meta);
      map.appendChild(row);
    });
  } catch (e) {
    map.innerHTML = '<div class="panel">Unable to load automations: ' + esc(e.message) + "</div>";
  }
}

/* ------------------------------------------------------------------
   Governance / Analytics / Settings
   ------------------------------------------------------------------ */

function renderGovernance() {
  const grid = $("#governance-grid");
  if (!grid) return;
  grid.innerHTML = "";
  const cards = [
    {
      title: "AI Inventory",
      icon: "◈",
      items: [
        ["Agents", "15", "green"],
        ["Models", "4", ""],
        ["Prompts", "23", ""],
        ["Skills", "12", ""],
        ["Tools", "7", ""],
      ],
    },
    {
      title: "Permissions",
      icon: "🔐",
      items: [
        ["RBAC", "Enabled", "green"],
        ["MFA", "Enabled", "green"],
        ["Least Privilege", "Enforced", "green"],
        ["Tool Permissions", "Scoped", ""],
        ["Data Boundaries", "Active", ""],
      ],
    },
    {
      title: "Risk & Compliance",
      icon: "▲",
      items: [
        ["Open Risks", "3", "amber"],
        ["Critical", "1", "red"],
        ["Compliance", "EU AI Act", ""],
        ["Audit Trail", "Complete", "green"],
        ["Human Approvals", "2 pending", "amber"],
      ],
    },
    {
      title: "Autonomy",
      icon: "◆",
      items: [
        ["Level 0 — Observe", "2 agents", ""],
        ["Level 1 — Recommend", "4 agents", ""],
        ["Level 2 — Assist", "6 agents", ""],
        ["Level 3 — Execute", "2 agents", ""],
        ["Level 4 — Autonomous", "1 agent", ""],
      ],
    },
  ];
  cards.forEach((c) => {
    const card = el("div", "gov-card");
    const h = el("h4");
    h.append(el("span", "gov-icon", c.icon), document.createTextNode(c.title));
    card.appendChild(h);
    const list = el("div", "gov-list");
    c.items.forEach(([name, value, cls]) => {
      const item = el("div", "gov-item");
      item.append(el("span", "gov-name", name), el("span", "gov-value " + (cls || ""), value));
      list.appendChild(item);
    });
    card.appendChild(list);
    grid.appendChild(card);
  });
}

function renderAnalytics() {
  const grid = $("#analytics-grid");
  if (!grid) return;
  grid.innerHTML = "";
  const cards = [
    {
      title: "Revenue",
      icon: "◆",
      items: [
        ["ARR", "$2.4M", "gold"],
        ["MRR", "$198K", "gold"],
        ["Q1 Target", "$650K", ""],
        ["On Track", "Yes", "green"],
      ],
    },
    {
      title: "Pipeline",
      icon: "◈",
      items: [
        ["Total Pipeline", "$1.2M", "blue"],
        ["Proposals", "2", ""],
        ["Negotiation", "1", ""],
        ["Win Rate", "68%", "green"],
      ],
    },
    {
      title: "Delivery",
      icon: "⚙",
      items: [
        ["Utilization", "82%", "green"],
        ["On-time", "94%", "green"],
        ["Margin", "38%", "gold"],
        ["Blockers", "1", "amber"],
      ],
    },
    {
      title: "AI Impact",
      icon: "✦",
      items: [
        ["Automation Savings", "$48K/yr", "green"],
        ["Hours Saved", "320/mo", "green"],
        ["AI ROI", "4.2x", "gold"],
        ["Skills Deployed", "12", ""],
      ],
    },
  ];
  cards.forEach((c) => {
    const card = el("div", "gov-card");
    const h = el("h4");
    h.append(el("span", "gov-icon", c.icon), document.createTextNode(c.title));
    card.appendChild(h);
    const list = el("div", "gov-list");
    c.items.forEach(([name, value, cls]) => {
      const item = el("div", "gov-item");
      item.append(el("span", "gov-name", name), el("span", "gov-value " + (cls || ""), value));
      list.appendChild(item);
    });
    card.appendChild(list);
    grid.appendChild(card);
  });
}

function renderSettings() {
  const grid = $("#settings-grid");
  if (!grid) return;
  grid.innerHTML = "";

  // ---- Businesses card (management) ----
  const bizCard = el("div", "setting-card");
  bizCard.style.gridColumn = "1 / -1";
  const bizHead = el("h4");
  bizHead.append(el("span", "gov-icon", "🏢"), document.createTextNode("Businesses"));
  bizCard.appendChild(bizHead);

  const bizDesc = el("p", "setting-desc", "Manage the businesses HEER operates. Each business has its own data vault, clients, projects and intelligence.");
  bizCard.appendChild(bizDesc);

  // Add-business form
  const addForm = el("div", "biz-add-form");
  const nameInput = el("input", "biz-input");
  nameInput.placeholder = "Business name";
  nameInput.id = "biz-name-input";
  const typeInput = el("input", "biz-input");
  typeInput.placeholder = "Type (e.g. Restaurant)";
  typeInput.id = "biz-type-input";
  const rootInput = el("input", "biz-input");
  rootInput.placeholder = "Data root (optional)";
  rootInput.id = "biz-root-input";
  const iconInput = el("input", "biz-input biz-input-sm");
  iconInput.placeholder = "Icon";
  iconInput.id = "biz-icon-input";
  iconInput.value = "🏢";
  iconInput.maxLength = 4;
  const colorInput = el("input", "biz-input biz-input-sm");
  colorInput.placeholder = "Hex color";
  colorInput.id = "biz-color-input";
  colorInput.value = "#4d9fff";
  const tagInput = el("input", "biz-input");
  tagInput.placeholder = "Tagline (optional)";
  tagInput.id = "biz-tag-input";
  const addBtn = el("button", "btn-mini approve", "+ Add");
  addBtn.addEventListener("click", async () => {
    const name = nameInput.value.trim();
    if (!name) { nameInput.focus(); return; }
    try {
      const res = await fetch("/api/business/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          type: typeInput.value.trim(),
          data_root: rootInput.value.trim(),
          icon: iconInput.value.trim() || "🏢",
          color: colorInput.value.trim() || "#4d9fff",
          tagline: tagInput.value.trim(),
        }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Failed to add business");
      // Clear form
      nameInput.value = ""; typeInput.value = ""; rootInput.value = "";
      iconInput.value = "🏢"; colorInput.value = "#4d9fff"; tagInput.value = "";
      // Refresh
      await loadBusinesses();
      renderSettingsBusinessList();
    } catch (e) {
      addMsg("Could not add business: " + e.message, "heer");
    }
  });

  const formRow = el("div", "biz-form-row");
  formRow.append(iconInput, colorInput, tagInput);
  addForm.append(nameInput, typeInput, rootInput, formRow, addBtn);
  bizCard.appendChild(addForm);

  // Business list
  const bizList = el("div", "biz-list");
  bizList.id = "settings-biz-list";
  bizCard.appendChild(bizList);

  grid.appendChild(bizCard);

  // ---- Existing setting cards ----
  const cards = [
    {
      title: "Autonomy",
      icon: "◆",
      rows: [
        ["Global Autonomy", "Assisted (L2)"],
        ["Allow autonomous research", "On"],
        ["Allow skill creation", "On"],
        ["Require approval for new skills", "On"],
      ],
    },
    {
      title: "Personalization",
      icon: "◈",
      rows: [
        ["Learn communication style", "On"],
        ["Learn decision patterns", "On"],
        ["Track recurring tasks", "On"],
        ["Inspect learned data", "View"],
      ],
    },
    {
      title: "Security",
      icon: "🔐",
      rows: [
        ["MFA", "Enabled"],
        ["Session timeout", "30 min"],
        ["Audit logging", "Complete"],
        ["Data encryption", "AES-256"],
      ],
    },
    {
      title: "Integrations",
      icon: "⚙",
      rows: [
        ["Microsoft 365", "Connected"],
        ["Google Workspace", "Connected"],
        ["Slack", "Connected"],
        ["GitHub", "Connected"],
      ],
    },
  ];
  cards.forEach((c) => {
    const card = el("div", "setting-card");
    const h = el("h4");
    h.append(el("span", "gov-icon", c.icon), document.createTextNode(c.title));
    card.appendChild(h);
    c.rows.forEach(([label, value]) => {
      const row = el("div", "setting-row");
      row.append(el("span", "setting-label", label), el("span", "setting-value", value));
      card.appendChild(row);
    });
    grid.appendChild(card);
  });

  // Populate business list
  renderSettingsBusinessList();
}

function renderSettingsBusinessList() {
  const list = $("#settings-biz-list");
  if (!list) return;
  list.innerHTML = "";
  const businesses = state.businesses || [];
  const cur = state.currentBusiness;
  businesses.forEach((b) => {
    const row = el("div", "biz-list-item" + (cur && cur.id === b.id ? " active" : ""));
    row.style.setProperty("--biz-color", b.color || "#4d9fff");

    const icon = el("span", "biz-list-icon", b.icon || "🏢");
    const info = el("div", "biz-list-info");
    const nameRow = el("div", "biz-list-name");
    nameRow.append(document.createTextNode(b.name || b.id));
    if (cur && cur.id === b.id) nameRow.append(el("span", "biz-current-badge", "Current"));
    info.appendChild(nameRow);
    info.appendChild(el("div", "biz-list-meta", (b.type || "Business") + (b.tagline ? " · " + b.tagline : "")));

    const actions = el("div", "biz-list-actions");
    if (!(cur && cur.id === b.id)) {
      const switchBtn = el("button", "btn-mini", "Switch");
      switchBtn.addEventListener("click", () => switchBusiness(b.id));
      actions.appendChild(switchBtn);
    }
    const editBtn = el("button", "btn-mini", "Edit");
    editBtn.addEventListener("click", () => {
      // Inline edit: prompt for new name/tagline/color
      const newName = prompt("Business name:", b.name || "");
      if (newName == null) return;
      const newTagline = prompt("Tagline:", b.tagline || "");
      if (newTagline == null) return;
      const newColor = prompt("Color (hex):", b.color || "#4d9fff");
      if (newColor == null) return;
      updateBusiness(b.id, { name: newName.trim(), tagline: newTagline.trim(), color: newColor.trim() });
    });
    actions.appendChild(editBtn);

    row.append(icon, info, actions);
    list.appendChild(row);
  });
}

async function updateBusiness(id, fields) {
  try {
    const res = await fetch("/api/business/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ business_id: id, ...fields }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "Failed to update business");
    await loadBusinesses();
    renderSettingsBusinessList();
    addMsg("Business updated.", "heer");
  } catch (e) {
    addMsg("Could not update business: " + e.message, "heer");
  }
}

/* ------------------------------------------------------------------
   Knowledge Graph (Canvas)
   ------------------------------------------------------------------ */

async function loadGraph() {
  try {
    const data = await api("/api/graph");
    state.graph = data;
    renderGraph();
  } catch (e) {
    /* silent */
  }
}

function renderGraph() {
  const canvas = $("#graph-render");
  if (!canvas || !state.graph) return;
  const ctx = canvas.getContext("2d");
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * (window.devicePixelRatio || 1);
  canvas.height = rect.height * (window.devicePixelRatio || 1);
  ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

  const W = rect.width;
  const H = rect.height;
  const nodes = state.graph.nodes || [];
  const links = state.graph.links || [];

  // Simple force layout (deterministic-ish)
  if (Object.keys(state.graphPositions).length === 0) {
    const cx = W / 2;
    const cy = H / 2;
    const radius = Math.min(W, H) * 0.32;
    nodes.forEach((n, i) => {
      const angle = (i / Math.max(nodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
      state.graphPositions[n.id] = {
        x: cx + radius * Math.cos(angle) + (Math.random() - 0.5) * 40,
        y: cy + radius * Math.sin(angle) + (Math.random() - 0.5) * 40,
      };
    });
  }

  const typeColors = {
    client: "#d4af37",
    project: "#4d9fff",
    note: "#3ddc84",
    report: "#c0c6cc",
    company: "#f5a623",
    venture: "#e5484d",
    person: "#e8eaed",
  };

  // Links
  ctx.clearRect(0, 0, W, H);
  ctx.lineWidth = 1;
  links.forEach((l) => {
    const a = state.graphPositions[l.source];
    const b = state.graphPositions[l.target];
    if (!a || !b) return;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.stroke();
  });

  // Nodes
  nodes.forEach((n) => {
    const p = state.graphPositions[n.id];
    if (!p) return;
    const color = typeColors[n.type] || "#9aa3ad";
    const size = 4 + Math.min(n.degree || 0, 8) * 1.2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.85;
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Label
    ctx.font = "10px 'SF Pro Text', -apple-system, sans-serif";
    ctx.fillStyle = "rgba(154, 163, 173, 0.8)";
    ctx.textAlign = "center";
    ctx.fillText(n.title.length > 24 ? n.title.slice(0, 22) + "…" : n.title, p.x, p.y + size + 12);
  });

  // Tooltip
  const tooltip = $("#graph-tooltip");
  canvas.onmousemove = (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    let found = null;
    for (const n of nodes) {
      const p = state.graphPositions[n.id];
      if (!p) continue;
      const size = Math.max(4 + Math.min(n.degree || 0, 8) * 1.2, 8);
      if (Math.hypot(mx - p.x, my - p.y) < size + 6) {
        found = n;
        break;
      }
    }
    if (found) {
      tooltip.style.display = "block";
      tooltip.style.left = (mx + 14) + "px";
      tooltip.style.top = (my + 10) + "px";
      tooltip.innerHTML =
        '<div class="tt-title">' + esc(found.title) + "</div>" +
        '<div class="tt-type">' + esc(found.type) + "</div>" +
        '<div class="tt-text">' + esc(found.rel || "") + "</div>";
    } else {
      tooltip.style.display = "none";
    }
  };
  canvas.onmouseleave = () => { tooltip.style.display = "none"; };
}

/* ------------------------------------------------------------------
   Chat / Command
   ------------------------------------------------------------------ */

function openChat() {
  $("#chat-panel").classList.add("open");
  $("#chat-input").focus();
}

function closeChat() {
  $("#chat-panel").classList.remove("open");
}

function addMsg(text, who, tool) {
  const log = $("#chat-log");
  const msg = el("div", "msg " + who, text);
  if (tool) {
    const t = el("span", "msg-tool", "⚙ " + tool);
    msg.appendChild(t);
  }
  log.appendChild(msg);
  log.scrollTop = log.scrollHeight;
}

function welcomeMessage() {
  const h = new Date().getHours();
  const greeting = h < 5 ? "Good night" : h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  const biz = state.currentBusiness;
  const bizName = biz ? biz.name : "the agency";
  return (
    greeting + ", Pankaj. I'm HEER — your Autonomous AI Operating Partner.\n\n" +
    "I've been watching " + bizName + " while you were away. The agents are active, " +
    "the knowledge base is growing, and I've prepared your priorities, decisions, " +
    "and opportunities.\n\n" +
    "Ask me to brief you, find opportunities, review the pipeline, or show you " +
    "what I've learned. I'm here to execute — not just to chat."
  );
}

async function sendChat(message) {
  if (!message) return;
  addMsg(message, "user");
  $("#chat-status").textContent = "thinking";
  try {
    const data = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const reply = data.reply || "No response.";
    addMsg(reply, "heer", data.tool);
    state.lastReply = reply;
    $("#chat-status").textContent = data.llm ? "llm" : "local";
    autoSpeak(reply);
  } catch (err) {
    addMsg("Sorry — " + err.message, "heer");
    $("#chat-status").textContent = "error";
  }
}

/* ------------------------------------------------------------------
   Voice
   ------------------------------------------------------------------ */

function setChatStatus(txt) {
  const el = $("#chat-status");
  if (el) el.textContent = txt;
}

function speakWithBrowser(text) {
  if (!("speechSynthesis" in window)) return false;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0;
    u.pitch = 1.0;
    u.volume = 1.0;
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find((v) => /en[-_]US/i.test(v.lang) && /female|samantha|zira|aria|jenny/i.test(v.name)) ||
                      voices.find((v) => /en[-_]US/i.test(v.lang)) ||
                      voices[0];
    if (preferred) u.voice = preferred;
    window.speechSynthesis.speak(u);
    return true;
  } catch (err) {
    return false;
  }
}

async function speakLast() {
  if (!state.lastReply) return;
  try {
    const res = await fetch("/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: state.lastReply }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "TTS failed");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    try {
      await audio.play();
    } catch (playErr) {
      // Autoplay blocked or audio decode failed — fall back to browser TTS
      speakWithBrowser(state.lastReply);
    }
  } catch (err) {
    // Server TTS unavailable — fall back to browser speech synthesis
    if (!speakWithBrowser(state.lastReply)) {
      addMsg("Voice unavailable — " + err.message, "heer");
    }
  }
}

function autoSpeak(text) {
  if (state.autoSpeak && text) {
    speakLast();
  }
}

function toggleAutoSpeak() {
  state.autoSpeak = !state.autoSpeak;
  const btn = $("#chat-autospeak");
  if (btn) {
    btn.classList.toggle("active", state.autoSpeak);
    btn.title = state.autoSpeak ? "Auto-speak replies (on)" : "Auto-speak replies (off)";
  }
}

/* --- Voice input: Web Speech API (browser-native) + PCM WAV recorder --- */

function webSpeechSupported() {
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

function startWebSpeech() {
  if (state.webSpeechActive) return;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return false;
  try {
    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.continuous = false;

    rec.onstart = () => {
      state.webSpeechActive = true;
      setChatStatus("listening");
    };
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript.trim();
      if (text) {
        $("#chat-input").value = text;
        sendChat(text);
      } else {
        addMsg("Could not hear you clearly.", "heer");
        setChatStatus("ready");
      }
    };
    rec.onerror = (e) => {
      state.webSpeechActive = false;
      setChatStatus("ready");
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        addMsg("Microphone permission denied. Allow mic access in your browser.", "heer");
      } else if (e.error !== "aborted" && e.error !== "no-speech") {
        addMsg("Voice input unavailable — " + e.error, "heer");
      }
    };
    rec.onend = () => {
      state.webSpeechActive = false;
      setChatStatus("ready");
    };

    state.webSpeechRec = rec;
    rec.start();
    return true;
  } catch (err) {
    return false;
  }
}

function stopWebSpeech() {
  if (state.webSpeechRec && state.webSpeechActive) {
    try { state.webSpeechRec.stop(); } catch (err) { /* noop */ }
    state.webSpeechActive = false;
    setChatStatus("ready");
  }
}

/* --- PCM WAV recorder (Web Audio API) — no ffmpeg needed on the server --- */

function encodeWav(samples, sampleRate) {
  // 16-bit mono PCM WAV — the format the macOS Speech framework accepts natively.
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeStr = (offset, str) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  };

  writeStr(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);          // PCM chunk size
  view.setUint16(20, 1, true);           // audio format = PCM
  view.setUint16(22, 1, true);           // mono
  view.setUint32(24, sampleRate, true);  // sample rate
  view.setUint32(28, sampleRate * 2, true); // byte rate
  view.setUint16(32, 2, true);           // block align
  view.setUint16(34, 16, true);          // bits per sample
  writeStr(36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }
  return new Blob([view], { type: "audio/wav" });
}

async function startPcmRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const Ctx = window.AudioContext || window.webkitAudioContext;
    const ctx = new Ctx();
    const source = ctx.createMediaStreamSource(stream);
    const processor = ctx.createScriptProcessor(4096, 1, 1);

    state.audioCtx = ctx;
    state.pcmStream = stream;
    state.pcmSource = source;
    state.pcmProcessor = processor;
    state.pcmSamples = [];
    state.pcmSampleRate = ctx.sampleRate;

    processor.onaudioprocess = (e) => {
      if (!state.recording) return;
      const input = e.inputBuffer.getChannelData(0);
      for (let i = 0; i < input.length; i++) {
        state.pcmSamples.push(input[i]);
      }
    };

    source.connect(processor);
    processor.connect(ctx.destination); // required for the processor to fire
    state.recording = true;
    setChatStatus("recording");
    return true;
  } catch (err) {
    addMsg("Microphone unavailable — " + err.message, "heer");
    setChatStatus("error");
    return false;
  }
}

async function stopPcmStream() {
  if (!state.recording) return;
  state.recording = false;

  const ctx = state.audioCtx;
  const stream = state.pcmStream;
  const processor = state.pcmProcessor;
  const source = state.pcmSource;
  const samples = state.pcmSamples;

  state.audioCtx = null;
  state.pcmStream = null;
  state.pcmProcessor = null;
  state.pcmSource = null;
  state.pcmSamples = [];

  try {
    if (source && processor) source.disconnect(processor);
    if (processor) processor.disconnect();
    if (stream) stream.getTracks().forEach((t) => t.stop());
    if (ctx && ctx.state !== "closed") ctx.close();
  } catch (err) { /* noop */ }

  if (!samples.length) {
    addMsg("Could not hear you clearly.", "heer");
    setChatStatus("ready");
    return;
  }

  const blob = encodeWav(samples, state.pcmSampleRate);
  const fd = new FormData();
  fd.append("audio", blob, "clip.wav");
  setChatStatus("listening");
  try {
    const res = await fetch("/api/listen", { method: "POST", body: fd });
    const data = await res.json();
    if (data.text) {
      $("#chat-input").value = data.text;
      sendChat(data.text);
    } else {
      addMsg("Could not hear you clearly.", "heer");
      setChatStatus("ready");
    }
  } catch (err) {
    addMsg("Voice unavailable — " + err.message, "heer");
    setChatStatus("error");
  }
}

/* --- Tap-to-toggle mic control --- */

function setMicActive(active) {
  const mic = $("#chat-mic");
  if (!mic) return;
  mic.classList.toggle("recording", active);
  mic.title = active ? "Stop recording" : "Speak to HEER";
}

async function toggleRecording() {
  if (state.recording) {
    // Stop: Web Speech first, then PCM stream
    if (state.webSpeechActive) {
      stopWebSpeech();
      state.recording = false;
      setMicActive(false);
      return;
    }
    await stopPcmStream();
    setMicActive(false);
    return;
  }

  // Start: Web Speech API first (no server dependency)
  if (webSpeechSupported()) {
    if (startWebSpeech()) {
      state.recording = true;
      setMicActive(true);
      return;
    }
  }

  // Fallback: PCM WAV recorder → server /api/listen
  const ok = await startPcmRecording();
  if (ok) setMicActive(true);
}

/* ------------------------------------------------------------------
   Missions / Task-Graph Execution
   ------------------------------------------------------------------ */

async function loadMissions() {
  const list = $("#mission-list");
  if (!list) return;
  try {
    const data = await api("/api/missions");
    renderMissionList(data.missions || []);
  } catch (e) {
    list.innerHTML = '<div class="panel">Unable to load missions: ' + esc(e.message) + "</div>";
  }
}

function renderMissionList(missions) {
  const list = $("#mission-list");
  if (!list) return;
  const count = $("#mission-count");
  if (count) count.textContent = missions.length;
  list.innerHTML = "";
  if (!missions.length) {
    list.appendChild(el("div", "mission-empty", "No missions yet. Create one to start executing a task DAG."));
    return;
  }
  missions.forEach((m) => {
    const item = el("div", "mission-item");
    const head = el("div", "mission-item-head");
    head.append(
      el("span", "mission-item-name", m.name || m.goal || m.id),
      el("span", "mission-item-status " + (m.status || "planned"), m.status || "planned")
    );
    item.appendChild(head);
    const goal = el("div", "mission-item-goal", m.goal || "");
    item.appendChild(goal);
    const meta = el("div", "mission-item-meta");
    const statuses = m.task_statuses || {};
    const total = m.task_count || 0;
    const done = statuses.completed || 0;
    meta.append(
      el("span", null, total + " tasks"),
      el("span", null, done + " completed"),
      el("span", null, m.owner || "Pankaj")
    );
    item.appendChild(meta);
    item.addEventListener("click", () => {
      loadMissionDetail(m.id);
    });
    list.appendChild(item);
  });
}

async function loadMissionDetail(missionId) {
  const panel = $("#mission-detail-panel");
  if (!panel) return;
  try {
    const data = await api("/api/missions/" + missionId);
    const m = data.mission;
    if (!m) throw new Error("Mission not found");
    renderMissionDetail(m);
  } catch (e) {
    addMsg("Could not load mission: " + e.message, "heer");
  }
}

function renderMissionDetail(m) {
  const panel = $("#mission-detail-panel");
  if (!panel) return;
  panel.hidden = false;
  $("#mission-detail-title").textContent = m.name || m.goal || m.id;
  const statusBadge = $("#mission-detail-status");
  statusBadge.textContent = m.status || "planned";
  statusBadge.className = "panel-badge " + (m.status || "planned");

  const body = $("#mission-detail-body");
  body.innerHTML = "";

  // Goal
  if (m.goal) body.appendChild(el("div", "mission-detail-goal", m.goal));

  // Task DAG
  const tasks = m.tasks || [];
    const dag = el("div", "mission-dag");
    tasks.forEach((t) => {
      const node = el("div", "dag-node " + (t.status || "pending"));
      const head = el("div", "dag-node-head");
      head.append(
        el("span", "dag-node-tool", t.tool || "tool"),
        el("span", "dag-node-name", t.name || t.action || "Task"),
        el("span", "dag-node-status", t.status || "pending")
      );
      node.appendChild(head);
      if (t.detail || t.description) {
        node.appendChild(el("div", "dag-node-detail", t.detail || t.description));
      }
      if (t.depends_on && t.depends_on.length) {
        node.appendChild(el("div", "dag-node-deps", "Depends on: " + t.depends_on.join(", ")));
      }
      dag.appendChild(node);
    });
    body.appendChild(dag);
  });
}

function showApproval(title, reason, evidence, confidence) {
  const modal = $("#approval-modal");
  const body = $("#modal-body");
  body.innerHTML = "";
  body.append(el("p", null, title));
  const reasonBox = el("div", "modal-reason");
  reasonBox.innerHTML = "<strong>Reason:</strong> " + esc(reason) + "<br><br><strong>Evidence:</strong> " + esc(evidence) + "<br><br><strong>Confidence:</strong> " + esc(confidence || "High");
  body.appendChild(reasonBox);
  modal.classList.add("open");
}

function closeApproval() {
  $("#approval-modal").classList.remove("open");
}

/* ------------------------------------------------------------------
   Init
   ------------------------------------------------------------------ */

function init() {
  renderHero();

  // Business switcher
  const bizBtn = $("#business-switcher-btn");
  if (bizBtn) {
    bizBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const dd = $("#business-dropdown");
      if (dd) dd.classList.toggle("open");
    });
  }
  document.addEventListener("click", (e) => {
    const sw = $("#business-switcher");
    if (sw && !sw.contains(e.target)) closeBusinessDropdown();
  });
  const bizAdd = $("#business-add-btn");
  if (bizAdd) {
    bizAdd.addEventListener("click", () => {
      closeBusinessDropdown();
      switchView("settings");
      addMsg("Business management is available in Settings. Ask HEER to add a business.", "heer");
    });
  }
  loadBusinesses();

  // Navigation
  $$(".nav-link").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      switchView(a.dataset.view);
    });
  });

  // Command bar
  const cmdInput = $("#command-input");
  const sendCmd = () => {
    const text = cmdInput.value.trim();
    if (!text) return;
    cmdInput.value = "";
    openChat();
    sendChat(text);
  };
  $("#command-send").addEventListener("click", sendCmd);
  cmdInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendCmd();
  });

  // Suggestions
  $$(".suggestion").forEach((s) => {
    s.addEventListener("click", () => {
      cmdInput.value = s.dataset.cmd;
      sendCmd();
    });
  });

  // Global command button
  $("#global-command-btn").addEventListener("click", () => {
    openChat();
    $("#chat-input").focus();
  });

  // Chat
  $("#chat-send").addEventListener("click", () => {
    const text = $("#chat-input").value.trim();
    if (text) {
      $("#chat-input").value = "";
      sendChat(text);
    }
  });
  $("#chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const text = $("#chat-input").value.trim();
      if (text) {
        $("#chat-input").value = "";
        sendChat(text);
      }
    }
  });
  $("#chat-close").addEventListener("click", closeChat);
  $("#chat-speaker").addEventListener("click", speakLast);
  $("#chat-autospeak").addEventListener("click", toggleAutoSpeak);
  $("#chat-mic").addEventListener("click", toggleRecording);

  // Proactive greeting — HEER introduces itself when the command center opens
  const log = $("#chat-log");
  if (log && log.children.length === 0) {
    const welcome = welcomeMessage();
    addMsg(welcome, "heer");
    state.lastReply = welcome;
    autoSpeak(welcome);
  }

  // Modal
  $("#modal-close").addEventListener("click", closeApproval);
  $("#modal-approve").addEventListener("click", () => {
    closeApproval();
    addMsg("Approved. HEER will execute within defined boundaries.", "heer");
  });
  $("#modal-deny").addEventListener("click", () => {
    closeApproval();
    addMsg("Denied. Action will not proceed.", "heer");
  });

  // Approval buttons in command center
  document.addEventListener("click", (e) => {
    const action = e.target.dataset && e.target.dataset.action;
    if (!action) return;
    if (action === "approve" || action === "approve-skill") {
      showApproval(
        "HEER requests approval to register a new skill.",
        "HEER detected a recurring proposal-generation workflow performed 7 times. Converting it into an autonomous skill would save ~4 hours per proposal.",
        "7 observed executions · 96% success rate · QA Agent validation passed",
        "High"
      );
    } else if (action === "approve-research") {
      showApproval(
        "HEER requests approval to run autonomous research.",
        "Research Agent identified a knowledge gap on EU AI Act enforcement timelines affecting the Meridian Bank engagement.",
        "Gap detected in knowledge graph · 3 authoritative sources identified",
        "High"
      );
    } else if (action === "deny" || action === "deny-skill" || action === "deny-research") {
      addMsg("Action denied. HEER will not proceed.", "heer");
    } else if (action === "review") {
      addMsg("Opening review context for Sip & Slice expansion…", "heer");
    }
  });

  // Graph search
  $("#graph-search").addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    if (!q) {
      renderGraph();
      return;
    }
    const nodes = state.graph ? state.graph.nodes : [];
    const matches = nodes.filter((n) => n.title.toLowerCase().includes(q));
    if (matches.length > 0) {
      const first = matches[0];
      const p = state.graphPositions[first.id];
      if (p) {
        const canvas = $("#graph-render");
        const rect = canvas.parentElement.getBoundingClientRect();
        state.graphOffset = { x: rect.width / 2 - p.x, y: rect.height / 2 - p.y };
        renderGraph();
      }
    }
  });
  $("#graph-reset").addEventListener("click", () => {
    state.graphPositions = {};
    state.graphOffset = { x: 0, y: 0 };
    loadGraph();
  });

  // Load data
  loadGraph();
  startActivityLoop();

  // Load agents for constellation
  api("/api/agents").then((data) => {
    renderConstellation(data.agents || []);
  }).catch(() => {});

  // Load activity
  api("/api/activity").then((data) => {
    renderActivity(data.items || []);
  }).catch(() => {});

  // Load learning center
  api("/api/learning").then((data) => {
    renderLearning(data);
  }).catch(() => {});

  // Load memory types
  api("/api/status").then((data) => {
    renderMemory(data);
  }).catch(() => {});

  // Load briefing into hero insights
  api("/api/briefing").then((data) => {
    renderHeroInsights(data);
  }).catch(() => {});

  // Load business KPIs
  api("/api/business").then((data) => {
    renderHeroKPIs(data);
  }).catch(() => {});

  // Load opportunities
  api("/api/opportunities").then((data) => {
    renderHeroOpportunities(data);
  }).catch(() => {});

  // System status
  api("/api/system").then((data) => {
    if (data.nodes != null) {
      const label = $("#agent-count-label");
      if (label) label.textContent = data.nodes;
    }
  }).catch(() => {});

  // Keyboard shortcut: Cmd/Ctrl+K opens command
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      $("#command-input").focus();
    }
    if (e.key === "Escape") {
      closeChat();
      closeApproval();
    }
  });
}

function renderLearning(data) {
  const center = $("#learning-center");
  if (!center) return;
  center.innerHTML = "";
  const items = data.items || [];
  items.forEach((item) => {
    const box = el("div", "learning-item");
    box.append(
      el("span", "li-type " + (item.type || "growth"), item.type || "Growth"),
      el("span", "li-text", item.text || ""),
      el("span", "li-meta", item.meta || "")
    );
    center.appendChild(box);
  });
}

function renderMemory(data) {
  const types = $("#memory-types");
  if (!types) return;
  types.innerHTML = "";
  const memoryTypes = [
    ["Working Memory", "Active context"],
    ["Personal Context", "Pankaj's preferences"],
    ["Project Memory", "Project state"],
    ["Client Memory", "Client intelligence"],
    ["Episodic Memory", "Past events"],
    ["Semantic Memory", "Facts & concepts"],
    ["Procedural Memory", "How-to knowledge"],
    ["Strategic Memory", "Goals & priorities"],
    ["Skill Memory", "Reusable capabilities"],
    ["Decision Memory", "Past decisions"],
  ];
  memoryTypes.forEach(([name, desc]) => {
    const box = el("div", "memory-type");
    box.append(el("span", "mt-name", name), el("span", "mt-desc", desc));
    types.appendChild(box);
  });
}

function renderHeroInsights(data) {
  const container = $("#hero-insights");
  if (!container) return;
  container.innerHTML = "";

  // Extract meaningful strings from the briefing payload
  const opp = Array.isArray(data.opportunities) && data.opportunities[0]
    ? data.opportunities[0].title || data.opportunities[0].detail
    : null;
  const decision = Array.isArray(data.decisions) && data.decisions[0]
    ? data.decisions[0].title
    : null;
  const rec = data.recommendation && typeof data.recommendation === "object"
    ? data.recommendation.title
    : data.recommendation;

  const insights = [
    { cls: "gold", icon: "◆", label: "Strategic Opportunity", text: opp || "3 opportunities could increase the current AI pipeline by 38%." },
    { cls: "amber", icon: "▲", label: "Requires Attention", text: decision || "Two client proposals require your review before close." },
    { cls: "blue", icon: "◈", label: "Autonomy", text: rec || "A recurring workflow can now be automated. Awaiting approval." },
    { cls: "green", icon: "✦", label: "Learning", text: "HEER learned a new proposal-generation skill from your last engagements." },
  ];
  insights.forEach((ins) => {
    const card = el("div", "insight-card " + ins.cls);
    card.append(el("div", "insight-icon", ins.icon));
    const body = el("div", "insight-body");
    body.append(el("span", "insight-label", ins.label), el("span", "insight-text", ins.text));
    card.appendChild(body);
    container.appendChild(card);
  });
}

function renderHeroKPIs(data) {
  const grid = $("#kpi-grid");
  if (!grid) return;
  grid.innerHTML = "";
  const kpis = [
    ["Revenue", data.revenue, "gold"],
    ["Pipeline", data.pipeline, "blue"],
    ["MRR", data.mrr, "green"],
    ["Gross Margin", data.gross_margin, "green"],
  ];
  kpis.forEach(([label, value, cls]) => {
    if (value == null) return;
    const card = el("div", "kpi-card");
    card.append(el("span", "kpi-label", label), el("span", "kpi-value " + cls, value));
    grid.appendChild(card);
  });
}

function renderHeroOpportunities(data) {
  const list = $("#opportunity-list");
  if (!list) return;
  list.innerHTML = "";
  const opps = (data.opportunities || []).slice(0, 5);
  opps.forEach((opp, i) => {
    const item = el("div", "opportunity-item");
    item.append(el("span", "opportunity-rank", String(i + 1).padStart(2, "0")));
    const score = Math.round((opp.score || 0) * 100);
    const ring = el("div", "score-ring " + (score >= 75 ? "high" : score >= 50 ? "med" : "low"));
    ring.append(el("span", null, score));
    item.appendChild(ring);
    const body = el("div", "opportunity-body");
    body.append(el("div", "opportunity-name", opp.title || opp.name), el("div", "opportunity-desc", opp.summary || opp.description || ""));
    item.appendChild(body);
    list.appendChild(item);
  });
}

/* Boot */
document.addEventListener("DOMContentLoaded", init);