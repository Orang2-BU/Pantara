# Adaptive Engine Dummy-Data Test Report

**Generated at**: 2026-09-21T06:04:57.675841+00:00

## Executive Summary

- **Total assertions**: 41
- **Passed**: 41
- **Failed**: 0
- **Pass rate**: 100.0%

This report exercises the adaptive engine across capability, capacity, access, policy, re-analysis, evidence workflow, and edge-case dimensions. Each assertion compares expected behavior against actual deterministic output.

## Capability Matching

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Capability Full Match | Eligible / Recommended | ELIGIBLE | PASS |
| Capability Partial Match | Alternative (partial fit) | ALTERNATIVE | PASS |
| Capability No Match | NOT_VIABLE | NOT_VIABLE | PASS |
| Capability Case Insensitivity | Eligible | ELIGIBLE | PASS |

### Capability Full Match
- **Description**: Strong Dev has all required skills (python, django).
- **Expected**: Eligible / Recommended
- **Actual**: ELIGIBLE
- **Status**: PASS

### Capability Partial Match
- **Description**: Partial Dev has only python; django is missing but ratio >= 0.5.
- **Expected**: Alternative (partial fit)
- **Actual**: ALTERNATIVE
- **Status**: PASS

### Capability No Match
- **Description**: Unskilled Dev only knows java; none of the required skills match.
- **Expected**: NOT_VIABLE
- **Actual**: NOT_VIABLE
- **Status**: PASS

### Capability Case Insensitivity
- **Description**: Skill matching normalizes reactjs->react and ignores case.
- **Expected**: Eligible
- **Actual**: ELIGIBLE
- **Status**: PASS

### Sample Data
```json
{
  "candidates": [
    {
      "member_id": "18cdcb4e-090e-4061-9984-d29926f60f24",
      "member_name": "Strong Dev",
      "role": "EMPLOYEE",
      "capability": {
        "status": "ELIGIBLE",
        "confidence": "LOW",
        "proficiency": {
          "python": {
            "declared": "INTERMEDIATE",
            "observed": "UNKNOWN",
            "confidence": "LOW",
            "stale": false
          },
          "django": {
            "declared": "INTERMEDIATE",
            "observed": "UNKNOWN",
            "confidence": "LOW",
            "stale": false
          }
        },
        "level": "STRONG",
        "fit": "STRONG",
        "score": 2.0,
        "skill_match": {
          "level": "FULL"
        },
        "required_match": 1.0,
        "matched_skills": [
          "django",
          "python"
        ],
        "missing_skills": [],
        "relevant_experience": [],
        "mandatory_missing": [],
        "preferred_matches": [],
        "missing_requirements": [],
        "considerations": [],
        "similar_completed_tasks": 0,
        "relevant_experience_result": {
          "level": "NONE",
          "evidence_task_ids": []
        },
        "task_familiarity": {
          "level": "UNKNOWN",
          "similar_task_ids": []
        },
        "evidence": "2/2 required skills matched; 0 experience records; 0 relevant completed tasks.",
        "reason_codes": [
          "REQUIRED_SKILLS_MATCH",
          "SELF_DECLARED_ONLY"
        
```

## Capacity Calculations

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Available Capacity | ALTERNATIVE / Eligible | RECOMMENDED | PASS |
| Balanced Capacity | ALTERNATIVE / Eligible | ALTERNATIVE | PASS |
| Near Capacity | ALTERNATIVE | ALTERNATIVE | PASS |
| Over Capacity Signal Override | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| Light Workload => AVAILABLE | AVAILABLE | AVAILABLE | PASS |

### Available Capacity
- **Description**: AVAILABLE signal keeps candidate viable.
- **Expected**: ALTERNATIVE / Eligible
- **Actual**: RECOMMENDED
- **Status**: PASS

### Balanced Capacity
- **Description**: BALANCED signal keeps candidate viable.
- **Expected**: ALTERNATIVE / Eligible
- **Actual**: ALTERNATIVE
- **Status**: PASS

### Near Capacity
- **Description**: NEAR_CAPACITY signal still yields ALTERNATIVE.
- **Expected**: ALTERNATIVE
- **Actual**: ALTERNATIVE
- **Status**: PASS

### Over Capacity Signal Override
- **Description**: OVER_CAPACITY signal triggers review.
- **Expected**: REVIEW_REQUIRED
- **Actual**: REVIEW_REQUIRED
- **Status**: PASS

### Light Workload => AVAILABLE
- **Description**: Member with no active assignments gets projected load < 15h.
- **Expected**: AVAILABLE
- **Actual**: AVAILABLE
- **Status**: PASS

### Sample Data
```json
{
  "candidates": [
    {
      "member_id": "7402e705-cc9d-4b01-9a27-86429bccea1f",
      "member_name": "Available Dev",
      "role": "EMPLOYEE",
      "capability": {
        "status": "ELIGIBLE",
        "confidence": "LOW",
        "proficiency": {
          "python": {
            "declared": "INTERMEDIATE",
            "observed": "UNKNOWN",
            "confidence": "LOW",
            "stale": false
          }
        },
        "level": "STRONG",
        "fit": "STRONG",
        "score": 2.0,
        "skill_match": {
          "level": "FULL"
        },
        "required_match": 1.0,
        "matched_skills": [
          "python"
        ],
        "missing_skills": [],
        "relevant_experience": [],
        "mandatory_missing": [],
        "preferred_matches": [],
        "missing_requirements": [],
        "considerations": [],
        "similar_completed_tasks": 0,
        "relevant_experience_result": {
          "level": "NONE",
          "evidence_task_ids": []
        },
        "task_familiarity": {
          "level": "UNKNOWN",
          "similar_task_ids": []
        },
        "evidence": "1/1 required skills matched; 0 experience records; 0 relevant completed tasks.",
        "reason_codes": [
          "REQUIRED_SKILLS_MATCH",
          "SELF_DECLARED_ONLY"
        ]
      },
      "capacity": {
        "fit": "AVAILABLE",
        "current_fit": "AVAILABLE",
        "system_fit": "AVAILABLE",
        "score": 2.0,
        "current_hours": 0,
       
```

## Access Readiness

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Access READY | READY / Eligible | READY | PASS |
| Access NEEDS_SUPPORT | NEEDS_SUPPORT / REVIEW_REQUIRED | NEEDS_SUPPORT | PASS |
| Access UNRESOLVED | UNRESOLVED / REVIEW_REQUIRED | UNRESOLVED | PASS |

### Access READY
- **Description**: Workspace supports Remote and employee prefers Remote.
- **Expected**: READY / Eligible
- **Actual**: READY
- **Status**: PASS

### Access NEEDS_SUPPORT
- **Description**: Flexible Hours is required but not supported and employee has no preference.
- **Expected**: NEEDS_SUPPORT / REVIEW_REQUIRED
- **Actual**: NEEDS_SUPPORT
- **Status**: PASS

### Access UNRESOLVED
- **Description**: Screen Reader is not supported at all.
- **Expected**: UNRESOLVED / REVIEW_REQUIRED
- **Actual**: UNRESOLVED
- **Status**: PASS

### Sample Data
```json
{
  "candidates": [
    {
      "member_id": "1c578018-4f32-4857-9346-5d70dd895a3f",
      "member_name": "Unresolved Dev",
      "role": "EMPLOYEE",
      "capability": {
        "status": "ELIGIBLE",
        "confidence": "LOW",
        "proficiency": {
          "python": {
            "declared": "INTERMEDIATE",
            "observed": "UNKNOWN",
            "confidence": "LOW",
            "stale": false
          }
        },
        "level": "STRONG",
        "fit": "STRONG",
        "score": 2.0,
        "skill_match": {
          "level": "FULL"
        },
        "required_match": 1.0,
        "matched_skills": [
          "python"
        ],
        "missing_skills": [],
        "relevant_experience": [],
        "mandatory_missing": [],
        "preferred_matches": [],
        "missing_requirements": [],
        "considerations": [],
        "similar_completed_tasks": 0,
        "relevant_experience_result": {
          "level": "NONE",
          "evidence_task_ids": []
        },
        "task_familiarity": {
          "level": "UNKNOWN",
          "similar_task_ids": []
        },
        "evidence": "1/1 required skills matched; 0 experience records; 0 relevant completed tasks.",
        "reason_codes": [
          "REQUIRED_SKILLS_MATCH",
          "SELF_DECLARED_ONLY"
        ]
      },
      "capacity": {
        "fit": "AVAILABLE",
        "current_fit": "AVAILABLE",
        "system_fit": "AVAILABLE",
        "score": 2.0,
        "current_hours": 0,
      
```

## Policy Evaluation (16 Adversarial Personas)

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Persona: cold_start_expert | ALTERNATIVE / LIMITED_HISTORICAL_EVIDENCE | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY', 'LIMITED_HISTORICAL_EVIDENCE'] | PASS |
| Persona: declared_observed_disagree | REVIEW_REQUIRED / MIXED_PROFICIENCY_EVIDENCE | REVIEW_REQUIRED / ['MIXED_PROFICIENCY_EVIDENCE'] | PASS |
| Persona: many_minor_evidence | ALTERNATIVE / MANDATORY_REQUIREMENTS_MET | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY'] | PASS |
| Persona: few_primary_evidence | ALTERNATIVE / LIMITED_HISTORICAL_EVIDENCE | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY', 'LIMITED_HISTORICAL_EVIDENCE'] | PASS |
| Persona: identical_contexts | ALTERNATIVE / SUSTAINABLE_PROJECTED_CAPACITY | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY'] | PASS |
| Persona: strong_but_stale | REVIEW_REQUIRED / STALE_OBSERVED_EVIDENCE | REVIEW_REQUIRED / ['STALE_OBSERVED_EVIDENCE'] | PASS |
| Persona: mandatory_missing | NOT_VIABLE / MANDATORY_REQUIREMENT_MISSING | NOT_VIABLE / ['MANDATORY_REQUIREMENT_MISSING'] | PASS |
| Persona: required_fit_missing | NOT_VIABLE / CAPABILITY_REQUIREMENT_NOT_MET | NOT_VIABLE / ['CAPABILITY_REQUIREMENT_NOT_MET'] | PASS |
| Persona: preferred_missing | ALTERNATIVE / MANDATORY_REQUIREMENTS_MET | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'STRONG_CAPABILITY_EVIDENCE', 'SUSTAINABLE_PROJECTED_CAPACITY'] | PASS |
| Persona: overqualified | ALTERNATIVE / ACCESS_READY | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'STRONG_CAPABILITY_EVIDENCE', 'SUSTAINABLE_PROJECTED_CAPACITY'] | PASS |
| Persona: strong_over_capacity | REVIEW_REQUIRED / PROJECTED_OVER_CAPACITY | REVIEW_REQUIRED / ['PROJECTED_OVER_CAPACITY'] | PASS |
| Persona: moderate_available | ALTERNATIVE / SUSTAINABLE_PROJECTED_CAPACITY | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY'] | PASS |
| Persona: unresolved_access | REVIEW_REQUIRED / ACCESS_UNRESOLVED | REVIEW_REQUIRED / ['ACCESS_UNRESOLVED'] | PASS |
| Persona: resolvable_access | REVIEW_REQUIRED / ACCESS_SUPPORT_REQUIRED | REVIEW_REQUIRED / ['ACCESS_SUPPORT_REQUIRED'] | PASS |
| Persona: employee_over_signal | REVIEW_REQUIRED / EMPLOYEE_CAPACITY_SIGNAL | REVIEW_REQUIRED / ['EMPLOYEE_CAPACITY_SIGNAL'] | PASS |
| Persona: near_capacity | ALTERNATIVE / PROJECTED_NEAR_CAPACITY | ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'STRONG_CAPABILITY_EVIDENCE', 'PROJECTED_NEAR_CAPACITY'] | PASS |
| Selection: Sustainable beats stronger overloaded | EMP-1 (sustainable) | EMP-1 | PASS |

### Persona: cold_start_expert
- **Description**: Expected category 'ALTERNATIVE' and reason code 'LIMITED_HISTORICAL_EVIDENCE'.
- **Expected**: ALTERNATIVE / LIMITED_HISTORICAL_EVIDENCE
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY', 'LIMITED_HISTORICAL_EVIDENCE']
- **Status**: PASS

### Persona: declared_observed_disagree
- **Description**: Expected category 'REVIEW_REQUIRED' and reason code 'MIXED_PROFICIENCY_EVIDENCE'.
- **Expected**: REVIEW_REQUIRED / MIXED_PROFICIENCY_EVIDENCE
- **Actual**: REVIEW_REQUIRED / ['MIXED_PROFICIENCY_EVIDENCE']
- **Status**: PASS

### Persona: many_minor_evidence
- **Description**: Expected category 'ALTERNATIVE' and reason code 'MANDATORY_REQUIREMENTS_MET'.
- **Expected**: ALTERNATIVE / MANDATORY_REQUIREMENTS_MET
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY']
- **Status**: PASS

### Persona: few_primary_evidence
- **Description**: Expected category 'ALTERNATIVE' and reason code 'LIMITED_HISTORICAL_EVIDENCE'.
- **Expected**: ALTERNATIVE / LIMITED_HISTORICAL_EVIDENCE
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY', 'LIMITED_HISTORICAL_EVIDENCE']
- **Status**: PASS

### Persona: identical_contexts
- **Description**: Expected category 'ALTERNATIVE' and reason code 'SUSTAINABLE_PROJECTED_CAPACITY'.
- **Expected**: ALTERNATIVE / SUSTAINABLE_PROJECTED_CAPACITY
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY']
- **Status**: PASS

### Persona: strong_but_stale
- **Description**: Expected category 'REVIEW_REQUIRED' and reason code 'STALE_OBSERVED_EVIDENCE'.
- **Expected**: REVIEW_REQUIRED / STALE_OBSERVED_EVIDENCE
- **Actual**: REVIEW_REQUIRED / ['STALE_OBSERVED_EVIDENCE']
- **Status**: PASS

### Persona: mandatory_missing
- **Description**: Expected category 'NOT_VIABLE' and reason code 'MANDATORY_REQUIREMENT_MISSING'.
- **Expected**: NOT_VIABLE / MANDATORY_REQUIREMENT_MISSING
- **Actual**: NOT_VIABLE / ['MANDATORY_REQUIREMENT_MISSING']
- **Status**: PASS

### Persona: required_fit_missing
- **Description**: Expected category 'NOT_VIABLE' and reason code 'CAPABILITY_REQUIREMENT_NOT_MET'.
- **Expected**: NOT_VIABLE / CAPABILITY_REQUIREMENT_NOT_MET
- **Actual**: NOT_VIABLE / ['CAPABILITY_REQUIREMENT_NOT_MET']
- **Status**: PASS

### Persona: preferred_missing
- **Description**: Expected category 'ALTERNATIVE' and reason code 'MANDATORY_REQUIREMENTS_MET'.
- **Expected**: ALTERNATIVE / MANDATORY_REQUIREMENTS_MET
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'STRONG_CAPABILITY_EVIDENCE', 'SUSTAINABLE_PROJECTED_CAPACITY']
- **Status**: PASS

### Persona: overqualified
- **Description**: Expected category 'ALTERNATIVE' and reason code 'ACCESS_READY'.
- **Expected**: ALTERNATIVE / ACCESS_READY
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'STRONG_CAPABILITY_EVIDENCE', 'SUSTAINABLE_PROJECTED_CAPACITY']
- **Status**: PASS

### Persona: strong_over_capacity
- **Description**: Expected category 'REVIEW_REQUIRED' and reason code 'PROJECTED_OVER_CAPACITY'.
- **Expected**: REVIEW_REQUIRED / PROJECTED_OVER_CAPACITY
- **Actual**: REVIEW_REQUIRED / ['PROJECTED_OVER_CAPACITY']
- **Status**: PASS

### Persona: moderate_available
- **Description**: Expected category 'ALTERNATIVE' and reason code 'SUSTAINABLE_PROJECTED_CAPACITY'.
- **Expected**: ALTERNATIVE / SUSTAINABLE_PROJECTED_CAPACITY
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'SUSTAINABLE_PROJECTED_CAPACITY']
- **Status**: PASS

### Persona: unresolved_access
- **Description**: Expected category 'REVIEW_REQUIRED' and reason code 'ACCESS_UNRESOLVED'.
- **Expected**: REVIEW_REQUIRED / ACCESS_UNRESOLVED
- **Actual**: REVIEW_REQUIRED / ['ACCESS_UNRESOLVED']
- **Status**: PASS

### Persona: resolvable_access
- **Description**: Expected category 'REVIEW_REQUIRED' and reason code 'ACCESS_SUPPORT_REQUIRED'.
- **Expected**: REVIEW_REQUIRED / ACCESS_SUPPORT_REQUIRED
- **Actual**: REVIEW_REQUIRED / ['ACCESS_SUPPORT_REQUIRED']
- **Status**: PASS

### Persona: employee_over_signal
- **Description**: Expected category 'REVIEW_REQUIRED' and reason code 'EMPLOYEE_CAPACITY_SIGNAL'.
- **Expected**: REVIEW_REQUIRED / EMPLOYEE_CAPACITY_SIGNAL
- **Actual**: REVIEW_REQUIRED / ['EMPLOYEE_CAPACITY_SIGNAL']
- **Status**: PASS

### Persona: near_capacity
- **Description**: Expected category 'ALTERNATIVE' and reason code 'PROJECTED_NEAR_CAPACITY'.
- **Expected**: ALTERNATIVE / PROJECTED_NEAR_CAPACITY
- **Actual**: ALTERNATIVE / ['MANDATORY_REQUIREMENTS_MET', 'ACCESS_READY', 'OBSERVED_PROFICIENCY_SUPPORTED', 'STRONG_CAPABILITY_EVIDENCE', 'PROJECTED_NEAR_CAPACITY']
- **Status**: PASS

### Selection: Sustainable beats stronger overloaded
- **Description**: select_candidate prefers lower workload over stronger capability.
- **Expected**: EMP-1 (sustainable)
- **Actual**: EMP-1
- **Status**: PASS

### Sample Data
```json
{
  "personas_total": 16,
  "invariant_test": "sustainable_beats_overloaded"
}
```

## Re-analysis Triggers

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| No Change => Same Analysis | first.pk == second.pk (24ac4581-e98c-413a-9b8d-7c4d5ce1cbf8) | first.pk == second.pk == 24ac4581-e98c-413a-9b8d-7c4d5ce1cbf8 | PASS |
| Capacity Signal Change => New Analysis | New AdaptiveAnalysis object | third.pk=70f1c600-5166-42cf-b4ab-5b5b67154bd6, first.pk=24ac4581-e98c-413a-9b8d-7c4d5ce1cbf8 | PASS |
| Redistribution Review Triggered | REDISTRIBUTION_REVIEW in reason_codes | ['HUMAN_REVIEW_REQUIRED', 'CONDITION_CHANGED', 'REANALYSIS_TRIGGERED', 'REDISTRIBUTION_REVIEW'] | PASS |
| Blocker => New Analysis | New AdaptiveAnalysis, open_blockers non-empty | fourth.pk=d149792b-a202-4c7c-beeb-bf848c43781d, open_blockers=['DEPENDENCY'] | PASS |
| Task Change => New Analysis | New AdaptiveAnalysis object | fifth.pk=9005cf2c-7938-4b1e-8f7b-50ea660b2fdf, fourth.pk=d149792b-a202-4c7c-beeb-bf848c43781d | PASS |

### No Change => Same Analysis
- **Description**: Re-running without changes returns the existing analysis.
- **Expected**: first.pk == second.pk (24ac4581-e98c-413a-9b8d-7c4d5ce1cbf8)
- **Actual**: first.pk == second.pk == 24ac4581-e98c-413a-9b8d-7c4d5ce1cbf8
- **Status**: PASS

### Capacity Signal Change => New Analysis
- **Description**: OVER_CAPACITY signal triggers reanalysis.
- **Expected**: New AdaptiveAnalysis object
- **Actual**: third.pk=70f1c600-5166-42cf-b4ab-5b5b67154bd6, first.pk=24ac4581-e98c-413a-9b8d-7c4d5ce1cbf8
- **Status**: PASS

### Redistribution Review Triggered
- **Description**: Reason codes include REDISTRIBUTION_REVIEW.
- **Expected**: REDISTRIBUTION_REVIEW in reason_codes
- **Actual**: ['HUMAN_REVIEW_REQUIRED', 'CONDITION_CHANGED', 'REANALYSIS_TRIGGERED', 'REDISTRIBUTION_REVIEW']
- **Status**: PASS

### Blocker => New Analysis
- **Description**: Adding an active blocker triggers reanalysis.
- **Expected**: New AdaptiveAnalysis, open_blockers non-empty
- **Actual**: fourth.pk=d149792b-a202-4c7c-beeb-bf848c43781d, open_blockers=['DEPENDENCY']
- **Status**: PASS

### Task Change => New Analysis
- **Description**: Modifying task attributes triggers reanalysis.
- **Expected**: New AdaptiveAnalysis object
- **Actual**: fifth.pk=9005cf2c-7938-4b1e-8f7b-50ea660b2fdf, fourth.pk=d149792b-a202-4c7c-beeb-bf848c43781d
- **Status**: PASS

### Sample Data
```json
{
  "recommendation": {
    "reason": "No sustainable eligible candidate; human review required.",
    "reason_codes": [
      "HUMAN_REVIEW_REQUIRED",
      "CONDITION_CHANGED",
      "REANALYSIS_TRIGGERED",
      "REDISTRIBUTION_REVIEW"
    ],
    "review_candidates": [
      "b6f8264f-f1bd-4b0e-bd6c-350223fd17ca"
    ],
    "trigger": "task_changed",
    "changed_from_previous": false,
    "intervention": "REVIEW_REDISTRIBUTION"
  },
  "evidence": {
    "task_title": "Reanalysis Task Updated",
    "complexity": "MEDIUM",
    "estimated_effort": 16,
    "required_skills": [
      "python"
    ],
    "access_requirements": [],
    "open_blockers": [
      "DEPENDENCY"
    ]
  }
}
```

## Skill Evidence Workflow

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Evidence Proposed | 1 SkillEvidence row, not confirmed | count=1, confirmed=False | PASS |
| Evidence Confirmed | confirmed_by_employee == True | confirmed=True | PASS |
| Observed Proficiency Updated | observed_proficiency in [BEGINNER, INTERMEDIATE, ADVANCED] and evidence_confidence set | observed=INTERMEDIATE, confidence=LOW | PASS |

### Evidence Proposed
- **Description**: propose_task_evidence creates a SkillEvidence row for the completed task.
- **Expected**: 1 SkillEvidence row, not confirmed
- **Actual**: count=1, confirmed=False
- **Status**: PASS

### Evidence Confirmed
- **Description**: confirm_evidence marks the row confirmed and updates EmployeeSkill.
- **Expected**: confirmed_by_employee == True
- **Actual**: confirmed=True
- **Status**: PASS

### Observed Proficiency Updated
- **Description**: Confirmed evidence updates observed_proficiency and evidence_confidence.
- **Expected**: observed_proficiency in [BEGINNER, INTERMEDIATE, ADVANCED] and evidence_confidence set
- **Actual**: observed=INTERMEDIATE, confidence=LOW
- **Status**: PASS

### Sample Data
```json
{
  "evidence_id": "4",
  "employee_skill": {
    "declared": "INTERMEDIATE",
    "observed": "INTERMEDIATE",
    "confidence": "LOW"
  }
}
```

## Edge Cases

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Cold Start | ELIGIBLE with LOW confidence, SELF_DECLARED_ONLY | status=ELIGIBLE, confidence=LOW | PASS |
| Stale Observed Evidence | REVIEW_REQUIRED, confidence MEDIUM or LOW, observed still ADVANCED | status=REVIEW_REQUIRED, confidence=MEDIUM, observed=ADVANCED | PASS |
| Conflicting Proficiency | REVIEW_REQUIRED, MIXED_PROFICIENCY_EVIDENCE | status=REVIEW_REQUIRED, reasons=['MISSING_REQUIRED_SKILLS', 'MANDATORY_REQUIREMENT_MISSING', 'MIXED_PROFICIENCY_EVIDENCE'] | PASS |
| Alias Normalization | Eligible | ELIGIBLE | PASS |

### Cold Start
- **Description**: Declared proficiency without observed evidence remains low confidence.
- **Expected**: ELIGIBLE with LOW confidence, SELF_DECLARED_ONLY
- **Actual**: status=ELIGIBLE, confidence=LOW
- **Status**: PASS

### Stale Observed Evidence
- **Description**: Evidence older than 365 days reduces confidence; declared INTERMEDIATE, observed ADVANCED triggers review.
- **Expected**: REVIEW_REQUIRED, confidence MEDIUM or LOW, observed still ADVANCED
- **Actual**: status=REVIEW_REQUIRED, confidence=MEDIUM, observed=ADVANCED
- **Status**: PASS

### Conflicting Proficiency
- **Description**: Declared ADVANCED but observed INTERMEDIATE with HIGH confidence triggers review.
- **Expected**: REVIEW_REQUIRED, MIXED_PROFICIENCY_EVIDENCE
- **Actual**: status=REVIEW_REQUIRED, reasons=['MISSING_REQUIRED_SKILLS', 'MANDATORY_REQUIREMENT_MISSING', 'MIXED_PROFICIENCY_EVIDENCE']
- **Status**: PASS

### Alias Normalization
- **Description**: ReactJS declared skill maps to canonical react.
- **Expected**: Eligible
- **Actual**: ELIGIBLE
- **Status**: PASS

### Sample Data
```json
{
  "status": "REVIEW_REQUIRED",
  "confidence": "HIGH",
  "proficiency": {
    "react": {
      "declared": "ADVANCED",
      "observed": "INTERMEDIATE",
      "confidence": "HIGH",
      "stale": false
    }
  },
  "level": "LIMITED",
  "fit": "LIMITED",
  "score": 0.0,
  "skill_match": {
    "level": "NONE"
  },
  "required_match": 0.0,
  "matched_skills": [],
  "missing_skills": [
    "react"
  ],
  "relevant_experience": [],
  "mandatory_missing": [
    "react"
  ],
  "preferred_matches": [],
  "missing_requirements": [
    "react"
  ],
  "considerations": [
    "MIXED_PROFICIENCY_EVIDENCE"
  ],
  "similar_completed_tasks": 0,
  "relevant_experience_result": {
    "level": "NONE",
    "evidence_task_ids": []
  },
  "task_familiarity": {
    "level": "UNKNOWN",
    "similar_task_ids": []
  },
  "evidence": "0/1 required skills matched; 0 experience records; 0 relevant completed tasks.",
  "reason_codes": [
    "MISSING_REQUIRED_SKILLS",
    "MANDATORY_REQUIREMENT_MISSING",
    "MIXED_PROFICIENCY_EVIDENCE"
  ]
}
```
