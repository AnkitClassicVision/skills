#!/usr/bin/env python3
"""
Skillify — Universal Repo Skillification v2.0

Usage:  python skillify.py [path]

Zero flags. Auto-detects repo size. Tiered analysis.
Produces .skill-pack/ with PROJECT.md, context layers, interfaces, ADRs.
Works on any codebase — Python, JS, Go, Rust, Markdown, monorepos.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".run-project", ".skill-pack", "dist", "build", ".tox",
    ".pytest_cache", ".mypy_cache", "*.egg-info", ".eggs",
    "target",  # Rust
    ".next", ".nuxt",  # JS frameworks
}

# ---------------------------------------------------------------------------
# Tiered Analysis Engine
# ---------------------------------------------------------------------------

class Skillifier:
    def __init__(self, repo_path: Path):
        self.repo = repo_path.resolve()
        self.pack = self.repo / ".skill-pack"
        self.pack.mkdir(exist_ok=True)
        (self.pack / "context").mkdir(exist_ok=True)
        (self.pack / "interfaces").mkdir(exist_ok=True)
        (self.pack / "adrs").mkdir(exist_ok=True)

        # Fresh scan — never read stale .run-project/
        self.files = self._scan_files()
        self.total_loc = self._count_loc()
        self.tier = self._determine_tier()

    def _scan_files(self) -> list[Path]:
        """Walk repo. Skip ignored dirs. Return sorted file list."""
        found = []
        for root, dirs, filenames in os.walk(self.repo):
            # Skip ignored dirs inline (modifies dirs in-place to prevent descent)
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in filenames:
                p = Path(root) / f
                if not p.is_file():
                    continue
                if any(part in IGNORED_DIRS for part in p.parts):
                    continue
                found.append(p)
        return sorted(found)

    def _count_loc(self) -> int:
        return sum(len(f.read_text(encoding="utf-8", errors="ignore").splitlines()) for f in self.files)

    def _determine_tier(self) -> str:
        if self.total_loc < 100:
            return "surface"
        elif self.total_loc < 2000:
            return "shallow"
        return "deep"

    # =====================================================================
    # Step 1: Structural Layer
    # =====================================================================
    def structural(self) -> dict[str, Any]:
        modules: dict[str, list[str]] = defaultdict(list)
        for f in self.files:
            rel = f.relative_to(self.repo)
            mod = rel.parts[0] if len(rel.parts) > 1 else "root"
            modules[mod].append(str(rel))

        exts: dict[str, int] = defaultdict(int)
        for f in self.files:
            exts[f.suffix or "(no-ext)"] += 1
        dominant = max(exts, key=exts.get) if exts else "(none)"

        # Import graph (Python only for now; extensible)
        imports = self._build_import_graph(modules)

        return {
            "tier": self.tier,
            "total_files": len(self.files),
            "total_loc": self.total_loc,
            "dominant_language": dominant,
            "file_extensions": dict(exts),
            "modules": dict(modules),
            "import_graph": imports,
            "circular_dependencies": self._find_cycles(imports),
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _build_import_graph(self, modules: dict[str, list[str]]) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = defaultdict(list)
        if self.tier == "surface":
            return {}

        py_files = [f for f in self.files if f.suffix == ".py"]
        for f in py_files:
            rel = str(f.relative_to(self.repo))
            mod = rel.split(os.sep)[0] if os.sep in rel else "root"
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        for alias in node.names:
                            dep_mod = alias.name.split(".")[0]
                            if dep_mod != mod and dep_mod in modules:
                                if dep_mod not in graph[mod]:
                                    graph[mod].append(dep_mod)
            except Exception:
                continue
        return dict(graph)

    def _find_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        """Find circular dependencies via DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: list[str]):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [node])
        return cycles

    # =====================================================================
    # Step 2: Semantic Layer
    # =====================================================================
    def semantic(self) -> dict[str, Any]:
        if self.tier == "surface":
            return {"note": "Surface tier — semantic analysis skipped (repo <100 LOC)"}

        contracts: dict[str, Any] = {}
        for f in self.files:
            if f.suffix != ".py":
                continue
            rel = str(f.relative_to(self.repo))
            mod = rel.split(os.sep)[0]
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(text)
                funcs = []
                classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                        funcs.append(self._func_sig(node))
                    elif isinstance(node, ast.ClassDef):
                        methods = [self._func_sig(m) for m in node.body if isinstance(m, ast.FunctionDef)]
                        classes.append({"name": node.name, "methods": methods})
                if mod not in contracts:
                    contracts[mod] = {"files": {}, "entry_points": []}
                contracts[mod]["files"][rel] = {"functions": funcs, "classes": classes}
                if "__main__" in text:
                    contracts[mod]["entry_points"].append(rel)
            except Exception:
                continue

        return {
            "contracts": contracts,
            "entry_points": [
                str(f.relative_to(self.repo))
                for f in self.files
                if f.suffix == ".py" and "__main__" in f.read_text(encoding="utf-8", errors="ignore")
            ],
        }

    def _func_sig(self, node: ast.FunctionDef) -> str:
        args = [a.arg for a in node.args.args]
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        return f"{node.name}({', '.join(args)})"

    # =====================================================================
    # Step 3: Philosophical Layer
    # =====================================================================
    def philosophical(self, structural: dict, semantic: dict) -> dict[str, Any]:
        if self.tier == "surface":
            return {
                "note": "Surface tier — philosophical analysis skipped",
                "recommendations": ["Add more code to enable deep analysis."],
            }

        modules = structural.get("modules", {})
        deep_scores: dict[str, float] = {}
        for mod, files in modules.items():
            loc = sum(
                len((self.repo / f).read_text(encoding="utf-8", errors="ignore").splitlines())
                for f in files
                if (self.repo / f).is_file()
            )
            # Simple deep score: complexity proxy = LOC × fan-out × (1 + cycle-penalty)
            fan_out = len(structural.get("import_graph", {}).get(mod, []))
            cycle_penalty = 2.0 if any(mod in c for c in structural.get("circular_dependencies", [])) else 0.0
            deep_scores[mod] = round((loc / 100) * (1 + fan_out) * (1 + cycle_penalty), 2)

        sorted_modules = sorted(deep_scores.items(), key=lambda x: x[1], reverse=True)
        top_deep = [{"module": m, "score": s} for m, s in sorted_modules[:3]]
        hotspots = [{"module": m, "score": s, "reason": "High coupling + complexity"} for m, s in sorted_modules[:2] if s > 5]

        recommendations = []
        if structural.get("circular_dependencies"):
            recommendations.append(f"Break circular dependencies: {structural['circular_dependencies']}")
        if self.total_loc > 5000:
            recommendations.append("Consider splitting large modules (>500 LOC) into smaller units.")
        if not semantic.get("entry_points"):
            recommendations.append("No clear entry points detected. Add a main.py or CLI module.")

        return {
            "deep_scores": deep_scores,
            "top_deep_modules": top_deep,
            "hotspots": hotspots,
            "recommendations": recommendations or ["Structure looks healthy. Continue deepening high-score modules."],
        }

    # =====================================================================
    # Step 4: PROJECT.md
    # =====================================================================
    def generate_project_md(self, structural: dict, semantic: dict, philosophical: dict) -> str:
        modules = structural.get("modules", {})
        deep_scores = philosophical.get("deep_scores", {})

        module_rows = []
        for mod, files in modules.items():
            score = deep_scores.get(mod, "—")
            mod_type = self._infer_mod_type(mod, files)
            module_rows.append(f"| {mod} | {score} | {mod_type} | {len(files)} files |")

        entry_pts = semantic.get("entry_points", [])
        entry_lines = "\n".join(f"- `{ep}`" for ep in entry_pts[:5]) or "- _(none detected)_"

        interfaces = []
        for mod in modules:
            contracts = semantic.get("contracts", {}).get(mod, {})
            iface_count = sum(len(f.get("functions", [])) for f in contracts.get("files", {}).values())
            interfaces.append(f"- `{mod}` — {iface_count} public functions/classes")

        non_goals = self._extract_non_goals()
        boundaries = self._extract_boundaries()

        adrs = sorted([f.name for f in (self.pack / "adrs").glob("adr-*.md")])
        adr_lines = "\n".join(f"- `{a}`" for a in adrs) or "- _(no ADRs yet — run after code changes)_"

        return f"""---
name: {self.repo.name}
description: Auto-generated skill manifest for {self.repo.name}
version: 2.0.0
type: service
status: active
tier: {self.tier}
generated: {datetime.now(timezone.utc).isoformat()}
source: /skillify
---

## Role

{self.repo.name} — {self._infer_role()}

## Module Map

| Module | Deep Score | Type | Files |
|--------|-----------|------|-------|
{chr(10).join(module_rows) if module_rows else "| root | — | unknown | — |"}

## Entry Points

{entry_lines}

## Interfaces

{chr(10).join(interfaces) if interfaces else "- _(no interfaces detected)_"}

## Non-Goals

{chr(10).join(f"- {ng}" for ng in non_goals) or "- _(none extracted)_"}

## Boundaries

{chr(10).join(f"- {b}" for b in boundaries) or "- Decision-support only; human approval required"}

## Context Files

- `.skill-pack/context/structural.json` — module map, import graph, circular deps
- `.skill-pack/context/semantic.json` — type signatures, contracts, complexity
- `.skill-pack/context/philosophical.json` — deep modules, hotspots, recommendations

## Interfaces Directory

- `.skill-pack/interfaces/{{module}}.md` — annotated public API per module

## ADRs

{adr_lines}
"""

    def _infer_mod_type(self, mod: str, files: list[str]) -> str:
        lower = mod.lower()
        if any(x in lower for x in ("api", "route", "endpoint", "server")):
            return "REST surface"
        elif any(x in lower for x in ("db", "model", "schema", "migration", "store")):
            return "Data layer"
        elif any(x in lower for x in ("test", "spec", "fixture")):
            return "Test suite"
        elif any(x in lower for x in ("core", "engine", "logic", "service", "domain")):
            return "Business logic"
        elif any(x in lower for x in ("ui", "view", "template", "component", "dashboard")):
            return "Presentation"
        elif any(x in lower for x in ("config", "setting", "env")):
            return "Configuration"
        elif any(x in lower for x in ("util", "helper", "common", "lib")):
            return "Utilities"
        elif any(x in lower for x in ("ingest", "sync", "import", "extract", "load")):
            return "Data ingestion"
        elif any(x in lower for x in ("queue", "worker", "job", "task", "scheduler")):
            return "Queue / worker"
        elif any(x in lower for x in ("method", "plugin", "extension", "adapter")):
            return "Plugin / seam"
        return f"Module ({len(files)} files)"

    def _infer_role(self) -> str:
        lower = self.repo.name.lower()
        if any(x in lower for x in ("inventory", "stock", "warehouse", "supply")):
            return "Inventory management and decision support system."
        elif any(x in lower for x in ("api", "service", "backend", "gateway")):
            return "Backend service providing structured APIs."
        elif any(x in lower for x in ("dashboard", "ui", "frontend", "app", "web")):
            return "Web dashboard for visualizing and managing data."
        elif any(x in lower for x in ("cli", "tool", "script", "automation")):
            return "Command-line tool or automation system."
        elif any(x in lower for x in ("lib", "sdk", "package", "module")):
            return "Reusable library or SDK."
        return "Software system. Inspect module map for specific responsibilities."

    def _extract_non_goals(self) -> list[str]:
        prd = self.repo / "PRD.md"
        if prd.exists():
            text = prd.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(r"^\s*[-•]\s*(No |Never |Not |Avoid |Do not ).+?(?=\n|$)", text, re.M | re.I)
            return [m.strip() for m in matches[:5]]
        return []

    def _extract_boundaries(self) -> list[str]:
        spec = self.repo / "AGENT_SPEC.md"
        if spec.exists():
            text = spec.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(r"^\s*[-•]\s*(DOES NOT|BOUNDARY|NEVER|NO ).+?(?=\n|$)", text, re.M | re.I)
            return [m.strip() for m in matches[:5]]
        return []

    # =====================================================================
    # Step 5: Interface Annotations
    # =====================================================================
    def generate_interfaces(self, semantic: dict) -> None:
        contracts = semantic.get("contracts", {})
        for mod, data in contracts.items():
            md = f"# {mod} — Interface Annotation\n\n"
            md += "## Public API\n\n"
            for fname, fdata in data.get("files", {}).items():
                md += f"### `{fname}`\n\n"
                for fn in fdata.get("functions", []):
                    md += f"- `{fn}`\n"
                for cls in fdata.get("classes", []):
                    md += f"- `class {cls['name']}`\n"
                    for m in cls.get("methods", []):
                        md += f"  - `{m}`\n"
                md += "\n"
            md += "## Side Effects\n\n_Inferred from AST. Review manually._\n\n"
            md += "## Invariants\n\n_Document assumptions callers must maintain._\n"
            (self.pack / "interfaces" / f"{mod}.md").write_text(md, encoding="utf-8")

    # =====================================================================
    # Step 6: ADRs (inferred)
    # =====================================================================
    def infer_adrs(self, structural: dict) -> None:
        adrs = []
        exts = structural.get("file_extensions", {})
        dominant = structural.get("dominant_language", "")

        # ADR-001: Language
        adrs.append(("ADR-001", f"Language: {dominant}", "Inferred from file distribution."))

        # ADR-002: Database
        if list(self.repo.rglob("*.db")) or "sqlite" in str(self.repo).lower():
            adrs.append(("ADR-002", "SQLite for local persistence", "Single-file, zero-config."))

        # ADR-003: Web framework
        if any(f.suffix == ".py" for f in self.files):
            for f in self.files:
                if f.suffix == ".py":
                    text = f.read_text(encoding="utf-8", errors="ignore")
                    if "fastapi" in text.lower():
                        adrs.append(("ADR-003", "FastAPI for API surface", "Async-native, type-safe."))
                        break
                    elif "flask" in text.lower():
                        adrs.append(("ADR-003", "Flask for API surface", "Lightweight WSGI framework."))
                        break
                    elif "django" in text.lower():
                        adrs.append(("ADR-003", "Django for API surface", "Batteries-included framework."))
                        break

        # ADR-004: UI approach
        if any(f.suffix == ".html" for f in self.files):
            for f in self.files:
                if f.suffix == ".html":
                    text = f.read_text(encoding="utf-8", errors="ignore")
                    if "htmx" in text.lower():
                        adrs.append(("ADR-004", "HTMX for server-rendered UI", "Minimal JS, server-driven updates."))
                        break
                    elif "react" in text.lower() or "vue" in text.lower():
                        adrs.append(("ADR-004", "SPA frontend", "Client-rendered JavaScript framework."))
                        break

        # ADR-005: Plugin architecture
        if (self.repo / "methods").exists() or (self.repo / "plugins").exists():
            adrs.append(("ADR-005", "Pluggable architecture", "Methods or plugins discovered at runtime."))

        # ADR-006: Testing
        test_count = len([f for f in self.files if "test" in f.name.lower()])
        if test_count > 0:
            adrs.append(("ADR-006", f"Tests present ({test_count} files)", "Test coverage detected."))
        else:
            adrs.append(("ADR-006", "No tests detected", "Add tests before major refactor."))

        for name, title, ctx in adrs:
            content = f"""# {name}: {title}

## Context

{ctx}

## Decision

Auto-inferred from codebase analysis on {datetime.now(timezone.utc).isoformat()}.

## Status

Proposed — review for accuracy.
"""
            (self.pack / "adrs" / f"{name.lower()}.md").write_text(content, encoding="utf-8")

    # =====================================================================
    # Step 7: Run Everything
    # =====================================================================
    def run(self) -> None:
        print(f"🔧 Skillifying: {self.repo}")
        print(f"   Tier: {self.tier} | Files: {len(self.files)} | LOC: {self.total_loc}")

        # Build layers
        s = self.structural()
        m = self.semantic()
        p = self.philosophical(s, m)

        # Write context files
        for layer_name, data in [("structural", s), ("semantic", m), ("philosophical", p)]:
            out = self.pack / "context" / f"{layer_name}.json"
            # Append with timestamp (never destructive)
            if out.exists():
                existing = json.loads(out.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                    existing[f"_snapshot_{ts}"] = data
                    data = existing
            out.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Write PROJECT.md
        project_md = self.generate_project_md(s, m, p)
        project_path = self.pack / "PROJECT.md"
        if project_path.exists():
            backup = self.pack / f"PROJECT_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
            backup.write_text(project_path.read_text(encoding="utf-8"), encoding="utf-8")
        project_path.write_text(project_md, encoding="utf-8")

        # Write interfaces
        self.generate_interfaces(m)

        # Write ADRs
        self.infer_adrs(s)

        print(f"✅ Skill-pack at {self.pack}")
        print(f"   PROJECT.md")
        print(f"   context/{{structural,semantic,philosophical}}.json")
        print(f"   interfaces/{{module}}.md")
        print(f"   adrs/adr-{{NNN}}.md")

        # Check .gitignore
        gitignore = self.repo / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8")
            if ".skill-pack/" not in content:
                print("\n⚠️  Add `.skill-pack/` to .gitignore")
        else:
            print("\n⚠️  No .gitignore. Consider creating one.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Repo Skillification")
    parser.add_argument("path", nargs="?", default=".", help="Repo path")
    args = parser.parse_args()
    Skillifier(Path(args.path)).run()


if __name__ == "__main__":
    main()
