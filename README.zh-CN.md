[English](README.md) | 简体中文

<div align="center">

# skill-doctor

<p align="center">
  <img src="assets/hero.png" alt="skill-doctor —— AI agent skill 的体检工具:诊断 SKILL.md 触发可靠性、路由召回、包结构" width="760" />
</p>

> *「模型从不触发的 skill,只是一份死掉的文档。」*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Claude%20Code%20%2B%20Codex-blueviolet.svg)]()
[![Checks](https://img.shields.io/badge/checks-4%20deterministic-2ea44f.svg)]()
[![Type](https://img.shields.io/badge/type-meta--skill-blue.svg)]()

<br>

**给你的 agent skill 做体检:让模型真能触发它、读完它、干净地路由穿过它。**

<br>

坏掉的 skill 从不报错。它只是不触发,或者模型读了一半就走开——你几周后才发现,自己写的 skill 一次都没被叫起来过。skill-doctor 就是逮住这件事的那道关。它给 `SKILL.md` 的触发可靠性打分,对每个 reference 文件跑一次路由召回测试,给毛病命名,路由断了就重构整个包。四个确定性脚本扛起核心检查,一个都不需要 API key。

<br>

[看它跑一遍](#看它跑一遍) · [装好就用](#装好就用) · [它能逮住什么](#它能逮住什么) · [怎么运作](#怎么运作) · [速查](#速查)

</div>

---

## 看它跑一遍

对着一个 skill 一指,它打出的是诊断,不是语法报告:

```text
[skill-doctor] Auditing: my-skill/SKILL.md   body=142 lines   description=64 chars
[skill-doctor] Budget: 38 skills installed, 31k chars vs ≈40k → fits
[skill-doctor] Dry-run prompt: "use my-skill to tag the photo"   broken links=1

[skill-doctor] Diagnosis

❌ Must fix (P0→P3)
  [P0 effect break]   Step 3 读一个 Step 1 从没写过的文件 → 流程走到死胡同
  [P1 trigger]        description 没有反向约束 → 触发率约 50%,而非约 100%
  [P2 specificity]    "process the image" 没有命令 → 给一个(例:`sips -s format png`)

⚠️ Suggested
  - [no-op] body 开头写 "This skill helps you…"——模型会跳过 → 删掉这行
  - [sprawl] references/tips.md 混了 3 个不相关主题 → 按主题各拆一个文件

✅ Passed
  - 路由:2 跳,0 orphan,0 断链
  - 每个流程步骤都有可见输出
```

它不会告诉你少了个逗号。它告诉你模型会**悄悄跳过 Step 3**,你的 description **只有一半概率触发**——然后说清为什么。

---

## 装好就用

skill 的安装方式,就是把它放进你的 skills 文件夹:

```bash
git clone https://github.com/Zane456/skill-doctor.git ~/.claude/skills/skill-doctor
```

四个脚本在 Python 3 上跑,零依赖。路由、预算、结构这几项不需要别的。一个可选检查——GLM 路由召回测试——会调一次 LLM,所以它从环境变量读 key:

```bash
export GLM_API_KEY=your_zai_key   # 可选,只给路由召回测试用
```

然后,在 **Claude Code 或 Codex** 里直接说一句——*「审查这个 skill」* / *"audit this SKILL.md"*——或者直接 invoke `skill-doctor`。它会读目标、跑检查、把一条真实 prompt 在流程里走一遍,打出 P0→P3 报告。**你不说,它绝不动你的文件。**

---

## 它能逮住什么

那些从不会自己喊出来的故障:

| 你根本不会注意到的症状 | 它会标出 |
| :--- | :--- |
| skill 大概一半时候才触发 | description 没有反向约束,或写成 "Use when" 而非 "ALWAYS invoke"——约 50% vs 约 100% 触发率([650 次实验](https://medium.com/@marc.bara.iniesta/claude-skills-have-two-reliability-problems-not-one-299401842ca8)) |
| 它压根不自动触发 | description 用第一人称,或整份清单超预算被降成只剩名字 |
| 模型读一半就走开 | body 超过约 500 行——`[sprawl]` |
| 某个 reference 文件从没被读到 | orphan 或断链,`check_routes.py` 抓出来 |
| 某个流程步骤被跳过 | 这步没有可见输出,模型就走过去了 |
| agent 提前结束某一步 | 收尾条件太模糊——`[premature-completion]` |
| 一行什么都没改变的指令 | 模型默认本来就会做——`[no-op]` |

每一项检查、阈值、规则,下面[速查](#速查)里全列了。

---

## 怎么运作

每一步都打印一行——一个没有可见输出的步骤,就是一个会被模型悄悄跳过的步骤。

```text
  SKILL.md + references/ + scripts/
        |
        v
  确定性脚本 .......... routes · budget · description-slim   (带退出码,无 LLM)
        |
        v
  GLM 路由召回 ........ 每个 reference 文件投票 3 次          (可选,需要 key)
        |
        v
  判断维度 ............ 触发强度 · 失效模式                   (按需加载)
        |
        v
  Dry-run 一条真 prompt  Step N 是否拿到了前面没产出过的输入?
        |
        v
  P0 -> P3 诊断 ....... 每条都带上它的失效模式名字
        |
        v
  确认后才应用 ........ 然后重跑 check_routes 复验
```

两个设计让它的结论值得信:

- **能确定的就确定。** 字符数、路由、预算,由带退出码的脚本定,不靠每次都会飘的主观判断。
- **不能确定的就诚实。** 如果 skill-doctor 在同一个会话里已经改过你的 skill,它会给报告每一行盖上 `[self-review]`,并提醒你换一个全新 agent 复核。它**故意给自己的结论打折**。

<!-- ============ 速查区——查东西时再看,平时可跳过 ============ -->

---

## 速查

下面全是查阅资料,用这个 skill 不需要读它。

### 诊断流程

| 步骤 | 做什么 | 输出 |
| :--- | :--- | :--- |
| 1 | 读目标 SKILL.md;把每个已装 description 对照清单预算数一遍 | body/description 体积 + 预算结论 |
| 2 | 只加载 `when-to-read` 命中的维度 | 加载/跳过清单 |
| 2.5 | Dry-run:把最典型那条 prompt 在 body 里走一遍 | 断链数(有就 P0) |
| 2.6 | Live-injection:本会话目标的 description 是真注入了,还是被降成只剩名字 | injected / dropped / skipped |
| 3 | 打出 P0→P3 诊断(❌ 必修 · ⚠️ 建议 · ✅ 通过),每条带失效模式名 | 报告 |
| 4 | 确认后才用 Edit 应用修复——然后重跑 `check_routes.py` | 已修复行数 |

### 自带脚本

无 LLM、无第三方依赖,`eval_retrieval.py` 除外(它按需调模型)。

| 脚本 | 检查什么 | 命令 | 退出码 |
| :--- | :--- | :--- | :--- |
| `check_routes.py` | 可达性、orphan、断链、6000 字符 compass 上限;`--before <snapshot>` 加一道内容守恒检查 | `python3 scripts/check_routes.py <skill_dir>` | 0 干净 / 1 有问题 |
| `check_listing_budget.py` | description 总字符 vs 约 1% 上下文的清单池;列出超 300 字符带的 description——**仅 Claude Code**(见下注) | `python3 scripts/check_listing_budget.py <root>` | 0 装得下 / 1 超出 / 2 不可用 |
| `check_desc_slim.py` | 给 description 瘦身上一道闸——保留的文字必须逐字不变,触发词必须存活 | `python3 scripts/check_desc_slim.py <before> <after>` | 0 干净 / 1 不安全 |
| `eval_retrieval.py` | 问 GLM(3 次多数投票)路由能不能凭 `when-to-read` 场景找到每个 reference | `python3 scripts/eval_retrieval.py <skill_dir> --glm` | 0 干净 / 1 有漏 |

> **预算检查只有 Claude Code 支持。** 它依赖 Claude Code 的一个机制:所有 skill 的描述共享一块预算,约为模型上下文的 1%。一旦超了,Claude Code 会悄悄把超出的描述砍掉、只留名字,而只剩名字的 skill 没法自动触发。Codex 没有这套预算机制,所以这一项在 Codex 上会跳过。其余三个脚本、所有判断维度,都是跨平台通用的。

### 什么样的 description 才触发

可靠性上最大的那个杠杆——是测出来的,不是猜的([Seleznov,650 次实验](https://medium.com/@marc.bara.iniesta/claude-skills-have-two-reliability-problems-not-one-299401842ca8)):

| description 写法 | 触发率 |
| :--- | :--- |
| `"[做什么]. Use when [何时]."`(Anthropic 默认) | 约 50% |
| `"[领域] expert. ALWAYS invoke when [触发]. Do not [默认动作] directly."`(Seleznov) | 约 100% |

最反直觉的是那条反向约束(`Do not … directly`)——去掉它,触发率就塌回约 50%。

### 硬规则

这里违反一条就是错,不是建议。

| 规则 | 出处 |
| :--- | :--- |
| description ≤ 1024 字符(Claude Code ≥ 2.1.105 收到 1536) | Anthropic spec / CC release notes |
| 清单预算超标一律上报——这是全局事实,靠全局瘦身解决,绝不靠改单个 skill | CC issues #56710 / #47627 |
| description 用第三人称 | Anthropic best practices |
| name 只用小写字母、数字、连字符 | Anthropic spec |
| body < 500 行 | Anthropic / 社区共识 |
| 路由深度 ≤ 2 跳(SKILL.md → index.md → 文件);禁止嵌套索引 | structure-surgery |
| 零断链、零 orphan 子文档 | structure-surgery 铁律 |
| description 写在单一逻辑 YAML 行(不用 `>` 或 `|`) | Prettier 重排会弄坏 |
| 多步流程每一步都要有可见输出 | Seleznov 实验 |
| skill 对自己性能的声明必须指向仓库内证据,否则删掉 | evidence-gating |

### 它会命名的失效模式

P 级说**有多严重**,名字说**是哪一类**。

- `[no-op]` —— 模型默认本来就会做的一行
- `[sediment]` —— 漂出相关性的陈旧行
- `[sprawl]` —— 单纯太长,哪怕每行都还有用
- `[duplication]` —— 同一个意思出现在不止一处
- `[premature-completion]` —— 收尾条件模糊到 agent 提前收工
- `[weak-leading-word]` —— 锚点词太弱,压不过模型默认

### 优先级分级

| 级别 | 含义 | 进 ❌ |
| :--- | :--- | :--- |
| **P0** | 效果断裂(跑起来流程接不上) | 总是 |
| **P1** | 违反结构硬规则 | 总是 |
| **P2** | 不够具体(没命令、没 I/O 规格) | 总是 |
| **P3** | 可读性 | 只有当它改变下一次运行的结果时;否则进 ⚠️ |

### 维度(按 `when-to-read` 条件按需加载)

`references/index.md` 路由到下面全部;只有条件命中的才会被读。

| Reference | 管什么 |
| :--- | :--- |
| `description-templates.md` | 触发强度模板 + 清单预算算法 |
| `body-quality-checklist.md` | body 体积、什么该挪进 references |
| `visible-output-rule.md` | 每个流程步骤都得有输出 |
| `yaml-pitfalls.md` | frontmatter 格式坑 |
| `hard-code-vs-llm-judgment.md` | 该写成脚本,还是留给模型 |
| `assets-vs-references.md` | 模板 vs reference 文档怎么分 |
| `structure-surgery.md` | 拆分、路由分层、2 跳上限 |
| `effect-dry-run.md` | 把一条 prompt 在流程里走一遍 |
| `priority-tiers.md` | P0–P3 定义与归类 |
| `predictability-glossary.md` | 失效模式词汇表 |
| `hard-rules.md` | 量化的必过规则 |
| `exception-fallback.md` | 路径或脚本出错时怎么办 |
| `language-policy.md` | 默认英文及其例外 |
| `apply-safety.md` | 体积闸、删除前检查、闭环收尾 |
| `live-injection-check.md` | 本会话 description 是否真被注入 |
| `rationale.md` | 这个 skill 为什么存在 |

### 仓库结构

```text
skill-doctor/
├── SKILL.md                              # compass:诊断流程 + 路由
├── references/
│   ├── index.md                          # 按 when-to-read 路由到每个维度
│   ├── apply-safety.md
│   ├── assets-vs-references.md
│   ├── body-quality-checklist.md
│   ├── description-templates.md
│   ├── effect-dry-run.md
│   ├── exception-fallback.md
│   ├── hard-code-vs-llm-judgment.md
│   ├── hard-rules.md
│   ├── language-policy.md
│   ├── live-injection-check.md
│   ├── predictability-glossary.md
│   ├── priority-tiers.md
│   ├── rationale.md
│   ├── structure-surgery.md
│   ├── visible-output-rule.md
│   └── yaml-pitfalls.md
├── scripts/
│   ├── check_routes.py                   # 可达性 / orphan / 断链 / compass 上限
│   ├── check_listing_budget.py           # description 清单预算(仅 Claude Code)
│   ├── check_desc_slim.py                # description 瘦身闸
│   └── eval_retrieval.py                 # GLM 路由召回投票
├── assets/
│   └── hero.png
├── LICENSE
├── README.md
└── README.zh-CN.md
```

---

<div align="center">

> *模型从不触发的 skill,只是一份死掉的文档。*

<br>

⭐ 如果 skill-doctor 在你某个 skill 里逮出了一步死掉的流程,给它点个 star。

<br>

**Zane456** —— [clear-chinese](https://github.com/Zane456/clear-chinese) 作者

| 平台 | 链接 |
| :--- | :--- |
| 🐙 GitHub | [@Zane456](https://github.com/Zane456) |

<br>

MIT License © [Zane456](https://github.com/Zane456)

</div>
