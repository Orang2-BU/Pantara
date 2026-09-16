# Testing & Validation

## Acceptance scenarios

### T1 — Strong skill, low capacity

Sarah sangat cocok tetapi Near capacity; Andi cukup cocok dan Available. Expected: Andi direkomendasikan dengan alasan capacity difference.

### T2 — Access support available

Task membutuhkan caption; employee membutuhkan caption; workspace memiliki support. Expected: Access Ready.

### T3 — Access unresolved

Task membutuhkan lokasi accessible; kondisi lokasi belum diketahui. Expected: Unresolved access barrier, bukan incapable.

### T4 — Assignment causes overload

Simulasi assignment menaikkan workload melewati batas. Expected: warning, alternative, human confirmation.

### T5 — Feedback changes recommendation

Employee memilih Over capacity atau melaporkan blocker. Expected: dashboard menandai workload change dan menawarkan review redistribution.

## Validation questions

- Apakah user memahami alasan rekomendasi dalam 10 detik?
- Apakah employee merasa capacity signal adalah kontrol kerja, bukan penilaian kesehatan?
- Apakah lead tetap tahu bahwa keputusan akhir berada padanya?
- Apakah barrier akses diarahkan ke dukungan, bukan disalahkan ke employee?
