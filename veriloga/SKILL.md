---
name: veriloga
description: >
  Verilog-A language authoring guidance for writing, reviewing, or explaining .va behavioral
  modules. Use for Verilog-A syntax and semantics: modules and ports, disciplines and natures,
  analog blocks, branch access, contributions, events, parameters, arrays, control flow,
  operators, and smooth behavioral output idioms. This skill is self-contained and gives
  language guidance only, without simulator workflows or project-specific repair policy.
---

# Verilog-A Language Authoring

Use this skill to write language-correct Verilog-A modules. Keep guidance tied to the
Verilog-A source file: declarations, continuous analog behavior, events, state, expressions,
and well-formed contribution statements.

## Authoring Workflow

1. State the module interface first: ports, directions, disciplines, and parameters.
2. Put shared constants, internal variables, branches, and functions before `analog begin`.
3. Initialize persistent state in `@(initial_step)` when the requested model genuinely needs
   memory; do not introduce state for syntax-only examples.
4. Use contribution statements (`<+`) to define analog behavior continuously.
5. Use event statements only for discrete language events such as threshold crossings, timed
   actions, messages, or state updates required by the requested behavior.
6. Smooth piecewise-constant output changes with `transition()`, `slew()`, or equivalent continuous
   expressions when abrupt jumps are not required by the language-level intent.
7. Finish with a syntax audit: matching `begin`/`end`, declared variables, valid branch access,
   compatible array indices, and no procedural assignment where a contribution is required.

## Load References As Needed

- `references/modules-ports-disciplines.md`: module headers, port declarations, disciplines,
  natures, branches, and include conventions.
- `references/analog-contributions.md`: `analog` blocks, branch access, contribution forms,
  continuous equations, smoothing, and expression discipline.
- `references/events-state-control.md`: `@(initial_step)`, `cross`, `timer`, event sequencing,
  persistent state, loops, arrays, and functions.
- `references/operators-system-tasks.md`: analog operators, math functions, noise functions,
  file/system tasks, and language-level portability cautions.
- `assets/template.va`: minimal neutral starting point for a new module.
- `assets/examples/`: small examples named by language construct, not by circuit function.

## Core Language Rules

- Include standard definitions when using built-in electrical disciplines:

```verilog
`include "constants.vams"
`include "disciplines.vams"
```

- Declare every port's direction and discipline. Prefer one ANSI port per line for clarity.
- Use `input`, `output`, or `inout` for module boundary intent; use the discipline declaration
  to define analog access.
- Read branch quantities with access functions such as `V(node)`, `V(p,n)`, `I(p,n)`.
- Drive analog quantities with contributions such as `V(out) <+ expr;` or `I(p,n) <+ expr;`.
- Use procedural assignments (`=`) for real/integer state, not for node voltages or
  branch currents.
- Keep event blocks short. For syntax probes, log or inspect the event without creating latch,
  toggle, counter, or sampled-output behavior.
- Prefer parameters for tunable quantities and local variables for derived values.
- Declare integer loop indices for procedural loops; use `genvar` only for elaboration-style
  repeated analog statements.
- Avoid relying on implicit declarations or undeclared net creation.

## Output Expectations

When producing a `.va` file, return complete source code unless the user asks for a patch.
After the code, briefly list the ports and parameters that matter for use of the module.
