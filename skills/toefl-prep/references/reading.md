# Reading：出题规格、技巧与示例

## 目录
1. Complete the Words
2. Read in Daily Life
3. Read an Academic Passage
4. 批改与讲解格式
5. 阅读基本功训练

---

## 1. Complete the Words

### 出题规格
1. 先原创一段 **70–100 词**的学术性短文：一个清楚的主题（生物、地质、天文、考古、心理、经济、艺术史等入门知识），4–6 句，句子结构自然，避免专有名词扎堆（脚本会跳过大写词，专有名词太多会让空位分布变得很怪）。
2. 用脚本生成挖空，不要自己手挖：
   ```bash
   python scripts/c_test.py make passage.txt --key-out key.json
   ```
   脚本保证：首句（三句以上时还有尾句）完整；从第二句第二个词开始每隔一个词挖掉后半部分；每条下划线正好对应一个缺失字母。
3. 把脚本输出的「题目」部分发给用户，「答案」部分留到批改时再用。
4. 批改：`python scripts/c_test.py check key.json "ght at ople ly ..."`（用户给完整单词或只给缺失字母都可以）。
5. 难度调节：
   - 易：日常学术话题、高频词为主（B1–B2）
   - 中：一般学术词汇（AWL 词表常见词）
   - 难：较抽象话题、更多派生词（-tion, -ity, -ive）和长单词

### 解题技巧（讲解时按需引用）
- 先通读全段抓主题，再填空：上下文决定词性和形式。
- 看空前后的语法线索：冠词后接名词；助动词后接动词原形；主语单复数决定 -s；前后时态一致。
- 已给出的字母和下划线数量是硬约束，先在脑中列候选词，再用长度筛。
- 功能词（that, with, their, which, about）常被挖空，送分题别丢。
- 拼写必须完全正确，复数、过去式、双写辅音（planned, occurred）是常见失分点。

### 示例

> Many early farming communities depended on a small number of crops. We mi\_\_\_[1] think th\_\_[2] prehistoric peo\_\_\_[3] concentrated on\_\_[4] on ba\_\_\_[5] survival, b\_\_[6] archaeological evid\_\_\_\_[7] suggests othe\_\_\_\_\_[8]. In sev\_\_\_\_[9] regions, peo\_\_\_[10] built storage pits and traded surplus grain with neighboring groups. These exchanges helped spread new tools and planting techniques across large areas. Over time, such networks laid the foundation for the first towns.

答案：might, that, people, only, basic, but, evidence, otherwise, several, people

---

## 2. Read in Daily Life

### 出题规格
- 文本类型轮换：校园通知、宿舍/图书馆规定、教授或职员的邮件、活动海报、菜单/价目表、课程日程表、二手交易帖、APP 推送、短信对话。
- 长度 15–150 词，保留真实格式（标题、时间地点、要点列表、署名）。
- 每篇 2–3 题，4 个选项。题型组合：
  - 目的题：What is the main purpose of the notice?
  - 细节题：According to the email, what must students bring?
  - 推断题：What can be inferred about the event? / What will the reader most likely do next?
  - 词义题：The word "waived" in line 3 is closest in meaning to …
- 干扰项设计：
  - 文本中出现过但答非所问的信息
  - 把时间、地点、条件张冠李戴
  - 过度推断（文本没说到那个程度）
  - 与常识相符但文本没提

### 技巧
- 先看文本类型和标题，预判目的（通知变更？请求？推销？）。
- 细节题回原文定位数字、日期、条件词（only, unless, at least, no later than）。
- 推断题的正确答案通常是原文信息“换个说法”，不会离原文太远。

### 示例

> **Riverside Hall – Laundry Room Update**
> Starting Monday, March 9, the laundry room will accept card payments only. Coins will no longer work in any machine. You can add money to your student ID card at the front desk or through the CampusPay app. Questions? Contact Dana Lee, Residence Coordinator, at ext. 4421.

1. What is the main purpose of the notice?
   (A) To announce new laundry room hours
   (B) To explain a change in how residents pay for laundry
   (C) To ask residents to report broken machines
   (D) To introduce a new residence coordinator
2. What can be inferred about residents who only have coins?
   (A) They can use the machines until the end of March.
   (B) They must exchange coins at the CampusPay office.
   (C) They will need to add money to their ID cards before doing laundry.
   (D) They should contact Dana Lee for a refund.

答案：1-B（A 时间没变；C、D 文中没提这个目的）；2-C（coins will no longer work + 可以充值到学生卡；A 与 Starting Monday 矛盾；B 文中没有“兑换硬币”；D 联系人是用于“有问题”，没说退款）。

---

## 3. Read an Academic Passage

### 出题规格
- 约 **180–230 词**，1–3 段，大学入门课程话题。结构常见：现象 → 解释/理论 → 证据或争议。
- 每篇 5 题，从以下题型中选，保证至少有 1 道推断或目的题：
  - 事实细节（According to the passage, …）
  - 否定事实（All of the following are mentioned EXCEPT …）
  - 词汇（The word "X" is closest in meaning to …）——选一个有多义、需要语境判断的词
  - 推断（What can be inferred about …）
  - 目的（Why does the author mention …）
  - 主旨（What is the passage mainly about?）
- 干扰项：偷换主语/因果、把“部分”说成“全部”、原文出现过的词拼接成错误意思、与常识相符但原文没说。
- 难度调节：易 = 话题具体、句子短；难 = 抽象概念、多重从句、作者对理论有保留态度。

### 技巧
- 先读第一句和每段首句抓结构，再看题。
- 词汇题把四个选项代回原句，看哪个保持原意；不要只凭“认识这个词”选。
- 目的题问“为什么提到 X”，答案是 X 在论证中的作用（举例支持、对比、反驳），不是 X 本身的内容。
- 绝对化选项（always, never, all, only）要警惕，除非原文同样绝对。

### 示例

> Bioluminescence, the production of light by living organisms, is surprisingly common in the deep ocean, where sunlight never reaches. In one large survey, roughly three quarters of the animals that researchers observed in deep water were able to produce their own light. The light usually results from a chemical reaction in which an enzyme, luciferase, causes a molecule called luciferin to release energy as light. Its functions vary widely. Some anglerfish dangle a glowing lure to attract prey, while certain shrimp release clouds of glowing fluid to confuse predators. A more subtle strategy, known as counterillumination, allows animals to match the faint light coming from above so that their silhouettes disappear when seen from below. Although researchers have described these behaviors in detail, they still know relatively little about how bioluminescence first evolved, partly because the chemical systems involved differ greatly from one group of organisms to another.

1. The word "subtle" in the passage is closest in meaning to
   (A) indirect (B) rapid (C) dangerous (D) temporary
2. According to the passage, what happens in counterillumination?
   (A) Animals produce bright flashes to frighten predators.
   (B) Animals adjust their light so they are hard to see from below.
   (C) Animals use glowing lures to attract food.
   (D) Animals stop producing light when predators are near.
3. Why does the author mention "certain shrimp"?
   (A) To show that bioluminescence can be used for defense
   (B) To explain how luciferin is produced
   (C) To compare deep-sea and shallow-water animals
   (D) To argue that bioluminescence evolved only once
4. What can be inferred about the origins of bioluminescence?
   (A) They are well understood because of research on anglerfish.
   (B) They may have developed separately in different groups of organisms.
   (C) They depend on sunlight reaching the deep ocean.
   (D) They are unrelated to chemical reactions.
5. What is the passage mainly about?
   (A) The chemistry of luciferase
   (B) How deep-sea animals find food
   (C) The prevalence, uses, and unanswered questions of bioluminescence in the deep sea
   (D) Why sunlight cannot reach the deep ocean

答案：1-A，2-B，3-A，4-B（化学系统在不同类群间差异很大 → 可能各自独立演化），5-C。

---

## 4. 批改与讲解格式

```markdown
**得分：x/y**

| 题号 | 你的答案 | 正确答案 | 题型 | 错因 |
|---|---|---|---|---|
| 3 | C | A | 目的题 | 把 X 的内容当成作用 |

**逐题解析**（只详细讲错题；对的题一句话确认思路）
- 第 3 题：定位句 → 为什么 A 对 → C 错在哪

**本组最该改的一点：** ……
**下一组练习建议：** （例如“再来 2 篇目的题比例高的学术短文”）
```

Complete the Words 的错因分类：词汇不认识 / 认识但拼错 / 词形错误（单复数、时态、词性）/ 上下文理解错。

---

## 5. 阅读基本功训练

- **拼写听写：** 每天 20 个本周新词，看中文写英文或听音写词，专治 Complete the Words。
- **长难句拆分：** 每天 3 个学术长句，找主干 → 标从句 → 翻译，同时服务 Build a Sentence。
- **限时速读：** 200 词学术短文，2 分钟内读完并用一句英文概括主旨。
- **生活文本积累：** 收集真实的校园网站通知、学校邮件，熟悉 deadline, waive, refundable, mandatory, eligible, prior to 这类“生活学术词”。
