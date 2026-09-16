# Product Requirements

## Prioritas

### P0 — wajib demo

| ID | Requirement | Acceptance |
|---|---|---|
| FR-01 | Workspace/team/project/task | Data dapat dibuat dan ditampilkan |
| FR-02 | Work profile | Skill dan pengalaman relevan tersimpan |
| FR-03 | Capacity signal | Employee dapat memilih status kapasitas |
| FR-04 | Task analysis | Sistem menghitung capability, capacity, access |
| FR-05 | Recommendation | Minimal dua kandidat dan alasan ditampilkan |
| FR-06 | Human assignment | Lead memilih dan mengonfirmasi assignment |
| FR-07 | Workload view | Beban sebelum/sesudah assignment terlihat |
| FR-08 | Feedback/blocker | Employee dapat memberi sinyal dan konteks |

### P1 — jika waktu cukup

- Workload trend beberapa project cycle.
- Simulation beberapa alternatif assignment.
- Suggested redistribution saat workload berubah.
- Completion evidence untuk task berikutnya.

## Acceptance utama

Untuk task dengan skill cocok tetapi kapasitas kandidat tinggi, sistem boleh memilih kandidat lain yang cukup capable dan lebih tersedia. Output wajib menyebutkan alasan, tidak boleh memakai skor performa tunggal, dan tidak boleh melakukan assignment otomatis.

## Non-functional

- Keyboard-accessible, focus terlihat, kontras cukup, label jelas.
- Data demo fiktif; jangan gunakan informasi kesehatan nyata.
- Error dan empty state harus memiliki instruksi pemulihan.
- Rekomendasi deterministik dapat diuji ulang dengan input sama.
