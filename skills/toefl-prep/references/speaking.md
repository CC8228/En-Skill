# Speaking：出题规格、评分、反馈与训练

## 目录
1. Listen and Repeat
2. Take an Interview
3. 评分标准
4. 反馈格式（文字稿批改）
5. 发音与流利度自查（中国考生高频问题）
6. 日常训练

---

## 1. Listen and Repeat

### 出题规格
- 一个具体场景，由一个“角色”说出 7 句话，例如：校园导览员介绍图书馆、实验室助理讲安全规则、博物馆讲解员介绍展品、新生指导员介绍报到流程。
- 句子长度递进：第 1–2 句 5–8 词，第 3–5 句 9–14 词，第 6–7 句 15–20 词以上。
- 句子要自然、口语化，包含复述时容易丢的细节：冠词、介词、复数 -s、过去式 -ed、数字和时间。
- 可以用 `scripts/tts.py`（每句一行）生成音频。没有音频时：每次只给一句，请用户读一遍后遮住（或滚动隐藏）再复述录音，然后把**复述的文字稿**发回来对比。

### 示例（实验室助理）
1. Please wash your hands before you begin.
2. Goggles are kept in the cabinet by the door.
3. Never leave a burner on when you step away.
4. If you spill anything, tell me or another assistant right away.
5. All of the chemicals on the top shelf need to be signed out.
6. Before you leave, make sure your station is clean and the waste has been sorted into the correct bins.
7. Students who finish early can use the extra time to start writing the results section of their lab report.

### 批改方法
逐句对比原句和用户复述，标出：遗漏的词、替换的词、加多的词、词形错误（-s/-ed）。统计“完整复述”句数，并指出遗漏的规律（例如总是丢冠词和介词 → 说明在“抓实词”，需要练习功能词的弱读听辨）。

### 技巧
- 听的时候按意群切分（chunking）：Before you leave, / make sure your station is clean / and the waste has been sorted / into the correct bins.
- 复述时保持原句的节奏和语调，不要逐词念。
- 长句记不全时，优先保证句子结构完整、意思准确，不要停住不说。

---

## 2. Take an Interview

### 出题规格
- 设定一个采访者身份和主题：研究人员调查学生的科技使用 / 城市规划部门调研交通习惯 / 校报记者采访学习方式 / 健康研究调查作息。
- 4 个问题，难度递进：
  1. 个人经历或习惯（How often do you…? Tell me about a time…）
  2. 偏好或比较（Do you prefer… or…? Why?）
  3. 观点（Some people think… What's your view?）
  4. 更抽象或假设性的问题（How do you think this will change in the future? What would you recommend to…?）
- 每题 45 秒作答、无准备时间。出题时一次只给一个问题，模拟“无准备”；用户也可以要求一次给全。

### 回答结构（45 秒）
1. **直接回答**（1 句，约 5 秒）：别铺垫，第一句就回答问题。
2. **理由**（1–2 句）：为什么。
3. **具体例子**（2–3 句，约 20 秒）：个人经历或具体场景，有细节（时间、地点、发生了什么）。
4. **收尾**（1 句，可选）：回扣观点。时间到了没说完也没关系，内容展开比收尾重要。

### 示例
**问题：** Do you prefer studying alone or with other people? Why?

**参考回答（约 110 词，45 秒左右）：**
> I usually prefer studying alone, especially when I'm preparing for exams. The main reason is that I can control my own pace. For example, last semester I was taking a statistics course, and some topics, like probability, took me much longer than my classmates. When I studied in a group, I felt like I had to keep up with everyone, so I would nod along even when I didn't really understand. When I started studying by myself in the library, I could spend an extra hour on the hard parts and skip what I already knew. My grades actually went up. That said, I still think group study is useful for reviewing right before a test.

---

## 3. 评分标准

这是依据 ETS 公开评分思路整理的教练用标准，用来给出**估计分**，不是官方评分。

### Take an Interview（0–5）
| 分数 | 描述 |
|---|---|
| **5** | 切题且展开充分，有具体例子；连贯自然；语法和用词准确多样；发音清晰、语速自然，几乎不影响理解。 |
| **4** | 切题，展开较好但有一处略单薄；整体连贯；有少量语言错误或发音问题，不影响理解。 |
| **3** | 基本切题但展开有限（理由泛泛、无例子或例子模糊）；有明显停顿或语言错误，偶尔需要听者费力理解。 |
| **2** | 内容很少或部分离题；语言错误频繁，表达受限；发音问题较多地影响理解。 |
| **1** | 只有零星相关内容，大部分难以理解。 |
| **0** | 未作答或完全离题。 |

### Listen and Repeat
按复述准确度估计：7 句中完整准确复述 6–7 句 → 强；4–5 句 → 中；≤ 3 句 → 需要重点训练。短句全对、长句丢词是常见模式。

**任务表现 → Speaking band 粗略参考：** Interview 平均 4.5+ 且复述 6–7 句准确 → 约 5.5–6；Interview 4 左右、复述 5 句 → 约 4.5–5；Interview 3 左右、复述 3–4 句 → 约 3.5–4。

---

## 4. 反馈格式（文字稿批改）

先跑 `python scripts/text_stats.py answer.txt --task interview --seconds 45`（有实际时长就用实际时长）。

```markdown
## 估分：x / 5（仅基于文字稿）
字数 N｜语速约 N 词/分钟

> 文字稿看不出发音、语调和停顿。请对照下面的「自查清单」回听自己的录音。

### 内容与结构
- 第一句是否直接回答问题：是 / 否
- 是否有具体例子：是 / 否（例子够不够具体）
- 45 秒内是否讲到了例子

### 最优先改进的 3 点
1. …（附改写示例）

### 逐句修改
| 原句 | 修改后 | 说明 |
|---|---|---|

### 升级版回答
（保留用户的观点和例子，控制在 100–120 词，用户可以拿来跟读练习）

### 下一步
- 例如：“用升级版跟读 3 遍，然后不看稿重新录一次同一题，再发给我”
```

如果用户发来的文字稿是语音转写的，转写错误（同音词错）不要算成语法错误，看不准时问用户。

---

## 5. 发音与流利度自查（中国考生高频问题）

请用户回听录音，逐条打勾：
- [ ] **词尾辅音**：good, need, back 结尾的 d/k 是否吞掉，或者加了元音（good-uh）
- [ ] **-s / -ed 词尾**：books, studied, finished 是否发出来
- [ ] **th 音**：think 不读成 sink/fink，this 不读成 dis/zis
- [ ] **v / w**：very 和 wary 是否区分
- [ ] **l / n**（部分方言区）：light 和 night 是否区分
- [ ] **长短元音**：ship/sheep、full/fool
- [ ] **单词重音**：deVElop, PHOtograph, phoTOgraphy
- [ ] **语调**：陈述句句末下降，不是每个词一样平
- [ ] **停顿位置**：在意群之间停，不在冠词或介词后面停
- [ ] **填充词**：um/uh 过多时，用 "Well," "Let me think—" "The main reason is…" 替代

---

## 6. 日常训练

- **跟读（每天 10 分钟）：** 选 1 段 30–60 秒的自然语速音频，先听 → 看稿跟读 → 不看稿跟读 → 录音对比。
- **复述练习：** 由短到长复述句子，每天 10 句，专门练长句不丢词。
- **45 秒限时：** 每天 2 道 Interview 题，计时录音，转写后让教练批改。同一题改完后重录一次，比换新题更有效。
- **话题素材库：** 准备 8–10 个可复用的个人经历（学习、科技、社团、旅行、兼职、家庭、健康、城市生活），用英文写成 3–4 句的小故事，答题时灵活调用。
