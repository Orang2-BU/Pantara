"""Human-readable assignment policy; no additive score decides eligibility."""

CAPACITY_ORDER = {'AVAILABLE': 3, 'BALANCED': 2, 'NEAR_CAPACITY': 1, 'OVER_CAPACITY': 0}
CAPABILITY_ORDER = {'VERY_STRONG': 4, 'STRONG': 3, 'MODERATE': 2, 'LIMITED': 1,
                    'INSUFFICIENT_EVIDENCE': 0}
CONFIDENCE_ORDER = {'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}


def evaluate_candidate(candidate, has_blocker=False):
    capability = candidate['capability']
    capacity = candidate['capacity']
    access = candidate['access']
    reasons = []
    considerations = []

    if capability['status'] == 'REVIEW_REQUIRED':
        category = 'REVIEW_REQUIRED'
        reasons.append('STALE_OBSERVED_EVIDENCE' if 'STALE_OBSERVED_EVIDENCE' in capability.get('reason_codes', [])
                       else 'MIXED_PROFICIENCY_EVIDENCE')
        considerations.append('Capability evidence needs human review.')
    elif capability.get('mandatory_missing') or capability['status'] == 'REQUIREMENT_NOT_MET':
        category = 'NOT_VIABLE'
        reasons.append('MANDATORY_REQUIREMENT_MISSING' if capability.get('mandatory_missing') else 'CAPABILITY_REQUIREMENT_NOT_MET')
    elif access['readiness'] != 'READY':
        category = 'REVIEW_REQUIRED'
        reasons.append('ACCESS_SUPPORT_REQUIRED' if access['readiness'] == 'NEEDS_SUPPORT' else 'ACCESS_UNRESOLVED')
        considerations.append('Resolve access conditions before assignment.')
    elif capacity['fit'] == 'OVER_CAPACITY' or capacity['signal_level'] == 'OVER_CAPACITY':
        category = 'REVIEW_REQUIRED'
        reasons.append('PROJECTED_OVER_CAPACITY' if capacity['fit'] == 'OVER_CAPACITY' else 'EMPLOYEE_CAPACITY_SIGNAL')
        considerations.append('Assignment needs a workload review.')
    else:
        category = 'ALTERNATIVE'
        reasons.extend(['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY'])
        if 'SELF_DECLARED_ONLY' in capability.get('reason_codes', []):
            reasons.append('DECLARED_PROFICIENCY_ONLY')
        if 'OBSERVED_EVIDENCE_SUPPORTS_REQUIREMENT' in capability.get('reason_codes', []):
            reasons.append('OBSERVED_PROFICIENCY_SUPPORTED')
        if capability['level'] in {'STRONG', 'VERY_STRONG'} and capability['confidence'] == 'HIGH':
            reasons.append('STRONG_CAPABILITY_EVIDENCE')
        reasons.append('PROJECTED_NEAR_CAPACITY' if capacity['fit'] == 'NEAR_CAPACITY'
                       else 'SUSTAINABLE_PROJECTED_CAPACITY')
        if capability['confidence'] == 'LOW':
            reasons.append('LIMITED_HISTORICAL_EVIDENCE')
        if capability['relevant_experience_result']['evidence_task_ids']:
            reasons.append('RELEVANT_EXPERIENCE_FOUND')
    if has_blocker:
        reasons.append('ACTIVE_BLOCKER')
        considerations.append('The task has an active blocker.')

    return {
        'member_id': candidate['member_id'], 'recommendation': category,
        'capability': {key: capability[key] for key in ('status', 'level', 'confidence')},
        'capacity': {'current': capacity['current_fit'], 'projected': capacity['fit'],
                     'employee_signal': capacity['signal_level']},
        'access': {'status': access['readiness']},
        'reason_codes': list(dict.fromkeys(reasons)), 'considerations': considerations,
    }


def select_candidate(candidates):
    """Prefer sustainable capacity, then capability evidence; return no final pick if all need review."""
    viable = [c for c in candidates if c['recommendation_result']['recommendation'] == 'ALTERNATIVE']
    viable.sort(key=lambda c: (
        CAPACITY_ORDER[c['capacity']['fit']], CAPABILITY_ORDER[c['capability']['level']],
        CONFIDENCE_ORDER[c['capability']['confidence']],
        len(c['capability']['relevant_experience_result']['evidence_task_ids']),
        c['member_id'],
    ), reverse=True)
    if viable:
        viable[0]['recommendation_result']['recommendation'] = 'RECOMMENDED'
    return viable[0] if viable else None
