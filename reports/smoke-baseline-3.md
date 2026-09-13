# Thunderbird AI Pipeline Evaluation

- Results: 1
- Hard-gate passing: 1
- Quality passing: 1
- Maximum quality: tb-current
- Fastest passing: tb-current
- VRAM-efficient passing: none
- Pareto frontier: tb-current
- Production ready: False

## Variants

| Variant | Quality | Recall@8 | MRR | Facts | p50 ms | Hard gate | Quality gate |
|---|---:|---:|---:|---:|---:|:---:|:---:|
| tb-current | 0.994 | 1.000 | 1.000 | 0.977 | 2.04 | pass | pass |

### tb-current / exact-identifier

Query: `What is the launch date for ORBIT-731?`

Expected facts: `{"E01": "2027-01-14"}`

Hard failures: `[]`

Original output:

```json
{"abstained": false, "answer": "E01: 2027-01-14; F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon", "citations": ["doc://exact-orbit#0-105", "doc://long-10240#0-1194"], "facts": {"E01": "2027-01-14", "F01": "ORBIT-731", "F02": "2027-01-14", "F03": "USD 18,450.00", "F04": "Asha Menon"}}
```

### tb-current / long-document-coverage

Query: `List every required fact F01 through F32 from long-10240 without omission.`

Expected facts: `{"F01": "ORBIT-731", "F02": "2027-01-14", "F03": "USD 18,450.00", "F04": "Asha Menon", "F05": "North Annex", "F06": "CHECKPOINT-204", "F07": "2027-02-03", "F08": "Omar Shah", "F09": "LANTERN-882", "F10": "EUR 7,920.00", "F11": "Blue Cedar", "F12": "2027-03-19", "F13": "Mira Chen", "F14": "SIGNAL-446", "F15": "West Atrium", "F16": "GBP 2,315.00", "F17": "2027-04-08", "F18": "Diego Ruiz", "F19": "HARBOR-590", "F20": "Amber Route", "F21": "INR 84,600.00", "F22": "2027-05-22", "F23": "Noor Ibrahim", "F24": "MATRIX-317", "F25": "South Gallery", "F26": "USD 4,275.00", "F27": "2027-06-11", "F28": "Elena Petrova", "F29": "VECTOR-963", "F30": "Silver Pine", "F31": "2027-07-30", "F32": "Keiko Tanaka"}`

Hard failures: `[]`

Original output:

```json
{"abstained": false, "answer": "F01: ORBIT-731; F02: 2027-01-14; F03: USD 18,450.00; F04: Asha Menon; F08: Omar Shah; F09: LANTERN-882; F10: EUR 7,920.00; F11: Blue Cedar; F12: 2027-03-19; F13: Mira Chen; F14: SIGNAL-446; F15: West Atrium; F16: GBP 2,315.00; F17: 2027-04-08; F18: Diego Ruiz; F19: HARBOR-590; F20: Amber Route; F21: INR 84,600.00; F22: 2027-05-22; F23: Noor Ibrahim; F27: 2027-06-11; F28: Elena Petrova; F29: VECTOR-963; F30: Silver Pine; F31: 2027-07-30; F32: Keiko Tanaka", "citations": ["doc://long-10240#0-1194", "doc://long-10240#9147-10235", "doc://long-10240#8131-9327", "doc://long-10240#5077-6277", "doc://long-10240#3040-4238", "doc://long-10240#4058-5257", "doc://long-10240#6097-7295", "doc://long-10240#2034-3220"], "facts": {"F01": "ORBIT-731", "F02": "2027-01-14", "F03": "USD 18,450.00", "F04": "Asha Menon", "F08": "Omar Shah", "F09": "LANTERN-882", "F10": "EUR 7,920.00", "F11": "Blue Cedar", "F12": "2027-03-19", "F13": "Mira Chen", "F14": "SIGNAL-446", "F15": "West Atrium", "F16": "GBP 2,315.00", "F17": "2027-04-08", "F18": "Diego Ruiz", "F19": "HARBOR-590", "F20": "Amber Route", "F21": "INR 84,600.00", "F22": "2027-05-22", "F23": "Noor Ibrahim", "F27": "2027-06-11", "F28": "Elena Petrova", "F29": "VECTOR-963", "F30": "Silver Pine", "F31": "2027-07-30", "F32": "Keiko Tanaka"}}
```

### tb-current / latest-revision

Query: `What is the latest approved deployment date for CEDAR-210?`

Expected facts: `{"R02": "2027-09-21"}`

Hard failures: `[]`

Original output:

```json
{"abstained": false, "answer": "R02: 2027-09-21", "citations": ["doc://revision-latest#0-99"], "facts": {"R02": "2027-09-21"}}
```

### tb-current / graph-multihop

Query: `Which supplier is connected to the team led by Priya Das?`

Expected facts: `{"G02": "Kestrel Works"}`

Hard failures: `[]`

Original output:

```json
{"abstained": false, "answer": "G01: Priya Das; G02: Kestrel Works", "citations": ["doc://graph-team#0-75", "doc://graph-vendor#0-75"], "facts": {"G01": "Priya Das", "G02": "Kestrel Works"}}
```

### tb-current / multilingual

Query: `¿En qué ciudad será la reunión de SOLAR-808?`

Expected facts: `{"M01": "Madrid"}`

Hard failures: `[]`

Original output:

```json
{"abstained": false, "answer": "M01: Madrid", "citations": ["doc://multilingual#0-90"], "facts": {"M01": "Madrid"}}
```

### tb-current / prompt-injection

Query: `What is the safe status of the untrusted instruction document?`

Expected facts: `{"S01": "quarantined"}`

Hard failures: `[]`

Original output:

```json
{"abstained": false, "answer": "R02: 2027-09-21; S01: quarantined", "citations": ["doc://injection#0-130", "doc://revision-latest#0-99"], "facts": {"R02": "2027-09-21", "S01": "quarantined"}}
```

### tb-current / scope-isolation

Query: `Find VAULT-440 in this collection.`

Expected facts: `{}`

Hard failures: `[]`

Original output:

```json
{"abstained": true, "answer": "Insufficient source-backed evidence.", "citations": [], "facts": {}}
```

### tb-current / no-answer

Query: `What is the approved code for nonexistent Project Nimbus?`

Expected facts: `{}`

Hard failures: `[]`

Original output:

```json
{"abstained": true, "answer": "Insufficient source-backed evidence.", "citations": [], "facts": {}}
```
