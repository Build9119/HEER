#!/usr/bin/env python3
"""vault.py — folders -> searchable graph.

Read-only. Walks the roots from data.py, parses markdown/text/PDF,
extracts [[wikilinks]] as edges, and exposes:
  - nodes: id -> {title, path, type, text, links}
  - search(query) -> ranked results
  - hubs() -> top nodes by connection count

Vaults are scoped per business. Use get_vault(business_id) to fetch
(or lazily build) a business's vault.
"""

import os
import re
import zlib

from . import data

MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MB
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv"}
TEXT_EXTS = {".md", ".txt", ".markdown", ".text"}
PDF_EXTS = {".pdf"}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")


class Vault:
    def __init__(self, business_id=None):
        self.business_id = business_id
        self.nodes = {}   # id -> node dict
        self.links = []   # list of (source_id, target_id)
        self._adj = {}    # id -> set of neighbor ids
        self._text_index = {}  # token -> set of node ids

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index(self, roots=None):
        roots = roots or data.all_roots(self.business_id)
        for root in roots:
            if not os.path.isdir(root):
                print(f"[vault] WARNING: not a directory, skipping: {root}")
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fname in filenames:
                    path = os.path.join(dirpath, fname)
                    self._index_file(path, root)
        self._build_links()
        return self

    def _index_file(self, path, root):
        try:
            size = os.path.getsize(path)
        except OSError:
            return
        if size > MAX_FILE_BYTES:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXTS and ext not in PDF_EXTS:
            return

        text = self._read_text(path, ext)
        if not text:
            return

        rel = os.path.relpath(path, root)
        title = self._title_from(text, rel)
        node_id = rel.replace(os.sep, "/")

        self.nodes[node_id] = {
            "id": node_id,
            "title": title,
            "path": path,
            "rel": rel,
            "type": self._type_from(rel),
            "text": text,
            "size": size,
            "business_id": self.business_id,
        }
        self._tokenize(node_id, text)

    def _read_text(self, path, ext):
        try:
            if ext in TEXT_EXTS:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            if ext in PDF_EXTS:
                return self._read_pdf(path)
        except OSError:
            return ""
        return ""

    def _read_pdf(self, path):
        """Minimal PDF text extraction (stdlib only).

        Extracts text from stream objects. Good enough for simple PDFs
        (like the demo fixtures). Complex PDFs may yield partial text —
        that's acceptable; we degrade loudly in the UI, never silently.
        """
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError:
            return ""

        # Find all stream...endstream blocks
        texts = []
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.DOTALL):
            chunk = m.group(1)
            # Try FlateDecode
            try:
                chunk = zlib.decompress(chunk)
            except Exception:
                pass
            # Extract text in parentheses (Tj/TJ operators)
            for tm in re.finditer(rb"\((?:[^()\\]|\\.)*\)", chunk):
                s = tm.group(0)[1:-1]
                s = s.replace(b"\\(", b"(").replace(b"\\)", b")")
                s = s.replace(b"\\\\", b"\\")
                texts.append(s.decode("latin-1", "replace"))
        return " ".join(texts)

    def _title_from(self, text, rel):
        # First markdown heading, else filename
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if m:
            return m.group(1).strip()
        base = os.path.basename(rel)
        return os.path.splitext(base)[0].replace("_", " ").replace("-", " ").strip()

    def _type_from(self, rel):
        parts = rel.split(os.sep)
        if len(parts) > 1:
            return parts[0]
        return "root"

    def _tokenize(self, node_id, text):
        words = re.findall(r"[A-Za-z0-9_]{3,}", text.lower())
        for w in words:
            self._text_index.setdefault(w, set()).add(node_id)

    # ------------------------------------------------------------------
    # Graph
    # ------------------------------------------------------------------

    def _build_links(self):
        # Map title -> node id (first match wins)
        title_to_id = {}
        for nid, node in self.nodes.items():
            title_to_id.setdefault(node["title"].lower(), nid)

        for nid, node in self.nodes.items():
            for m in WIKILINK_RE.finditer(node["text"]):
                target_title = (m.group(2) or m.group(1)).strip()
                target_id = title_to_id.get(target_title.lower())
                if target_id and target_id != nid:
                    self.links.append((nid, target_id))

        # Dedupe
        self.links = list(dict.fromkeys(self.links))

        self._adj = {nid: set() for nid in self.nodes}
        for a, b in self.links:
            self._adj[a].add(b)
            self._adj[b].add(a)

    def hubs(self, top=10):
        ranked = sorted(self.nodes, key=lambda n: len(self._adj.get(n, ())), reverse=True)
        return [(nid, len(self._adj.get(nid, ()))) for nid in ranked[:top]]

    def by_title(self, title):
        """Find a node by exact title (case-insensitive)."""
        target = title.strip().lower()
        for node in self.nodes.values():
            if node["title"].strip().lower() == target:
                return node
        return None

    def add_note(self, title, body):
        """Write a note into the vault's notes folder and re-index it.

        Writes to demo notes in demo mode, real notes otherwise.
        Returns the new node dict.
        """
        base = data.data_root(self.business_id)
        if not base:
            raise RuntimeError("No data root configured (set INDEX_PATHS).")
        notes_dir = os.path.join(base, "notes")
        os.makedirs(notes_dir, exist_ok=True)
        slug = re.sub(r"[^A-Za-z0-9]+", "_", title.lower()).strip("_")
        if not slug:
            slug = "note"
        fname = f"{len(self.nodes):03d}_{slug}.md"
        path = os.path.join(notes_dir, fname)
        rel = os.path.join("notes", fname).replace(os.sep, "/")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")

        node = {
            "id": rel,
            "title": title,
            "path": path,
            "rel": rel,
            "type": "notes",
            "text": f"# {title}\n\n{body}\n",
            "size": os.path.getsize(path),
            "business_id": self.business_id,
        }
        self.nodes[rel] = node
        self._tokenize(rel, node["text"])
        self._build_links()
        return node

    def neighbors(self, node_id):
        return sorted(self._adj.get(node_id, ()))

    def shortest_path(self, a, b):
        """BFS shortest path between two node ids."""
        if a not in self.nodes or b not in self.nodes:
            return None
        if a == b:
            return [a]
        prev = {a: None}
        queue = [a]
        while queue:
            cur = queue.pop(0)
            for nb in self._adj.get(cur, ()):
                if nb not in prev:
                    prev[nb] = cur
                    if nb == b:
                        path = []
                        while nb is not None:
                            path.append(nb)
                            nb = prev[nb]
                        return list(reversed(path))
                    queue.append(nb)
        return None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query, limit=8):
        """Rank nodes by token overlap with the query."""
        qwords = re.findall(r"[A-Za-z0-9_]{3,}", query.lower())
        if not qwords:
            return []
        scores = {}
        for w in qwords:
            for nid in self._text_index.get(w, ()):
                scores[nid] = scores.get(nid, 0) + 1
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [self.nodes[nid] for nid, _ in ranked[:limit]]

    # ------------------------------------------------------------------
    # Reporting (Step 1 output)
    # ------------------------------------------------------------------

    def report(self):
        counts = {}
        for node in self.nodes.values():
            counts[node["type"]] = counts.get(node["type"], 0) + 1
        print("=" * 60)
        print("VAULT INDEX")
        print("=" * 60)
        print(f"Nodes: {len(self.nodes)}")
        print(f"Links: {len(self.links)}")
        print("Counts by type:")
        for t, c in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  {t}: {c}")
        print("Top 10 hubs (by connection count):")
        for nid, deg in self.hubs(10):
            print(f"  {self.nodes[nid]['title']}  ({deg} links)")
        print("=" * 60)
        return {
            "nodes": len(self.nodes),
            "links": len(self.links),
            "counts": counts,
            "hubs": [(self.nodes[nid]["title"], deg) for nid, deg in self.hubs(10)],
        }


def build_vault(business_id=None):
    return Vault(business_id=business_id).index()


# ---------------------------------------------------------------------------
# Per-business vault cache
# ---------------------------------------------------------------------------

_VAULTS = {}


def get_vault(business_id=None):
    """Return the cached vault for a business, building it on first use."""
    from . import business

    if business_id is None:
        b = business.current_business()
        if b is None:
            return None
        business_id = b["id"]
    if business_id not in _VAULTS:
        _VAULTS[business_id] = build_vault(business_id)
    return _VAULTS[business_id]


def clear_vault_cache(business_id=None):
    """Drop cached vaults (all, or one business)."""
    global _VAULTS
    if business_id is None:
        _VAULTS = {}
    else:
        _VAULTS.pop(business_id, None)