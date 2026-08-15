#!/usr/bin/env python3
"""Verify JARVIS skills are properly integrated with HEER."""
import sys
from collections import Counter

sys.path.insert(0, '.')

from agent import heer

p = heer.skills_payload()

# Structure checks
assert p['total'] == 36, f'Expected 36 total, got {p["total"]}'
assert p['jarvis_skills'] == 30, f'Expected 30 jarvis, got {p["jarvis_skills"]}'
assert 'JARVIS Skills' not in p['jarvis_categories'], 'Fallback category still present!'

# Field checks
required = ['id', 'name', 'purpose', 'version', 'success_rate', 'executions',
            'last_validated', 'autonomy', 'inputs', 'tools', 'workflow',
            'decision_logic', 'output', 'validation', 'dependencies',
            'permissions', 'risk', 'owner', 'status', 'source', 'category',
            'path', 'tags']
for s in p['skills']:
    if s.get('source') == 'jarvis':
        missing = [k for k in required if k not in s]
        assert not missing, f'{s["name"]} missing: {missing}'
        assert s['category'] in p['jarvis_categories'], f'{s["name"]} bad category: {s["category"]}'
        assert s['tools'], f'{s["name"]} has no tools'
        assert s['workflow'], f'{s["name"]} has no workflow'

print('All checks passed!')
print(f'  Total skills: {p["total"]}')
print(f'  JARVIS skills: {p["jarvis_skills"]}')
print(f'  Categories: {p["jarvis_categories"]}')
print()
print('Category breakdown:')
c = Counter(s['category'] for s in p['skills'] if s.get('source') == 'jarvis')
for cat, n in sorted(c.items()):
    print(f'  {cat}: {n}')