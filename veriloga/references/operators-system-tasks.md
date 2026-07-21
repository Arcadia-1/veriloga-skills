# Operators And System Tasks

## Common Math

Use built-in math functions in expressions:

```verilog
real y;
y = sin(phase) + exp(-t / tau);
```

Common functions include `abs`, `sqrt`, `pow`, `ln`, `log`, `exp`, `sin`, `cos`, `tan`,
`asin`, `acos`, `atan`, `min`, and `max`.

## Analog Operators

Analog operators represent dynamic behavior:

```verilog
I(p, n) <+ c * ddt(V(p, n));
V(out) <+ laplace_nd(V(in), {1.0}, {1.0, tau});
phase = idtmod(freq, 0.0, 1.0);
```

Use analog operators in continuous analog context, not as ordinary one-shot procedural helpers.

## Noise Functions

Noise functions belong in analog expressions:

```verilog
I(p, n) <+ white_noise(density, "thermal_like");
```

Names attached to noise sources are labels; keep them stable and descriptive.

## Time And Step Hints

`$abstime` reads current analysis time. `$bound_step(max_step)` requests an upper bound on
future step size where the execution environment honors it.

```verilog
analog begin
    $bound_step(max_dt);
    angle = 2.0 * `M_PI * freq * $abstime;
end
```

## Messages And File I/O

Use message tasks sparingly in reusable modules:

```verilog
$strobe("state=%d value=%g", state, value);
```

File tasks such as `$fopen`, `$fscanf`, `$fdisplay`, and `$fclose` are language features, but
they create side effects and should be isolated from the core behavioral equations unless the
user explicitly asks for file-driven behavior.
