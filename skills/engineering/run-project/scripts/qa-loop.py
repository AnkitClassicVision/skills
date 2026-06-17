#!/usr/bin/env python3
"""
QA Subagent Loop
================
Runs a QA review on implementation output and loops back to the
implementation agent until passing or max iterations reached.

Supports three evaluation modes:
1. Automated checks (tests, lint, types, security) — always runs
2. Blind evals — reads .run-project/evals/ and checks implementation against criteria
3. Dark Factory holdout evaluations — runs if .holdout/scenarios/ exist

Usage:
    python qa-loop.py <repo-path> [--max-iterations 3] [--strict]

Integration:
    - Phase 13 (Execute): Auto-triggered after implementation
    - Blind evals are the primary QA mechanism for /run-project v2.1+
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class QAFinding:
    severity: str  # critical, warning, info
    category: str  # test, lint, type, security, style, logic, eval-{phase}
    file: str
    line: Optional[int]
    message: str
    suggestion: str

@dataclass
class QAReport:
    iteration: int
    passed: bool
    findings: List[QAFinding]
    summary: str
    timestamp: str

def run_tests(repo_path: str) -> List[QAFinding]:
    """Run test suite and collect failures."""
    findings = []
    repo_path = Path(repo_path)

    test_commands = [
        ("pytest", ["pytest", "-v", "--tb=short"]),
        ("jest", ["npm", "test", "--", "--verbose"]),
        ("vitest", ["npx", "vitest", "run"]),
        ("go test", ["go", "test", "./..."]),
        ("cargo test", ["cargo", "test"]),
    ]

    for name, cmd in test_commands:
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                for line in result.stdout.split('\n') + result.stderr.split('\n'):
                    if 'FAILED' in line or 'failed' in line or 'Error:' in line:
                        findings.append(QAFinding(
                            severity='critical',
                            category='test',
                            file='',
                            line=None,
                            message=line.strip(),
                            suggestion='Fix failing test before proceeding'
                        ))
            break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    return findings

def run_linter(repo_path: str) -> List[QAFinding]:
    """Run linter and collect issues."""
    findings = []
    repo_path = Path(repo_path)

    linters = [
        ("ruff", ["ruff", "check", "."]),
        ("eslint", ["npx", "eslint", "."]),
        ("pylint", ["pylint", "."]),
        ("flake8", ["flake8", "."]),
        ("golangci-lint", ["golangci-lint", "run"]),
        ("clippy", ["cargo", "clippy"]),
    ]

    for name, cmd in linters:
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                for line in result.stdout.split('\n') + result.stderr.split('\n'):
                    if line.strip() and not line.startswith('Checking'):
                        findings.append(QAFinding(
                            severity='warning',
                            category='lint',
                            file='',
                            line=None,
                            message=line.strip(),
                            suggestion=f'Fix {name} issue'
                        ))
            break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    return findings

def run_type_checker(repo_path: str) -> List[QAFinding]:
    """Run type checker and collect issues."""
    findings = []
    repo_path = Path(repo_path)

    type_checkers = [
        ("mypy", ["mypy", "."]),
        ("tsc", ["npx", "tsc", "--noEmit"]),
        ("pyright", ["npx", "pyright"]),
    ]

    for name, cmd in type_checkers:
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                for line in result.stdout.split('\n') + result.stderr.split('\n'):
                    if 'error' in line.lower():
                        findings.append(QAFinding(
                            severity='warning',
                            category='type',
                            file='',
                            line=None,
                            message=line.strip(),
                            suggestion=f'Fix type error ({name})'
                        ))
            break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    return findings

def run_security_scan(repo_path: str) -> List[QAFinding]:
    """Run basic security checks."""
    findings = []
    repo_path = Path(repo_path)

    security_patterns = {
        'hardcoded_password': r'password\s*=\s*["\'][^"\']+["\']',
        'hardcoded_secret': r'secret\s*=\s*["\'][^"\']+["\']',
        'hardcoded_api_key': r'api_key\s*=\s*["\'][^"\']+["\']',
        'eval_usage': r'\beval\s*\(',
        'exec_usage': r'\bexec\s*\(',
    }

    for file_path in repo_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in {'.py', '.js', '.ts', '.jsx', '.tsx'}:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                for pattern_name, pattern in security_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        findings.append(QAFinding(
                            severity='critical',
                            category='security',
                            file=str(file_path.relative_to(repo_path)),
                            line=content[:match.start()].count('\n') + 1,
                            message=f'Potential security issue: {pattern_name}',
                            suggestion='Use environment variables or secret management'
                        ))
            except Exception:
                pass

    return findings

def run_blind_evals(repo_path: str) -> List[QAFinding]:
    """
    Read all hidden eval files and check implementation against each criterion.
    This is the ONLY place evals are ever read by an agent that also sees code.

    Eval files are generated by blind subagents after each artifact phase.
    They remain hidden until this QA step.
    """
    findings = []
    repo_path = Path(repo_path)
    evals_dir = repo_path / '.run-project' / 'evals'

    if not evals_dir.exists():
        return findings

    eval_files = sorted(evals_dir.glob('*-eval.md'))

    if not eval_files:
        return findings

    print(f"Checking implementation against {len(eval_files)} hidden eval file(s)...")

    for eval_file in eval_files:
        phase = eval_file.stem.replace('-eval', '')
        content = eval_file.read_text(encoding='utf-8')

        # Parse eval items (## E1, ## E2, etc.)
        eval_items = re.findall(r'## (E\d+): (.+?)\n(.*?)(?=## E\d+:|$)', content, re.DOTALL)

        for eval_id, eval_title, eval_body in eval_items:
            finding = evaluate_criterion(repo_path, phase, eval_id, eval_title, eval_body)
            if finding:
                findings.append(finding)

    return findings

def evaluate_criterion(repo_path: Path, phase: str, eval_id: str, title: str, body: str) -> Optional[QAFinding]:
    """
    Check one eval criterion against the implementation.
    Returns a QAFinding if the criterion FAILS, None if it PASSES.
    """
    # Extract Check, Method, Pass if from markdown-style eval body
    check_method = None
    pass_condition = None

    method_match = re.search(r'(?:\*\*)?Method(?:\*\*)?\s*:\s*(.+?)(?=\n|$)', body, re.IGNORECASE)
    if method_match:
        check_method = method_match.group(1).strip()

    pass_match = re.search(r'(?:\*\*)?Pass if(?:\*\*)?\s*:\s*(.+?)(?=\n|$)', body, re.IGNORECASE)
    if pass_match:
        pass_condition = pass_match.group(1).strip()

    # Try automated checks first
    if check_method:
        # Grep-based checks
        if 'grep' in check_method.lower():
            try:
                result = subprocess.run(
                    check_method, shell=True, cwd=repo_path,
                    capture_output=True, text=True, timeout=30
                )
                has_matches = result.returncode == 0 and result.stdout.strip()
                pass_lower = (pass_condition or '').lower()

                # Determine expectation from pass condition
                expects_missing = any(w in pass_lower for w in ['no ', 'not ', 'absent', 'missing', 'no matches'])
                expects_found = not expects_missing and any(w in pass_lower for w in ['found', 'exists', 'present', 'match'])

                if expects_found and not has_matches:
                    return QAFinding(
                        severity='critical', category=f'eval-{phase}',
                        file='', line=None,
                        message=f'[{phase} {eval_id}] {title}',
                        suggestion=f'Expected pattern not found. Check: {check_method}\nExpected: {pass_condition}'
                    )
                if expects_missing and has_matches:
                    return QAFinding(
                        severity='critical', category=f'eval-{phase}',
                        file='', line=None,
                        message=f'[{phase} {eval_id}] {title}',
                        suggestion=f'Unexpected pattern found. Check: {check_method}\nFound: {result.stdout[:200]}'
                    )
                return None  # PASS
            except Exception as e:
                return QAFinding(
                    severity='warning', category=f'eval-{phase}',
                    file='', line=None,
                    message=f'[{phase} {eval_id}] {title}',
                    suggestion=f'Grep check error: {e}'
                )

        # File existence checks
        if any(kw in check_method.lower() for kw in ['file exists', 'path exists']):
            path_match = re.search(r'(?:file|path)\s+exists\s+([\w\-/]+(?:\.[\w]+)?)', check_method, re.IGNORECASE)
            if path_match:
                check_path = repo_path / path_match.group(1)
                if not check_path.exists():
                    return QAFinding(
                        severity='critical', category=f'eval-{phase}',
                        file='', line=None,
                        message=f'[{phase} {eval_id}] {title}',
                        suggestion=f'Expected file not found: {check_path.relative_to(repo_path)}'
                    )
                return None  # PASS

    # No automated method or can't parse — flag for AI QA subagent review
    desc_match = re.search(r'(?:\*\*)?Check(?:\*\*)?\s*:\s*(.+?)(?=\n|$)', body, re.IGNORECASE)
    desc = desc_match.group(1).strip() if desc_match else body[:200]

    return QAFinding(
        severity='warning', category=f'eval-{phase}',
        file='', line=None,
        message=f'[{phase} {eval_id}] {title}',
        suggestion=f'Requires verification: {desc}'
    )

def run_dark_factory_qa(repo_path: str) -> List[QAFinding]:
    """Run Dark Factory holdout evaluations if .holdout/scenarios/ exist."""
    findings = []
    repo_path = Path(repo_path)
    holdout_dir = repo_path / '.holdout' / 'scenarios'
    results_dir = repo_path / '.holdout' / 'results'

    if not holdout_dir.exists():
        return findings

    scenario_files = list(holdout_dir.glob('*.yml'))
    if not scenario_files:
        return findings

    print(f"Running Dark Factory QA with {len(scenario_files)} scenario(s)...")

    dark_factory_skill = Path.home() / '.hermes' / 'skills' / 'dark-factory-qa'
    if not dark_factory_skill.exists():
        dark_factory_skill = Path.home() / '.claude' / 'skills' / 'dark-factory-qa'

    if not dark_factory_skill.exists():
        findings.append(QAFinding(
            severity='warning',
            category='dark-factory',
            file='.holdout/',
            line=None,
            message='Dark Factory scenarios found but skill not installed',
            suggestion=f'Install dark-factory-qa skill'
        ))
        return findings

    for scenario_file in scenario_files:
        scenario_name = scenario_file.stem
        print(f"  Evaluating scenario: {scenario_name}")

        output_candidates = [
            repo_path / 'output' / f'{scenario_name}.md',
            repo_path / 'output' / f'{scenario_name}.json',
            repo_path / 'output' / f'{scenario_name}.txt',
        ]

        output_file = None
        for candidate in output_candidates:
            if candidate.exists():
                output_file = candidate
                break

        if not output_file:
            output_dir = repo_path / 'output'
            if output_dir.exists():
                output_files = list(output_dir.glob('*'))
                if output_files:
                    output_file = output_files[0]

        if not output_file:
            findings.append(QAFinding(
                severity='warning',
                category='dark-factory',
                file=str(scenario_file),
                line=None,
                message=f'No output found to evaluate against scenario {scenario_name}',
                suggestion='Ensure output is saved to output/ directory before QA'
            ))
            continue

        run_qa_script = dark_factory_skill / 'scripts' / 'run-qa.sh'
        if run_qa_script.exists():
            try:
                result = subprocess.run(
                    ['bash', str(run_qa_script), str(output_file), scenario_name],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if 'FAIL' in result.stdout or result.returncode != 0:
                    for line in result.stdout.split('\n'):
                        if line.strip().startswith('- FAIL') or line.strip().startswith('- PARTIAL'):
                            findings.append(QAFinding(
                                severity='critical' if 'FAIL' in line else 'warning',
                                category='dark-factory',
                                file=str(output_file.relative_to(repo_path)),
                                line=None,
                                message=f'[{scenario_name}] {line.strip()}',
                                suggestion='Fix according to holdout scenario criteria'
                            ))

                results_dir.mkdir(parents=True, exist_ok=True)
                result_file = results_dir / f'{scenario_name}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.md'
                result_file.write_text(result.stdout, encoding='utf-8')

            except Exception as e:
                findings.append(QAFinding(
                    severity='warning',
                    category='dark-factory',
                    file=str(scenario_file),
                    line=None,
                    message=f'Error running Dark Factory QA for {scenario_name}: {e}',
                    suggestion='Check dark-factory-qa skill installation'
                ))
        else:
            findings.append(QAFinding(
                severity='warning',
                category='dark-factory',
                file=str(dark_factory_skill),
                line=None,
                message=f'Dark Factory run-qa.sh not found',
                suggestion='Reinstall dark-factory-qa skill'
            ))

    return findings

def generate_qa_report(iteration: int, findings: List[QAFinding], strict: bool = False) -> QAReport:
    """Generate QA report from findings."""
    critical = [f for f in findings if f.severity == 'critical']
    warnings = [f for f in findings if f.severity == 'warning']
    infos = [f for f in findings if f.severity == 'info']

    passed = len(critical) == 0 if not strict else len(critical) == 0 and len(warnings) == 0

    summary = f"""
QA Iteration {iteration} Results:
- Critical issues: {len(critical)}
- Warnings: {len(warnings)}
- Info: {len(infos)}
- Status: {'PASS' if passed else 'FAIL'}
"""

    return QAReport(
        iteration=iteration,
        passed=passed,
        findings=findings,
        summary=summary,
        timestamp=datetime.now().isoformat()
    )

def save_report(repo_path: str, report: QAReport):
    """Save QA report to .run-project/qa/."""
    qa_dir = Path(repo_path) / '.run-project' / 'qa'
    qa_dir.mkdir(parents=True, exist_ok=True)

    report_path = qa_dir / f'iteration-{report.iteration}.json'
    with open(report_path, 'w') as f:
        json.dump(asdict(report), f, indent=2, default=lambda o: str(o))

    md_path = qa_dir / f'iteration-{report.iteration}.md'
    with open(md_path, 'w') as f:
        f.write(f"# QA Iteration {report.iteration}\n\n")
        f.write(f"**Status**: {'PASS' if report.passed else 'FAIL'}\n\n")
        f.write(f"**Timestamp**: {report.timestamp}\n\n")
        f.write(f"## Findings ({len(report.findings)} total)\n\n")

        for finding in report.findings:
            f.write(f"### {finding.severity.upper()}: {finding.category}\n")
            f.write(f"- **File**: {finding.file or 'N/A'}\n")
            if finding.line:
                f.write(f"- **Line**: {finding.line}\n")
            f.write(f"- **Message**: {finding.message}\n")
            f.write(f"- **Suggestion**: {finding.suggestion}\n\n")

    return str(report_path)

def run_qa_loop(repo_path: str, max_iterations: int = 3, strict: bool = False) -> Dict:
    """Main QA loop. Returns final status."""
    repo_path = Path(repo_path).resolve()

    print(f"Starting QA loop for {repo_path}")
    print(f"Max iterations: {max_iterations}, Strict mode: {strict}")

    for iteration in range(1, max_iterations + 1):
        print(f"\n{'='*60}")
        print(f"QA Iteration {iteration}/{max_iterations}")
        print(f"{'='*60}")

        findings = []

        print("Running tests...")
        findings.extend(run_tests(str(repo_path)))

        print("Running linters...")
        findings.extend(run_linter(str(repo_path)))

        print("Running type checker...")
        findings.extend(run_type_checker(str(repo_path)))

        print("Running security scan...")
        findings.extend(run_security_scan(str(repo_path)))

        print("Running blind eval checks...")
        findings.extend(run_blind_evals(str(repo_path)))

        print("Running Dark Factory holdout evaluations...")
        findings.extend(run_dark_factory_qa(str(repo_path)))

        report = generate_qa_report(iteration, findings, strict)
        report_path = save_report(str(repo_path), report)

        print(report.summary)

        if report.passed:
            print(f"\n✓ QA PASSED after {iteration} iteration(s)")
            return {
                'status': 'passed',
                'iterations': iteration,
                'report_path': report_path,
                'findings_count': len(findings)
            }

        if iteration < max_iterations:
            print(f"\n→ Sending {len(findings)} findings back to implementation agent...")
            print(f"→ Report saved to: {report_path}")
        else:
            print(f"\n✗ QA FAILED after {max_iterations} iterations")
            print(f"→ Manual intervention required")
            print(f"→ Final report: {report_path}")

    return {
        'status': 'failed',
        'iterations': max_iterations,
        'report_path': report_path,
        'findings_count': len(findings)
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='QA subagent loop')
    parser.add_argument('repo_path', help='Path to repository')
    parser.add_argument('--max-iterations', type=int, default=3,
                        help='Maximum QA iterations (default: 3)')
    parser.add_argument('--strict', action='store_true',
                        help='Fail on warnings too')
    args = parser.parse_args()

    result = run_qa_loop(args.repo_path, args.max_iterations, args.strict)

    print(f"\n{'='*60}")
    print("QA LOOP COMPLETE")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2))

    sys.exit(0 if result['status'] == 'passed' else 1)

if __name__ == '__main__':
    main()
