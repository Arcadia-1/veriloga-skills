# behavioral-va-eval

Benchmark design package for evaluating the pure voltage-domain portion of the
`veriloga` skill stack on EVAS-compatible modules.

This benchmark is modeled after the strengths of VerilogEval v2:

- task cases stored as plain files/directories
- generation separated from execution/scoring
- deterministic `Pass@1` as the primary metric
- executable evidence instead of text-only rubric matching

## Scope

This benchmark is intentionally **EVAS-only**.

It only covers **pure voltage-domain Verilog-A modules** that can be verified by
EVAS. Current-domain and mixed-domain modules are out of scope for this
benchmark.

It is split into four task families:

1. `spec-to-va`
   Natural-language specification -> DUT `.va`
2. `bugfix`
   Broken voltage-domain `.va` -> corrected DUT `.va`
3. `tb-generation`
   DUT + behavior intent -> minimal valid `.scs`
4. `end-to-end`
   Spec -> DUT -> testbench -> simulation -> minimum behavioral check

## Primary evaluation axes

Every meaningful case should be judged on these three executable questions:

1. `dut_compile_pass`
   Can EVAS accept the generated DUT `.va`?
2. `tb_compile_pass`
   Can EVAS accept the generated `.scs` testbench?
3. `sim_correct_pass`
   Does the simulated behavior satisfy the minimum case checks?

These are the real benchmark signals. Text-only prechecks are not benchmark
results.

## Primary metrics

- `Pass@1-deterministic`
  Temperature 0 / single sample
- Optional per-axis rates:
  - DUT compile rate
  - testbench compile rate
  - simulation correctness rate

Primary reporting should remain deterministic `Pass@1`.

## Failure labels

Use explicit failure attribution instead of a single generic failure bucket:

- `FAIL_DUT_COMPILE`
- `FAIL_TB_COMPILE`
- `FAIL_SIM_CORRECTNESS`
- `FAIL_INFRA`

## Layout

```text
behavioral-va-eval/
  README.md
  schemas/
    task.schema.json
    result.schema.json
  tasks/
    spec-to-va/
    bugfix/
    tb-generation/
    end-to-end/
  examples/
    manifest.json
  runners/
    README.md
```

Each benchmark case is a directory containing:

- `prompt.md`
- `meta.json`
- `checks.yaml`
- optional `gold/`

The self-contained executable assets used by the first benchmark wave live under
`examples/`. The default 14-group smoke suite is driven from
`examples/manifest.json`.

## Initial benchmark strategy

Start small and stable:

- 8 to 12 `spec-to-va` cases
- 4 to 6 `bugfix` cases
- 4 to 6 `tb-generation` cases
- 4 to 6 `end-to-end` cases

The first end-to-end set should prefer stable voltage-domain modules such as:

- `clk_div`
- `comparator`
- `ramp_gen`
- `d2b_4b`
- `dac_binary_clk_4b`
- `lfsr`

## Relationship to existing evals

Existing files:

- `veriloga/evals/evals.json`
- `evas-sim/evals/evals.json`
- `openvaf/evals/evals.json`

should be treated as seed prompts and expectations, not as the final benchmark
format. `behavioral-va-eval/` is the structured benchmark layer intended to sit
above those skill-local eval lists.
