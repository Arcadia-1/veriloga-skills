# Analog Blocks And Contributions

## Analog Evaluation

Code inside `analog begin ... end` is evaluated as part of the continuous analog behavior.
Separate two kinds of statements:

- Procedural assignments update real/integer state: `x = expr;`
- Contributions define branch equations: `V(out) <+ expr;`, `I(p,n) <+ expr;`

Do not assign to `V(...)` or `I(...)` with `=`. Branch quantities are driven through `<+`.

## Voltage And Current Contributions

Use voltage contributions for controlled potential:

```verilog
V(out, ref) <+ target;
```

Use current contributions for controlled flow:

```verilog
I(p, n) <+ conductance * V(p, n);
```

Multiple contributions to the same branch add together. Keep this intentional and easy to
audit.

## Continuous Expressions

Prefer continuous expressions for behavior that should be valid at every analog evaluation:

```verilog
real limited;

analog begin
    limited = max(min(V(in), vmax), vmin);
    V(out) <+ gain * limited;
end
```

## Smoothing

Use smoothing functions when a state variable changes abruptly but the driven branch should
change continuously:

```verilog
V(out) <+ transition(level, delay, rise_time, fall_time);
```

`transition()` is best for piecewise constant targets. For continuously varying expressions,
prefer algebraic limiting, `slew()`, or other continuous forms.

## Contributions Inside Conditionals

Keep every analog branch defined on every path unless an intentionally absent contribution is
part of the model:

```verilog
analog begin
    if (enable)
        target = high;
    else
        target = low;

    V(out) <+ transition(target, 0, tt);
end
```
