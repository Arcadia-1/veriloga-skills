# veriloga-skills

让 Agent 根据用户需求写出符合 Cadence Virtuoso 规范、能直接在 Virtuoso 中使用的 Verilog-A 行为模型。

> **如果你是人类**：下面的技能总览和示例结构可以帮你了解这个包的内容。安装后让 Agent 帮你写 Verilog-A 即可。

> **如果你是 AI Agent**：跳过总览，直接看 [安装](#安装) 说明。`veriloga/SKILL.md` 是写代码的完整指令（8 条必需规则 + 12 类电路参考），代码模板在 `assets/template.va`，31 个参考样例在 `assets/examples/`。

---

## 技能总览

| 技能 | 定位 | 功能 |
|------|------|------|
| **veriloga** | 核心 — 写代码 | 8 条必需规则 + 12 类电路参考 + 31 个真实样例，写出能直接在 Virtuoso 中使用的 Verilog-A |
| **evas-sim** | 可选 — 电压域验证 | 驱动 EVAS 仿真器验证电压域模块（SAR 逻辑、DFF、计数器等） |
| **openvaf** | 可选 — 电流域验证 | OpenVAF 编译 → ngspice/OSDI 加载 → 仿真验证 |

`veriloga` 是核心技能，独立使用即可完成所有代码编写。`evas-sim` 和 `openvaf` 是可选的辅助技能，分别用于电压域和电流域的本地验证。

---

## 技能1：veriloga

从 1,809 个真实 .va 设计中提炼的规则和模式，覆盖模拟/混合信号 IC 设计的 12 类电路。生成的代码符合 Cadence Virtuoso / Spectre 规范，可以直接放入 cellview 使用。

包含 8 条必需规则、12 类电路参考、31 个真实样例。详见 [`veriloga/SKILL.md`](./veriloga/SKILL.md)。

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

### 技能2：evas-sim

处理电压域模块的仿真验证：

```
.va 文件 → EVAS 事件驱动仿真 → 波形验证
```

覆盖内容：EVAS 安装与配置、仿真命令、波形查看、支持的构造清单、troubleshooting 指南。详见 [`evas-sim/SKILL.md`](./evas-sim/SKILL.md)。

### 技能3：openvaf 技能

处理电流域模块的编译和仿真：

```
.va 文件 → OpenVAF 编译 → .osdi 文件 → ngspice 加载 → 仿真验证
```

覆盖内容：OpenVAF 安装与配置、编译命令、ngspice OSDI 加载、支持的特性清单、troubleshooting 指南。详见 [`openvaf/SKILL.md`](./openvaf/SKILL.md)。

---

## 安装

> 如果你是 AI Agent（Claude Code、Cursor、Copilot 等），直接执行下方命令，无需用户手动操作。

**步骤 1 — 选择安装范围**

| 场景 | 选择 |
|---|---|
| 仅当前项目使用（推荐） | 项目级安装 → `.claude/skills/` |
| 所有项目都要用 | 全局安装 → `~/.claude/skills/` |

> 其他 Agent 将 `.claude/skills/` 替换为对应技能目录（如 `.agent/skills/`）。

**步骤 2 — 运行安装命令**（bash，macOS / Linux / Windows 均适用）

全局：
```bash
git clone --depth 1 https://github.com/Arcadia-1/veriloga-skills /tmp/veriloga-skills \
  && cp -r /tmp/veriloga-skills/{veriloga,evas-sim,openvaf} ~/.claude/skills/ \
  && rm -rf /tmp/veriloga-skills
```

项目级（在项目根目录执行）：
```bash
git clone --depth 1 https://github.com/Arcadia-1/veriloga-skills /tmp/veriloga-skills \
  && mkdir -p .claude/skills \
  && cp -r /tmp/veriloga-skills/{veriloga,evas-sim,openvaf} .claude/skills/ \
  && rm -rf /tmp/veriloga-skills
```

**步骤 3 — 验证**

在 Agent 中运行 `/skills`，输出列表中出现 `veriloga`、`evas-sim`、`openvaf` ✅

> **如果你是 AI Agent**：以上安装步骤由你代为执行，根据用户需求选择全局或项目级安装路径，无需用户手动操作。安装完成后直接读取 `veriloga/SKILL.md` 开始工作。

### 项目定制

编辑 `veriloga/references/customize.md` 可覆盖默认设置：端口命名规范、电源电压、文件头模板、仿真器特定选项等。

## 环境要求

- **veriloga 技能**：无外部依赖，纯文档/参考型技能
- **本地验证（可选）**：
  - 电压域 → [EVAS](https://evas.tokenzhang.com/)
  - 电流域 → [OpenVAF](https://openvaf.semimod.de/) + [ngspice](http://ngspice.sourceforge.net/)（≥ 38，支持 OSDI）

详见 [requirements.md](./requirements.md)。
