# Project Brief

## Identitas

- Codename: Pantara-MindCraft
- Nama final: belum ditentukan
- Kategori: adaptive human-centered workload workspace
- One-liner: Workspace kolaboratif yang membantu tim mendistribusikan pekerjaan berdasarkan kemampuan, kapasitas, kebutuhan akses, dan bukti pekerjaan sebelumnya.

## Masalah

Tools project management biasanya mengutamakan status task, bukan kapasitas orang yang mengerjakannya. Akibatnya high performer dapat terus menerima pekerjaan, task kompleks dihitung sama seperti task ringan, dan overload baru terlihat setelah terlambat.

Distribusi workload yang tidak seimbang dapat berkontribusi pada tekanan kerja dan risiko terhadap well-being. Produk ini menangani faktor kerja tersebut; produk bukan layanan diagnosis mental health dan tidak memprediksi resign.

## Prinsip produk

> Can do ≠ Can take ≠ Can access.

Assignment yang baik mempertimbangkan:

- **Capability** — apakah orang ini mampu mengerjakan task?
- **Capacity** — apakah ia punya ruang kerja yang cukup sekarang?
- **Access** — apakah kondisi dan dukungan kerja memungkinkan task dikerjakan?

## Core loop

`Create task → Analyze team → Recommend → Human assigns → Employee works → Signal/feedback → Adapt/redistribute → Learn`

## Peran

- Team lead: membuat task, melihat analisis, mengambil keputusan, redistribusi.
- Employee: melihat pekerjaan, memberi capacity signal, melaporkan blocker, memberi konteks hasil.
- Admin: mengelola workspace, team, role, dan dukungan kerja.

## MVP

- Workspace, team, project, task.
- Work profile: skills, pengalaman relevan, preferensi akses.
- Capacity signal: Available, Balanced, Near capacity, Over capacity.
- Analisis capability/capacity/access.
- Rekomendasi dengan alasan yang dapat dibaca.
- Human-in-the-loop assignment.
- Task progress, blocker, completion feedback.
- Workload view dan redistribusi manual yang dibantu rekomendasi.

## Di luar MVP

- Diagnosis burnout atau kondisi psikologis.
- Prediksi siapa yang akan resign.
- Employee ranking atau performance score tunggal.
- Automatic assignment tanpa persetujuan manusia.
- Pengawasan aktivitas pribadi atau isi komunikasi.

## Guardrails

- Gunakan sinyal kerja yang relevan, bukan data kesehatan sensitif.
- Employee dapat mengubah capacity signal dan melihat penggunaannya.
- Rekomendasi selalu menjelaskan faktor utama dan ketidakpastian.
- Barrier akses tidak boleh diterjemahkan sebagai ketidakmampuan.
- Human decides; system assists.

## Definition of done produk

Seorang team lead dapat membuat task, melihat minimal dua kandidat dengan alasan berbeda, memilih assignment, lalu melihat perubahan workload dan menerima feedback employee dalam satu demo end-to-end.
