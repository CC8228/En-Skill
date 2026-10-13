# En-Skill

英语考试备考用的 Claude Skills。

## toefl-prep：托福备考专项（2026 新版）

`skills/toefl-prep/` 是一个按 **2026 年 1 月 21 日起的新版 TOEFL iBT** 设计的备考教练 skill，题型和 1–6 分制都按新版来。

### 能做什么

| 功能 | 说明 |
|---|---|
| 备考计划 | 根据考试日期、目标分、当前水平和可用时间，生成分阶段计划和每周安排 |
| 专项练习 | 按新版 12 种题型原创练习题，先做题后讲解，错因归类 |
| 写作批改 | Write an Email / Academic Discussion：0–5 估分、3 条优先改进、逐句修改、升级范文 |
| 口语批改 | Take an Interview / Listen and Repeat：基于文字稿批改内容和语言，附发音自查清单 |
| 模考 | 对话版整套或单 section 模考，模拟两阶段自适应，输出估分报告 |
| 分数换算 | 1–6 band ↔ 0–120 ↔ CEFR，四项算总分，目标分拆解 |
| 词汇与错题 | 学术话题词表、校园生活词表、拼写训练、错题本模板 |

### 目录结构

```
skills/toefl-prep/
├── SKILL.md                       # 入口：原则、工作流、考试速览、分数速查
├── references/
│   ├── exam-format-2026.md        # 新版考试结构、计分、新旧对照
│   ├── study-plan.md              # 诊断、排期、计划模板
│   ├── reading.md                 # 阅读三题型：出题规格、技巧、示例
│   ├── listening.md               # 听力四题型 + 文字环境下的练习法
│   ├── writing.md                 # 写作三题型 + 评分标准 + 反馈格式
│   ├── speaking.md                # 口语两题型 + 评分标准 + 发音自查
│   ├── vocabulary.md              # 词汇方法与词表
│   └── mock-test.md               # 模考流程与估分
├── scripts/
│   ├── score_convert.py           # 分数换算 / 总分 / 目标拆解
│   ├── c_test.py                  # 生成并批改 Complete the Words
│   ├── text_stats.py              # 写作/口语文字稿统计
│   └── tts.py                     # 听力原文转音频（可选后端）
├── assets/
│   └── error-log-template.md      # 错题本模板
└── evals/evals.json               # 测试用例
```

### 安装

**Claude Code**

```bash
# 个人全局可用
mkdir -p ~/.claude/skills && cp -r skills/toefl-prep ~/.claude/skills/

# 或只在某个项目中可用
mkdir -p .claude/skills && cp -r skills/toefl-prep .claude/skills/
```

**Claude.ai / Claude 桌面端**

把 `skills/toefl-prep` 文件夹打包成 zip（或使用发布的 `toefl-prep.skill` 文件），在 设置 → Capabilities → Skills 中上传。

### 使用示例

直接用自然语言说就行，不需要特殊命令：

- “我 12 月 20 号考托福，目标 100 分，帮我做个计划”
- “出 10 道 Build a Sentence，先别给答案”
- “帮我改这封托福邮件：……”
- “来一套听力模考”
- “旧版 95 分相当于新版多少？”

### 脚本依赖

脚本只依赖 Python 3 标准库。`tts.py` 需要以下任一语音合成后端（都没有时会提示改用文字替代练习法）：

```bash
pip install edge-tts      # 推荐，需联网
pip install gTTS          # 需联网
# macOS 自带 say；Linux 可 apt install espeak-ng
# 多段对话拼接、插入停顿建议安装 ffmpeg
```

### 说明

- 练习题均为原创仿真题，不包含 ETS 官方试题。
- 评分标准是依据 ETS 公开评分思路整理的教练用估分标准，不代表官方评分。
- 新版考试的部分细节（题量、时长）因自适应而浮动，报名、费用等以 [ets.org](https://www.ets.org/toefl.html) 官方为准。
