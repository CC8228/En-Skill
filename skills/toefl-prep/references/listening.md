# Listening：出题规格、文字环境练习法与示例

## 目录
1. 文字环境下的听力练习（先读这个）
2. Listen and Choose a Response
3. Listen to a Conversation
4. Listen to an Announcement
5. Listen to an Academic Talk
6. 批改与讲解格式
7. 听力基本功训练

---

## 1. 文字环境下的听力练习

聊天里没有音频，处理方式按优先级：

1. **能运行脚本时生成音频。** 把听力原文写进文件后运行：
   ```bash
   python scripts/tts.py script.txt -o lecture        # 对话写成 "Student: ..." / "Professor: ..." 会自动换声音
   python scripts/tts.py script.txt -o lecture --slow # 慢速版，用于精听/听写
   ```
   成功则把音频文件发给用户，题目单独给出，**不展示原文**。批改完再给原文。
2. **不能生成音频时，用“两步法”：**
   - 第一条消息只给原文，并提示：“请用手机朗读功能（iOS 设置→辅助功能→朗读内容；安卓 TTS）或请同伴读给你听；实在不行就按正常语速只读一遍，读完不要回看，回复‘好了’。”
   - 用户回复后，第二条消息才给题目。这样用户没法边看原文边找答案。
   - 告诉用户这是替代方案，正式听力训练建议配合 ETS 官方样题和模考音频。
3. 精听训练（听写、跟读）用文字稿没有问题，可以直接给。

---

## 2. Listen and Choose a Response

### 出题规格
- 一句话（5–15 词）：问题、请求、邀请、抱怨、提议、陈述某个情况。场景：校园、宿舍、餐厅、办公室、课堂、朋友之间。
- 4 个书面选项，只有一个自然得体。干扰项设计：
  - **近音/同词陷阱：** 选项重复原句里的词，但答非所问（问 "Did you sign up for the trip?" 选项 "The sign is up there."）
  - **话题相关但功能错：** 对邀请回应成对事实的描述
  - **时态/人称不搭**
  - 正确答案常常是**间接回答**（"Did you finish the reading?" → "I'm still on chapter two."）
- 一组 6–8 题，难度从直接回应到间接/语用回应递进。

### 技巧
- 先判断句子的“功能”：问信息？请求帮忙？提建议？抱怨？再找对应功能的回应。
- 和原句重复词最多的选项往往是陷阱。
- 间接回答是常态，不要只找 yes/no。

### 示例
（原文）Woman: "Would you mind if I borrowed your notes from Tuesday's lecture?"
- (A) Yes, the lecture was on Tuesday.
- (B) Sure, I'll bring them to the library this afternoon.
- (C) I noted that the room was changed.
- (D) No, I didn't mind the lecture.

答案 B。注意 "Would you mind…?" 同意时常回答 "Sure / Not at all / Go ahead"；A、C、D 都在重复原句里的词。

---

## 3. Listen to a Conversation

### 出题规格
- 两人对话，约 100–200 词（约 40–80 秒）。常见组合：学生 + 学生、学生 + 职员（宿舍、图书馆、注册处、食堂、就业中心）、学生 + 教授（办公时间）。
- 结构：提出问题/需求 → 讨论选项 → 决定或下一步。
- 2 题：目的/主要问题 1 题 + 细节、态度或下一步行动 1 题。
- 用 "Speaker: text" 格式写，方便 `tts.py` 自动分配声音。

### 示例
```
Student: Hi, I'm trying to register for Biology 210, but the system says the class is full.
Advisor: Let me check. Yes, it filled up yesterday. There's a waitlist, though, and people usually drop during the first week.
Student: The problem is that I need it this semester to stay on track for my major.
Advisor: In that case, email the professor directly. Professors can approve a few extra students if there's lab space. Mention your major and your planned graduation date.
Student: Okay, I'll do that today. Should I still join the waitlist?
Advisor: Definitely. Do both.
```
1. What is the student's problem? → 想选的课已满
2. What will the student probably do next? → 给教授发邮件并加入候补名单

---

## 4. Listen to an Announcement

### 出题规格
- 一人播报，约 80–150 词：课堂上教授宣布作业/考试变更、校园广播活动通知、设施临时关闭、讲座嘉宾介绍。
- 必含：发生了什么变化、原因（可选）、听众需要做什么、时间节点。
- 2 题：目的 + 听众需要做的事 / 某个细节。

### 示例
（原文）"Before you leave, a quick change to the schedule. The field trip to the wetlands that was planned for this Saturday is moving to next Saturday, because heavy rain is expected this weekend. The bus will still leave from the science building at 8 a.m. If the new date doesn't work for you, send me an email by Wednesday so I can arrange an alternative assignment."
1. Why did the professor make the announcement? → 实地考察改期
2. What should students do if they can't attend on the new date? → 周三前给教授发邮件

---

## 5. Listen to an Academic Talk

### 出题规格
- 教授讲解，约 200–350 词（约 1.5–3 分钟），可以有一两次学生插话提问。入门课程话题，讲解一个概念 + 例子，或比较两种理论。
- 口语特征要保留：Okay, so… / Now, here's the interesting part… / You might be wondering… 自然的重复和自我修正。
- 4 题：主旨 1 + 细节 1–2 + “讲者为什么提到 X” 或讲者态度 1。

### 技巧
- 笔记只记结构：主题 → 要点 1/2 → 例子 → 讲者态度。不要逐字记。
- 信号词提示考点："The key point is…", "What's surprising is…", "But here's the problem…", "For example…"
- 讲者语气（actually, of course, I'm not convinced…）常是态度题的依据。

### 示例开头（完整题目按规格扩写）
"Okay, so last time we talked about how bees communicate the location of food. Today I want to look at a different question: how do bees decide where to build a new nest? This is actually a group decision, and it's surprisingly democratic…"

---

## 6. 批改与讲解格式

```markdown
**得分：x/y**

| 题号 | 你的答案 | 正确答案 | 题型 | 错因 |
|---|---|---|---|---|

**关键原句**（批改后给出原文中对应的句子，标出信号词）
**错因归类：** 没听到 / 听到但没理解 / 理解了但被干扰项带偏 / 词汇不认识
**下一步：** 针对错因的 1 个练习（例如“把第 2 段原文做一遍听写”）
```

---

## 7. 听力基本功训练

- **精听听写（每天 10–15 分钟）：** 一段 30–60 秒的音频，逐句听写 → 对照原文 → 标出没听出的原因（连读、弱读、生词、语速）。
- **跟读 shadowing：** 和音频同步或稍慢跟读，同时提升听力和 Listen and Repeat。
- **生活场景口语积累：** 校园对话里的高频表达（I'm swamped / It slipped my mind / I'm on the waitlist / Can I get an extension?）比学术词更容易在 Choose a Response 里失分。
- **泛听素材：** 大学公开课入门讲座、校园类播客、学校官方 YouTube 频道的校园介绍视频。
