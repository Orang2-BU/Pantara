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

- Capability: minimal 50% required skills untuk kandidat viable; tugas selesai dengan skill yang sama menjadi evidence relevan, tanpa penalti dari actual effort.
- Capacity: sisa `estimated_effort × (1 - progress/100) × complexity × deadline pressure` untuk task aktif. Modifier complexity: 0.8/1.0/1.3; deadline ≤7 hari: 1.2, <3 hari: 1.5. Batas weighted hours 15/30/40 dan self-report dipakai sebagai evidence; sinyal over-capacity sendiri tidak otomatis menghasilkan skor nol, tetapi menandai perlunya review. Semua angka adalah heuristik demo yang perlu kalibrasi.
- Access: kebutuhan task dicocokkan dengan preferensi member dan `workspace.access_support`. Kebutuhan yang belum terpenuhi memerlukan review; capability tetap dihitung terpisah.
- Recommendation: kandidat dengan skill dan access viable dibandingkan berdasarkan capacity, lalu capability dan riwayat. Over-capacity memerlukan review. Tanpa kandidat viable, API tidak memberikan `recommended_member_id`.
- Analisis ulang: perubahan task, assignment, blocker, completion evidence, profil, kapasitas, atau dukungan workspace memperbarui snapshot analisis untuk task terbuka. `recommendation.trigger` dan `changed_from_previous` menunjukkan perubahan; perpindahan assignment tetap keputusan manusia.

`progress` adalah persentase 0–100 pada Task. `access_support` adalah daftar dukungan tersedia pada Workspace. Riwayat analisis dapat dibaca di `/api/adaptive-analyses/`.

## AI boundary

AI boleh membantu merangkum evidence dan menjelaskan rekomendasi. Perhitungan workload, deadline, eligibility, dan access matching harus deterministik. AI tidak boleh mendiagnosis mental health, menyimpulkan kondisi pribadi, atau membuat keputusan assignment final.
