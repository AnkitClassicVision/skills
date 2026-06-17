#!/usr/bin/env python3
"""
Project Type Detector
=====================
Auto-detects whether a project needs AAC Process Design pre-phase.

Detection methods:
1. Keyword scan of user intent
2. File scan for agent-related patterns
3. Explicit --aac flag override

Usage:
    python detect-project-type.py <repo-path> [--intent-text <text>]

Returns JSON with:
    {
        "aac_required": true/false,
        "confidence": "high|medium|low",
        "reason": "...",
        "detected_signals": [...]
    }
"""

import os
import re
import json
import sys
from pathlib import Path

AGENT_KEYWORDS = {
    'high_confidence': [
        'agent', 'workflow', 'automation', 'ai agent', 'agentic',
        'bot', 'chatbot', 'llm pipeline', 'rag pipeline',
        'aac', 'agenttwin', 'agent registry'
    ],
    'medium_confidence': [
        'cron job', 'scheduled task', 'email automation',
        'data pipeline', 'integration', 'webhook handler',
        'notification system', 'alerting'
    ]
}

AGENT_FILE_PATTERNS = [
    r'agent_registry',
    r'aac-v2',
    r'agenttwin',
    r'agent_factory',
    r'agent_spec',
    r'workflow.*engine',
    r'orchestrator',
    r'pipeline.*config',
    r'\.agent\.',
    r'bot\.',
]

AGENT_FILE_INDICATORS = [
    'agent_registry.json',
    'aac-config.yaml',
    'agent-spec.md',
    'workflows/',
    'agents/',
    'bots/',
    'automations/',
    '.github/workflows/',
]

def scan_intent(text: str) -> tuple:
    """Scan user intent text for agent keywords."""
    text_lower = text.lower()
    signals = []

    for keyword in AGENT_KEYWORDS['high_confidence']:
        if keyword in text_lower:
            signals.append(f"intent:keyword:{keyword}")

    for keyword in AGENT_KEYWORDS['medium_confidence']:
        if keyword in text_lower:
            signals.append(f"intent:keyword:{keyword}")

    if signals:
        confidence = 'high' if any('high_confidence' in str(k) for k in signals) else 'medium'
        return True, confidence, signals

    return False, 'low', []

def scan_repo(repo_path: str) -> tuple:
    """Scan repository for agent-related files and patterns."""
    signals = []
    repo_path = Path(repo_path).resolve()

    if not repo_path.exists():
        return False, 'low', []

    # Check for indicator files/directories
    for indicator in AGENT_FILE_INDICATORS:
        indicator_path = repo_path / indicator
        if indicator_path.exists():
            signals.append(f"repo:indicator:{indicator}")

    # Scan top-level files for patterns
    for file_path in repo_path.iterdir():
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                for pattern in AGENT_FILE_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        signals.append(f"repo:pattern:{pattern} in {file_path.name}")
                        break
            except Exception:
                pass

    # Check package.json / requirements.txt / Cargo.toml for agent libs
    dep_files = {
        'package.json': [r'langchain', r'openai', r'anthropic', r'ai', r'vercel\/ai'],
        'requirements.txt': [r'langchain', r'openai', r'anthropic', r'haystack', r'crewai'],
        'Cargo.toml': [r'rig-', r'kalosm'],
        'go.mod': [r'github.com\/tmc\/langchaingo'],
    }

    for dep_file, patterns in dep_files.items():
        dep_path = repo_path / dep_file
        if dep_path.exists():
            try:
                content = dep_path.read_text(encoding='utf-8', errors='ignore')
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        signals.append(f"repo:dependency:{pattern} in {dep_file}")
            except Exception:
                pass

    if signals:
        confidence = 'high' if len(signals) >= 2 else 'medium'
        return True, confidence, signals

    return False, 'low', []

def detect_project_type(repo_path: str, intent_text: str = None) -> dict:
    """Main detection logic."""
    all_signals = []

    # Scan intent if provided
    if intent_text:
        is_agent, conf, signals = scan_intent(intent_text)
        all_signals.extend(signals)
        if is_agent and conf == 'high':
            return {
                'aac_required': True,
                'confidence': 'high',
                'reason': f'High-confidence agent keywords detected in intent',
                'detected_signals': all_signals
            }

    # Scan repo
    is_agent, conf, signals = scan_repo(repo_path)
    all_signals.extend(signals)

    if is_agent:
        return {
            'aac_required': True,
            'confidence': conf,
            'reason': f'Agent-related files/patterns detected in repository',
            'detected_signals': all_signals
        }

    return {
        'aac_required': False,
        'confidence': 'high',
        'reason': 'No agent-related signals detected',
        'detected_signals': all_signals
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Detect if project needs AAC')
    parser.add_argument('repo_path', help='Path to repository')
    parser.add_argument('--intent-text', help='User intent text')
    args = parser.parse_args()

    result = detect_project_type(args.repo_path, args.intent_text)
    print(json.dumps(result, indent=2))

    # Exit code: 0 = AAC needed, 1 = not needed
    sys.exit(0 if result['aac_required'] else 1)

if __name__ == '__main__':
    main()
