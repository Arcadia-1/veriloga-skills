# 环境要求 / Requirements

## veriloga 技能

**无外部依赖。** 纯文档/参考型技能，任何 Agent 直接使用。

## 本地验证（可选）

写好的模块可以在本地验证。根据模块使用的构造，有两种验证路径：

### 电压域验证 — EVAS

适用于使用 `V() <+` + `@(cross())` / `transition()` 的模块（SAR 逻辑、DFF、计数器等）。

```bash
pip install evas
```

| 工具 | 用途 | 获取方式 |
|------|------|----------|
| [EVAS](https://evas.tokenzhang.com/) | 事件驱动 Verilog-A 仿真器 | `pip install evas` |
| **evas-sim 技能** | Agent 驱动 EVAS 仿真的完整指令 | 本项目 `evas-sim/SKILL.md` |

### 电流域验证 — OpenVAF + ngspice

适用于使用 `I() <+` / `ddt()` / `laplace_nd()` 的模块（Opamp、RLC、VCO 等）。

> **安装较繁琐**：需要分别安装 OpenVAF 编译器、ngspice（≥ 38，需支持 OSDI），Windows 上还需要 Visual C++ Build Tools。详见 [`openvaf/references/install.md`](./openvaf/references/install.md)。
