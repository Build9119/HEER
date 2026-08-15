#!/usr/bin/env python3
"""skills.py — HEER Master Skill Set + Auto-Learning Engine.

The master skill set is the complete catalog of skills HEER can learn,
grow, and execute. Each skill has a definition, workflow, decision logic,
validation gates, and autonomy level.

The learning engine:
  - Persists skill state, learnings, executions, and knowledge gaps in SQLite
  - Auto-discovers new skills from repeated patterns in the vault
  - Auto-improves existing skills from execution outcomes
  - Tracks knowledge gaps and proposes learning actions
  - Grows HEER's autonomy as skills mature

Run:  python3 -m agent.skills
"""

import datetime as _dt
import json
import os
import re
import sqlite3

from . import data

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(BASE, "memory")
SKILLS_DB = os.path.join(MEMORY_DIR, "skills.db")


# ---------------------------------------------------------------------------
# Master Skill Set — the full catalog HEER can learn from
# ---------------------------------------------------------------------------

MASTER_SKILLS = [
    # ── Business & Strategy ──────────────────────────────────────────────
    {
        "id": "enterprise_ai_assessment",
        "name": "Enterprise AI Assessment",
        "category": "business",
        "purpose": "Assess a client's AI readiness and produce a structured assessment report.",
        "version": "2.4",
        "success_rate": 0.96,
        "executions": 48,
        "autonomy": 2,
        "inputs": ["client profile", "current stack", "business goals"],
        "tools": ["vault_search", "assessment_template", "report_gen"],
        "workflow": ["Gather client context", "Map AI opportunities", "Score readiness", "Generate report"],
        "decision_logic": "Score each opportunity by Impact × Feasibility × Urgency × Strategic Value.",
        "output": "Structured AI readiness assessment report.",
        "validation": "QA Agent validates against 12 quality gates.",
        "dependencies": ["vault", "report_gen"],
        "permissions": ["read:clients", "read:projects", "write:reports"],
        "risk": "low",
        "owner": "Delivery Agent",
        "status": "validated",
        "category": "Business & Strategy",
        "prerequisites": [],
        "learning_path": ["client_health", "market_scan", "proposal_generation"],
    },
    {
        "id": "ceo_briefing",
        "name": "CEO Briefing",
        "category": "Business & Strategy",
        "purpose": "Synthesize the agency's state into a daily executive briefing.",
        "version": "2.1",
        "success_rate": 0.95,
        "executions": 40,
        "autonomy": 2,
        "inputs": ["all agent states", "vault context"],
        "tools": ["all_agents", "briefing_engine"],
        "workflow": ["Collect agent states", "Aggregate insights", "Rank by importance", "Generate briefing"],
        "output": "Daily CEO briefing with priorities, decisions, risks, opportunities.",
        "validation": "CEO Agent validates completeness.",
        "dependencies": ["all_agents"],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Chief-of-Staff Agent",
        "status": "validated",
        "prerequisites": [],
        "learning": ["business_pulse", "opportunity_radar", "risk_detection"],
    },
    {
        "id": "business_health",
        "name": "Business Health Score",
        "category": "Business & Strategy",
        "purpose": "Compute a composite health score for the business across revenue, delivery, clients, and risk.",
        "version": "1.0",
        "success_rate": 0.9,
        "executions": 12,
        "autonomy": 2,
        "inputs": ["financial data", "client health", "delivery status", "risk flags"],
        "tools": ["financial_db", "client_db", "project_tracker"],
        "workflow": ["Load all business dimensions", "Score each dimension", "Weighted composite", "Trend vs last period"],
        "decision_logic": "Health = 0.3×Revenue + 0.2×Margin + 0.2×Client Health + 0.15×Delivery + 0.15×Risk.",
        "output": "Composite health score with dimension breakdown.",
        "validation": "CEO Agent reviews composite.",
        "dependencies": ["financial_db", "client_db"],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Chief-of-Staff Agent",
        "status": "validated",
        "prerequisites": ["margin_analysis", "client_health"],
        "learning_path": ["revenue_forecast", "risk_detection"],
    },
    {
        "id": "revenue_forecast",
        "name": "Revenue Forecasting",
        "category": "Business & Strategy",
        "purpose": "Forecast revenue from pipeline, historical trends, and seasonality.",
        "version": "0.9",
        "success_rate": 0.82,
        "autonomy": 1,
        "inputs": ["pipeline", "historical revenue", "conversion rates"],
        "tools": ["financial_db", "forecast_engine"],
        "workflow": ["Load pipeline", "Apply conversion rates", "Seasonality adjustment", "Generate forecast"],
        "decision_logic": "Forecast = Σ(pipeline stage × stage conversion) × seasonality factor.",
        "output": "Revenue forecast with confidence bands.",
        "validation": "Financial Intelligence Agent reviews.",
        "dependencies": ["financial_db"],
        "permissions": ["read:finance"],
        "risk": "medium",
        "owner": "Financial Intelligence Agent",
        "status": "learning",
        "prerequisites": ["margin_analysis"],
        "learning_path": ["pricing_strategy"],
    },
    {
        "id": "pricing_strategy",
        "name": "Pricing Strategy",
        "category": "Business & Strategy",
        "purpose": "Recommend pricing models and anchors from client context and market benchmarks.",
        "version": "1.1",
        "success_rate": 0.87,
        "autonomy": 1,
        "inputs": ["client context", "scope", "market benchmarks"],
        "tools": ["pricing_engine", "market_research"],
        "workflow": ["Load pricing principles", "Map scope to value", "Benchmark market", "Recommend model"],
        "decision_logic": "Select value-based vs hourly vs retainer from client signals and margin targets.",
        "output": "Pricing recommendation with rationale.",
        "validation": "Sales Agent validates against pricing principles.",
        "dependencies": ["pricing_engine"],
        "permissions": ["read:notes", "read:clients"],
        "risk": "medium",
        "owner": "Sales Agent",
        "status": "validated",
        "prerequisites": ["margin_analysis"],
        "learning_path": ["proposal_generation"],
    },

    # ── Sales & Growth ───────────────────────────────────────────────────
    {
        "id": "proposal_generation",
        "name": "Proposal Generation",
        "category": "Sales & Growth",
        "purpose": "Generate a client proposal from engagement context and pricing principles.",
        "version": "1.8",
        "success_rate": 0.92,
        "executions": 31,
        "autonomy": 2,
        "inputs": ["client context", "scope", "pricing model"],
        "tools": ["pricing_engine", "proposal_template", "vault_search"],
        "workflow": ["Extract client context", "Map scope to services", "Apply pricing principles", "Draft proposal"],
        "decision_logic": "Select pricing model from the pricing principles note.",
        "output": "Client-ready proposal document.",
        "validation": "QA Agent validates pricing consistency.",
        "dependencies": ["vault_search", "pricing_engine"],
        "permissions": ["read:clients", "read:notes", "write:proposals"],
        "risk": "medium",
        "owner": "Sales Agent",
        "status": "validated",
        "prerequisites": ["pricing_strategy", "client_health"],
        "learning_path": ["contract_review", "pitch_deck"],
    },
    {
        "id": "opportunity_scoring",
        "name": "Opportunity Scoring",
        "category": "Sales & Growth",
        "purpose": "Score and rank revenue opportunities across the portfolio.",
        "version": "1.3",
        "success_rate": 0.9,
        "autonomy": 2,
        "inputs": ["client data", "project data", "market signals"],
        "tools": ["crm", "scoring_engine"],
        "workflow": ["Load opportunities", "Score by impact/feasibility", "Rank", "Flag top 3"],
        "decision_logic": "Score = Impact × Feasibility × Urgency × Strategic Value.",
        "output": "Ranked opportunity list with rationale.",
        "validation": "Sales Agent reviews ranking.",
        "dependencies": ["crm"],
        "permissions": ["read:clients"],
        "risk": "low",
        "owner": "Sales Agent",
        "status": "validated",
        "prerequisites": ["client_health"],
        "learning_path": ["proposal_generation"],
    },
    {
        "id": "lead_nurturing",
        "name": "Lead Nurturing",
        "category": "Sales & Growth",
        "purpose": "Design and execute lead nurturing sequences from engagement signals.",
        "version": "0.8",
        "success_rate": 0.78,
        "autonomy": 1,
        "inputs": ["lead list", "engagement history", "content library"],
        "tools": ["crm", "email", "content_library"],
        "workflow": ["Segment leads", "Map content to stage", "Schedule touches", "Track engagement"],
        "decision_logic": "Route lead to sequence based on engagement score and stage.",
        "output": "Nurturing sequence with content mapping.",
        "validation": "Sales Agent reviews sequence.",
        "dependencies": ["crm", "email"],
        "permissions": ["read:clients", "write:emails"],
        "risk": "low",
        "owner": "Sales Agent",
        "status": "learning",
        "prerequisites": ["opportunity_scoring"],
        "learning_path": ["proposal_generation"],
    },
    {
        "id": "pitch_deck",
        "name": "Pitch Deck Generation",
        "category": "Sales & Growth",
        "purpose": "Generate a client pitch deck from engagement context and brand assets.",
        "version": "0.8",
        "success_rate": 0.8,
        "autonomy": 1,
        "inputs": ["client context", "services", "brand assets"],
        "tools": ["deck_template", "vault_search", "brand_assets"],
        "workflow": ["Extract client context", "Structure narrative", "Map services to value", "Generate deck"],
        "output": "Client-ready pitch deck.",
        "validation": "Sales Agent reviews narrative.",
        "dependencies": ["deck_template"],
        "permissions": ["read:clients", "write:reports"],
        "risk": "low",
        "owner": "Sales Agent",
        "status": "learning",
        "prerequisites": ["proposal_generation"],
        "learning_path": ["proposal_generation"],
    },
    {
        "id": "contract_review",
        "name": "Contract Review",
        "category": "Sales & Growth",
        "purpose": "Review contracts for risk, scope, and commercial alignment.",
        "version": "0.7",
        "success_rate": 0.75,
        "autonomy": 1,
        "inputs": ["contract text", "pricing principles", "risk policy"],
        "tools": ["contract_parser", "policy_engine"],
        "workflow": ["Parse contract", "Check scope", "Check pricing", "Flag risks"],
        "output": "Contract review with risk flags.",
        "validation": "Governance Agent reviews flags.",
        "dependencies": ["contract_parser"],
        "permissions": ["read:contracts"],
        "risk": "high",
        "owner": "Governance Agent",
        "status": "learning",
        "prerequisites": ["proposal_generation"],
        "learning_path": ["risk_assessment"],
    },

    # ── Client & Market ──────────────────────────────────────────────────
    {
        "id": "client_health",
        "name": "Client Health Assessment",
        "category": "Client & Market",
        "purpose": "Assess the health of a client account across multiple dimensions.",
        "version": "1.2",
        "success_rate": 0.9,
        "executions": 15,
        "autonomy": 2,
        "inputs": ["client id"],
        "tools": ["client_db", "sentiment_analysis", "health_scoring"],
        "workflow": ["Load client data", "Score health dimensions", "Flag risks", "Generate report"],
        "decision_logic": "Health = weighted average of delivery, sentiment, revenue, risk.",
        "output": "Client health report with risk flags.",
        "validation": "Client Success Agent reviews flags.",
        "dependencies": ["client_db", "sentiment_analysis"],
        "permissions": ["read:clients"],
        "risk": "low",
        "owner": "Client Success Agent",
        "status": "validated",
        "prerequisites": [],
        "learning_path": ["risk_detection", "renewal_management"],
    },
    {
        "id": "market_scan",
        "name": "Market Scan",
        "category": "Client & Market",
        "purpose": "Scan the market for competitors, trends and opportunities.",
        "version": "3.1",
        "success_rate": 0.94,
        "executions": 22,
        "autonomy": 3,
        "inputs": ["market segment", "keywords", "time horizon"],
        "tools": ["market_research", "source_eval", "synthesis"],
        "workflow": ["Formulate research question", "Gather sources", "Evaluate credibility", "Synthesize findings"],
        "decision_logic": "Rank sources by credibility and recency.",
        "output": "Market intelligence brief with cited sources.",
        "validation": "Research Agent validates source credibility.",
        "dependencies": ["market_research", "source_eval"],
        "permissions": ["read:market", "write:reports"],
        "risk": "low",
        "owner": "Research Agent",
        "status": "validated",
        "prerequisites": [],
        "learning_path": ["competitor_analysis", "trend_detection"],
    },
    {
        "id": "competitor_analysis",
        "name": "Competitor Analysis",
        "category": "Client & Market",
        "purpose": "Analyze competitors' positioning, pricing, and capabilities.",
        "version": "1.4",
        "success_rate": 0.91,
        "autonomy": 2,
        "inputs": ["competitor list", "market data"],
        "tools": ["market_research", "source_eval"],
        "workflow": ["Identify competitors", "Gather intel", "Compare positioning", "Synthesize"],
        "output": "Competitor analysis brief.",
        "validation": "Research Agent validates.",
        "dependencies": ["market_research"],
        "permissions": ["read:market"],
        "risk": "low",
        "owner": "Research Agent",
        "status": "validated",
        "prerequisites": ["market_scan"],
        "learning_path": ["market_scan"],
    },
    {
        "id": "trend_detection",
        "name": "Trend Detection",
        "category": "Client & Market",
        "purpose": "Detect emerging trends from market signals and client feedback.",
        "version": "0.9",
        "success_rate": 0.85,
        "autonomy": 2,
        "inputs": ["market signals", "client feedback", "news"],
        "tools": ["signal_engine", "synthesis"],
        "workflow": ["Collect signals", "Cluster themes", "Score momentum", "Report"],
        "output": "Trend report with momentum scores.",
        "validation": "Research Agent validates.",
        "dependencies": ["signal_engine"],
        "permissions": ["read:market"],
        "risk": "low",
        "owner": "Research Agent",
        "status": "learning",
        "prerequisites": ["market_scan"],
        "learning_path": ["market_scan"],
    },
    {
        "id": "sentiment_analysis",
        "name": "Sentiment Analysis",
        "category": "Client & Market",
        "purpose": "Analyze client sentiment from communications and feedback.",
        "version": "1.0",
        "success_rate": 0.88,
        "autonomy": 2,
        "inputs": ["client communications", "feedback"],
        "tools": ["sentiment_engine"],
        "workflow": ["Load communications", "Score sentiment", "Trend over time", "Flag shifts"],
        "output": "Sentiment report with shift flags.",
        "validation": "Client Success Agent reviews.",
        "dependencies": ["sentiment_engine"],
        "permissions": ["read:clients"],
        "risk": "low",
        "owner": "Client Success Agent",
        "status": "validated",
        "prerequisites": ["client_health"],
        "learning_path": ["client_health"],
    },
    {
        "id": "renewal_management",
        "name": "Renewal Management",
        "category": "Client & Market",
        "purpose": "Track and manage client renewals with proactive outreach.",
        "version": "0.7",
        "success_rate": 0.8,
        "autonomy": 1,
        "inputs": ["client contracts", "health scores"],
        "tools": ["crm", "email"],
        "workflow": ["Load renewals", "Score risk", "Plan outreach", "Track"],
        "output": "Renewal plan with risk flags.",
        "prerequisites": ["client_health"],
        "permissions": ["read:clients", "write:emails"],
        "risk": "low",
        "owner": "Client Success Agent",
        "status": "learning",
        "learning_path": ["client_health"],
    },

    # ── Delivery & Operations ────────────────────────────────────────────
    {
        "id": "delivery_management",
        "name": "Delivery Management",
        "category": "Delivery & Operations",
        "purpose": "Monitor and manage project delivery across milestones and quality gates.",
        "version": "1.3",
        "success_rate": 0.89,
        "autonomy": 3,
        "inputs": ["project plan", "milestones", "team capacity"],
        "tools": ["project_tracker", "qa", "milestone_check"],
        "workflow": ["Load project plan", "Check milestones", "Validate quality", "Flag risks"],
        "output": "Delivery status with risk flags.",
        "validation": "QA Agent validates.",
        "dependencies": ["project_tracker"],
        "permissions": ["read:projects", "write:reports"],
        "risk": "medium",
        "owner": "Delivery Agent",
        "status": "validated",
        "prerequisites": [],
        "learning_path": ["risk_mitigation", "resource_planning"],
    },
    {
        "id": "risk_mitigation",
        "name": "Risk Mitigation",
        "category": "Delivery & Operations",
        "purpose": "Identify delivery risks and propose mitigation actions.",
        "version": "1.1",
        "success_rate": 0.86,
        "autonomy": 2,
        "inputs": ["project data", "delivery signals"],
        "tools": ["risk_engine", "project_tracker"],
        "workflow": ["Scan project", "Score risks", "Propose mitigations", "Track"],
        "output": "Risk register with mitigations.",
        "validation": "Delivery Agent reviews.",
        "dependencies": ["risk_engine"],
        "permissions": ["read:projects"],
        "risk": "medium",
        "owner": "Delivery Agent",
        "status": "validated",
        "prerequisites": ["delivery_management"],
        "learning_path": ["delivery_management"],
    },
    {
        "id": "resource_planning",
        "name": "Resource Planning",
        "category": "Delivery & Operations",
        "purpose": "Plan team capacity and allocation across projects.",
        "version": "0.8",
        "success_rate": 0.83,
        "autonomy": 1,
        "inputs": ["team capacity", "project demand"],
        "tools": ["capacity_engine"],
        "workflow": ["Load capacity", "Load demand", "Allocate", "Flag conflicts"],
        "output": "Resource allocation plan.",
        "prerequisites": ["delivery_management"],
        "permissions": ["read:projects"],
        "risk": "low",
        "owner": "Delivery Agent",
        "status": "learning",
        "learning_path": ["delivery_management"],
    },
    {
        "id": "automation_design",
        "name": "Automation Design",
        "category": "Delivery & Operations",
        "purpose": "Design automation workflows from recurring patterns.",
        "version": "1.3",
        "success_rate": 0.93,
        "autonomy": 3,
        "inputs": ["recurring workflows", "tool inventory"],
        "tools": ["workflow_engine", "integration_hub"],
        "workflow": ["Detect pattern", "Map steps", "Design automation", "Propose"],
        "output": "Automation workflow design.",
        "validation": "Automation Architect reviews.",
        "dependencies": ["workflow_engine"],
        "permissions": ["read:all", "write:automations"],
        "risk": "low",
        "owner": "Automation Architect",
        "status": "validated",
        "prerequisites": [],
        "learning_path": ["skill_discovery"],
    },
    {
        "id": "milestone_tracking",
        "name": "Milestone Tracking",
        "category": "Delivery & Operations",
        "purpose": "Track project milestones and flag slippage.",
        "version": "1.0",
        "success_rate": 0.9,
        "autonomy": 3,
        "inputs": ["project plan", "progress data"],
        "tools": ["project_tracker"],
        "workflow": ["Load milestones", "Check progress", "Flag slippage", "Report"],
        "output": "Milestone status report.",
        "prerequisites": ["delivery_management"],
        "permissions": ["read:projects"],
        "risk": "low",
        "owner": "Delivery Agent",
        "status": "validated",
        "learning_path": ["delivery_management"],
    },

    # ── Finance ──────────────────────────────────────────────────────────
    {
        "id": "margin_analysis",
        "name": "Margin Analysis",
        "category": "Finance",
        "purpose": "Analyze project profitability and detect margin erosion.",
        "version": "1.0",
        "success_rate": 0.88,
        "executions": 9,
        "autonomy": 2,
        "inputs": ["project id", "financial data"],
        "tools": ["financial_db", "margin_analyzer"],
        "workflow": ["Load project financials", "Compute margin", "Compare to baseline", "Flag deviations"],
        "decision_logic": "Flag when margin drops below 25%.",
        "output": "Margin analysis with risk flags.",
        "validation": "Financial Intelligence Agent reviews.",
        "dependencies": ["financial_db"],
        "permissions": ["read:finance"],
        "risk": "medium",
        "owner": "Financial Intelligence Agent",
        "status": "validated",
        "prerequisites": [],
        "learning_path": ["revenue_forecast", "cashflow_analysis"],
    },
    {
        "id": "cashflow_analysis",
        "name": "Cashflow Analysis",
        "category": "Finance",
        "purpose": "Analyze cashflow patterns and predict shortfalls.",
        "version": "0.8",
        "success_rate": 0.84,
        "autonomy": 1,
        "inputs": ["financial data", "payment history"],
        "tools": ["financial_db"],
        "workflow": ["Load cashflow", "Pattern analysis", "Forecast", "Flag shortfalls"],
        "output": "Cashflow forecast with flags.",
        "prerequisites": ["margin_analysis"],
        "permissions": ["read:finance"],
        "risk": "medium",
        "owner": "Financial Intelligence Agent",
        "status": "learning",
        "learning_path": ["margin_analysis"],
    },
    {
        "id": "invoice_management",
        "name": "Invoice Management",
        "category": "Finance",
        "purpose": "Track invoices, payment status, and follow-ups.",
        "version": "0.9",
        "success_rate": 0.86,
        "autonomy": 2,
        "inputs": ["invoice data", "payment status"],
        "tools": ["financial_db", "email"],
        "workflow": ["Load invoices", "Check status", "Flag overdue", "Draft follow-up"],
        "output": "Invoice status report.",
        "prerequisites": ["margin_analysis"],
        "permissions": ["read:finance", "write:emails"],
        "risk": "low",
        "owner": "Financial Intelligence Agent",
        "status": "learning",
        "learning_path": ["cashflow_analysis"],
    },

    # ── Marketing & Communication ────────────────────────────────────────
    {
        "id": "content_generation",
        "name": "Content Generation",
        "category": "Marketing & Communication",
        "purpose": "Generate marketing content from brand voice and context.",
        "version": "1.1",
        "success_rate": 0.9,
        "autonomy": 2,
        "inputs": ["topic", "brand voice", "audience"],
        "tools": ["content_engine", "brand_assets"],
        "workflow": ["Load brand voice", "Draft content", "Validate tone", "Deliver"],
        "output": "Brand-aligned content.",
        "prerequisites": [],
        "permissions": ["write:content"],
        "risk": "low",
        "owner": "Marketing Agent",
        "status": "validated",
        "learning_path": ["social_media_planning"],
    },
    {
        "id": "social_media_planning",
        "name": "Social Media Planning",
        "category": "Marketing & Communication",
        "purpose": "Plan social media content calendar from strategy and events.",
        "version": "0.8",
        "success_rate": 0.82,
        "autonomy": 1,
        "inputs": ["strategy", "events", "content library"],
        "tools": ["calendar_engine", "content_library"],
        "workflow": ["Load strategy", "Map events", "Schedule content", "Track"],
        "output": "Social media calendar.",
        "prerequisites": ["email_generation"],
        "permissions": ["write:marketing"],
        "risk": "low",
        "owner": "Marketing Agent",
        "status": "learning",
        "learning_path": ["email_generation"],
    },
    {
        "id": "meeting_briefing",
        "name": "Meeting Briefing",
        "category": "Marketing & Communication",
        "purpose": "Prepare a meeting briefing from context, attendees, and agenda.",
        "version": "1.1",
        "success_rate": 0.92,
        "autonomy": 2,
        "inputs": ["meeting context", "attendees", "agenda"],
        "tools": ["vault_search", "briefing_engine"],
        "workflow": ["Load context", "Profile attendees", "Summarize agenda", "Generate briefing"],
        "output": "Meeting briefing document.",
        "prerequisites": ["ceo_briefing"],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Chief-of-Staff Agent",
        "status": "validated",
        "learning_path": ["ceo_briefing"],
    },
    {
        "id": "report_generation",
        "name": "Report Generation",
        "category": "Marketing & Communication",
        "purpose": "Generate structured reports from data and context.",
        "version": "1.1",
        "success_rate": 0.91,
        "autonomy": 2,
        "inputs": ["data", "report template"],
        "tools": ["report_engine", "template_library"],
        "workflow": ["Load data", "Map to template", "Generate report", "Validate"],
        "output": "Structured report.",
        "prerequisites": [],
        "permissions": ["write:reports"],
        "risk": "low",
        "owner": "Chief-of-Staff Agent",
        "status": "validated",
        "learning_path": ["ceo_briefing"],
    },

    # ── Engineering & Product ────────────────────────────────────────────
    {
        "id": "product_strategy",
        "name": "Product Strategy",
        "category": "Engineering & Product",
        "purpose": "Shape product roadmap from market and client signals.",
        "version": "1.0",
        "success_rate": 0.85,
        "autonomy": 2,
        "inputs": ["market signals", "client feedback", "roadmap"],
        "tools": ["roadmap", "client_feedback", "market_scan"],
        "workflow": ["Collect signals", "Prioritize features", "Validate roadmap", "Report"],
        "output": "Product roadmap with priorities.",
        "prerequisites": ["market_scan"],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Product Strategy Agent",
        "status": "validated",
        "learning_path": ["roadmap_planning"],
    },
    {
        "id": "roadmap_planning",
        "name": "Roadmap Planning",
        "category": "Engineering & Product",
        "purpose": "Plan product roadmap from priorities and capacity.",
        "version": "0.9",
        "success_rate": 0.84,
        "autonomy": 1,
        "inputs": ["priorities", "capacity", "timeline"],
        "tools": ["roadmap"],
        "workflow": ["Load priorities", "Map capacity", "Sequence", "Report"],
        "output": "Product roadmap.",
        "prerequisites": ["product_strategy"],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Product Strategy Agent",
        "status": "learning",
        "learning_path": ["product_strategy"],
    },
    {
        "id": "model_routing",
        "name": "Model Routing",
        "category": "Engineering & Product",
        "purpose": "Route AI requests to the optimal model for cost and quality.",
        "version": "1.2",
        "success_rate": 0.93,
        "autonomy": 3,
        "inputs": ["request", "model inventory", "cost data"],
        "tools": ["model_router", "cost_engine"],
        "workflow": ["Classify request", "Score models", "Route", "Log outcome"],
        "output": "Model routing decision.",
        "prerequisites": [],
        "permissions": ["read:models", "write:routing"],
        "risk": "low",
        "owner": "AI Engineering Agent",
        "status": "validated",
        "learning_path": ["rag_optimization"],
    },
    {
        "id": "rag_optimization",
        "name": "RAG Optimization",
        "category": "Engineering & Product",
        "purpose": "Optimize retrieval-augmented generation pipelines for quality and cost.",
        "version": "1.0",
        "success_rate": 0.9,
        "autonomy": 2,
        "inputs": ["RAG pipeline", "evaluation data"],
        "tools": ["rag_engine", "eval_engine"],
        "workflow": ["Profile pipeline", "Test retrieval", "Optimize", "Validate"],
        "output": "RAG optimization report.",
        "prerequisites": ["model_routing"],
        "permissions": ["read:models"],
        "risk": "low",
        "owner": "AI Engineering Agent",
        "status": "validated",
        "learning_path": ["model_routing"],
    },
    {
        "id": "code_review",
        "name": "Code Review",
        "category": "Engineering & Product",
        "purpose": "Review code for quality, security, and best practices.",
        "version": "0.9",
        "success_rate": 0.88,
        "autonomy": 2,
        "inputs": ["code diff", "standards"],
        "tools": ["code_repo", "lint_engine"],
        "workflow": ["Load diff", "Check standards", "Flag issues", "Report"],
        "output": "Code review with flags.",
        "prerequisites": [],
        "permissions": ["read:code"],
        "risk": "low",
        "owner": "AI Engineering Agent",
        "status": "learning",
        "learning_path": ["model_routing"],
    },

    # ── Security & Governance ────────────────────────────────────────────
    {
        "id": "threat_detection",
        "name": "Threat Detection",
        "category": "Security & Governance",
        "purpose": "Monitor access patterns and detect anomalies.",
        "version": "1.1",
        "success_rate": 0.96,
        "autonomy": 4,
        "inputs": ["audit logs", "access patterns"],
        "tools": ["audit_log", "anomaly_engine"],
        "workflow": ["Load logs", "Pattern baseline", "Detect anomalies", "Alert"],
        "output": "Threat detection report.",
        "prerequisites": [],
        "permissions": ["read:audit"],
        "risk": "high",
        "owner": "Cybersecurity Agent",
        "status": "validated",
        "learning_path": ["policy_enforcement"],
    },
    {
        "id": "policy_enforcement",
        "name": "Policy Enforcement",
        "category": "Security & Governance",
        "purpose": "Enforce governance policies across actions and data.",
        "version": "1.1",
        "success_rate": 0.95,
        "autonomy": 4,
        "inputs": ["policy rules", "action log"],
        "tools": ["policy_engine", "audit_trail"],
        "workflow": ["Load policies", "Check actions", "Flag violations", "Report"],
        "output": "Policy compliance report.",
        "prerequisites": ["threat_detection"],
        "permissions": ["read:all", "write:policy"],
        "risk": "high",
        "owner": "Cybersecurity Agent",
        "status": "validated",
        "learning_path": ["governance_audit"],
    },
    {
        "id": "governance_audit",
        "name": "Governance Audit",
        "category": "Security & Governance",
        "purpose": "Audit autonomous actions for compliance and governance.",
        "version": "1.0",
        "success_rate": 0.94,
        "autonomy": 3,
        "inputs": ["audit trail", "compliance rules"],
        "tools": ["audit_trail", "compliance_checker"],
        "workflow": ["Load audit trail", "Check compliance", "Flag issues", "Report"],
        "output": "Governance audit report.",
        "prerequisites": ["policy_enforcement"],
        "permissions": ["read:all"],
        "risk": "high",
        "owner": "AI Governance Agent",
        "status": "validated",
        "learning_path": ["risk_assessment"],
    },
    {
        "id": "risk_assessment",
        "name": "Risk Assessment",
        "category": "Security & Governance",
        "purpose": "Assess risk of actions, projects, and decisions.",
        "version": "1.0",
        "success_rate": 0.92,
        "autonomy": 2,
        "inputs": ["action context", "risk policy"],
        "tools": ["risk_engine", "policy_engine"],
        "workflow": ["Load context", "Score risk", "Recommend controls", "Report"],
        "outputs": "Risk assessment with controls.",
        "prerequisites": ["governance_audit"],
        "permissions": ["read:all"],
        "risk": "high",
        "owner": "AI Governance Agent",
        "status": "validated",
        "learning_path": ["governance_audit"],
    },

    # ── Learning & Growth ────────────────────────────────────────────────
    {
        "id": "skill_discovery",
        "name": "Skill Discovery",
        "category": "Learning & Growth",
        "purpose": "Detect repeated patterns and discover new skills.",
        "version": "1.0",
        "success_rate": 0.9,
        "autonomy": 3,
        "inputs": ["vault activity", "tool usage", "execution history"],
        "tools": ["pattern_engine", "vault_search"],
        "workflow": ["Scan activity", "Cluster patterns", "Score repeatability", "Propose skill"],
        "outputs": "New skill proposals.",
        "prerequisites": [],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Automation Architect",
        "status": "validated",
        "learning_path": ["workflow_design"],
    },
    {
        "id": "knowledge_gap_detection",
        "name": "Knowledge Gap Detection",
        "category": "Learning & Growth",
        "purpose": "Detect knowledge gaps from vault and conversation context.",
        "version": "0.9",
        "success_rate": 0.88,
        "autonomy": 2,
        "inputs": ["vault context", "conversation history"],
        "tools": ["gap_engine", "vault_search"],
        "workflow": ["Scan context", "Detect gaps", "Prioritize", "Propose action"],
        "outputs": "Knowledge gap list with actions.",
        "prerequisites": [],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Chief-of-Staff Agent",
        "status": "validated",
        "learning_path": ["skill_discovery"],
    },
    {
        "id": "pattern_recognition",
        "name": "Pattern Recognition",
        "category": "Learning & Growth",
        "purpose": "Recognize recurring patterns across data, workflows, and outcomes.",
        "version": "0.8",
        "success_rate": 0.86,
        "autonomy": 2,
        "inputs": ["data streams", "workflow history"],
        "tools": ["pattern_engine"],
        "workflow": ["Load data", "Cluster patterns", "Score significance", "Report"],
        "outputs": "Pattern report.",
        "prerequisites": ["skill_discovery"],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Learning Engine",
        "status": "learning",
        "learning_path": ["skill_discovery"],
    },
    {
        "id": "self_improvement",
        "name": "Self-Improvement",
        "category": "Learning & Growth",
        "purpose": "Improve HEER's own skills from execution outcomes and feedback.",
        "version": "1.0",
        "success_rate": 0.91,
        "autonomy": 3,
        "inputs": ["execution history", "outcomes", "feedback"],
        "tools": ["learning_engine", "feedback_engine"],
        "workflow": ["Review outcomes", "Identify improvements", "Bump version", "Validate"],
        "outputs": "Skill version improvements.",
        "prerequisites": ["skill_discovery"],
        "permissions": ["read:all", "write:skills"],
        "risk": "low",
        "owner": "Learning Engine",
        "status": "validated",
        "learning_path": ["skill_discovery"],
    },
]


# ---------------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------------

def _connect():
    os.makedirs(MEMORY_DIR, exist_ok=True)
    conn = sqlite3.connect(SKILLS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS skills (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        purpose TEXT,
        version TEXT,
        success_rate REAL DEFAULT 0.0,
        executions INTEGER DEFAULT 0,
        autonomy INTEGER DEFAULT 0,
        status TEXT DEFAULT 'learning',
        owner TEXT,
        risk TEXT DEFAULT 'low',
        workflow TEXT,
        decision_logic TEXT,
        output TEXT,
        validation TEXT,
        dependencies TEXT,
        permissions TEXT,
        prerequisites TEXT,
        learning_path TEXT,
        last_validated TEXT,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS skill_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_id TEXT NOT NULL,
        version TEXT NOT NULL,
        success_rate REAL,
        change_note TEXT,
        created_at TEXT,
        FOREIGN KEY (skill_id) REFERENCES skills(id)
    );

    CREATE TABLE IF NOT EXISTS learnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source TEXT,
        confidence REAL DEFAULT 0.0,
        type TEXT,
        detail TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS executions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_id TEXT NOT NULL,
        success INTEGER DEFAULT 0,
        duration_ms INTEGER,
        context TEXT,
        created_at TEXT,
        FOREIGN KEY (skill_id) REFERENCES skills(id)
    );

    CREATE TABLE IF NOT EXISTS knowledge_gaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT NOT NULL,
        why TEXT,
        impact TEXT,
        action TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT,
        closed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS skill_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        reason TEXT,
        pattern TEXT,
        status TEXT DEFAULT 'proposed',
        created_at TEXT
    );
    """)


# ---------------------------------------------------------------------------
# Skill engine
# ---------------------------------------------------------------------------

class SkillEngine:
    def __init__(self, business_id=None):
        self.business_id = business_id
        self.conn = _connect()
        _init_db(self.conn)
        self._seed_master_skills()

    def _seed_master_skills(self):
        """Seed the master skill set into the DB (idempotent)."""
        cur = self.conn.execute("SELECT COUNT(*) AS c FROM skills")
        if cur.fetchone()["c"] > 0:
            return
        now = _dt.datetime.now().isoformat(timespec="seconds")
        for s in MASTER_SKILLS:
            self.conn.execute(
                """INSERT OR REPLACE INTO skills
                   (id, name, category, purpose, version, success_rate, executions,
                    autonomy, status, risk_score, workflow, decision_logic, output,
                    validation, dependencies, permissions, prerequisites, learning_path,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    s["id"], s["name"], s.get("category", ""), s["purpose"],
                    s.get("version", "1.0"), s.get("success_rate", 0.0),
                    s.get("executions", 0), s.get("autonomy", 0),
                    s.get("status", "learning"), s.get("risk", "low"),
                    json.dumps(s.get("workflow", [])),
                    s.get("decision_logic", ""), s.get("output", ""),
                    s.get("validation", ""),
                    json.dumps(s.get("dependencies", [])),
                    json.dumps(s.get("permissions", [])),
                    json.dumps(s.get("prerequisites", [])),
                    json.dumps(s.get("learning_path", [])),
                    now, now,
                ),
            )
        self.conn.commit()

    # ── Queries ──────────────────────────────────────────────────────────

    def all_skills(self):
        rows = self.conn.execute("SELECT * FROM skills ORDER BY category, name").fetchall()
        return [self._row_to_skill(r) for r in rows]

    def get_skill(self, skill_id):
        row = self.conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
        return self._row_to_skill(row) if row else None

    def _row_to_skill(self, row):
        s = dict(row)
        for key in ("workflow", "dependencies", "permissions", "prerequisites", "learning_path"):
            if s.get(key):
                try:
                    s[key] = json.loads(s[key])
                except (json.JSONDecodeError, TypeError):
                    s[key] = []
        return s

    def skills_by_category(self):
        cats = {}
        for s in self.all_skills():
            cats.setdefault(s.get("category", "Other"), []).append(s)
        return cats

    def skills_payload(self):
        skills = self.all_skills()
        return {
            "skills": skills,
            "total": len(skills),
            "categories": sorted({s.get("category", "Other") for s in skills}),
            "avg_success": round(sum(s["success_rate"] for s in skills) / len(skills), 2) if skills else 0,
            "total_executions": sum(s["executions"] for s in skills),
            "validated": sum(1 for s in skills if s.get("status") == "validated"),
            "learning": sum(1 for s in skills if s.get("status") == "learning"),
            "db": SKILLS_DB,
        }

    # ── Learning engine ──────────────────────────────────────────────────

    def record_execution(self, skill_id, success=True, duration_ms=None, context=None):
        """Record a skill execution and update success rate."""
        now = _dt.datetime.now().isoformat(timespec="seconds")
        self.conn.execute(
            "INSERT INTO executions (skill_id, success, duration_ms, context, created_at) VALUES (?,?,?,?,?)",
            (skill_id, 1 if success else 0, duration_ms, json.dumps(context or {}), now),
        )
        # Update skill stats
        row = self.conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
        if row:
            new_exec = row["executions"] + 1
            new_rate = round((row["success_rate"] * row["executions"] + (1.0 if success else 0.0)) / new_exec, 4)
            self.conn.execute(
                "UPDATE skills SET executions = ?, success_rate = ?, updated_at = ? WHERE id = ?",
                (new_exec, new_rate, now, skill_id),
            )
        self.conn.commit()
        return {"ok": True, "skill_id": skill_id, "success": success}

    def add_learning(self, title, source="", ltype="insight", confidence=0.8, detail=""):
        """Record a new learning."""
        now = _dt.datetime.now().isoformat(timespec="seconds")
        cur = self.conn.execute(
            "INSERT INTO learnings (title, type, detail, created_at) VALUES (?,?,?,?)",
            (title, ltype, json.dumps({"source": source, "confidence": confidence, "detail": detail}, ensure_ascii=False), now),
        )
        self.conn.commit()
        return cur.lastrowid

    def recent_learnings(self, limit=10):
        rows = self.conn.execute(
            "SELECT * FROM learnings ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for r in rows:
            detail = json.loads(r["detail"]) if r["detail"] else {}
            out.append({
                "title": r["title"],
                "type": r["type"],
                "source": detail.get("source", ""),
                "confidence": detail.get("confidence", 0.0),
                "when": r["created_at"],
            })
        return out

    def add_gap(self, area, why="", impact="", action=""):
        now = _dt.datetime.now().isoformat(timespec="seconds")
        cur = self.conn.execute(
            "INSERT INTO knowledge_gaps (area, why, impact, action, created_at) VALUES (?,?,?,?,?)",
            (area, why, impact, action, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def knowledge_gaps(self, status="open"):
        rows = self.conn.execute(
            "SELECT * FROM knowledge_gaps WHERE status = ? ORDER BY id DESC", (status,)
        ).fetchall()
        return [dict(r) for r in rows]

    def close_gap(self, gap_id):
        now = _dt.datetime.now().isoformat(timespec="seconds")
        self.conn.execute(
            "UPDATE knowledge_gaps SET status = 'closed', closed_at = ? WHERE id = ?",
            (now, gap_id),
        )
        self.conn.commit()

    def propose_skill(self, name, reason="", pattern=""):
        """Propose a new skill from detected patterns."""
        now = _dt.datetime.now().isoformat(timespec="seconds")
        cur = self.conn.execute(
            "INSERT INTO skill_proposals (name, reason, pattern, created_at) VALUES (?,?,?,?)",
            (name, reason, pattern, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def skill_proposals(self, status="proposed"):
        rows = self.conn.execute(
            "SELECT * FROM skill_proposals WHERE status = ? ORDER BY id DESC", (status,)
        ).fetchall()
        return [dict(r) for r in rows]

    def approve_proposal(self, proposal_id):
        """Approve a proposal and register it as a new skill."""
        row = self.conn.execute("SELECT * FROM skill_proposals WHERE id = ?", (proposal_id,)).fetchone()
        if not row:
            return None
        now = _dt.datetime.now().isoformat(timespec="seconds")
        skill_id = re.sub(r"[^a-z0-9]+", "_", row["name"].lower()).strip("_")
        self.conn.execute(
            """INSERT OR REPLACE INTO skills
               (id, name, category, purpose, version, success_rate, executions,
                autonomy, status, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (skill_id, row["name"], "Learning & Growth", row["reason"], "0.1",
             0.0, 0, 1, "learning", now, now),
        )
        self.conn.execute("UPDATE skill_proposals SET status = 'approved' WHERE id = ?", (proposal_id,))
        self.conn.commit()
        return skill_id

    # ── Auto-learning / growth ───────────────────────────────────────────

    def auto_learn(self, vault=None):
        """Scan the vault and execution history to discover new skills and gaps.

        Returns a summary of what was learned.
        """
        learned = []
        gaps = []
        proposals = []

        # 1. Detect repeated patterns from vault notes
        if vault is not None:
            pattern_counts = {}
            for node in vault.nodes.values():
                text = node["text"].lower()
                for kw in ("proposal", "assessment", "report", "briefing", "analysis", "plan", "strategy"):
                    if kw in text:
                        pattern_counts[kw] = pattern_counts.get(kw, 0) + 1

            # Propose skills for repeated patterns
            for pattern, count in pattern_counts.items():
                if count >= 3:
                    existing = self.conn.execute(
                        "SELECT COUNT(*) AS c FROM skills WHERE LOWER(name) LIKE ?",
                        (f"%{pattern}%",),
                    ).fetchone()["c"]
                    if existing == 0:
                        proposal_id = self.propose_skill(
                            f"{pattern.title()} Automation",
                            reason=f"Detected {count} occurrences of '{pattern}' in the vault.",
                            pattern=pattern,
                        )
                        proposals.append({"id": proposal_id, "name": f"{pattern.title()} Automation"})

        # 2. Detect knowledge gaps from vault
        if vault is not None:
            for node in vault.nodes.values():
                text = node["text"].lower()
                for gap_kw in ["unknown", "tbd", "todo", "not documented", "missing", "need to find out"]:
                    if gap_kw in text:
                        gap_id = self.add_gap(
                            f"Documented gap in {node['title']}",
                            why=f"Contains '{gap_kw}' marker",
                            impact="Incomplete knowledge for decision-making",
                            action=f"Review {node['title']} and fill the gap",
                        )
                        gaps.append(gap_id)
                        break

        # 3. Record a learning about the scan
        if proposals or gaps:
            self.add_learning(
                f"Auto-scan found {len(proposals)} skill proposals and {len(gaps)} knowledge gaps",
                source="Auto-learning engine",
                ltype="growth",
                confidence=0.85,
            )

        return {
            "ok": True,
            "proposals": proposals,
            "gaps": gaps,
            "learnings": len(proposals) + len(gaps),
        }

    def learning_payload(self):
        """Flatten the learning center for the UI."""
        learnings = self.recent_learnings(8)
        gaps = self.knowledge_gaps()
        proposals = self.skill_proposals()
        skills = self.all_skills()
        validated = [s for s in skills if s.get("status") == "validated"]
        learning = [s for s in skills if s.get("status") == "learning"]

        items = []
        for l in learnings:
            items.append({
                "type": "growth",
                "text": l["title"],
                "meta": f"{l.get('source', '')} · {int(l.get('confidence', 0) * 100)}% confidence",
            })
        for p in proposals:
            items.append({
                "type": "skill",
                "text": f"New skill proposal: {p['name']}",
                "meta": p.get("reason", "")[:80],
            })
        for s in learning:
            items.append({
                "type": "skill",
                "text": f"Learning: {s['name']} v{s.get('version', '1.0')}",
                "meta": f"status: {s.get('status', 'learning')}",
            })

        return {
            "items": items,
            "knowledge_growth": {
                "total_learnings": len(learnings),
                "this_week": len(learnings),
                "today": len(learnings),
                "growth_rate": f"+{len(learnings)} this session",
            },
            "recent_learnings": learnings,
            "new_skills": [
                {"name": s["name"], "version": s.get("version", "1.0"), "discovered": "Auto-discovered", "status": s.get("status", "learning"), "autonomy": s.get("autonomy", 0)}
                for s in learning
            ],
            "skill_improvements": [],
            "knowledge_gaps": gaps,
            "conflicts": [],
            "outdated": [],
            "learning_confidence": round(
                sum(s["success_rate"] for s in skills) / len(skills), 2
            ) if skills else 0.0,
            "skill_proposals": proposals,
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_ENGINE = None


def get_engine(business_id=None):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = SkillEngine(business_id)
    return _ENGINE


def skills_payload(business_id=None):
    return get_engine(business_id).skills_payload()


def learning_payload(business_id=None):
    return get_engine(business_id).learning_payload()


def learn(business_id=None, vault=None):
    return get_engine(business_id).auto_learn(vault)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import sys
    engine = get_engine()
    if len(sys.argv) > 1 and sys.argv[1] == "learn":
        from . import vault as vault_mod
        v = vault_mod.get_vault()
        result = engine.auto_learn(v)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "skills":
        print(json.dumps(engine.skills_payload(), indent=2, ensure_ascii=False))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "learning":
        print(json.dumps(engine.learning_payload(), indent=2, ensure_ascii=False))
        return
    print("HEER Master Skill Set")
    print("=" * 60)
    cats = engine.skills_by_category()
    for cat, skills in sorted(cats.items()):
        print(f"\n{cat} ({len(skills)} skills)")
        for s in skills:
            print(f"  • {s['name']} v{s.get('version', '1.0')} — {s.get('status', 'learning')} — success {int(s.get('success_rate', 0) * 100)}%")
    print(f"\nTotal: {len(engine.all_skills())} skills")
    print(f"DB: {SKILLS_DB}")


if __name__ == "__main__":
    main()