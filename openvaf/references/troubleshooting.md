# Troubleshooting Guide

## Compilation Errors (OpenVAF)

### `LINK: fatal error LNK1104: cannot open file 'msvcrt.lib'`
**Cause:** MSVC Build Tools not installed on Windows.
**Fix:** Install "Build Tools for Visual Studio" with the "Desktop development with C++"
workload. See `install.md` for details.

### `error: unknown compiler directive` or `unsupported feature`
**Cause:** The `.va` file uses features OpenVAF doesn't support (e.g., `@(cross())`,
arrays, `genvar`).
**Fix:** OpenVAF only supports the compact-model subset of Verilog-A. If your model
uses behavioral features, it cannot be compiled with OpenVAF. Use a full Verilog-AMS
simulator instead.

### `internal compiler error` or panic
**Cause:** OpenVAF hit an unhandled case, often from unsupported features.
**Fix:** Check `references/supported_features.md` to confirm your code uses only
supported constructs. If it does and still crashes, file a bug at
https://github.com/OpenVAF/OpenVAF-Reloaded/issues

### OpenVAF binary not found
**Cause:** Not on PATH, or file lacks `.exe` extension (Windows).
**Fix:**
```bash
# Check if it's on PATH
openvaf --help

# Windows: make sure the file is named openvaf.exe
# And the directory containing it is in PATH
```

---

## Loading Errors (ngspice)

### `Library 'mymodel.osdi' couldn't be loaded`
**Cause:** ngspice can't find the `.osdi` file.
**Fix:** Use a relative path with `./` prefix, or an absolute path:
```spice
.control
pre_osdi ./mymodel.osdi       * relative to netlist directory
pre_osdi C:/models/mymodel.osdi  * absolute
.endc
```

### Model type not recognized / instance ignored
**Cause 1:** Used `osdi` instead of `pre_osdi`.
**Fix:** Always use `pre_osdi` so the model loads before netlist parsing:
```spice
.control
pre_osdi ./mymodel.osdi    * correct
.endc
```

**Cause 2:** Instance name doesn't start with `N`.
**Fix:** Rename instance:
```spice
Nr1 in out mymod    * correct — starts with N
R1  in out mymod    * wrong — ngspice treats as built-in resistor
```

### `unrecognized parameter` in `.model` line
**Cause:** The model name in `.model` doesn't match the Verilog-A `module` name exactly.
**Fix:** Check the `.va` source for the exact `module` identifier and use it verbatim.

### Module name conflicts with ngspice built-in
**Cause:** Module named `resistor`, `capacitor`, `diode`, `nmos`, `pmos`, etc.
**Fix:** Rename to a unique name: `myresistor`, `custom_diode`, `nmos_sq`.

### Crash: `Illegal instruction` (SIGILL)
**Cause:** Missing Visual C++ runtime libraries on Windows.
**Fix:** Install "Microsoft Visual C++ 2015-2022 Redistributable" from:
https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist

### `UTF-8 syntax error in line N`
**Cause:** Netlist file has non-ASCII characters (smart quotes, BOM, etc.).
**Fix:** Re-save the file as plain UTF-8 without BOM. Avoid copy-pasting from
web pages or Word documents.

### ngspice OSDI not enabled
**Cause:** `unset osdi_enabled` in `spinit` file disables OSDI loading.
**Fix:** Edit `share/ngspice/scripts/spinit` and comment out:
```
* unset osdi_enabled
```

### Port limit exceeded (>20 terminals)
**Cause:** ngspice has a hard-coded limit on the number of OSDI device terminals.
**Fix:** This requires modifying ngspice source code (`inpcom.c` line 5326,
`inp2n.c` lines 29-30). For most compact models, 4-6 terminals is typical and
this limit is not an issue.

---

## OSDI API Version Mismatch

### Symptom: model loads but simulation produces wrong results or crashes
**Cause:** The `.osdi` file was compiled with OSDI 0.4 (OpenVAF-Reloaded master)
but ngspice expects OSDI 0.3.
**Fix:** Use the `osdi_0.3` branch of OpenVAF-Reloaded, or the original v23.5.0
binary, which produces OSDI 0.3 compatible output.
