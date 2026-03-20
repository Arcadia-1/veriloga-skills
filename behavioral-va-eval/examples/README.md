# behavioral-va-eval Example Library

This directory is the primary example library for the `behavioral-va-eval`
benchmark dataset.

Use it for:

- runnable voltage-domain verification examples
- reference `.scs` testbenches
- reference `.va` DUT/helper models
- analysis and validation scripts

The `evas-sim` PyPI package may still bundle a small smoke-test demo set for
`evas list` and installation checks, but the benchmark-owned example library
belongs here.

## Classification

Examples are grouped by verification intent first, not by PyPI packaging:

- `data-converter/` - ADC, DAC, mixed ADC/DAC flows
- `comparator/` - comparator-focused verification
- `digital-logic/` - event-driven logic/state-machine examples
- `calibration/` - calibration and dynamic element matching flows
- `stimulus/` - reusable source/stimulus examples
- `measurement/` - measurement/extraction flows

## Layout

Each example directory may contain:

- one or more DUT/helper `.va` files
- one or more `tb_*.scs` netlists
- `analyze_*.py` scripts
- `validate_*.py` scripts

See `manifest.json` for the canonical index.
