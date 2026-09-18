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

Capability dan capacity masing-masing punya skor 0–2 sebagai evidence internal. Akses adalah syarat kelayakan: jika belum ready, kandidat memerlukan klarifikasi dan tidak direkomendasikan final. Kandidat viable dibandingkan berdasarkan kapasitas berkelanjutan, lalu kemampuan. Skor tidak menjadi ranking performa karyawan.

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
- Saat task selesai, requirement pada assignment terbaru menjadi usulan `SkillEvidence`. Employee yang login dengan email yang sama dapat mengedit usage/context melalui `PATCH /api/skill-evidence/{id}/review/`, lalu menyetujui melalui `POST /api/skill-evidence/{id}/confirm/`. Bukti yang belum dikonfirmasi tidak mengubah observed proficiency.
- Evaluator deterministik memakai bukti terkonfirmasi dari 365 hari terakhir. Dua penggunaan utama pada task kompleks menghasilkan `ADVANCED`; tiga penggunaan utama dengan minimal dua konteks menghasilkan confidence `HIGH`. Bukti completion tidak menaikkan proficiency secara otomatis satu tingkat per task. Declared proficiency tidak ditimpa.
- Capability menghasilkan `status`, `confidence`, `skill_match`, `relevant_experience_result`, dan `task_familiarity` dengan ID task sumber. Task familiarity membandingkan skill, category, dan tags dari task selesai; tanpa riwayat hasilnya `UNKNOWN`.

Admin mengelola katalog di `/api/skills/` atau Django admin. Employee mengelola deklarasi skill di `/api/employee-skills/`. Admin mengelola requirement di `/api/task-skill-requirements/`. Jalankan `python manage.py migrate` setelah update.

`progress` adalah persentase 0–100 pada Task. `access_support` adalah daftar dukungan tersedia pada Workspace. Riwayat analisis dapat dibaca di `/api/adaptive-analyses/`.

## AI boundary

AI boleh membantu merangkum evidence dan menjelaskan rekomendasi. Perhitungan workload, deadline, eligibility, dan access matching harus deterministik. AI tidak boleh mendiagnosis mental health, menyimpulkan kondisi pribadi, atau membuat keputusan assignment final.
