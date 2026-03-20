# Runner design

This directory is reserved for the benchmark harness implementation.

Planned runner split:

- `migrate_veriloga_evals.py`
  Converts the legacy `veriloga/evals/evals.json` list into structured
  `behavioral-va-eval/tasks/...` case directories
- `generate.py`
  Calls the model/agent and materializes DUT/testbench outputs
- `simulate_evas.py`
  Runs voltage-domain `.scs` cases under EVAS and collects DUT/testbench/sim outcomes
- `run_examples_suite.py`
  Executes the 14 self-contained benchmark examples from `examples/manifest.json`
  with their default testbenches and emits a smoke-suite report
- `simulate_openvaf.py`
  Out of scope for this benchmark
- `score.py`
  Computes per-layer scores and aggregate reports from executable evidence

Recommended workflow:

1. load task case directory
2. generate candidate output
3. invoke EVAS on the DUT/testbench pair
4. run behavior checks
5. score from compiled/simulated artifacts
7. emit `result.schema.json`-compatible output

Do not introduce precheck-only scorers as benchmark outputs. Syntax/rule checks
may exist internally inside executable runners, but benchmark results should be
driven by DUT compile, testbench compile, and behavioral evidence.

Current implemented executable runner:

- `simulate_evas.py`
  Inputs: `task_dir`, `dut.va`, `tb_*.scs`
  Outputs:
  - `dut_compile`
  - `tb_compile`
  - `sim_correct`
- `run_examples_suite.py`
  Inputs: benchmark `examples/manifest.json`
  Outputs:
  - per-example EVAS smoke result for the 14 default examples
