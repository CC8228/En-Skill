# En-Skill

自用的 Claude Skills：英语考试备考、修图助理。

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

## pixcake-retouch：修片助理（像素蛋糕）

`skills/pixcake-retouch/` 是一个修片助理 skill：你把 RAW（或 JPEG）照片给 Claude，它诊断照片、找参考并拆解博主的修片思路，然后按像素蛋糕（PixCake）的面板顺序告诉你怎么调。**不直接出图**，你在像素蛋糕里照着操作。

### 能做什么

| 功能 | 说明 |
|---|---|
| 照片诊断 | 题材、光线、主色、九种影调、RAW 高光溢出与暗部噪点风险、偏色、分离色调、HSL 分布、暗角 |
| 找参考 | 按风格给 IG hashtag 和摄影师方向；能访问就直接看，访问不到就用你发的截图 |
| 拆博主思路 | 多张参考图的共同处理 = 博主的风格签名（影调、配色、冷暖、局部、质感） |
| 量化对比 | 原片 vs 参考图：曝光、对比、黑白位（换算成曲线 0–255）、白平衡、颜色分级、HSL、肤色、暗角的起步值 |
| 修图方案 | 面板 → 滑块 → 起步值 → 判断标准，按像素蛋糕操作顺序 |
| 复盘微调 | 修完的导出图再和参考对比，给 3–5 条微调 |
| 参数换算 | Lightroom 参数 → 像素蛋糕面板名 |

### 目录结构

```
skills/pixcake-retouch/
├── SKILL.md                       # 入口：原则、工作流、能力边界
├── references/
│   ├── photo-analysis.md          # 诊断清单、报告解读、九种影调
│   ├── reference-research.md      # 找参考、截图流程、hashtag/摄影师、拆解博主思路
│   ├── photographers-jp.md        # 日系人像 15 位、风景 10 位摄影师及 IG 账号
│   ├── style-recipes.md           # 12 种常见风格的像素蛋糕配方
│   └── pixcake-panels.md          # 面板对照、操作顺序、滑块含义、曲线/色轮/HSL 方向、LR 换算
├── scripts/
│   ├── analyze_raw.py             # 单张诊断，输出预览图、分析图和中文报告
│   ├── compare_ref.py             # 原片 vs 参考图，输出差异表和起步值
│   └── photo_stats.py             # 共用的读取与计算代码
├── assets/
│   └── edit-plan-template.md      # 修图方案输出模板
└── evals/evals.json               # 测试用例
```

### 使用示例

- “这是我昨天拍的 RAW，帮我看看适合修成什么风格”
- “这两张是 ins 上的参考截图，按这个感觉修我的照片”
- “想修成胶片感 / 日系清新 / 电影感青橙 / 港风，像素蛋糕里怎么调？”
- “博主给的 Lightroom 参数，在像素蛋糕里怎么对应？”
- “我调完了，跟参考比还差点，帮我看看差在哪”

### 脚本依赖

```bash
pip install rawpy exifread numpy pillow
```

`rawpy`（LibRaw）负责读 RAW，`exifread` 读拍摄参数；只分析 JPEG/PNG 时只需要 numpy 和 Pillow。

### 说明

- Instagram 需要登录且常拒绝自动访问，Claude 看不到时会直说，改用你发的截图；不会编造博主作品或参数。
- 脚本给的是统计反推的起步值，受画面内容影响（例如大片天空），方案里会和肉眼判断对照取舍。
- 像素蛋糕版本更新快，面板名称以你的界面为准。
