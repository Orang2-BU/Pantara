# Technical Specification

## Arsitektur MVP

`Web frontend → API → database`

Adaptive engine dapat menjadi modul backend sederhana terlebih dahulu. Pisahkan fungsi perhitungan dari UI agar bisa diuji.

## Modul

- Auth and roles
- Workspace/team
- Projects/tasks
- Profiles and capacity signals
- Adaptive analysis
- Assignments and feedback

## Data flow

1. Frontend mengirim task id dan team id.
2. Backend mengambil task, profile, workload, access support.
3. Engine menghitung hasil deterministik.
4. API mengembalikan recommendation + evidence.
5. Lead mengirim keputusan assignment.
6. Employee mengirim progress, signal, blocker, completion context.

## Minimum API

`GET /projects/:id`, `POST /tasks`, `POST /tasks/:id/analyze`, `POST /tasks/:id/assign`, `POST /members/:id/capacity`, `POST /tasks/:id/blockers`, `POST /tasks/:id/complete`.

## Security and privacy

Role-based access, least data collection, no health diagnosis fields, validation at API boundary, and demo data separated from production data.
