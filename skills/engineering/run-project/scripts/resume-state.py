#!/usr/bin/env python3
"""
Resume State Manager
====================
Manages .run-project/state.json for the /run-project orchestrator.
Supports resume, phase jumping, and state inspection.

Usage:
    python resume-state.py <repo-path> [--show] [--reset] [--advance <phase>]
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

STATE_FILE = '.run-project/state.json'

DEFAULT_STATE = {
    "repo_path": "",
    "current_phase": 0,
    "phases_completed": [],
    "handoffs": [],
    "human_gates_passed": [],
    "aac_required": False,
    "organization_complete": False,
    "organization_report": None,
    "started_at": None,
    "last_updated": None,
    "version": "1.0.0"
}

PHASES = [
    "aac-process-design",
    "grill",
    "prd",
    "agent-spec",
    "context-layer",
    "seeit",
    "to-issues",
    "writing-plans",
    "effort-proof",
    "execute",
    "accept"
]

def load_state(repo_path: str) -> dict:
    state_path = Path(repo_path) / STATE_FILE
    if state_path.exists():
        with open(state_path, 'r') as f:
            return json.load(f)
    return None

def save_state(repo_path: str, state: dict):
    state_path = Path(repo_path) / STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state['last_updated'] = datetime.now(timezone.utc).isoformat()
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

def init_state(repo_path: str, aac_required: bool = False) -> dict:
    state = DEFAULT_STATE.copy()
    state['repo_path'] = str(Path(repo_path).resolve())
    state['aac_required'] = aac_required
    state['started_at'] = datetime.now(timezone.utc).isoformat()
    state['last_updated'] = state['started_at']

    # If AAC not required, start at phase 1 (grill)
    # If AAC required, start at phase 0 (aac-process-design)
    state['current_phase'] = 0 if aac_required else 1

    save_state(repo_path, state)
    return state

def advance_phase(repo_path: str, phase_name: str = None) -> dict:
    state = load_state(repo_path)
    if not state:
        print(f"No state found. Run init first.", file=sys.stderr)
        sys.exit(1)

    if phase_name:
        if phase_name not in PHASES:
            print(f"Unknown phase: {phase_name}", file=sys.stderr)
            sys.exit(1)
        new_phase = PHASES.index(phase_name)
    else:
        new_phase = state['current_phase'] + 1

    if new_phase <= state['current_phase']:
        print(f"Warning: Moving backward or staying at phase {new_phase}")

    # Mark current phase as completed
    if state['current_phase'] >= 0 and state['current_phase'] not in state['phases_completed']:
        state['phases_completed'].append(state['current_phase'])

    state['current_phase'] = new_phase
    save_state(repo_path, state)
    return state

def mark_gate_passed(repo_path: str, phase_index: int) -> dict:
    state = load_state(repo_path)
    if not state:
        print(f"No state found.", file=sys.stderr)
        sys.exit(1)

    if phase_index not in state['human_gates_passed']:
        state['human_gates_passed'].append(phase_index)

    save_state(repo_path, state)
    return state

def add_handoff(repo_path: str, handoff_path: str) -> dict:
    state = load_state(repo_path)
    if not state:
        print(f"No state found.", file=sys.stderr)
        sys.exit(1)

    if handoff_path not in state['handoffs']:
        state['handoffs'].append(handoff_path)

    save_state(repo_path, state)
    return state

def show_state(repo_path: str):
    state = load_state(repo_path)
    if not state:
        print(f"No state found at {repo_path}/{STATE_FILE}")
        return

    print(f"\n📁 Repo: {state['repo_path']}")
    print(f"📅 Started: {state['started_at']}")
    print(f"🔄 Last updated: {state['last_updated']}")
    print(f"\n📊 Progress:")

    for i, phase in enumerate(PHASES):
        status = "⬜"
        if i in state['phases_completed']:
            status = "✅"
        elif i == state['current_phase']:
            status = "▶️"

        gate = " 🔒" if i in [1, 5] and i not in state['human_gates_passed'] else ""
        print(f"  {status} Phase {i}: {phase}{gate}")

    print(f"\n📄 Handoffs: {len(state['handoffs'])}")
    for h in state['handoffs']:
        print(f"  - {h}")

    print(f"\n🔓 Gates passed: {state['human_gates_passed']}")
    print(f"🤖 AAC required: {state['aac_required']}")
    print(f"📐 Organization complete: {state['organization_complete']}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Manage /run-project state')
    parser.add_argument('repo_path', help='Path to repository')
    parser.add_argument('--init', action='store_true', help='Initialize state')
    parser.add_argument('--aac', action='store_true', help='AAC required (with --init)')
    parser.add_argument('--show', action='store_true', help='Show current state')
    parser.add_argument('--advance', metavar='PHASE', help='Advance to phase')
    parser.add_argument('--gate-passed', type=int, metavar='PHASE_IDX', help='Mark gate passed')
    parser.add_argument('--add-handoff', metavar='PATH', help='Add handoff document')
    parser.add_argument('--reset', action='store_true', help='Reset state')
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()

    if args.init:
        state = init_state(str(repo_path), aac_required=args.aac)
        print(f"Initialized state at {repo_path}/{STATE_FILE}")
        show_state(str(repo_path))
    elif args.reset:
        state_path = repo_path / STATE_FILE
        if state_path.exists():
            state_path.unlink()
            print(f"Reset state at {repo_path}/{STATE_FILE}")
    elif args.advance:
        state = advance_phase(str(repo_path), args.advance)
        print(f"Advanced to phase: {PHASES[state['current_phase']]}")
    elif args.gate_passed is not None:
        state = mark_gate_passed(str(repo_path), args.gate_passed)
        print(f"Marked gate passed for phase {args.gate_passed}")
    elif args.add_handoff:
        state = add_handoff(str(repo_path), args.add_handoff)
        print(f"Added handoff: {args.add_handoff}")
    else:
        show_state(str(repo_path))

if __name__ == '__main__':
    main()
