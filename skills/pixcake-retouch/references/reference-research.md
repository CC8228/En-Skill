# 找参考、学博主的修片思路

目标：找到 2–5 张和用户照片**题材相同、光线相近**的博主作品，拆出博主稳定使用的处理手法，再落到用户照片上。参考选错（拿金色时刻的图去参考阴天正午的照片），后面参数再准也修不出来。

## 1. 先确认能不能直接看 Instagram

- 用 WebFetch 试一次博主主页或标签页（`https://www.instagram.com/<账号>/`、`https://www.instagram.com/explore/tags/<标签>/`）。
- Instagram 大部分内容需要登录，也经常拒绝自动访问；运行环境的网络策略也可能直接不放行。访问失败或只拿到登录页时，**直接告诉用户看不到**，不要假装浏览过、不要描述没看到的图。
- WebSearch 一般搜不到 IG 帖子本身，但能搜到关于博主的文章、采访、教程和预设说明，这些是了解博主修图思路的正当来源，引用时附链接。

## 2. 截图流程（最可靠）

告诉用户：

1. 在 IG 里按下面的标签或博主去找，挑 2–5 张**同题材、同类光线**的图（例如都是阴天户外人像）。
2. 截图发过来；能只截照片区域最好，带了 IG 界面也没关系，你来裁。
3. 一张图只能看出“这张怎么修的”，多张图才能看出“这个博主怎么修”。

收到截图后：

```bash
# 截图带界面时先裁（比例：左,上,右,下），裁好的 *_preview.jpg 当参考图用
python3 scripts/analyze_raw.py ref1.png --crop 0,0.13,1,0.75 --out <目录>
# 原片 vs 参考
python3 scripts/compare_ref.py <原片> <目录>/ref1_preview.jpg <目录>/ref2_preview.jpg
```

裁剪比例先 Read 截图估计照片区域的上下边界；裁完 Read 一下 `_preview.jpg` 确认界面已经去掉。

## 3. 按风格给搜索方向

给用户 1–2 个方向的标签和博主即可，不要一次列一大堆。

| 风格 | 推荐 hashtag | 可以看的摄影师（风格倾向） |
|---|---|---|
| 日系清新 / 空气感 | #ポートレート #写真好きな人と繋がりたい #japaneseportrait #airyphotography | 濱田英明 Hideaki Hamada（@hamadahideaki，柔和自然光、低对比的家庭和儿童） |
| 日本街头 / 人文 | #tokyostreet #streetsnap #ファインダー越しの私の世界 | Takashi Yasui（@_tuck4，沉静低调的日本日常与街景） |
| 胶片感 | #portra400 #kodakportra #filmisnotdead #35mmfilm #shootfilm | 搜 “portra 400 portrait” 找真胶片作品当参考 |
| 电影感 / 青橙 | #cinematicphotography #moodygrams #tealandorange #cinestill800t | — |
| 暗调情绪 | #moodyportrait #lowkeyphotography #darkmood | — |
| 城市夜景 / 赛博 | #tokyonight #neonlights #cyberpunkphotography #nightphotography | Liam Wong（作品集 TO:KY:OO，青/洋红夜景） |
| 夜景人像 / 灯串光斑 | #fairylights #bokehportrait | Brandon Woelfel（黑位压深、阴影偏蓝、粉蓝配色） |
| 港风 | #hongkongstyle #hkig #wongkarwai #cinestill | — |
| 冷调风光 | #icelandtravel #moodylandscape #arcticphotography | Benjamin Hardman（@benjaminhardman，冰岛、北极，冷蓝低饱和） |
| 暖调风光 / 金色时刻 | #goldenhour #landscapephotography #sunsetlovers | — |
| 黑白 | #bnw #blackandwhitephotography #monochrome | — |
| 韩系 / 奶油 | #감성사진 #인물사진 #creamytones | — |
| 街拍 | #streetphotography #streetphotographyinternational #lensculture | — |

账号来自公开报道和资料，**可能改名或停更**，推荐时请用户以 IG 实际搜索结果为准；标“—”的直接用标签搜。用户有自己关注的博主时优先用用户的。

## 4. 用户只给了博主名字

1. WebSearch：`<博主名> editing style lightroom`、`<博主名> interview editing`、`<博主名> 修图 教程`、`<博主名> preset`。
2. 找到博主本人或可靠媒体讲过的做法（例如“曲线压深黑位、阴影加蓝”）就引用，并附来源链接。
3. 找不到时说明“下面是基于这类风格的一般做法，不是这位博主公开的参数”，同时请用户发截图。
4. 不要编造博主的具体数值。

## 5. 拆解博主思路（看参考图时逐项过）

| 维度 | 看什么 |
|---|---|
| 影调 | 整体亮还是暗；黑位死黑还是发灰（哑光）；最亮处纯白还是被压住；光比大还是小 |
| 配色 | 画面只保留哪两三种颜色；哪些颜色被压掉（常见：绿色降饱和偏黄或偏青，蓝色偏青） |
| 冷暖关系 | 阴影和高光是不是不同颜色（分离色调）；整体偏冷还是偏暖 |
| 肤色 | 偏粉、偏橙、偏黄还是偏白；通透还是浓郁 |
| 局部 | 主体有没有被提亮；背景有没有压暗或降饱和；有没有暗角、光晕 |
| 质感 | 颗粒、锐度、柔焦/辉光、磨皮程度（截图压缩后只能目测） |
| 一致性 | 几张图共同的处理 = 博主的风格签名；只有一张有的处理多半来自场景 |

写给用户的“博主思路”控制在 3–5 句，例如：

> 这几张的共同点：黑位都抬到发灰（哑光），高光被压住不到纯白；绿色全部偏黄、饱和度很低，画面基本只剩暖肤色和米白；阴影带一点青，高光偏暖。光线上她偏爱阴天或背光的柔光，所以脸上没有硬阴影——你的照片是晴天侧光，光比更大，影调上要多压高光、多提阴影才接近。

## 6. 参考图和原片差距太大时

- 光线完全不同（硬光 vs 柔光、白天 vs 夜晚）：后期只能接近色调，光比和光的方向追不上，提前说明。
- 场景内容差异大（参考图大片天空，原片没有天空）：`compare_ref.py` 的白平衡、HSL 数值参考性下降，以肉眼判断为主。
- 用户的照片更适合另一种风格时，可以直说并给出替代方向，由用户决定。
