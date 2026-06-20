[English](README.md) | 简体中文

<div align="center">

# skill-doctor

<p align="center">
  <img src="assets/hero.png" alt="skill-doctor —— AI agent skill 体检工具:诊断 SKILL.md 触发率、路由召回与包结构" width="760" />
</p>

> *「触发不了的 skill，只是没人读的文档。」*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/works_on-Claude_Code_·_Codex_·_Hermes_·_OpenClaw-blueviolet.svg)]()
[![Checks](https://img.shields.io/badge/checks-4%20deterministic-blue.svg)]()
[![Type](https://img.shields.io/badge/type-meta--skill-green.svg)]()

<br>

**给 AI agent 的 skill 做体检:诊断、路由测试、重构包结构 —— 让模型真的会触发它。**

<br>

skill-doctor 是一个 meta-skill,也就是一个用来管理其他 skill 的 skill。它按 LLM 真正读取 skill 的方式来检查 SKILL.md。普通 linter 只看 frontmatter 格式和死链。skill-doctor 深入到三件事:触发可不可靠、路由找不找得到、结构要不要重构。核心检查由确定性脚本完成、不需要任何 API key,且在 Claude Code、Codex、Hermes、OpenClaw 上都能用。

<br>

[看效果](#看效果) · [装上就能跑](#装上就能跑) · [用数字说话](#用数字说话) · [工作原理](#工作原理)

</div>

---

## 看效果

指向一个 skill,它给的是诊断,不是语法报告:

```text
[skill-doctor] Auditing: my-skill/SKILL.md   body=142 lines   description=64 chars
[skill-doctor] Budget (claude_code): 38 skills, 31k vs ≈40k → fits

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

**最省事 —— 让 agent 帮你装。** 克隆仓库,在你的 agent(Claude Code / Codex / Hermes / OpenClaw)里打开,说一句*「装一下 skill-doctor」*。它会探测你的平台、装进正确的 skills 目录、再问你要不要开可选的 LLM 检查。流程写在 [GETTING_STARTED.md](GETTING_STARTED.md) 里,装完即可删。

**手动** —— skill 的安装就是把它放进 skills 文件夹:

```bash
git clone https://github.com/Zane456/skill-doctor.git ~/.claude/skills/skill-doctor
# Codex / OpenClaw: ~/.agents/skills/skill-doctor   ·   Hermes: ~/.hermes/skills/skill-doctor
```

脚本跑在 Python 3 上,零依赖。每个核心检查(路由、预算、结构)**都不用 key**。

**可选 —— 一个更深的 AI 检查。** 在免费检查之外,skill-doctor 还能让一个 LLM **真测一遍**"模型会不会给每个任务挑对 reference",抓出关键词查不出的、易混淆的措辞。**几乎不花钱**:一轮大约几万 token —— 付费 key 几分钱,免费厂商免费。自带任意 OpenAI 兼容厂商的 key 即可:

```bash
export EVAL_LLM_BASE_URL=https://api.deepseek.com   # 以 DeepSeek 为例;Groq / OpenRouter / Gemini / z.ai 都行
export EVAL_LLM_MODEL=deepseek-v4-flash             # 便宜款
export EVAL_LLM_API_KEY=sk-...                      # 在 platform.deepseek.com 申请
```

key 只在运行时从环境变量读 —— skill-doctor **不落盘、不写日志、不提交进仓库**,也只发往你设的 base URL(`.env` 已在 `.gitignore` 里)。

装好后,在你的 agent 里让它审一个 skill,说一句*「审查这个 skill」*,或直接 invoke `skill-doctor`。

---

## 用数字说话

每一条都能在仓库里找到对应的脚本或文件。

| 能力 | 你得到什么 |
| :--- | :--- |
| **确定性脚本** | 4 个检查:路由、清单预算、结构、描述精简。全程不调 LLM。跑完给一个退出码,可以接进 CI |
| **触发模板** | Seleznov 三段式,一种实测出来的 description 写法。它把触发率从 ~50% 提到 ~100%(650 次实验) |
| **路由召回测试** | 测一测模型凭描述找不找得到每个 reference 文件(这一步叫路由召回)。可选:任意 OpenAI 兼容模型投 3 票,多数说了算 |
| **失效模式命名** | 6 种命名好的常见毛病:`no-op`、`sediment`、`premature-completion`、`sprawl`、`weak-leading-word`、`duplication` |
| **结构手术** | 强制 2 跳路由上限。拆文件时逐字搬运,不留一个孤儿文件 |
| **预算预警** | 量一量所有 description 加起来会不会撑爆该平台的清单预算 —— **Claude Code · Codex · Hermes · OpenClaw**(见下注) |
| **指南针上限** | SKILL.md 不超过 6000 字符。它自己的 18 个 reference 全部按需加载 |

> **注 —— 预算检查是平台感知的。** 四个平台都会把每个 skill 的名字+描述塞进系统提示、都有预算、超了都会降级,只是常量不同:Claude Code ≈ 上下文的 1%(静默砍成只剩名字),Codex ≈ 2% 或 8000 字符(先缩描述再省略 skill 并报警),OpenClaw 用 `maxSkillsPromptChars` 上限,Hermes 直接量它的注入快照。`detect_platform.py` 自动选对规则;平台或上下文窗口未知时,脚本会问你。其余三个脚本、所有判断维度,都是跨平台通用的。

---

## 工作原理

skill-doctor 跑一条固定的诊断流程。每一步都会打印一行 —— 没有可见输出的步骤,就是模型会偷偷跳过的步骤。

```text
SKILL.md + references/ + scripts/
        |
        v
   skill-doctor
        |
   |-- 确定性脚本      (探测 · 路由 · 预算 · 精简)
   |-- LLM 路由召回    (可选 · 每文件投 3 票)
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
├── GETTING_STARTED.md                  # 一次性、agent 驱动的安装引导(装完可删)
├── SKILL.md                            # 指南针 —— 路由到其余一切
├── references/                         # 18 个按需加载的维度与策略
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
│   ├── output-style.md                 # skill-doctor 给人看时的输出风格
│   └── rationale.md                    # 这个 skill 为什么存在
└── scripts/                            # 确定性检查,零依赖
    ├── detect_platform.py              # 探测平台 + 它的清单预算规则
    ├── check_routes.py                 # 可达性、孤儿、6000 字符上限
    ├── check_listing_budget.py         # description 预算(CC · Codex · Hermes · OpenClaw)
    ├── eval_retrieval.py               # 可选的 LLM 路由召回投票(自带 key)
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
