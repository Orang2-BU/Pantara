# Data Model

```text
Workspace 1—N Team
Team 1—N Member
Workspace 1—N Project
Project 1—N Task
Member 1—1 WorkProfile
Member 1—N CapacitySignal
Task 1—N Assignment
Task 1—N Blocker
Task 1—1 CompletionEvidence
Task 1—N AdaptiveAnalysis
```

## Minimal fields

- `Member`: id, name, role, teamId.
- `WorkProfile`: memberId, skills[], experience[], accessPreferences[].
- `Project`: id, name, deadline, teamId.
- `Task`: id, projectId, title, requiredSkills[], complexity, effort, deadline, accessRequirements[], status.
- `CapacitySignal`: memberId, level, context[], createdAt.
- `Assignment`: taskId, memberId, decidedBy, reason, createdAt.
- `Blocker`: taskId, type, note, status.
- `CompletionEvidence`: taskId, estimatedEffort, actualEffort, factors[].
- `AdaptiveAnalysis`: taskId, candidates[], recommendation, evidence, createdAt.

Jangan menyimpan diagnosis, label kesehatan mental, atau private note yang tidak diperlukan untuk kerja.
