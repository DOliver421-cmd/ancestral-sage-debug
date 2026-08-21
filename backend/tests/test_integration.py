"""Integration tests — Step 9."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.hybrid_nam.designation import HybridNAMDesignation
from ai.hybrid_nam.soul_kernel import SoulKernel
from ai.hybrid_nam.knowledge_forge import KnowledgeForge
from ai.hybrid_nam.knowledge_graph import retrieve, classify_domains
from ai.hybrid_nam.memory_engine import (create_memory, create_autobiographical_event, create_intention, retrieve_memories, detect_drift, analyze_team_context)
from ai.hybrid_nam.dream_engine import assemble_dream_inputs, generate_dream
from ai.hybrid_nam.reflection_engine import create_reflection, generate_constitutional_tension
from ai.hybrid_nam.leadership_engine import evaluate_action, create_ledger_entry
from ai.hybrid_nam.jamil_protocol import create_review_request, process_review, classify_autonomy, escalate, resolve_escalation

p = f = 0

def ok(n):
    global p; p += 1; print(f'  PASS {n}')

def no(n, e):
    global f; f += 1; print(f'  FAIL {n}: {e}')

def t(n, fn):
    try: fn(); ok(n)
    except Exception as e: no(n, e)

def eq(a, b):
    if a != b: raise AssertionError(f'{a!r} != {b!r}')

def gt(a, b):
    if not (a > b): raise AssertionError(f'{a!r} not > {b!r}')

def ge(a, b):
    if not (a >= b): raise AssertionError(f'{a!r} not >= {b!r}')

def ok_(v):
    if not v: raise AssertionError('not true')

def has(k, d):
    if k not in d: raise AssertionError(f'{k!r} not in keys')

print('=== NAM IDENTITY ===')
nam = HybridNAMDesignation()
t('NAM identity', lambda: eq(nam.identity['name'], 'Hybrid NAM'))
t('NAM role', lambda: eq(nam.identity['role'], 'Assistant Director'))
t('NAM not human', lambda: eq(nam.identity['is_human'], False))
t('NAM constitution', lambda: ok_(len(nam.constitution) > 0))
t('NAM hash', lambda: ok_(len(nam.get_hash()) > 0))
t('NAM designation prompt', lambda: ok_(len(nam.get_designation_prompt()) > 0))

print('\n=== SOUL KERNEL ===')
soul = SoulKernel()
t('Soul identity exists', lambda: ok_(isinstance(soul.identity, dict)))
t('Soul constitution exists', lambda: ok_(isinstance(soul.constitution, list)))
t('Soul personality exists', lambda: ok_(isinstance(soul.personality, dict)))
t('Soul snapshot', lambda: ok_(len(soul.snapshot()) > 0))

# Store a memory and retrieve it
soul.store_memory({'memory_type': 'semantic', 'content': 'Test memory content', 'importance': 0.8})
t('Soul store memory', lambda: ok_(len(soul.memories) > 0))

print('\n=== KNOWLEDGE FORGE ===')
forge = KnowledgeForge()
forge.ingest('AI should increase human capability', {'source_type': 'founding_archive', 'source_origin': 'NAM Oshun', 'content_type': 'principle', 'title': 'Human Capability', 'domains': ['mission'], 'keywords': ['human', 'capability']})
forge.ingest('Protect human agency', {'source_type': 'founding_archive', 'source_origin': 'NAM Oshun', 'content_type': 'principle', 'title': 'Human Agency', 'domains': ['mission', 'values'], 'keywords': ['human', 'agency']})
t('Knowledge ingest', lambda: ok_(len(forge.knowledge_base) >= 2))
t('Knowledge search', lambda: gt(len(forge.search('human capability')), 0))
t('Knowledge stats', lambda: has('total', forge.get_stats()))

print('\n=== KNOWLEDGE GRAPH ===')
kb_items = [item.to_dict() for item in forge.knowledge_base]
t('Graph search', lambda: gt(len(retrieve('human capability', kb_items)['context']['context_items']), 0))
t('Domain classification', lambda: gt(len(classify_domains('How to improve onboarding?')), 0))

print('\n=== MEMORY ENGINE ===')
m1 = create_memory('semantic', 'NAM created to serve WAI', importance=0.9, participants=['NAM Oshun'])
m2 = create_memory('episodic', 'First user interaction', importance=0.7)
t('Memory creation', lambda: ok_(m1['memory_id'].startswith('MEM-')))
t('Memory by type', lambda: eq(len(retrieve_memories([m1, m2], memory_type='semantic')), 1))
t('Memory by importance', lambda: eq(len(retrieve_memories([m1, m2], min_importance=0.8)), 1))
ev = create_autobiographical_event('NAM_CREATED', 'NAM initialized', ['NAM Oshun'], 'Begins', 'Operational', 'Every system needs a beginning', 1.0)
t('Autobiographical', lambda: eq(ev['memory_type'], 'episodic'))
intn = create_intention('Improve onboarding', '2026-09-01', ['kb'], 'Hybrid NAM', 'Critical')
t('Prospective memory', lambda: ok_(intn['intention_id'].startswith('INT-')))
drift_result = detect_drift([intn], [m2])
t('Drift detection', lambda: ok_(isinstance(drift_result, list)))
team = [{'name': 'Alice', 'skills': ['Python', 'React'], 'development_goals': [{'name': 'Learn Go', 'required_skills': ['Go']}]}]
t('Team analysis', lambda: gt(len(analyze_team_context(team)['capability_gaps']), 0))

print('\n=== DREAM ENGINE ===')
inp = assemble_dream_inputs([m1], ['What next?'], ['New feature'], ['Retention'], [intn], [m2])
dream = generate_dream(inp)
t('Dream gen', lambda: ok_(dream['dream_id'].startswith('DR-')))
t('Dream synthetic', lambda: eq(dream['ontology'], 'synthetic'))
t('Dream themes', lambda: gt(len(dream['themes']), 0))

print('\n=== REFLECTION ENGINE ===')
ref = create_reflection({'type': 'test', 'description': 'Test', 'importance': 0.5}, 'Perfect', 'Not perfect')
t('Reflection', lambda: ok_(ref['reflection_id'].startswith('REF-')))
t('Gap analysis', lambda: has('gap_type', ref['gap_analysis']))
refs = [create_reflection({'type': 'test', 'description': f'Event {i}', 'importance': 0.5}, 'Expected', 'Reality differs significantly') for i in range(5)]
t('Tension detection', lambda: has('tensions_detected', generate_constitutional_tension(refs)))

print('\n=== LEADERSHIP ENGINE ===')
e1 = evaluate_action({'description': 'Teach users', 'actor': 'Jamil', 'purpose': 'Education', 'beneficiary': 'student'})
t('Alignment', lambda: gt(e1['overall_alignment'], 0.5))
t('Escalation', lambda: ge(e1['escalation_level']['level'], 0))
t('Recommendation', lambda: gt(len(e1['recommendation']), 0))
t('Ledger', lambda: ok_(create_ledger_entry(e1)['decision_id'].startswith('DEC-')))

print('\n=== JAMIL PROTOCOL ===')
req = create_review_request('New feature', 'Improve platform', ['Must be safe'], ['Security risk'], 'Better platform')
resp = process_review(req, e1)
t('Jamil review', lambda: has('alignment', resp) and has('recommendation', resp))
ar = classify_autonomy('search_information')
ac = classify_autonomy('modify_constitution')
t('Autonomy', lambda: eq(ar['autonomy_level'], 'observe') and eq(ac['autonomy_level'], 'require_approval'))
esc = escalate('Test', 'advisory', {}, 'Jamil', 'Test')
t('Escalation', lambda: ok_(esc['escalation_id'].startswith('ESC-')) and eq(esc['status'], 'open'))
res = resolve_escalation(esc, 'NAM Oshun', 'Resolved', True)
t('Resolution', lambda: eq(res['status'], 'resolved') and eq(res['approved'], True))

print('\n=== AUTHORIZATION ===')
sens = ['modify_constitution', 'change_organizational_policy', 'delete_memory', 'major_external_commitment', 'modify_mission', 'budget_allocation', 'user_data_access', 'security_operation']
t('Sensitive require approval', lambda: ok_(all(classify_autonomy(a)['autonomy_level'] == 'require_approval' for a in sens)))
rout = ['search_information', 'organize_knowledge']
t('Routine autonomous', lambda: ok_(all(classify_autonomy(a)['autonomy_level'] in ['observe', 'execute_reversible'] for a in rout)))

print('\n=== CROSS-ECOSYSTEM ===')
t('NAM->Create', lambda: gt(evaluate_action({'description': 'Help create content', 'actor': 'NAM', 'purpose': 'Creation', 'beneficiary': 'creator'})['overall_alignment'], 0.5))
t('NAM->Learn', lambda: gt(evaluate_action({'description': 'Recommend learning path', 'actor': 'NAM', 'purpose': 'Education', 'beneficiary': 'student'})['overall_alignment'], 0.5))
t('Create->Publish', lambda: gt(evaluate_action({'description': 'Publish course', 'actor': 'Jamil', 'purpose': 'Distribution', 'beneficiary': 'creator'})['overall_alignment'], 0.5))

print(f'\n{"="*50}')
print(f'RESULTS: {p} passed, {f} failed')
print(f'{"="*50}')
