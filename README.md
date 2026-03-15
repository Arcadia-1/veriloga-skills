# veriloga-skills

两个让 Agent 具有编写和仿真 Verilog-A 行为模型能力的技能包：**veriloga**（写代码）/ **openvaf**（编译仿真）。

写出的模块会根据代码构造自动分为**电压域**和**电流域**，分别路由到不同的仿真器：

- **电压域**（`V() <+` + `@(cross())` + `transition()`）→ [EVAS](https://evas.tokenzhang.com/) 事件驱动仿真器
- **电流域**（`I() <+` / `ddt()` / `laplace_nd()`）→ OpenVAF + ngspice SPICE 仿真

> **如果你是人类**：下面的技能总览和示例结构可以帮你了解这个包的内容。安装后让 Agent 帮你写 Verilog-A 即可。

> **如果你是 AI Agent**：跳过总览，直接看 [安装](#安装) 说明。`veriloga/SKILL.md` 是写代码的完整指令（8 条必需规则 + 12 类电路参考），`openvaf/SKILL.md` 是编译仿真的指令。代码模板在 `assets/template.va`，31 个参考样例在 `assets/examples/`。

---

## 技能总览

| 技能 | 定位 | 功能 |
|------|------|------|
| **veriloga** | 写代码 | 8 条必需规则 + 12 类电路参考 + 31 个真实样例，从零写出 simulator-ready 的 Verilog-A |
| **openvaf** | 电流域仿真 | OpenVAF 编译 → ngspice/OSDI 加载 → 仿真验证（处理 `I() <+`、`ddt()`、`laplace` 等构造） |

`veriloga` 负责写代码并自动分类域，电流域模块交给 `openvaf` 跑，电压域模块交给 EVAS 跑。

---

## 技能1：veriloga

从 1,638 个真实 .va 设计中提炼的规则和模式，覆盖模拟/混合信号 IC 设计的 12 类电路。

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

## 技能2：openvaf

`veriloga` 的互补技能——处理**电流域**模块的编译和仿真。

### 工作流程

```
.va 文件 → OpenVAF 编译 → .osdi 文件 → ngspice 加载 → 仿真验证
```

适用于包含 `I() <+`、`ddt()`、`idt()`、`laplace_nd()` 等电流域构造的模块。

### 覆盖内容

- OpenVAF 安装与配置
- 编译命令与常见报错处理
- ngspice OSDI 加载方式
- 支持的 Verilog-A 特性清单
- 完整的 troubleshooting 指南

详见 [`openvaf/SKILL.md`](./openvaf/SKILL.md)。

---

## 仿真路由

`veriloga` 写完代码后会自动扫描 `analog begin` 块，根据使用的构造分类域并路由到正确的仿真器：

```
写完模块 → 扫描代码构造 → 分类域
                           ├── 电压域 → EVAS 事件驱动仿真器
                           ├── 电流域 → openvaf 技能 (OpenVAF + ngspice)
                           └── 混合域 → 拒绝，建议拆分模块
```

| 域 | 判定依据 | 仿真器 | 典型模块 |
|---|---|---|---|
| **电压域** | `V() <+` + `@(cross())` / `transition()`，无 `I() <+` | [EVAS](https://evas.tokenzhang.com/) | SAR 逻辑、DFF、计数器、比较器 |
| **电流域** | `I() <+` / `ddt()` / `idt()` / `laplace_nd()` | OpenVAF + ngspice | Opamp、RLC、VCO 核心、LDO |
| **混合域** | 同时包含电压域和电流域构造 | 不可直接仿真 | 需拆分为两个子模块 |

域分类和路由的完整逻辑见 `veriloga/references/domain-routing.md`，EVAS 支持的构造清单见 `veriloga/references/evas-capabilities.manifest`。

---

## 安装

### 推荐使用 Agent 来安装和使用本技能

Agent 会自动处理路径和配置。如果要手动操作，参考以下说明。

安装到用户根目录（全局可用）：

```bash
cp -r veriloga  ~/.claude/skills/
cp -r openvaf   ~/.claude/skills/
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
- **openvaf 技能**：需要 [OpenVAF](https://openvaf.semimod.de/) 和 [ngspice](http://ngspice.sourceforge.net/)（≥ 38，支持 OSDI）

## License

This repository is intended for educational and reference purposes.
