# 环境要求 / Requirements

## veriloga 技能

**无外部依赖。** 纯文档/参考型技能，任何 Agent 直接使用。

## 本地验证（可选）

写好的模块可以在本地验证。根据模块使用的构造，有两种验证路径：

### 电压域验证 — EVAS

适用于使用 `V() <+` + `@(cross())` / `transition()` 的模块（SAR 逻辑、DFF、计数器等）。

| 工具 | 用途 | 获取方式 |
|------|------|----------|
| [EVAS](https://evas.tokenzhang.com/) | 事件驱动 Verilog-A 仿真器 | 见官网 |

### 电流域验证 — OpenVAF + ngspice

适用于使用 `I() <+` / `ddt()` / `laplace_nd()` 的模块（Opamp、RLC、VCO 等）。

| 工具 | 最低版本 | 用途 | 安装方式 |
|------|----------|------|----------|
| [OpenVAF](https://openvaf.semimod.de/) | 最新 | 将 `.va` 编译为 `.osdi` | 见 `openvaf/references/install.md` |
| [ngspice](http://ngspice.sourceforge.net/) | ≥ 38 | 加载 `.osdi` 并仿真 | 系统包管理器或源码编译 |

#### Windows 额外依赖

| 工具 | 用途 |
|------|------|
| [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) | OpenVAF 编译器运行时依赖 |

#### 安装验证

```bash
# 检查 OpenVAF
openvaf --version

# 检查 ngspice（需 ≥ 38 且支持 OSDI）
ngspice --version

# 编译测试
openvaf my_module.va        # 生成 my_module.osdi
```

#### ngspice 中加载 OSDI 模块

```spice
.control
pre_osdi my_module.osdi
.endc
```

详细安装和 troubleshooting 见 [`openvaf/references/install.md`](./openvaf/references/install.md) 和 [`openvaf/references/troubleshooting.md`](./openvaf/references/troubleshooting.md)。
