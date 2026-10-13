# 模考：在对话中运行整套或单 section 模考

## 目录
1. 开始前
2. 模考结构（对话版）
3. 自适应的模拟方式
4. 估分方法
5. 模考报告格式

---

## 1. 开始前

告诉用户三件事：
1. **计时靠用户自己：** 你无法计时。请用户准备计时器，每个部分结束时报告用时。
2. **听力没有真实音频：** 能运行 `scripts/tts.py` 就生成音频；否则用 `listening.md` 的“两步法”。
3. **估分仅供参考：** 原创题的难度和官方题有差异，估分是区间，用来找薄弱点，不是预测成绩。

问用户：做整套还是单个 section？整套建议分两次（Reading + Listening 一次，Writing + Speaking 一次），一次性在对话里做完太长。

---

## 2. 模考结构（对话版）

题量按真实考试缩减到适合对话的规模，题型比例保持一致。

| Section | 模块 1（所有人相同） | 模块 2（根据模块 1 选难/易） | 建议用时 |
|---|---|---|---|
| Reading | Complete the Words ×1 段（10 空）+ Daily Life ×2 篇 + Academic Passage ×1 篇 | Complete the Words ×1 段 + Daily Life ×1 篇 + Academic Passage ×1 篇 | 共约 25 分钟 |
| Listening | Choose a Response ×6 + Conversation ×1 + Announcement ×1 + Academic Talk ×1 | Choose a Response ×4 + Conversation ×1 + Academic Talk ×1 | 共约 25 分钟 |
| Writing | Build a Sentence ×10 → Write an Email ×1（7 分钟）→ Academic Discussion ×1（10 分钟） | — | 约 23 分钟 |
| Speaking | Listen and Repeat ×7 → Take an Interview ×4（每题 45 秒） | — | 约 8 分钟 |

**发题节奏：**
- Reading：一个模块的题一次发完，用户全部作答后再批改，并进入模块 2。
- Listening：每段音频（或两步法的原文）单独发，题目在用户“听完”后再发。
- Writing：Build a Sentence 一次发完；Email 和 Discussion 各单独发，提醒计时。
- Speaking：Listen and Repeat 一句一句发；Interview 一题一题发，用户录音后发文字稿（和录音时长）。

---

## 3. 自适应的模拟方式

Reading 和 Listening 模块 1 结束后：
- 正确率 ≥ 70% → 模块 2 用**难**版（更抽象的话题、更长的词、更多推断/目的题、更隐晦的回应）
- 正确率 < 70% → 模块 2 用**易**版

告诉用户进入了哪个模块，并说明：真实考试中进入难模块是拿高分的前提，所以模块 1 要稳。

---

## 4. 估分方法

这是粗略估计，报告中写成区间。

### Reading / Listening
按两个模块合计正确率和模块 2 难度：

| 合计正确率 | 模块 2 = 难 | 模块 2 = 易 |
|---|---|---|
| ≥ 90% | 5.5–6 | 4–4.5 |
| 75–89% | 5–5.5 | 3.5–4 |
| 60–74% | 4–4.5 | 3–3.5 |
| 45–59% | 3.5–4 | 2.5–3 |
| < 45% | 3 左右 | ≤ 2.5 |

### Writing
Build a Sentence 正确率 + Email 和 Discussion 的 0–5 任务分，参考 `writing.md` 的对照表综合判断：Build a Sentence 正确率 < 60% 时，整体下调约 0.5。

### Speaking
参考 `speaking.md` 的对照，并注明只基于文字稿，发音因素未计入。

### 总分
用 `python scripts/score_convert.py overall -r X -l X -s X -w X`（区间时分别用下限和上限算两次）。

---

## 5. 模考报告格式

```markdown
# 模考报告（日期）

## 估分
| | Reading | Listening | Writing | Speaking | 总分 |
|---|---|---|---|---|---|
| 本次估分 | x–x | x–x | x–x | x–x | x–x（约 xx–xx / 120） |
| 目标 | | | | | |

## 题型表现
| 题型 | 正确率/任务分 | 判断 |
|---|---|---|
| Complete the Words | 7/10 | 拼写失分 3 处 |
| … | | |

## 时间
（用户报告的各部分用时，是否超时、哪里卡住）

## 最该补的 3 个点
1. …（对应的练习方式和每周频次）

## 与上次模考对比
（如有历史记录）

## 下一步
（直接给出接下来一周的调整建议，或“回复‘开始’练第一个薄弱题型”）
```
