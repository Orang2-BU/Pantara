# Adaptive Engine

## Tujuan

Memberi rekomendasi assignment yang dapat dijelaskan, bukan menggantikan keputusan team lead.

## Input task

`requiredSkills`, `complexity`, `estimatedEffort`, `deadline`, `accessRequirements`.

## Tiga dimensi

### Capability — Can do?

Evidence: skill relevan, pengalaman, task serupa, hasil task sebelumnya. Output: Strong / Partial / Limited.

### Capacity — Can take?

Evidence: active workload berbobot complexity dan effort, deadline terdekat, availability, capacity signal terbaru. Output: Available / Balanced / Near capacity / Over capacity.

### Access — Can access?

Evidence: kebutuhan task, preferensi kerja, workplace support. Output: Ready / Needs support / Unresolved.

## MVP decision policy

Gunakan aturan transparan, bukan LLM sebagai penentu utama:

Capability dan capacity masih menyimpan skor internal untuk kompatibilitas, tetapi policy V1.2 tidak menjumlahkannya. Akses yang belum ready memerlukan klarifikasi dan tidak direkomendasikan final. Kandidat viable dibandingkan berdasarkan kapasitas berkelanjutan, lalu kemampuan.

## Output

- Recommended candidate.
- Alternatives.
- Evidence per dimensi.
- Workload impact before/after.
- Missing or uncertain data.
- Actions: Assign, Choose another, Resolve access, Assign manually.

## Feedback loop

Simpan estimated vs actual effort, blocker context, capacity signal, dan outcome task. Gunakan sebagai evidence kontekstual; jangan mengubahnya menjadi ranking pribadi.

## Implementasi backend saat ini

- Capability: menerima string lama dan format V1 `{skill, priority, min_level}`. Alias seperti `React.js` dinormalisasi ke `react`; proficiency memakai `BEGINNER` sampai `EXPERT`. Mandatory requirement yang gagal menjadi gate. Riwayat tugas menjadi evidence relevan tanpa penalti actual effort.
- Capacity: menyimpan `system_fit`, `signal_level`, dan `weighted_workload_units` secara terpisah. Sinyal employee dapat menaikkan status review tanpa mengubah observasi sistem. Load memakai sisa effort, kompleksitas, dan deadline; angka tetap heuristik demo yang perlu kalibrasi.
- Access: `Task.access_requirements` adalah kondisi task, `WorkProfile.access_needs` kebutuhan employee, dan `Workspace.access_support` dukungan tersedia. `access_preferences` lama tetap dibaca untuk kompatibilitas.
- Recommendation: kandidat dengan skill dan access viable dibandingkan berdasarkan capacity, lalu capability dan riwayat. Over-capacity memerlukan review. Tanpa kandidat viable, API tidak memberikan `recommended_member_id`.
- Analisis ulang: perubahan task, assignment, blocker, completion evidence, profil, kapasitas, atau dukungan workspace memperbarui snapshot analisis untuk task terbuka. `recommendation.trigger` dan `changed_from_previous` menunjukkan perubahan; perpindahan assignment tetap keputusan manusia.

## Capability evidence layer

- `Skill` menyimpan nama kanonis dan alias. Migrasi mengimpor skill dari data lama. Skill baru harus ditambahkan ke katalog oleh admin; API task/profile mengembalikan `UNRESOLVED_SKILL` untuk nama yang belum ada.
- `EmployeeSkill` menyimpan proficiency yang dinyatakan employee secara terpisah dari hasil observasi dan confidence. `TaskSkillRequirement` menyimpan prioritas dan minimum proficiency per skill. Edit lewat API baru juga memperbarui field JSON lama.
- Saat task selesai, requirement pada assignment terbaru menjadi usulan `SkillEvidence`. Hanya user yang tertaut melalui `Member.user` dapat mengedit usage/context melalui `PATCH /api/skill-evidence/{id}/review/`, lalu menyetujui melalui `POST /api/skill-evidence/{id}/confirm/`. Bukti yang belum dikonfirmasi tidak mengubah observed proficiency.
- Evaluator deterministik memakai seluruh bukti terkonfirmasi. Dua penggunaan utama pada task kompleks menghasilkan `ADVANCED`; tiga penggunaan utama dengan minimal dua konteks menghasilkan confidence `HIGH`. Bukti lama tetap ada; usia lebih dari 365 hari menurunkan confidence. Bukti completion tidak menaikkan proficiency secara otomatis satu tingkat per task. Declared proficiency tidak ditimpa.
- Capability menghasilkan `status`, `confidence`, `skill_match`, `relevant_experience_result`, dan `task_familiarity` dengan ID task sumber. Task familiarity membandingkan skill, category, dan tags dari task selesai; tanpa riwayat hasilnya `UNKNOWN`.

Admin mengelola katalog di `/api/skills/` atau Django admin. Employee mengelola deklarasi skill di `/api/employee-skills/`. Admin mengelola requirement di `/api/task-skill-requirements/`. Jalankan `python manage.py migrate` setelah update.

`progress` adalah persentase 0–100 pada Task. `access_support` adalah daftar dukungan tersedia pada Workspace. Riwayat analisis dapat dibaca di `/api/adaptive-analyses/`.

## AI boundary

## V1.2 robustness dan recommendation policy

Policy final bersifat hierarkis: capability viability, access readiness, projected capacity, lalu kualitas evidence. Mandatory requirement yang gagal menjadi `NOT_VIABLE`; access belum siap, proficiency yang perlu klarifikasi, atau projected over-capacity menjadi `REVIEW_REQUIRED`. Kandidat yang aman menjadi `RECOMMENDED` atau `ALTERNATIVE`. Total score tidak dipakai untuk keputusan.

`candidates[].recommendation_result` berisi kategori, capability status/level/confidence, capacity current/projected, access status, reason codes, dan considerations. Tanpa kandidat aman, tidak ada `recommended_member_id`. Analisis ulang memberi reason codes `CONDITION_CHANGED`, `REANALYSIS_TRIGGERED`, dan jika perlu `REDISTRIBUTION_REVIEW`; perpindahan assignment tetap keputusan manusia.

Seluruh `SkillEvidence` terkonfirmasi tetap dihitung untuk observed proficiency. Bila bukti terakhir lebih tua dari 365 hari, confidence turun, bukan proficiency yang terhapus. Hanya user yang ditautkan lewat `Member.user` ke pemilik evidence dapat review/confirm. Setelah migrasi, admin perlu menautkan akun lama ke member yang benar; email tidak dipakai untuk otorisasi maupun migrasi otomatis. Jalankan `python manage.py migrate` setelah update.

Suite V1.2 mencakup 16 persona adversarial, monotonicity confidence, isolasi capability dari access/capacity, riwayat tak relevan, recency, re-analysis, dan penyalahgunaan identitas evidence. Threshold masih heuristik demo, bukan kalibrasi data nyata.

### Hasil 16 persona sintetis

Semua input lain memakai baseline: capability eligible/strong/high, access ready, projected capacity balanced. `Actual` berasal dari `RecommendationPolicyScenarios` dan diverifikasi dengan `manage.py test`.

| Scenario | Input pembeda | Expected invariant | Actual | Reason code utama | Hasil |
| --- | --- | --- | --- | --- | --- |
| Cold-start expert | Confidence low | Deklarasi saja tidak menjadi evidence kuat | ALTERNATIVE | LIMITED_HISTORICAL_EVIDENCE | PASS |
| Declared/observed disagreement | Capability review | Konflik tidak final | REVIEW_REQUIRED | MIXED_PROFICIENCY_EVIDENCE | PASS |
| Banyak evidence minor | Capability limited | Banyak bukti minor tidak otomatis sangat kuat | ALTERNATIVE | MANDATORY_REQUIREMENTS_MET | PASS |
| Sedikit primary | Confidence low | Bukti terbatas terlihat | ALTERNATIVE | LIMITED_HISTORICAL_EVIDENCE | PASS |
| Konteks identik | Confidence medium | Tidak mengklaim confidence high | ALTERNATIVE | SUSTAINABLE_PROJECTED_CAPACITY | PASS |
| Evidence kuat usang | Stale observed | Tidak final tanpa review | REVIEW_REQUIRED | STALE_OBSERVED_EVIDENCE | PASS |
| Mandatory missing | React mandatory hilang | Tidak viable meski level sangat kuat | NOT_VIABLE | MANDATORY_REQUIREMENT_MISSING | PASS |
| Required fit gagal | Requirement not met | Tidak viable | NOT_VIABLE | CAPABILITY_REQUIREMENT_NOT_MET | PASS |
| Preferred missing | Mandatory terpenuhi | Preferred tidak menjadi gate | ALTERNATIVE | MANDATORY_REQUIREMENTS_MET | PASS |
| Overqualified | Very strong | Skill tinggi saja bukan otomatis recommended | ALTERNATIVE | ACCESS_READY | PASS |
| Strong over-capacity | Projected over | Tidak dipilih otomatis | REVIEW_REQUIRED | PROJECTED_OVER_CAPACITY | PASS |
| Moderate available | Projected available | Tetap kandidat aman | ALTERNATIVE | SUSTAINABLE_PROJECTED_CAPACITY | PASS |
| Access unresolved | Unresolved | Tidak final | REVIEW_REQUIRED | ACCESS_UNRESOLVED | PASS |
| Access resolvable | Needs support | Dukungan perlu dituntaskan | REVIEW_REQUIRED | ACCESS_SUPPORT_REQUIRED | PASS |
| Employee over signal | Signal over | Sinyal employee dihormati | REVIEW_REQUIRED | EMPLOYEE_CAPACITY_SIGNAL | PASS |
| Near capacity | Projected near | Dipertimbangkan dengan peringatan | ALTERNATIVE | PROJECTED_NEAR_CAPACITY | PASS |

AI boleh membantu merangkum evidence dan menjelaskan rekomendasi. Perhitungan workload, deadline, eligibility, dan access matching harus deterministik. AI tidak boleh mendiagnosis mental health, menyimpulkan kondisi pribadi, atau membuat keputusan assignment final.
