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

## MVP scoring

Gunakan aturan transparan, bukan LLM sebagai penentu utama:

```text
candidate score = capability fit + capacity fit + access readiness
```

Capability fit: 0–2, capacity fit: 0–2, access readiness: 0–2. Jika access unresolved, kandidat ditandai perlu klarifikasi dan tidak diberi rekomendasi final. Jika capacity over, kurangi prioritas secara signifikan. Tampilkan komponen score dan evidence, bukan hanya total.

## Output

- Recommended candidate.
- Alternatives.
- Evidence per dimensi.
- Workload impact before/after.
- Missing or uncertain data.
- Actions: Assign, Choose another, Resolve access, Assign manually.

## Feedback loop

Simpan estimated vs actual effort, blocker context, capacity signal, dan outcome task. Gunakan sebagai evidence kontekstual; jangan mengubahnya menjadi ranking pribadi.

## AI boundary

AI boleh membantu merangkum evidence dan menjelaskan rekomendasi. Perhitungan workload, deadline, eligibility, dan access matching harus deterministik. AI tidak boleh mendiagnosis mental health, menyimpulkan kondisi pribadi, atau membuat keputusan assignment final.
