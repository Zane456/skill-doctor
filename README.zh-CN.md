[English](README.md) | 简体中文

<div align="center">

# skill-doctor

<p align="center">
  <img src="assets/hero.png" alt="skill-doctor —— AI agent skill 体检工具:诊断 SKILL.md 触发率、路由召回与包结构" width="760" />
</p>

> *「触发不了的 skill，只是没人读的文档。」*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Claude%20Code%20%2B%20Codex-blueviolet.svg)]()
[![Checks](https://img.shields.io/badge/checks-4%20deterministic-blue.svg)]()
[![Type](https://img.shields.io/badge/type-meta--skill-green.svg)]()

<br>

**给 AI agent 的 skill 做体检:诊断、路由测试、重构包结构 —— 让模型真的会触发它。**

<br>

skill-doctor 是一个 meta-skill,也就是一个用来管理其他 skill 的 skill。它按 LLM 真正读取 skill 的方式来检查 SKILL.md。普通 linter 只看 frontmatter 格式和死链。skill-doctor 深入到三件事:触发可不可靠、路由找不找得到、结构要不要重构。核心检查由四个确定性脚本完成,不需要任何 API key。

<br>

[看效果](#看效果) · [装上就能跑](#装上就能跑) · [用数字说话](#用数字说话) · [工作原理](#工作原理)

</div>

---

## 看效果

指向一个 skill,它给的是诊断,不是语法报告:

```text
[skill-doctor] Auditing: my-skill/SKILL.md   body=142 lines   description=64 chars
[skill-doctor] Budget: 38 skills installed, descriptions 31k vs ≈40k → fits

[skill-doctor] Diagnosis

❌ Must fix (P0→P3)
  [P0 effect break]    Step 3 reads a file Step 1 never writes → the workflow dead-ends
  [P1 trigger]         description has no negative constraint → trigger rate ~50%, not ~100%
  [weak-leading-word]  body opens with "This skill helps you..." → a no-op line the model skips

⚠️ Suggested
  - references/tips.md mixes 3 unrelated topics → split by topic, one file each

✅ Passed
  - routing: 2 hops, 0 orphans, 0 dangling links
  - 17 references reachable from SKILL.md
```

它不查 Markdown 语法。它会告诉你:模型会偷偷跳过第 3 步,你的 description 只有一半概率会触发。然后它说清为什么。

---

## 装上就能跑

skill 的安装,就是把它放进你的 skills 文件夹:

```bash
git clone https://github.com/Zane456/skill-doctor.git ~/.claude/skills/skill-doctor
```

四个脚本跑在 Python 3 上,零依赖。核心检查(路由、预算、结构)什么都不用装。只有一个检查是可选的:GLM 路由召回测试要调用 LLM,所以它从环境变量读 key。

```bash
export GLM_API_KEY=你的_zai_key   # 可选,只给路由召回测试用
```

装好之后,在 Claude Code 或 Codex 里让它审一个 skill。你可以说一句*「审查这个 skill」*,或者直接 invoke `skill-doctor`。

---

## 用数字说话

每一条都能在仓库里找到对应的脚本或文件。

| 能力 | 你得到什么 |
| :--- | :--- |
| **确定性脚本** | 4 个检查:路由、清单预算、结构、描述精简。全程不调 LLM。跑完给一个退出码,可以接进 CI |
| **触发模板** | Seleznov 三段式,一种实测出来的 description 写法。它把触发率从 ~50% 提到 ~100%(650 次实验) |
| **路由召回测试** | 测一测模型凭描述找不找得到每个 reference 文件(这一步叫路由召回)。GLM 投 3 票,多数说了算 |
| **失效模式命名** | 6 种命名好的常见毛病:`no-op`、`sediment`、`premature-completion`、`sprawl`、`weak-leading-word`、`duplication` |
| **结构手术** | 强制 2 跳路由上限。拆文件时逐字搬运,不留一个孤儿文件 |
| **预算预警** | 量一量所有 description 加起来会不会撑爆约 1% 的上下文预算 —— **仅 Claude Code**(见下注) |
| **指南针上限** | SKILL.md 不超过 6000 字符。它自己的 17 个 reference 全部按需加载 |

> **注 —— 预算检查只有 Claude Code 支持。** 它依赖 Claude Code 的一个机制:所有 skill 的描述共享一块预算,大约是模型上下文的 1%。一旦超了,Claude Code 会悄悄把超出的描述砍掉、只留一个名字,而只剩名字的 skill 没法自动触发。Codex 没有这套预算机制,所以这一项在 Codex 上会跳过。其余三个脚本、所有判断维度,都是跨平台通用的。

---

## 工作原理

skill-doctor 跑一条固定的诊断流程。每一步都会打印一行 —— 没有可见输出的步骤,就是模型会偷偷跳过的步骤。

```text
SKILL.md + references/ + scripts/
        |
        v
   skill-doctor
        |
   |-- 确定性脚本      (路由 · 预算 · 精简)
   |-- GLM 路由召回    (每文件投 3 票)
   |-- 判断维度        (触发 · 失效模式)
        |
        v
   P0-P3 诊断  +  失效模式命名
        |
        v
   你确认后才改  ->  重验路由
```

**1. 读全文、算预算**:先读完整个 SKILL.md。再把所有已安装 skill 的 description 加起来,算算会不会超出清单预算。这样判断这一个 skill 时,就知道它在跟多少同类挤。

**2. 命中才加载**:一个质量维度,只在它的 when-to-read 条件命中时才读进来。这正是它要求被审查的 skill 做到的「按需加载」。

**3. 干跑一条真 prompt**:拿一条典型 prompt,走一遍 body 的步骤。如果第 3 步要的输入前面没有任何步骤产出,那就是 P0 级的效果断裂。

**4. 报告、命名**:打出一份 P0 到 P3 的问题清单。每条都贴上失效模式的名字。这样「写得不好」就变成了具体的「这一行是 no-op」(no-op 指空操作,删掉它行为也不变)。

**5. 修完再验**:你确认之后,它才动手改。改完会重跑 `check_routes.py`。只要路由还是红的,重构就不算完。

---

## 仓库里有什么

```
skill-doctor/
├── SKILL.md                            # 指南针 —— 5988 字符,路由到其余一切
├── references/                         # 17 个按需加载的维度与策略
│   ├── index.md                        # reference 路由表(when-to-read + 关键词)
│   ├── description-templates.md        # 触发强度模板 + 清单预算算法
│   ├── body-quality-checklist.md       # 正文太长时,砍什么、降级什么
│   ├── visible-output-rule.md          # 每个工作流步骤都得打印点东西
│   ├── yaml-pitfalls.md                # frontmatter 格式陷阱
│   ├── hard-code-vs-llm-judgment.md    # 这一步该写脚本,还是交给 LLM
│   ├── assets-vs-references.md         # 模板归 assets,文档归 references
│   ├── structure-surgery.md            # 拆分 / 重构 / 路由,2 跳上限
│   ├── effect-dry-run.md               # 拿一条 prompt 走一遍工作流
│   ├── priority-tiers.md               # P0–P3 严重度定义
│   ├── predictability-glossary.md      # 命名好的失效模式
│   ├── hard-rules.md                   # 量化的必过硬规则
│   ├── exception-fallback.md           # 出错时怎么办
│   ├── language-policy.md              # 默认英文的语言策略
│   ├── apply-safety.md                 # 体量门、删除前检查、收尾
│   ├── live-injection-check.md         # description 到底有没有被注入
│   └── rationale.md                    # 这个 skill 为什么存在
└── scripts/                            # 4 个确定性检查,零依赖
    ├── check_routes.py                 # 可达性、孤儿、6000 字符上限
    ├── check_listing_budget.py         # description 预算(仅 Claude Code)
    ├── eval_retrieval.py               # GLM 路由召回投票
    └── check_desc_slim.py              # 安全的 description 精简门
```

MIT —— 随便用,随便改,随便造。

---

<div align="center">

> *触发不了的 skill，只是没人读的文档。*

<br>

⭐ 如果 skill-doctor 在你的 skill 里揪出了一处死步骤，给它点个 star。

<br>

**Zane456** — [clear-chinese](https://github.com/Zane456/clear-chinese) 作者

| 平台 | 链接 |
| :--- | :--- |
| 🐙 GitHub | [@Zane456](https://github.com/Zane456) |

<br>

MIT License © [Zane456](https://github.com/Zane456)

</div>
