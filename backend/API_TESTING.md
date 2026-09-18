# Pantara-MindCraft API Testing Guide

## Base URL
```
http://localhost:8000
```

## API Endpoints

### 1. Workspaces
```bash
# List workspaces
curl http://localhost:8000/api/workspaces/

# Get workspace
curl http://localhost:8000/api/workspaces/{id}/

# Create workspace
curl -X POST http://localhost:8000/api/workspaces/ \
  -H "Content-Type: application/json" \
  -d '{"name": "New Workspace"}'
```

### 2. Teams
```bash
# List teams
curl http://localhost:8000/api/teams/

# Create team
curl -X POST http://localhost:8000/api/teams/ \
  -H "Content-Type: application/json" \
  -d '{"workspace": "workspace-uuid", "name": "New Team"}'
```

### 3. Members
```bash
# List members
curl http://localhost:8000/api/members/

# Create member
curl -X POST http://localhost:8000/api/members/ \
  -H "Content-Type: application/json" \
  -d '{
    "team": "team-uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "EMPLOYEE"
  }'

# Update capacity signal
curl -X POST http://localhost:8000/api/members/{id}/capacity/ \
  -H "Content-Type: application/json" \
  -d '{
    "level": "AVAILABLE",
    "context": ["Ready for work"]
  }'
```

### 4. Projects & Tasks
```bash
# List projects
curl http://localhost:8000/api/projects/

# Create project
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "workspace": "workspace-uuid",
    "team": "team-uuid",
    "name": "New Project",
    "deadline": "2026-12-31"
  }'

# Create task
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "project": "project-uuid",
    "title": "Build Feature X",
    "description": "Description here",
    "required_skills": ["Python", "Django"],
    "complexity": "MEDIUM",
    "estimated_effort": 8,
    "deadline": "2026-10-01",
    "access_requirements": ["Remote"]
  }'
```

### 5. Adaptive Analysis (Core Feature)
```bash
# Analyze task - Get recommendations
curl -X POST http://localhost:8000/api/tasks/{task-id}/analyze/

# Response includes:
# - candidates[] with scores (capability + capacity + access)
# - recommendation with reason
# - evidence per dimension
# - workload_impact (before/after hours)
```

### 6. Assignment (Human Decision)
```bash
# Assign task to member
curl -X POST http://localhost:8000/api/tasks/{task-id}/assign/ \
  -H "Content-Type: application/json" \
  -d '{
    "task": "task-uuid",
    "member": "member-uuid",
    "decided_by": "lead-uuid",
    "reason": "Best fit based on capability and capacity"
  }'
```

### 7. Blockers
```bash
# Report blocker
curl -X POST http://localhost:8000/api/blockers/ \
  -H "Content-Type: application/json" \
  -d '{
    "task": "task-uuid",
    "type": "TECHNICAL",
    "note": "Waiting for API access"
  }'
```

### 8. Task Completion
```bash
# Complete task with evidence
curl -X POST http://localhost:8000/api/tasks/{task-id}/complete/ \
  -H "Content-Type: application/json" \
  -d '{
    "task": "task-uuid",
    "estimated_effort": 8,
    "actual_effort": 10,
    "factors": ["More complex than expected", "New requirement added"]
  }'
```

## Demo Flow (Golden Path)

```bash
# 1. Get seeded data
curl http://localhost:8000/api/workspaces/
curl http://localhost:8000/api/teams/
curl http://localhost:8000/api/members/
curl http://localhost:8000/api/projects/

# 2. Get pending tasks
curl http://localhost:8000/api/tasks/

# 3. Run adaptive analysis on first task
TASK_ID="get-from-step-2"
curl -X POST http://localhost:8000/api/tasks/$TASK_ID/analyze/

# 4. Review recommendation (shows top candidate with reasoning)
# Expected: Budi Pratama recommended for "Implement Adaptive Workload Engine"
# Reason: Strong Python/Django/Algorithm skills + Available capacity

# 5. Make assignment (human decision)
curl -X POST http://localhost:8000/api/tasks/$TASK_ID/assign/ \
  -H "Content-Type: application/json" \
  -d '{
    "task": "'$TASK_ID'",
    "member": "budi-member-uuid",
    "decided_by": "hadi-lead-uuid",
    "reason": "Accepted recommendation"
  }'

# 6. Member updates capacity
curl -X POST http://localhost:8000/api/members/budi-uuid/capacity/ \
  -H "Content-Type: application/json" \
  -d '{"level": "BALANCED", "context": ["Working on engine"]}'
```

## OpenAPI Documentation

Live interactive docs:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema JSON**: http://localhost:8000/api/schema/

## Adaptive Engine Logic

**Capability Fit (0-2):**
- 2.0 = STRONG (100% skills match)
- 1.0 = PARTIAL (≥50% skills match)
- 0.0 = LIMITED (<50% skills match)

**Capacity Fit (0-2):**
- 2.0 = AVAILABLE (<15h workload)
- 1.5 = BALANCED (15-25h workload)
- 0.8 = NEAR_CAPACITY (25-35h workload)
- 0.0 = OVER_CAPACITY (≥35h workload)

**Access Readiness (0-2):**
- 2.0 = READY (all requirements met)
- 1.0 = NEEDS_SUPPORT (partial match)
- 0.0 = UNRESOLVED (no match, needs clarification)

**Total Score = Capability + Capacity + Access (max 6.0)**

Candidates sorted by eligibility (access resolved) then score descending.

## Testing Determinism

Same input = same output:
```bash
# Run analysis twice on same task
curl -X POST http://localhost:8000/api/tasks/$TASK_ID/analyze/
curl -X POST http://localhost:8000/api/tasks/$TASK_ID/analyze/

# Scores and recommendations should be identical
```

## Admin Panel

Access Django admin at: http://localhost:8000/admin/

Create superuser first:
```bash
python manage.py createsuperuser
```
