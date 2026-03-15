# Installation Guide

## OpenVAF (Verilog-A Compiler)

### Windows

1. **Download** the prebuilt binary:
   - Go to https://openvaf.semimod.de/download/
   - Download the Windows AMD64 build (v23.5.0 or later)
   - The file may be named `openvaf_23_5_0_windows_amd64` without an extension

2. **Install Microsoft Visual C++ Build Tools FIRST (required):**
   OpenVAF uses the MSVC `link.exe` linker internally. Without it, OpenVAF crashes
   immediately (exit code -1073741819 / access violation).

   > **Critical:** Git ships its own `link.exe` which is NOT the MSVC linker.
   > If only Git's `link.exe` is in PATH, OpenVAF will crash. You must install
   > the real MSVC Build Tools.

   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Run the installer
   - Select the **"Desktop development with C++"** workload
   - Click Install (~2 GB)
   - You do NOT need the full Visual Studio IDE

   Verify the MSVC linker is installed:
   ```powershell
   # Should show a path like C:\Program Files\Microsoft Visual Studio\...
   # NOT C:\Program Files\Git\usr\bin\link.exe
   where.exe link
   ```

3. **Rename and place on PATH:**
   ```powershell
   # Rename to openvaf.exe
   ren openvaf_23_5_0_windows_amd64 openvaf.exe

   # Create a tools directory if you don't have one
   mkdir C:\tools

   # Move the binary there
   move openvaf.exe C:\tools\

   # Add to PATH (run as Administrator, or use System Properties > Environment Variables)
   setx PATH "%PATH%;C:\tools" /M
   ```

   - Download "Build Tools for Visual Studio" from:
     https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Run the installer
   - Select the **"Desktop development with C++"** workload
   - Click Install (this downloads ~2 GB)
   - You do NOT need the full Visual Studio IDE

4. **Running OpenVAF on Windows:**
   The MSVC linker is NOT added to the global PATH by default. You must load the
   MSVC environment before running OpenVAF. Use this pattern:

   ```bash
   cmd.exe /c "call \"C:\Program Files (x86)\Microsoft Visual Studio\<ver>\BuildTools\VC\Auxiliary\Build\vcvarsall.bat\" x64 >nul 2>&1 & C:\tools\openvaf.exe mymodel.va"
   ```

   Replace `<ver>` with your VS version number (e.g., `18` for VS 2025,
   `2022` for VS 2022). To find your version:
   ```powershell
   dir "C:\Program Files (x86)\Microsoft Visual Studio"
   ```

   Without `vcvarsall.bat`, OpenVAF crashes with exit code -1073741819 (access
   violation) because it finds Git's `link.exe` instead of MSVC's `link.exe`.

### Linux

1. **Download:**
   ```bash
   wget https://openvaf.semimod.de/download/openvaf_23_5_0_linux_amd64 -O openvaf
   chmod +x openvaf
   sudo mv openvaf /usr/local/bin/
   ```

2. **Verify:**
   ```bash
   openvaf --help
   ```

No additional dependencies on Linux (LLVM and the linker are bundled).

### macOS

Not supported. OpenVAF only targets Windows and Linux.

### Community Fork: OpenVAF-Reloaded

The original OpenVAF (by Pascal Kuthe / SemiMod) has not received updates since
late 2023. The community fork **OpenVAF-Reloaded** is the active development path:

- GitHub: https://github.com/OpenVAF/OpenVAF-Reloaded
- Adds OSDI 0.4 support, `$fatal`/`$finish`/`$stop`
- The `osdi_0.3` branch produces models compatible with current ngspice (39+)
- The `master` branch produces OSDI 0.4 models (may need a newer ngspice build)

For most users, the original v23.5.0 binary is fine.

---

## ngspice (Simulator)

### Minimum Version

**ngspice 39** is the minimum for OSDI support. Current stable is **45.2** (as of
early 2026). Always use the latest stable release.

### Windows

1. Download from https://sourceforge.net/projects/ngspice/files/ng-spice-rework/
   - Get the `ngspice-XX_64.7z` archive (or `.zip` if available)
2. Extract with 7-Zip to `C:\Spice64`
3. The executable is at `C:\Spice64\bin\ngspice.exe`
4. Add `C:\Spice64\bin` to your PATH

### Linux

```bash
# Ubuntu/Debian (may be an older version)
sudo apt install ngspice

# From source (for latest with OSDI):
wget https://sourceforge.net/projects/ngspice/files/ng-spice-rework/45/ngspice-45.tar.gz
tar xzf ngspice-45.tar.gz
cd ngspice-45
./configure --enable-osdi --with-readline
make -j$(nproc)
sudo make install
```

### Enabling OSDI (if models fail to load)

Check `share/ngspice/scripts/spinit` (or `C:\Spice64\share\ngspice\scripts\spinit`
on Windows). If you see this line:

```
unset osdi_enabled
```

Comment it out:

```
* unset osdi_enabled
```

This enables automatic OSDI model loading from the `lib/ngspice/` directory.

### OSDI model directory

Place `.osdi` files in:
- Windows: `C:\Spice64\lib\ngspice\`
- Linux: `/usr/local/lib/ngspice/` (or wherever ngspice is installed)

Models placed here can be loaded by bare filename without a path prefix.
