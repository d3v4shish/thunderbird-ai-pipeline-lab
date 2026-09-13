# Live Context and Output Parameter Evaluation

Model: `qwen3:8b`. Bounded map-page facts: 32 of a 50-message thread.

| Factor | Value | Fact recall | Valid | Prompt tokens | Output tokens | Wall ms |
|---|---|---|---|---|---|---|
| baseline | current-candidate | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [22183.999689999837, 22817.469890998836, 22693.45487099963] |
| context_window | 4096 | [0.0, 0.0, 0.0] | [False, False, False] | [0, 0, 0] | [0, 0, 0] | [5156.624782999643, 5093.03847099909, 5084.911250000005] |
| context_window | 8192 | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [22832.083203000366, 23013.4123250009, 22807.629491000625] |
| context_window | 32768 | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [22865.64137700043, 23006.24766799956, 22846.25960000085] |
| max_output_tokens | 256 | [0.0, 0.0, 0.0] | [False, False, False] | [0, 0, 0] | [0, 0, 0] | [5747.037143999478, 5731.2918700008595, 5842.824276000101] |
| max_output_tokens | 512 | [0.0, 0.0, 0.0] | [False, False, False] | [0, 0, 0] | [0, 0, 0] | [5235.870637001426, 5178.580587000397, 5173.084820999065] |
| max_output_tokens | 1024 | [0.0, 0.0, 0.0] | [False, False, False] | [0, 0, 0] | [0, 0, 0] | [10481.638788000055, 10374.742003999927, 10329.529508999258] |
| max_output_tokens | 2048 | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [20010.242434998872, 19795.456702999218, 19717.09922199807] |
| evidence_budget | 4096 | [0.40625, 0.40625, 0.40625] | [True, True, True] | [2012, 2012, 2012] | [811, 811, 811] | [8026.3139639992005, 8091.520795000179, 8008.193369001674] |
| evidence_budget | 8192 | [0.84375, 0.84375, 0.84375] | [True, True, True] | [3799, 3799, 3799] | [1637, 1637, 1637] | [17000.658418999592, 17234.36000899892, 17176.617261997308] |
| evidence_budget | 16384 | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [20198.686046998773, 20011.17048299966, 19975.710706999962] |
| temperature | 0.2 | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [19970.272130000012, 19785.785017998933, 19967.880517000594] |
| combined_context_output | 6144/2048 | [0.0, 0.0, 0.0] | [False, False, False] | [0, 0, 0] | [0, 0, 0] | [22872.89435999992, 23170.823688999008, 23073.503798001184] |
| combined_context_output | 7168/2048 | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [23038.583931000176, 22876.52389899995, 22987.38787700131] |
| combined_context_output | 8192/2048 | [1.0, 1.0, 1.0] | [True, True, True] | [4410, 4410, 4410] | [1932, 1932, 1932] | [22870.960427999307, 22755.533130000913, 23113.505916000577] |

## Recommendations

- `context_window`: `{"source_lane": {"factor": "context_window", "value": 8192}, "status": "keep-or-change", "value": 8192}`
- `max_output_tokens`: `{"source_lane": {"factor": "max_output_tokens", "value": 2048}, "status": "keep-or-change", "value": 2048}`
- `evidence_budget`: `{"source_lane": {"factor": "baseline", "value": "current-candidate"}, "status": "keep-or-change", "value": 0}`
- `temperature`: `{"source_lane": {"factor": "baseline", "value": "current-candidate"}, "status": "keep-or-change", "value": 0.0}`
- `combined_context_output`: `{"context_window": 7168, "max_output_tokens": 2048, "status": "keep-or-change"}`

Use one-factor lanes to identify safe reductions, then select the smallest three-repeat combined context/output finalist that returns all 32 map-page facts with valid structure. Full-thread completeness is evaluated by the paged hierarchical lane, never by expanding this prompt.
