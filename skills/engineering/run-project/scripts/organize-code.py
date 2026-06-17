#!/usr/bin/env python3
"""
Repo-to-Skill Organizer
========================
Analyzes any codebase and produces skill-structured recommendations.
Can be invoked from any pipeline phase when brownfield context is encountered.
Outputs are saved to .run-project/organization/ and stay tied to repo context.

Usage:
    python organize-code.py <repo-path> [--output-dir <dir>] [--depth <shallow|deep>]

Integration points:
    - Phase 1 (Grill): Auto-triggered if repo > 1000 LOC
    - Phase 4 (Context Layer): Structural layer input
    - Phase 5 (SEEIT): Visualization data source
    - Any phase: Manual trigger via /run-project --organize
"""

import os
import sys
import json
import ast
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Set
from collections import defaultdict

@dataclass
class ModuleInfo:
    path: str
    language: str
    loc: int
    imports: List[str]
    exports: List[str]
    classes: List[str]
    functions: List[str]
    depth_score: float  # 0 = shallow, 1 = deep module

@dataclass
class RepoProfile:
    repo_path: str
    total_loc: int
    languages: Dict[str, int]
    modules: List[ModuleInfo]
    entry_points: List[str]
    deepest_modules: List[ModuleInfo]
    shallowest_modules: List[ModuleInfo]
    orphaned_files: List[str]
    circular_deps: List[tuple]
    suggested_skill_structure: Dict

def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    mapping = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.tsx': 'typescript-react', '.jsx': 'javascript-react',
        '.go': 'go', '.rs': 'rust', '.java': 'java', '.kt': 'kotlin',
        '.rb': 'ruby', '.php': 'php', '.cs': 'csharp', '.swift': 'swift',
        '.c': 'c', '.cpp': 'cpp', '.h': 'c-header', '.hpp': 'cpp-header',
        '.sh': 'bash', '.yml': 'yaml', '.yaml': 'yaml', '.json': 'json',
        '.toml': 'toml', '.md': 'markdown', '.sql': 'sql'
    }
    return mapping.get(ext, 'unknown')

def analyze_python_file(file_path: str) -> Optional[ModuleInfo]:
    """Parse a Python file for structure metrics."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        tree = ast.parse(source)
        loc = len(source.splitlines())

        imports = []
        exports = []
        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                # Public methods = exports
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                        exports.append(f"{node.name}.{item.name}")
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                functions.append(node.name)

        # Deep module score: simple interface / complex implementation
        # Few public exports + many private functions/classes = deep
        public_count = len(exports) + len([f for f in functions if not f.startswith('_')])
        private_count = len([f for f in functions if f.startswith('_')]) + len(source.splitlines())
        depth_score = min(1.0, private_count / max(public_count * 10, 1))

        return ModuleInfo(
            path=file_path,
            language='python',
            loc=loc,
            imports=imports,
            exports=exports,
            classes=classes,
            functions=functions,
            depth_score=round(depth_score, 2)
        )
    except SyntaxError:
        return None
    except Exception as e:
        print(f"Warning: Could not analyze {file_path}: {e}", file=sys.stderr)
        return None

def analyze_js_ts_file(file_path: str) -> Optional[ModuleInfo]:
    """Lightweight JS/TS analysis without full parser."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        loc = len(source.splitlines())
        language = 'typescript' if file_path.endswith(('.ts', '.tsx')) else 'javascript'

        # Regex-based extraction (good enough for structural analysis)
        imports = re.findall(r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]', source)
        exports = re.findall(r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)', source)
        classes = re.findall(r'(?:class|interface)\s+(\w+)', source)
        functions = re.findall(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()', source)
        functions = [f[0] or f[1] for f in functions if f[0] or f[1]]

        # Depth score: exported items vs LOC
        public_count = len(exports) + len([f for f in functions if not f.startswith('_')])
        depth_score = min(1.0, loc / max(public_count * 50, 1))

        return ModuleInfo(
            path=file_path,
            language=language,
            loc=loc,
            imports=imports,
            exports=exports,
            classes=classes,
            functions=functions,
            depth_score=round(depth_score, 2)
        )
    except Exception as e:
        print(f"Warning: Could not analyze {file_path}: {e}", file=sys.stderr)
        return None

def analyze_file(file_path: str) -> Optional[ModuleInfo]:
    """Route to appropriate analyzer based on language."""
    language = detect_language(file_path)

    if language == 'python':
        return analyze_python_file(file_path)
    elif language in ('javascript', 'typescript', 'javascript-react', 'typescript-react'):
        return analyze_js_ts_file(file_path)
    else:
        # For other languages, do basic LOC count only
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            loc = len(source.splitlines())
            return ModuleInfo(
                path=file_path,
                language=language,
                loc=loc,
                imports=[],
                exports=[],
                classes=[],
                functions=[],
                depth_score=0.5  # Unknown = neutral
            )
        except Exception:
            return None

def should_analyze(file_path: str, ignore_patterns: List[str]) -> bool:
    """Check if file should be analyzed."""
    path = Path(file_path)

    # Skip hidden dirs, node_modules, etc.
    skip_dirs = {'node_modules', '.git', 'venv', '.venv', '__pycache__', '.pytest_cache',
                 'dist', 'build', '.next', '.hermes', '.claude', '.codex', 'coverage',
                 '.run-project'}
    for part in path.parts:
        if part in skip_dirs:
            return False

    # Skip non-code files
    if path.suffix.lower() not in {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs',
                                    '.java', '.kt', '.rb', '.php', '.cs', '.swift',
                                    '.c', '.cpp', '.h', '.hpp', '.sh'}:
        return False

    return True

def find_entry_points(repo_path: str) -> List[str]:
    """Find likely entry points in repo."""
    entries = []

    # Common patterns
    patterns = [
        'main.py', 'main.js', 'main.ts', 'index.py', 'index.js', 'index.ts',
        'app.py', 'server.py', 'server.js', 'server.ts',
        'cli.py', 'cli.js', 'cli.ts',
        'setup.py', 'setup.js', 'package.json', 'Cargo.toml', 'go.mod',
        'Dockerfile', 'docker-compose.yml', 'Makefile'
    ]

    for pattern in patterns:
        path = Path(repo_path) / pattern
        if path.exists():
            entries.append(str(path.relative_to(repo_path)))

    return entries

def detect_circular_deps(modules: List[ModuleInfo]) -> List[tuple]:
    """Detect circular import dependencies."""
    # Build import graph
    graph = defaultdict(set)
    module_names = {}

    for mod in modules:
        base_name = Path(mod.path).stem
        module_names[base_name] = mod.path
        for imp in mod.imports:
            # Extract module name from import
            if '.' in imp:
                imp_base = imp.split('.')[0]
            else:
                imp_base = imp
            graph[base_name].add(imp_base)

    # Find cycles (simple DFS)
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                result = dfs(neighbor, path)
                if result:
                    return result
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                return tuple(path[cycle_start:])

        path.pop()
        rec_stack.remove(node)
        return None

    for mod_name in module_names:
        if mod_name not in visited:
            cycle = dfs(mod_name, [])
            if cycle and cycle not in cycles:
                cycles.append(cycle)

    return cycles

def suggest_skill_structure(modules: List[ModuleInfo], repo_path: str) -> Dict:
    """Suggest how to organize this repo as a skill."""

    # Group by directory
    dir_groups = defaultdict(list)
    for mod in modules:
        rel_path = str(Path(mod.path).relative_to(repo_path))
        parent = str(Path(rel_path).parent)
        if parent == '.':
            parent = 'root'
        dir_groups[parent].append(mod)

    # Identify potential skill components
    skill_components = {
        'SKILL.md': {
            'purpose': 'Main skill manifest (auto-generated from repo analysis)',
            'template': 'Use skill-creator template'
        },
        'references/': {
            'purpose': 'API docs, design docs, architecture decisions',
            'detected': []
        },
        'templates/': {
            'purpose': 'Reusable code templates, scaffolding files',
            'detected': []
        },
        'scripts/': {
            'purpose': 'Automation scripts, build scripts, utilities',
            'detected': []
        },
        'tests/': {
            'purpose': 'Test suites, test fixtures',
            'detected': []
        }
    }

    # Categorize directories
    for dirname, mods in dir_groups.items():
        dirname_lower = dirname.lower()

        if any(x in dirname_lower for x in ['test', 'spec', '__test__']):
            skill_components['tests/']['detected'].append(dirname)
        elif any(x in dirname_lower for x in ['script', 'bin', 'cmd', 'cli']):
            skill_components['scripts/']['detected'].append(dirname)
        elif any(x in dirname_lower for x in ['template', 'scaffold', 'boiler']):
            skill_components['templates/']['detected'].append(dirname)
        elif any(x in dirname_lower for x in ['doc', 'ref', 'design', 'arch']):
            skill_components['references/']['detected'].append(dirname)

    # Identify deep modules (good interfaces)
    deep_modules = [m for m in modules if m.depth_score > 0.7]
    shallow_modules = [m for m in modules if m.depth_score < 0.3]

    return {
        'directory_structure': dict(dir_groups),
        'suggested_skill_layout': skill_components,
        'deep_modules': [asdict(m) for m in deep_modules[:5]],
        'shallow_modules': [asdict(m) for m in shallow_modules[:5]],
        'recommendations': [
            'Consider extracting deep modules into skill references/',
            'Shallow modules may need interface consolidation',
            'Entry points suggest script/ targets',
            f'Found {len(deep_modules)} deep modules, {len(shallow_modules)} shallow modules'
        ]
    }

def analyze_repo(repo_path: str, depth: str = 'deep') -> RepoProfile:
    """Main analysis function."""
    repo_path = Path(repo_path).resolve()

    if not repo_path.exists():
        raise ValueError(f"Repo path does not exist: {repo_path}")

    modules = []
    languages = defaultdict(int)
    total_loc = 0

    # Walk the repo
    for root, dirs, files in os.walk(repo_path):
        # Filter dirs in-place to skip irrelevant ones
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                   {'node_modules', 'venv', '__pycache__', 'dist', 'build'}]

        for file in files:
            file_path = os.path.join(root, file)

            if not should_analyze(file_path, []):
                continue

            mod = analyze_file(file_path)
            if mod:
                modules.append(mod)
                languages[mod.language] += mod.loc
                total_loc += mod.loc

    # Find entry points
    entries = find_entry_points(str(repo_path))

    # Sort by depth
    modules_by_depth = sorted(modules, key=lambda m: m.depth_score, reverse=True)
    deepest = modules_by_depth[:10]
    shallowest = modules_by_depth[-10:]

    # Detect circular deps
    cycles = detect_circular_deps(modules)

    # Find orphaned files (no imports, not imported)
    all_imported = set()
    all_exports = set()
    for mod in modules:
        for imp in mod.imports:
            all_imported.add(imp.split('.')[0])
        for exp in mod.exports:
            all_exports.add(exp.split('.')[0] if '.' in exp else exp)

    orphaned = []
    for mod in modules:
        base = Path(mod.path).stem
        if base not in all_imported and not any(base in e for e in entries):
            orphaned.append(str(Path(mod.path).relative_to(repo_path)))

    # Suggest skill structure
    skill_structure = suggest_skill_structure(modules, str(repo_path))

    return RepoProfile(
        repo_path=str(repo_path),
        total_loc=total_loc,
        languages=dict(languages),
        modules=modules,
        entry_points=entries,
        deepest_modules=deepest,
        shallowest_modules=shallowest,
        orphaned_files=orphaned[:20],
        circular_deps=cycles[:10],
        suggested_skill_structure=skill_structure
    )

def generate_report(profile: RepoProfile, output_dir: str) -> str:
    """Generate markdown report and JSON data."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # JSON output
    json_path = output_path / 'organization.json'
    with open(json_path, 'w') as f:
        json.dump(asdict(profile), f, indent=2, default=lambda o: str(o))

    # Markdown report
    md_path = output_path / 'organization-report.md'
    with open(md_path, 'w') as f:
        f.write("# Repo Organization Analysis\n\n")
        f.write(f"**Repo**: `{profile.repo_path}`\n\n")
        f.write(f"**Total LOC**: {profile.total_loc:,}\n\n")

        f.write("## Languages\n\n")
        for lang, loc in sorted(profile.languages.items(), key=lambda x: -x[1]):
            pct = (loc / profile.total_loc) * 100
            f.write(f"- **{lang}**: {loc:,} lines ({pct:.1f}%)\n")
        f.write("\n")

        f.write("## Entry Points\n\n")
        for entry in profile.entry_points:
            f.write(f"- `{entry}`\n")
        f.write("\n")

        f.write("## Deepest Modules (Best Interfaces)\n\n")
        for mod in profile.deepest_modules[:5]:
            rel = str(Path(mod.path).relative_to(profile.repo_path))
            f.write(f"- `{rel}` — depth score: {mod.depth_score}\n")
            f.write(f"  - Classes: {', '.join(mod.classes[:3]) or 'none'}\n")
            f.write(f"  - Exports: {', '.join(mod.exports[:3]) or 'none'}\n")
        f.write("\n")

        f.write("## Shallowest Modules (Need Refactoring)\n\n")
        for mod in profile.shallowest_modules[:5]:
            rel = str(Path(mod.path).relative_to(profile.repo_path))
            f.write(f"- `{rel}` — depth score: {mod.depth_score}\n")
            f.write(f"  - Classes: {len(mod.classes)}, Functions: {len(mod.functions)}\n")
        f.write("\n")

        f.write("## Circular Dependencies\n\n")
        if profile.circular_deps:
            for cycle in profile.circular_deps:
                f.write(f"- {' → '.join(cycle)} → {cycle[0]}\n")
        else:
            f.write("None detected ✓\n")
        f.write("\n")

        f.write("## Orphaned Files\n\n")
        if profile.orphaned_files:
            for orphan in profile.orphaned_files[:10]:
                f.write(f"- `{orphan}`\n")
            if len(profile.orphaned_files) > 10:
                f.write(f"- ... and {len(profile.orphaned_files) - 10} more\n")
        else:
            f.write("None detected ✓\n")
        f.write("\n")

        f.write("## Suggested Skill Structure\n\n")
        f.write("```\n")
        f.write("SKILL.md          # Main manifest (generated from analysis)\n")
        f.write("references/       # Extracted from:")
        for d in profile.suggested_skill_structure['suggested_skill_layout']['references/']['detected']:
            f.write(f"\n  - {d}")
        if not profile.suggested_skill_structure['suggested_skill_layout']['references/']['detected']:
            f.write("\n  (none detected — consider moving docs here)")
        f.write("\nscripts/          # Extracted from:")
        for d in profile.suggested_skill_structure['suggested_skill_layout']['scripts/']['detected']:
            f.write(f"\n  - {d}")
        if not profile.suggested_skill_structure['suggested_skill_layout']['scripts_']['detected']:
            f.write("\n  (none detected — consider moving CLI tools here)")
        f.write("\ntemplates/        # Extracted from:")
        for d in profile.suggested_skill_structure['suggested_skill_layout']['templates/']['detected']:
            f.write(f"\n  - {d}")
        if not profile.suggested_skill_structure['suggested_skill_layout']['templates/']['detected']:
            f.write("\n  (none detected)")
        f.write("\n```\n\n")

        f.write("## Recommendations\n\n")
        for rec in profile.suggested_skill_structure['recommendations']:
            f.write(f"- {rec}\n")

    return str(md_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze repo and suggest skill structure')
    parser.add_argument('repo_path', help='Path to repository')
    parser.add_argument('--output-dir', default='.run-project/organization',
                        help='Output directory')
    parser.add_argument('--depth', choices=['shallow', 'deep'], default='deep',
                        help='Analysis depth')
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    output_dir = repo_path / args.output_dir

    print(f"Analyzing {repo_path}...")
    profile = analyze_repo(str(repo_path), depth=args.depth)

    print(f"Found {len(profile.modules)} modules, {profile.total_loc:,} total LOC")
    print(f"Languages: {', '.join(profile.languages.keys())}")

    report_path = generate_report(profile, str(output_dir))
    print(f"\nReport saved to: {report_path}")
    print(f"JSON data saved to: {output_dir}/organization.json")

    # Update state.json if it exists
    state_path = repo_path / '.run-project' / 'state.json'
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = json.load(f)
        state['organization_complete'] = True
        state['organization_report'] = str(report_path)
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
        print("Updated .run-project/state.json")

if __name__ == '__main__':
    main()
