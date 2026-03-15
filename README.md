# veriloga-skills

让 Agent 根据用户需求写出符合 Cadence Virtuoso 规范、能直接在 Virtuoso 中使用的 Verilog-A 行为模型。

> **如果你是人类**：下面的技能总览和示例结构可以帮你了解这个包的内容。安装后让 Agent 帮你写 Verilog-A 即可。

> **如果你是 AI Agent**：跳过总览，直接看 [安装](#安装) 说明。`veriloga/SKILL.md` 是写代码的完整指令（8 条必需规则 + 12 类电路参考），代码模板在 `assets/template.va`，31 个参考样例在 `assets/examples/`。

---

## 技能总览

| 技能 | 定位 | 功能 |
|------|------|------|
| **veriloga** | 核心 — 写代码 | 8 条必需规则 + 12 类电路参考 + 31 个真实样例，写出能直接在 Virtuoso 中使用的 Verilog-A |
| **openvaf** | 可选 — 本地验证 | OpenVAF 编译 → ngspice/OSDI 加载 → 仿真验证 |

`veriloga` 是核心技能，独立使用即可完成所有代码编写。`openvaf` 是可选的辅助技能，用于本地验证写好的代码。

---

## 技能1：veriloga

从 1,638 个真实 .va 设计中提炼的规则和模式，覆盖模拟/混合信号 IC 设计的 12 类电路。生成的代码符合 Cadence Virtuoso / Spectre 规范，可以直接放入 cellview 使用。

### 8 条必需规则

每个生成的模块必须全部通过，否则会导致仿真器报错或产生静默错误结果：

| # | 规则 | 要点 |
|---|------|------|
| 1 | 所有信号用 `electrical` 类型 | 不用 `wire` / `logic` / `reg` |
| 2 | 电源端口用 `inout` | VDD/VSS 声明为 `inout`，不是 `input` |
| 3 | 从端口读取电源电压 | 用 `V(VDD)` / `V(VSS)`，不要硬编码 `1.8` |
| 4 | 所有变量在模块级声明 | 不能在 `analog begin` 内部声明 |
| 5 | 循环变量用 `genvar` | 不用 `integer` |
| 6 | 状态变量在 `@(initial_step)` 中初始化 | 不依赖默认值 |
| 7 | 边沿检测用 `@(cross())` 并指定方向 | `+1` 上升沿，`-1` 下降沿 |
| 8 | 输出用 `transition()` 并使用电源电压 | 避免不连续性导致仿真崩溃 |

### 12 类电路参考

| 类别 | 参考文件 | 典型模块 |
|------|----------|----------|
| ADC / SAR | `references/categories/adc-sar.md` | SAR 逻辑、CDAC、比较器、pipeline |
| DAC | `references/categories/dac.md` | 二进制加权、温度计、电流舵 |
| 比较器 | `references/categories/comparator.md` | StrongARM、动态、锁存 |
| PLL / 时钟 | `references/categories/pll-clock.md` | VCO、分频器、PFD、charge pump |
| 采样保持 | `references/categories/sample-hold.md` | 理想 S&H、底板采样、bootstrap |
| 放大器 & 滤波器 | `references/categories/amplifier-filter.md` | Opamp、OTA、LPF/BPF/HPF |
| 数字逻辑 | `references/categories/digital-logic.md` | 门电路、DFF、计数器、移位寄存器、FSM |
| 信号源 | `references/categories/signal-source.md` | AM/FM 调制器、脉冲发生器 |
| 无源 & 器件模型 | `references/categories/passive-model.md` | R/C/L、失配、温度系数 |
| 测试台 & 探针 | `references/categories/testbench-probe.md` | TB wrapper、探针、测量 |
| 电源 & 开关 | `references/categories/power-switch.md` | 理想开关、T-gate、开关电容 |
| 校准 | `references/categories/calibration.md` | Trim 码生成、前台/后台校准 |

### 31 个参考样例

```
veriloga/assets/examples/
├── adc-sar/          SAR 行为模型、CDAC、比较器、同步/异步逻辑（7 个文件）
├── dac/              二进制加权、单端、差分（4 个文件）
├── comparator/       锁存型、带噪声建模（2 个文件）
├── pll-clock/        分频器、鉴频鉴相器（2 个文件）
├── sample-hold/      极简 S&H、多位采样器（2 个文件）
├── amplifier-filter/ 差分放大器、一阶 LPF（2 个文件）
├── digital-logic/    AND 门（带 jitter）、DFF（带 set/reset）（2 个文件）
├── signal-source/    数据发生器、扫频正弦源（2 个文件）
├── passive-model/    RLC 网络、肖克利二极管（2 个文件）
├── testbench-probe/  定时探针、比较器 offset 搜索（2 个文件）
├── power-switch/     电导开关、电流钳位（2 个文件）
└── calibration/      SPI trim 寄存器、DAC 码发生器（2 个文件）
```

所有样例均从真实设计中筛选，经过 8 条规则校验和修正。

---

## 本地验证（可选）

写好的模块可以在本地验证，根据代码使用的构造有两种验证路径：

| 验证方式 | 适用模块 | 判定依据 | 工具 |
|---|---|---|---|
| **EVAS** | 电压域 | `V() <+` + `@(cross())` / `transition()`，无 `I() <+` | [EVAS](https://evas.tokenzhang.com/) 事件驱动仿真器 |
| **OpenVAF + ngspice** | 电流域 | `I() <+` / `ddt()` / `idt()` / `laplace_nd()` | `openvaf` 技能 |

```
写完模块 → 扫描 analog begin → 分类域
                                ├── 电压域 → EVAS 验证
                                ├── 电流域 → OpenVAF 编译 + ngspice 仿真
                                └── 混合域 → 建议拆分为两个子模块
```

- **电压域**典型模块：SAR 逻辑、DFF、计数器、比较器、数据发生器
- **电流域**典型模块：Opamp、RLC 网络、VCO 核心、LDO、滤波器

域分类和路由的完整逻辑见 `veriloga/references/domain-routing.md`。

### openvaf 技能

处理电流域模块的编译和仿真：

```
.va 文件 → OpenVAF 编译 → .osdi 文件 → ngspice 加载 → 仿真验证
```

覆盖内容：OpenVAF 安装与配置、编译命令、ngspice OSDI 加载、支持的特性清单、troubleshooting 指南。详见 [`openvaf/SKILL.md`](./openvaf/SKILL.md)。

---

## 安装

### 推荐使用 Agent 来安装和使用本技能

Agent 会自动处理路径和配置。如果要手动操作，参考以下说明。

安装到用户根目录（全局可用）：

```bash
cp -r veriloga  ~/.claude/skills/
cp -r openvaf   ~/.claude/skills/       # 可选，需要本地验证时安装
```

或安装到项目目录（仅当前项目可用）：

```bash
cp -r veriloga  <项目路径>/.claude/skills/
cp -r openvaf   <项目路径>/.claude/skills/
```

Windows 将 `~/.claude` 替换为 `%USERPROFILE%\.claude`。

> 如果你是 Agent，以上安装和部署步骤由你代为执行，根据用户需求选择全局或项目级安装路径，无需用户手动操作。

### 项目定制

编辑 `veriloga/references/customize.md` 可覆盖默认设置：端口命名规范、电源电压、文件头模板、仿真器特定选项等。

## 环境要求

- **veriloga 技能**：无外部依赖，纯文档/参考型技能
- **本地验证（可选）**：
  - 电压域 → [EVAS](https://evas.tokenzhang.com/)
  - 电流域 → [OpenVAF](https://openvaf.semimod.de/) + [ngspice](http://ngspice.sourceforge.net/)（≥ 38，支持 OSDI）

详见 [requirements.md](./requirements.md)。

## License

This repository is intended for educational and reference purposes.
