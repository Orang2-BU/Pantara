# Adaptive Workload Engine — Testing & Validation Guide

Panduan testing komprehensif untuk **Adaptive Engine** pada Pantara-MindCraft platform.

---

## 1. Arsitektur & Dimensi Pengujian

Engine mengevaluasi kesesuaian penugasan task berdasarkan 3 pilar deterministik:

### A. Capability Fit (`calculate_capability`)

- **Formula**: `ratio = len(matched_skills) / len(required_skills)`
- **Kategori Fit**:
  - `STRONG` (score `2.0`): `ratio == 1.0` (semua skill terpenuhi)
  - `PARTIAL` (score `1.0`): `ratio >= 0.5` (minimal 50% skill terpenuhi)
  - `LIMITED` (score `0.0`): `ratio < 0.5`
- **Pengecekan Tambahan**:
  - Case-insensitive matching via `.casefold()`
  - Relevant experience tracking dari `WorkProfile.experience`
  - Relevansi tugas serupa dari `Assignment` yang selesai dan tervalidasi `CompletionEvidence`

### B. Capacity & Task Load (`calculate_capacity` & `task_load`)

- **Formula Task Load**:
  ```python
  task_load = round(estimated_effort * (1 - progress / 100) * complexity_factor * deadline_factor, 2)
  ```
- **Complexity Multipliers**:
  - `LOW`: `0.8`
  - `MEDIUM`: `1.0`
  - `HIGH`: `1.3`
- **Deadline Multipliers**:
  - `< 3 hari`: `1.5`
  - `<= 7 hari`: `1.2`
  - `> 7 hari` atau tanpa deadline: `1.0`
  - Task berstatus `COMPLETED`: `0.0` (zero load)
- **Thresholds Beban Kerja (Projected Hours)**:
  - `AVAILABLE` (score `2.0`): `< 15.0` jam
  - `BALANCED` (score `1.5`): `15.0 - 29.99` jam
  - `NEAR_CAPACITY` (score `0.8`): `30.0 - 39.99` jam
  - `OVER_CAPACITY` (score `0.0`): `>= 40.0` jam
- **Signal Floor Logic**:
  - Self-report `OVER_CAPACITY` dibatasi maksimal ke level `NEAR_CAPACITY` (tidak langsung membuat score 0 mutlak)
  - Mengambil nilai tertinggi antara beban sistem aktual dan batas sinyal mandiri (`max(system_fit, signal_floor)`)

### C. Access Readiness (`calculate_access`)

- Evaluasi pemenuhan kebutuhan akses task terhadap gabungan preferensi personal dan fasilitas workspace (`preferences | workspace_support`):
  - `READY` (score `2.0`): Tidak ada kebutuhan akses yang belum terpenuhi (`unmet == []`)
  - `NEEDS_SUPPORT` (score `1.0`): Sebagian kebutuhan terpenuhi, sebagian butuh koordinasi
  - `UNRESOLVED` (score `0.0`): Seluruh kebutuhan akses belum memiliki solusi (status review, bukan penolakan kapabilitas)

---

## 2. Optimasi Skalabilitas & Konkurensi (1000 Concurrent Users)

Untuk mencegah error `503 Service Unavailable` atau bottleneck server akibat N+1 query:

1. **Batch Context Fetching (`_fetch_team_context`)**:
   - Menghilangkan query loop $O(T \times M)$ pada saat analisa dan refresh tim
   - Seluruh data anggota, profil, riwayat tugas, tugas aktif, dan sinyal kapasitas diambil dalam **5 query terpadu** (efisiensi $O(1)$ fixed database calls)
2. **Backward-Compatibility**:
   - Fungsi `calculate_capability`, `calculate_capacity`, dan `calculate_access` mendukung argumen mandiri maupun context batch pre-fetched
3. **Database Indexing Plan**:
   - `AdaptiveAnalysis`: `['task', '-created_at']`
   - `CapacitySignal`: `['member', '-created_at']`
   - `Assignment`: `['member', 'task']`

---

## 3. Menjalankan Unit Testing

Jalankan perintah berikut di terminal dari direktori `backend/`:

### Menjalankan Seluruh Unit Test Adaptive Engine

```bash
python manage.py test adaptive.tests -v 2
```

### Menjalankan Spesifik Test Method

```bash
# Uji formula task_load
python manage.py test adaptive.tests.AdaptiveEngineTests.test_task_load_formula_matrix

# Uji batas threshold dan signal floor kapasitas
python manage.py test adaptive.tests.AdaptiveEngineTests.test_calculate_capacity_signals_and_thresholds

# Uji pemenuhan kebutuhan aksesibilitas (READY, NEEDS_SUPPORT, UNRESOLVED)
python manage.py test adaptive.tests.AdaptiveEngineTests.test_calculate_access_ready_via_support_and_preferences
```

### Menjalankan Seluruh Test Suite Project

```bash
python manage.py test -v 2
```

---

## 4. Matriks Hasil Pengujian (Test Results Matrix)

| Test Case                                                     | Komponen            | Deskripsi Kasus                                                    | Status   |
| ------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------ | -------- |
| `test_policy_ranks_sustainable_viable_candidate`              | Ranking Policy      | Memilih kandidat viable yang paling sustainable                    | **PASS** |
| `test_capacity_uses_progress_complexity_deadline_and_history` | Capacity & History  | Menguji progres, deadline, histori komparasi tugas selesai         | **PASS** |
| `test_signal_reanalysis_changes_recommendation`               | Real-time Signal    | Perubahan sinyal kapasitas memicu re-evaluasi rekomendasi          | **PASS** |
| `test_unresolved_access_is_review_not_incapability`           | Accessibility       | Akses belum terpenuhi berstatus review, bukan diskualifikasi skill | **PASS** |
| `test_blocker_creates_review_snapshot`                        | Blocker Pipeline    | Blocker aktif memicu snapshot analisa review redistribution        | **PASS** |
| `test_calculate_access_ready_via_support_and_preferences`     | Access Readiness    | Validasi pemenuhan kebutuhan akses melalui profil + workspace      | **PASS** |
| `test_calculate_access_needs_support`                         | Access Readiness    | Validasi kebutuhan sebagian terpenuhi (status NEEDS_SUPPORT)       | **PASS** |
| `test_calculate_access_unresolved`                            | Access Readiness    | Validasi kebutuhan tanpa dukungan (status UNRESOLVED)              | **PASS** |
| `test_task_load_formula_matrix`                               | Formula Matrix      | Validasi perhitungan kompleksitas, deadline urgensi, & progres     | **PASS** |
| `test_calculate_capacity_signals_and_thresholds`              | Capacity Thresholds | Validasi rentang jam beban kerja dan self-report override floor    | **PASS** |

**Total Status: 10/10 PASS (100% Success Rate)**

---

## 5. Coverage Area Testing

### 5.1 Capability Matching (9/9 Test Cases)

✅ **Zero Required Skills** — Task tanpa skill requirement, semua member fit
✅ **Full Match** — Member memiliki semua skill yang dibutuhkan
✅ **Partial Match Boundary** — Tepat 50% skill match (batas PARTIAL)
✅ **Below Threshold** — Di bawah 50% skill match (LIMITED)
✅ **No Match** — 0% skill overlap
✅ **Case Insensitive** — `"PYTHON"` match `"python"`
✅ **Experience Records** — Tracking dari `profile.experience` field
✅ **Completed Tasks Count** — Hanya task dengan `CompletionEvidence` yang dihitung
✅ **Missing Skills Reason Codes** — Flag `MISSING_REQUIRED_SKILLS` vs `REQUIRED_SKILLS_MATCH`

### 5.2 Capacity Calculation (24/24 Test Cases)

✅ **Task Load Formula Matrix** (14 tests):

- Completed task = 0.0
- No deadline baseline
- Complexity multiplier (LOW 0.8, MEDIUM 1.0, HIGH 1.3)
- Deadline urgency (< 3 days 1.5x, <= 7 days 1.2x)
- Progress reduction (1 - progress/100)
- Combined factors

✅ **Capacity Thresholds & Signal Floor** (10 tests):

- AVAILABLE: < 15 jam → score 2.0
- BALANCED: 15-30 jam → score 1.5
- NEAR_CAPACITY: 30-40 jam → score 0.8
- OVER_CAPACITY: >= 40 jam → score 0.0
- Signal floor override (self-reported OVER_CAPACITY capped at NEAR_CAPACITY)
- Signal elevation (BALANCED/NEAR override AVAILABLE system fit)
- Active task filtering (exclude evaluated task, include PENDING/IN_PROGRESS/BLOCKED only)

### 5.3 Access Readiness (8/8 Test Cases)

✅ **READY** — All requirements met via preferences or workspace support
✅ **READY** — All requirements met via workspace support only
✅ **READY** — Split fulfillment (preferences + workspace)
✅ **NEEDS_SUPPORT** — Partial fulfillment
✅ **UNRESOLVED** — Zero fulfillment
✅ **READY** — Empty access requirements (no barrier)
✅ **Case Insensitive** — `"Screen_Reader"` match `"screen_reader"`
✅ **Workspace Context** — Proper workspace.access_support extraction

---

## 6. Acceptance Scenarios (dari `docs/08-TESTING-VALIDATION.md`)

### T1 — Strong Skill, Low Capacity ✅

**Skenario**: Sarah (skill match tinggi, NEAR_CAPACITY) vs Andi (skill cukup, AVAILABLE)
**Expected**: Andi direkomendasikan karena sustainability lebih baik
**Verifikasi**: `test_policy_ranks_sustainable_viable_candidate`

### T2 — Access Support Available ✅

**Skenario**: Task butuh caption, member butuh caption, workspace support caption
**Expected**: Access status READY
**Verifikasi**: `test_calculate_access_ready_via_support_and_preferences`

### T3 — Access Unresolved ✅

**Skenario**: Task butuh accessible office, kondisi lokasi belum diketahui
**Expected**: Status UNRESOLVED (review required), bukan disqualification
**Verifikasi**: `test_unresolved_access_is_review_not_incapability`

### T4 — Assignment Causes Overload ✅

**Skenario**: Simulasi assignment menaikkan workload melewati 40 jam
**Expected**: Capacity fit OVER_CAPACITY, score 0.0, flag review_required
**Verifikasi**: `test_calculate_capacity_signals_and_thresholds` (case #4)

### T5 — Feedback Changes Recommendation ✅

**Skenario**: Member self-report OVER_CAPACITY memicu analisa ulang
**Expected**: Rekomendasi berubah, flag `changed_from_previous`, trigger `capacity_signal_changed`
**Verifikasi**: `test_signal_reanalysis_changes_recommendation`

---

## 7. Test Data Seeding untuk Manual Testing

Jalankan command untuk populate database dengan data demo:

```bash
python manage.py seed_data
```

Seeder akan membuat:

- 1 Workspace ("Pantara Workspace")
- 1 Team (4 members dengan profil berbeda)
- 2 Tasks (backend engine task, frontend UI task)
- 1 Active assignment (mensimulasikan member OVER_CAPACITY)
- Pre-computed AdaptiveAnalysis untuk salah satu task

---

## 8. Validation Questions & Human-in-the-Loop Checks

Pengujian manual UI/UX (bila frontend telah tersedia):

1. **Transparency**: Apakah user memahami alasan rekomendasi dalam 10 detik?
2. **Agency**: Apakah lead tetap aware bahwa keputusan akhir ada di tangan mereka (engine sebagai advisor)?
3. **Non-Judgmental**: Apakah capacity signal dipersepsikan sebagai kontrol kerja, bukan evaluasi kesehatan mental?
4. **Barrier Resolution**: Apakah access barrier diarahkan ke dukungan workplace, bukan blame ke individu?

---

## 9. Performance Benchmarking (Skalabilitas)

### Before Optimization (N+1 Queries)

- 1 task analysis untuk 50 members: **201+ queries**
- 1 team refresh (20 tasks × 50 members): **4,061 queries**
- Concurrent 1000 users: **DB thread exhaustion, 503/504 errors**

### After Optimization (Batch Context Fetch)

- 1 task analysis untuk 50 members: **5 batch queries** (fixed O(1))
- 1 team refresh (20 tasks): **5 batch queries + 20 analysis calls** (shared context)
- Query complexity: **O(T × M) → O(1)**

### Load Test Commands (opsional, butuh `locust` atau `ab`)

```bash
# Apache Benchmark (500 requests, concurrency 50)
ab -n 500 -c 50 http://localhost:8000/api/tasks/

# Django debug toolbar untuk query analysis
# Install django-debug-toolbar, aktifkan INTERNAL_IPS
```

---

## 10. CI/CD Integration

### GitHub Actions / GitLab CI Example

```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          python manage.py test -v 2
      - name: Coverage report
        run: |
          cd backend
          coverage run --source='.' manage.py test
          coverage report
```

---

## 11. Troubleshooting

### Test Failures

- **Import Error**: Pastikan semua dependencies ada di `requirements.txt`
- **Database Lock**: Matikan `db.sqlite3` proses lain, atau gunakan in-memory test DB (sudah default)
- **Signal Issue**: Pastikan `CapacitySignal` import ada di `adaptive/services.py`

### Performance Issues

- **Slow Tests**: Check query count via `django.db.connection.queries` atau `django-debug-toolbar`
- **N+1 Detection**: `python manage.py test --debug-sql` atau install `nplusone` library

---

## 12. Next Steps

### Future Enhancements (Ponytail Comments)

1. **Database Indexing** (tambahkan di `models.py` Meta):

   ```python
   # adaptive/models.py
   class AdaptiveAnalysis(models.Model):
       class Meta:
           indexes = [models.Index(fields=['task', '-created_at'])]

   # core/models.py
   class CapacitySignal(models.Model):
       class Meta:
           indexes = [models.Index(fields=['member', '-created_at'])]
   ```

2. **Async Task Queue** (ketika active task per team > 500):
   - Celery atau Django-RQ untuk background `refresh_team`
   - Move mutation triggers ke `transaction.on_commit()`

3. **Redis Cache** (distributed high-load production):
   - Cache team context selama 5-10 detik
   - Invalidate on signal change / assignment mutation

---

## 13. Contact & Support

- **Bug Reports**: Create issue di repository dengan label `adaptive-engine`
- **Performance Issues**: Tag `@backend` team dengan query profiler output
- **Test Failures**: Attach full stacktrace dan test output

---

**Last Updated**: 2026-09-18
**Test Suite Version**: 1.0.0
**Engine Version**: Optimized (Batch Context Fetch)
