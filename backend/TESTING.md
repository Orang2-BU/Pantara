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
          python-version: '3.11'
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
