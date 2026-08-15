"""jarvis_skills.py — Load downloaded JARVIS skills into HEER.

Scans `.agents/skills/*/SKILL.md`, parses the YAML frontmatter
(name, description, version, tags, etc.) and converts each skill
into HEER's skill-dict format so the HEER dashboard, network map,
and learning engine can use them.
"""

import os
import re
import json

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(_BASE_DIR, ".agents", "skills")


# ---------------------------------------------------------------------------
# Frontmatter parsing (lightweight, no PyYAML dependency)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text):
    """Parse YAML-ish frontmatter between leading `---` markers.

    Returns (meta_dict, body_text). Handles simple `key: value` lines,
    quoted strings, JSON-ish values, and YAML block scalars (`>` / `|`).
    """
    meta = {}
    body = text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if m:
        fm = m.group(1)
        body = text[m.end():]
        lines = fm.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if not key:
                continue
            # YAML block scalar: `key: >` or `key: |`
            if val in (">", "|"):
                block_lines = []
                while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t")):
                    block_lines.append(lines[i].strip())
                    i += 1
                sep = " " if val == ">" else "\n"
                val = sep.join(block_lines)
            # Try JSON parse for dict/list/bool/number values
            try:
                parsed = json.loads(val)
                if isinstance(parsed, (dict, list, bool, int, float)) or parsed is None:
                    meta[key] = parsed
                    continue
            except (json.JSONDecodeError, ValueError):
                pass
            # Strip surrounding quotes
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            meta[key] = val
    return meta, body


def _slugify(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------------------
# Skill loading
# ---------------------------------------------------------------------------

def _load_skill_dir(skill_dir):
    """Load a single skill directory -> HEER skill dict (or None)."""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        return None

    with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    meta, body = _parse_frontmatter(text)
    name = meta.get("name", os.path.basename(skill_dir))
    description = meta.get("description", "")
    version = str(meta.get("version", "1.0"))
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Determine category from tags, description, and name using a
    # scoring system — each keyword match adds weight, highest wins.
    # Word-boundary matching avoids false positives like "codex" matching "code".
    category = "JARVIS Skills"
    tag_text = " ".join(tags).lower()
    desc_text = (description + " " + name).lower()

    def _has_word(text, word):
        # Use ASCII-only word boundaries so CJK characters (which Python's
        # \w treats as word chars) don't block matches like "API文档".
        return re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])", text) is not None

    cat_map = {
        "development": ["code", "dev", "programming", "frontend", "backend", "flutter", "react", "ios", "android", "rest api", "api endpoint", "api doc", "crud", "generator", "refactor", "test", "github", "pull request", "code review"],
        "research": ["research", "search", "keyword", "seo", "look up", "information", "find", "weather", "forecast", "forecasts", "contract", "legal"],
        "content": ["content", "writing", "copy", "social", "video", "audio", "speech", "tts", "stt", "podcast", "voice", "transcri", "image generation", "image-generate", "picture", "generate"],
        "communication": ["email", "wechat", "telegram", "gmail", "calendar", "meeting", "message", "session", "会议"],
        "operations": ["docker", "k8s", "kubernetes", "monitor", "health", "security", "backup", "database", "container", "observability", "infrastructure", "deploy"],
        "productivity": ["note", "document", "pdf", "report", "file", "project", "summary", "organize", "manage", "translate", "summarize", "翻译", "论文"],
    }
    scores = {}
    for cat, kws in cat_map.items():
        score = 0
        for kw in kws:
            if _has_word(tag_text, kw):
                score += 2
            if _has_word(desc_text, kw):
                score += 1
        scores[cat] = score
    best = None
    best_score = 0
    for cat, score in scores.items():
        if score > best_score:
            best = cat
            best_score = score
    if best and best_score > 0:
        category = best.title()

    # Build workflow steps from the body's section headers
    workflow = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("## "):
            workflow.append(line[3:].strip())
        elif line.startswith("# "):
            workflow.append(line[2:].strip())
    if not workflow:
        workflow = [description[:80]] if description else ["Use skill"]

    # Collect script files as tools
    tools = []
    for root, _dirs, files in os.walk(skill_dir):
        for fn in files:
            if fn.endswith((".py", ".js", ".ts", ".sh", ".cjs", ".mjs")):
                rel = os.path.relpath(os.path.join(root, fn), skill_dir)
                tools.append(rel)
    if not tools:
        tools = ["skill_docs"]

    # Permissions derived from category
    permissions = ["read:skills"]
    if category.lower() in ("dev", "operations"):
        permissions.append("execute:scripts")
    if category.lower() in ("communication", "content"):
        permissions.append("write:content")

    return {
        "id": _slugify(meta.get("name", os.path.basename(skill_dir))),
        "name": meta.get("name", os.path.basename(skill_dir)),
        "purpose": description or f"Execute the {meta.get('name', 'skill')} workflow.",
        "version": version,
        "success_rate": 0.0,
        "executions": 0,
        "last_validated": "Imported",
        "autonomy": 1,
        "inputs": tags[:4] or ["user request"],
        "tools": tools[:6],
        "workflow": workflow[:6],
        "decision_logic": "Follow the SKILL.md instructions for this skill.",
        "output": "Skill-specific output as described in SKILL.md.",
        "validation": "HEER validates the skill output against the SKILL.md spec.",
        "dependencies": ["vault"],
        "permissions": permissions,
        "risk": "low",
        "owner": "HEER Agent",
        "status": "learning",
        "source": "jarvis",
        "category": category,
        "path": os.path.relpath(skill_dir, _BASE_DIR),
        "tags": tags,
    }


def load_all_skills(skills_dir=None):
    """Load all JARVIS skills from the skills directory."""
    skills_dir = skills_dir or SKILLS_DIR
    if not os.path.isdir(skills_dir):
        return []
    skills = []
    for entry in sorted(os.listdir(skills_dir)):
        full = os.path.join(skills_dir, entry)
        if os.path.isdir(full):
            skill = _load_skill_dir(full)
            if skill:
                skills.append(skill)
    return skills


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_JARVIS_SKILLS = None


def get_jarvis_skills():
    global _JARVIS_SKILLS
    if _JARVIS_SKILLS is None:
        _JARVIS_SKILLS = load_all_skills()
    return _JARVIS_SKILLS


def jarvis_skills_payload():
    skills = get_jarvis_skills()
    return {
        "skills": skills,
        "total": len(skills),
        "source": "JARVIS Skills Marketplace",
        "categories": sorted({s.get("category", "Other") for s in skills}),
    }


if __name__ == "__main__":
    import sys
    payload = jarvis_skills_payload()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nTotal JARVIS skills loaded: {payload['total']}")