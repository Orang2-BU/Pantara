# Pantara-MindCraft Backend

Django REST API backend untuk Pantara-MindCraft - Adaptive Human-Centered Workload Workspace.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_data

# Run development server
python manage.py runserver
```

## API Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Architecture

**3 Django Apps:**

1. **core** - Workspace, Team, Member, WorkProfile, CapacitySignal
2. **work** - Project, Task, Assignment, Blocker, CompletionEvidence
3. **adaptive** - AdaptiveAnalysis, AdaptiveEngine (deterministic algorithm)

## Key Endpoints

### Core
- `GET/POST /api/workspaces/`
- `GET/POST /api/teams/`
- `GET/POST /api/members/`
- `POST /api/members/{id}/capacity/` - Update capacity signal

### Work
- `GET/POST /api/projects/`
- `GET/POST /api/tasks/`
- `POST /api/tasks/{id}/analyze/` - Run adaptive analysis
- `POST /api/tasks/{id}/assign/` - Human assignment decision
- `POST /api/tasks/{id}/complete/` - Complete with evidence
- `POST /api/blockers/` - Report blocker

### Adaptive
- `GET /api/adaptive-analyses/` - View analysis history

## Adaptive Engine

Deterministik scoring (0-6):
- **Capability Fit** (0-2): Strong/Partial/Limited based on skills match
- **Capacity Fit** (0-2): Available/Balanced/Near/Over based on workload + signal
- **Access Readiness** (0-2): Ready/Needs Support/Unresolved based on requirements match

Engine returns ranked candidates with evidence + workload impact visualization.

## Demo Data

Seeder creates:
- 1 Workspace, 1 Team, 4 Members (1 Lead, 3 Developers)
- Work profiles with skills, experience, access preferences
- Capacity signals (1 member OVER_CAPACITY untuk demonstrasi)
- 1 Project dengan 2 pending tasks
- Pre-computed adaptive analysis untuk task pertama

## Security Guardrails

✅ NO mental health diagnosis fields  
✅ NO resign prediction  
✅ NO performance ranking  
✅ Human-in-the-loop assignment only  
✅ Transparent recommendation reasoning  
✅ Access barrier ≠ incapability labeling
