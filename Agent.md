# Agent.md

给后续维护这个博客的 Agent 的交接文档。

**这个站点主要由 Agent 维护**，所以这里记录的不是「介绍」，而是**踩过的坑、做过的取舍、以及改哪里会炸**。动手前请先读完「首要陷阱」和「已知陷阱」两节。

---

## 1. 项目概览

| 项 | 值 |
|---|---|
| 类型 | Hugo 静态博客 |
| 主题 | PaperMod **已内置在仓库里**（不再是 submodule），上游 commit `d376885` |
| Hugo | `v0.166.0+extended+withdeploy`（Homebrew / macOS arm64） |
| 站点目录 | 仓库根目录（`hugo.yaml` 在根） |
| 线上域名 | `blog.lvxinrong.com`（`hugo.yaml` 的 `baseURL`）—— 尚未部署，参见第 11 节 |
| 语言 | 简体中文（`zh-CN`），单语言 |

内容分三个系列：`llm`（手搓 LLM）、`ai`（AI 随想）、`craft`（工程手记）。

---

## 2. 常用命令

```bash
# 本地预览。--renderToMemory 是必须的，原因见第 3 节（本文件最重要的一节）
hugo server --port 1313 --bind 127.0.0.1 --renderToMemory

# 生产构建（产物在 public/，已 gitignore）
hugo

# 检查构建是否有警告／错误（不要加 --quiet，它会吞掉错误）
hugo 2>&1 | grep -iE "warn|error"
```

**不要用 `--quiet`**：本项目曾因为 `hugo --quiet` 隐藏了一个模板错误，导致误判了整整一轮。

在受限沙箱里 `hugo --gc` 会报 `failed to prune cache "modulequeries"` —— 那是 Hugo 想写 `~/Library/Caches/hugo_cache` 被拦，**与站点无关，可以忽略**，或者干脆不用 `--gc`。

---

## 3. ⚠️ 最重要的一条纪律：dev server 必须加 `--renderToMemory`

**这是本项目出过的最严重的 bug，务必遵守。**

`hugo server` 默认会**把渲染结果写到 `public/` 并从磁盘读**（官方帮助原文：*"will by default write and serve files from disk"*）。而 `public/` 同时也是生产构建的输出目录。于是：

> 只要 dev server 在跑，你同时又执行了生产构建 `hugo`，`public/` 就会被覆盖成「所有链接都指向线上域名的 HTML」，dev server 会把这些文件原样吐给浏览器。

症状：本地 `localhost:1313` 能打开，但点任何文章都跳到线上域名 → 「无法访问此网站」。当时排查确认过：端口返回的 HTML 与 `public/index.html` **逐字节相同**。

### 规则

```bash
# ✅ 本地预览一律这么起
hugo server --port 1313 --bind 127.0.0.1 --renderToMemory

# ❌ 不要这样起（会写 public/ 并从中读取）
hugo server
```

`--renderToMemory` 让 dev server 完全不落盘，`public/` 就归生产构建独占了。**已验证**：dev server 跑着的时候执行生产构建，dev server 仍正常返回 localhost 链接。

### 为什么不用「配置隔离」这个更省事的方案

曾经试过一个自动方案：用 `config/development/hugo.yaml` 把开发环境的 `publishDir` 改到 `.dev-output/`，这样不加 flag 也不会冲突。**已回退**，原因是**线上安全**：

这个方案依赖 Hugo 的**环境隔离**能力，而 Hugo 历史上出过「命令把所有环境配置都应用一遍」的隔离缺陷（[gohugoio/hugo#14763](https://github.com/gohugoio/hugo/issues/14763)，后续修复提交 `1eea9fb`、`2bbc865`）。**若线上云构建用的 Hugo 版本仍有该缺陷**，`.dev-output` 会被误用到生产 → 产物不落在 Cloudflare 期望的 `public/` → **部署失败**。

本站在 Cloudflare Pages 上是**连 Git 自动构建**的，仓库里的配置会直接决定线上构建行为，所以选择「不改任何生产会读到的配置」。

**因此：`hugo.yaml` 里不要设置 `publishDir`，也不要新增 `config/` 目录。** 一旦引入环境相关的输出目录差异，就等于把线上的部署成功率押在云端的 Hugo 版本上。

> 如果哪天确实需要环境差异配置，先在 Cloudflare 固定 `HUGO_VERSION` 与本地一致，再考虑。

### 备忘：忘了加 flag 会怎样

Bug 复现需要两个条件同时成立：**dev server 正在运行** + **期间执行了生产构建 `hugo`**。只跑 `hugo server` 不跑生产构建是没事的，反之亦然。最容易被触发的是：「开着预览，另开一个终端构建验证」。


## 4. 目录结构

```
hugo.yaml                  全站配置（不要在 config/ 里放环境差异配置，见第 3 节）
content/
  {llm,ai,craft}/          三个系列，**每个必须有自己的 _index.md**
  {tags,categories}/_index.md   中文标题（否则会渲染成英文复数）
  about.md  archives.md
assets/css/extended/
  custom.css               全部自定义样式（唯一一个文件，16 个小节）
layouts/                   9 个主题覆盖文件（见下）
static/                    favicon 全套
public/                    构建产物，gitignore
themes/PaperMod/           主题源码（已内置，见第 5.3 节；改动优先写在站点 layouts/）
```

### 内容约定

- **新增系列**：建 `content/<名字>/`，里面放 `_index.md`（带 `title`、`description`），再把名字加进 `hugo.yaml` 的 `params.mainSections`。首页卡片、系列配色、归档页都跟着这个列表走。
- **不建 `_index.md` 会出事**：Hugo 会拿目录名自动衍生成英文复数标题（`llm` → "Llms"）。这个坑踩过一次。
- 文章用 `#` 或 `##` 作章节标题（`markup.tableOfContents.startLevel: 1` 才能抓到）。

### ⚠️ 文章 `date` 写在未来 → 会静默消失

Hugo 默认 **不构建 `date` 在未来的页面**（`buildFuture: false`）。症状很迷惑：**文章不报错、不提示，就是哪儿都不出现** —— 列表页、归档、RSS 全都没有。

新写文章时如果把 `date` 设成了「几分钟后」（比如手写一个整点时间），在那一刻到来之前它就是不存在的。

```bash
# 想立刻看到，本地可以加这个 flag
hugo server --renderToMemory --buildFuture
```

排查：对比文件里的 `date` 和当前时间。

```bash
date "+%Y-%m-%dT%H:%M:%S%z"
grep -m1 '^date' content/xxx.md
```

### ⚠️ `panic: Shift: unknown type *hugolib.pageMetaSource`

见过一次：dev server 直接崩溃退出。**这不是模板或样式的问题。**

它是 Hugo 自身的一个 bug（0.166 实测），触发条件是**文件正在被写入时被 dev server 读到** —— 日志里会先出现一条内容解析错误（例如 `unmarshal failed: toml: expected newline`），紧接着就是 panic。

处理方式：确认文件内容已保存完整，然后**重启 dev server** 即可。不需要改任何模板。

### ⚠️ 中文写作陷阱：`**加粗**` 在中文标点后会失效

CommonMark 有一条 **flanking（侧翼）规则**：闭合的 `**` 必须满足 right-flanking —— 不能「前一个字符是标点、后一个字符既不是空白也不是标点」。

而中文标点（`。，、；：？！` 等）在 Unicode 里属于 `P*` 类别，**是标点**。于是：

```text
❌ 我相信三件事：**好奇，毅力，自我思考。**它们跟代码无关
                                       ↑ 前是「。」(标点)，后是「它」(文字) → 闭合失败，** 原样显示
✅ 我相信三件事：**好奇，毅力，自我思考**。它们跟代码无关
                                       ↑ 前是「考」(文字) → 正常闭合
```

**规则：加粗片段若以中文标点结尾、且后面紧接中文字符，就把那个标点挪到 `**` 外面。**

以下写法都没问题（可作为替代）：

- 加粗在**行尾**结束：`**……。**` —— 行尾视同空白
- 闭合符**后面加空格**：`**……。** 它们`
- 闭合符**前面是文字**：`**……坑里**。`

**这不是 Hugo 的问题**，任何 CommonMark 实现（GitHub、Typora、Obsidian）行为都一致。

自查脚本（列出所有会渲染失败的加粗；本文档撰写时用它查出并修掉了 5 处 / 共 66 处）：

```bash
python3 - <<'EOF'
import re, glob, unicodedata
def is_punct(c): return bool(c) and unicodedata.category(c).startswith('P')
for f in sorted(glob.glob('content/**/*.md', recursive=True)):
    for ln, line in enumerate(open(f, encoding='utf-8'), 1):
        for m in re.finditer(r'\*\*(.+?)\*\*', line):
            inner = m.group(1); j = m.end()
            nxt = line[j] if j < len(line) else ''
            if inner and is_punct(inner[-1]) and nxt and not nxt.isspace() and not is_punct(nxt):
                print(f"{f}:{ln}  {m.group(0)[:50]}")
EOF
```

---

## 5. layouts/ 覆盖清单（9 个）

Hugo 里站点 `layouts/` 优先于主题，所以这些文件覆盖主题行为，**且主题升级不会冲掉**。代价是升级后不会自动获得更新。

### 5.1 「逐字复制 + 只改一处」型 —— 升级时需要 diff

| 文件 | 改了什么 | 为什么 |
|---|---|---|
| `baseof.html` | `dir` 由 `.Language.*Direction` 改成字面量 `"auto"` | 见下方「版本地雷」 |
| `rss.xml` | `<language>` 改用 `params.languageTag` | 同上 |
| `_partials/templates/opengraph.html` | `og:locale` 改用 `params.languageTag` | 同上 |

这三个存在的唯一原因是**修掉 Hugo 的弃用警告**，同时**不能引入版本特有的 API**。当时也考虑过直接改主题，但那时主题还是 submodule —— 改脏了会被 `git submodule update` 静默还原。

`opengraph.html`（86 行）风险最高：逻辑多、主题更新时改动概率也大。**升级主题后如果 OG 标签行为异常，优先查这个文件。**

### 💣 版本地雷：本地 Hugo 与 Cloudflare 不同版本

**这个坑真炸过一次，导致线上构建失败。**

- 本地：`v0.166.0`
- Cloudflare：`v0.147.7`

`.Language.LanguageDirection`（旧名）在 0.158 起弃用，改用它建议的 `.Language.Direction`（新名）在 0.166 正常，**但在 0.147.7 上直接致命报错**：

```
layouts/baseof.html:13:50: at <.Language.Direction>: can't evaluate field Direction in type *langs.Language
```

而且因为报错发生在 `baseof.html` 的 `<html>` 行（早于 `<head>`），`rss.xml` / `opengraph.html` 里同类写法**根本没机会执行**，看日志会以为只有一处有问题 —— 实际上三个文件都得改。

**规则：这几个模板里禁止出现任何跨版本改过名的 API**（`LanguageCode` / `Locale` / `Direction` / `LanguageDirection`）。需要语言标签就用 `params.languageTag`，需要方向就写字面量。

### 改模板后必须用 0.147.7 复测

```bash
cd /tmp && mkdir -p hugo147 && cd hugo147
curl -sSL -o h.tgz "https://github.com/gohugoio/hugo/releases/download/v0.147.7/hugo_extended_0.147.7_darwin-universal.tar.gz"
tar xzf h.tgz

cd /path/to/site
/tmp/hugo147/hugo --destination /tmp/out147 2>&1 | grep -iE "error|can't evaluate"
```

**零 ERROR 才算过。** 光在本地 0.166 上通过是不够的 —— 这正是上次翻车的原因。

> 更彻底的解法是在 Cloudflare 设 `HUGO_VERSION` 固定线上版本。但无论是否固定，上面的复测都值得做：Cloudflare 的默认版本会随其镜像更新而漂移。

### 5.2 定制型 —— 升级基本不影响

| 文件 | 作用 |
|---|---|
| `home.html` | 首页 = Hero + 系列入口卡 + 最新 6 篇。主题的 `list.html` 是把所有文章平铺，观感「三个系列混在一起」 |
| `archives.html` | 主题硬编码 `GroupByDate "January"`，中文站会显示英文月份。改成按 `2006-01` 分组（字典序即时间序）再渲染成「9 月」 |
| `404.html` | 主题只渲染一个光秃秃的 `404`，加了说明和回首页入口 |
| `_partials/footer.html` | 在版权行上方插入社交按钮。**注意 `extend_footer.html` 挂载点在 `</footer>` 之后，塞不进去，必须覆盖整个 partial** |
| `_partials/social_icons.html` | 主题只渲染裸图标，认不出是 GitHub。加了文字标签，支持 `variant: hero/footer` 两种尺寸 |
| `_partials/extend_footer.html` | 三件事：吸顶导航滚动分隔线、≥1280px 自动展开目录、按 URL 给分区页打系列标记 |

### 5.3 主题已内置（2026-09 起不再是 submodule）

**背景**：Cloudflare Pages 构建时反复拉取 submodule 失败：

```
Cloning into '/opt/buildhome/clone/themes/PaperMod'...
fatal: could not read Username for 'https://github.com': No such device or address
fatal: expected flush after ref listing
```

PaperMod 是**公开仓库**，不该需要认证。这是 GitHub 对**未认证请求限流/抖动**的表现 —— Cloudflare 构建机是共享出口 IP，容易撞上。本机同一时刻匿名克隆是成功的，说明不是权限配置问题。

**处理**：把主题 125 个文件直接内置进仓库，删除 `.gitmodules` 和 submodule 记录。构建因此完全不依赖外网拉子模块。

**升级主题的正确做法**：

```bash
# 1. 取一份上游新版本到临时目录
cd /tmp && rm -rf pm-new
git clone --depth 1 https://github.com/adityatelange/hugo-PaperMod.git pm-new

# 2. 先看差异，重点确认布局有没有变
diff -rq /tmp/pm-new themes/PaperMod | grep -v '^Only in /tmp/pm-new: .git'

# 3. 确认后整体替换（保留 LICENSE）
rm -rf themes/PaperMod && cp -R /tmp/pm-new themes/PaperMod
rm -rf themes/PaperMod/.git

# 4. 检查站点覆盖的 9 个 layouts/ 文件是否仍与新版主题兼容
hugo --destination /tmp/out && /tmp/hugo147/hugo --destination /tmp/out147
```

⚠️ **升级后必须跑第 4 步的两个版本构建**（见「版本地雷」一节）。

---

## 6. 配置决策（`hugo.yaml`）

改动前请理解这些「为什么」，很多是踩坑后才对的：

| 配置 | 值 | 为什么 |
|---|---|---|
| `defaultContentLanguage` | `zh-CN` | **原来的 `locale: zh-CN` 根本不是 Hugo 的键**，等于没写，所以中文站渲染出 `September 23, 2026` / `1 min` |
| `hasCJKLanguage` | `true` | 不开的话 Hugo 按空格数「词」，3543 字的长文算成 1 个词、阅读时长恒为 1 分钟 |
| `defaultTheme` + `disableThemeToggle` | `light` + `true` | **必须成对设置**：只设前者按钮还在；只设后者会退回「跟随系统」，系统深色时页面反而变暗 |
| `mainSections` | `llm / ai / craft` | 同时驱动首页系列卡、归档页、系列配色 |
| `markup.tableOfContents.startLevel` | `1` | 文章用 `#` 当章节标题，从 2 开始抓会得到空目录 |
| `params.DateFormat` | `2006年1月2日` | Go 时间布局写法 |
| `params.label.text` | `写代码，也写自己` | **只覆盖顶栏那行字**，不影响 `<title>` / RSS / 页脚（那些用 `site.Title`） |
| `homeInfoParams.Title` | `吕炘嵘` | 首页 Hero 大标题 |
| `pagination.pagerSize` | `10` | **首页已不分页**（自定义 `home.html` 只出最新 6 篇），这个值只影响分区列表 |

### 顶栏与 Hero 的分工（别放同一句话）

- **顶栏**（`params.label.text`）出现在**每一页**，是常驻标识 —— 承载「态度 / 标语」
- **Hero**（`homeInfoParams.Title`）只出现在**首页**，是开场 —— 承载「我是谁」

两者取值来自不同配置项，但**如果写成同一句话，首页会把它们上下紧挨着显示两遍**，看起来像渲染 bug（这个坑真出现过一次，见 `homeInfoParams` 附近的注释）。

`layouts/home.html` 里 Hero 的 `h1` 是**条件渲染**的：`Title` 为空时不输出 `<header>`，否则会留一个空标题，而 CSS 给 `.home-info h1` 加的强调色短线会变成一道孤零零的横杠。

### 已知配置问题

- `content/about.md` 会显示「1 分钟 · 48 字」——静态页显示阅读时长没意义。要关就在该文件的 front matter 加 `ShowReadingTime = false`（**没改，属于你的正文，等确认**）。

---

## 7. 样式系统

**所有自定义样式集中在 `assets/css/extended/custom.css` 一个文件。** PaperMod 会把 `assets/css/extended/*.css` 追加在主题样式之后，所以能覆盖主题、且主题升级不冲掉。前 16 个小节按功能划分。

### 设计变量（在文件顶部 `:root` / `:root[data-theme="dark"]`）

| 变量 | 作用 |
|---|---|
| `--accent` | 全站强调色（靛蓝） |
| `--glass-bg` / `--glass-filter` / `--glass-hi` / `--glass-line` | 玻璃材质四要素。**`--glass-hi`（顶部镜面高光）和 `--glass-line`（发丝线）比模糊半径更决定「像不像玻璃」，别省** |
| `--glow-1` / `--glow-2` / `--wash` | 背景色雾：顶部聚色 / 两侧留色 / 中心留白 |
| `--series-llm` / `-ai` / `-craft` | 三个系列的专属色 |
| `--main-width` | 版心宽度 `740px` —— **改它会连带影响侧栏目录定位，见陷阱 4** |
| `--footer-height` | 必须等于页脚真实高度，见陷阱 3 |

### 深色模式样式仍在文件里

`defaultTheme: light` + `disableThemeToggle: true` 之后，`:root[data-theme="dark"]` 这些块**永远不会匹配，不生效也没有开销**。保留是为了以后想恢复时改两行配置即可，不用重写配色。想彻底删干净再说。

---

## 8. 已知陷阱（都是实际出过的 bug）

### CSS

**1. `.footer a` 会盖掉页脚社交按钮的颜色。**
两者优先级相同（都是 0,1,1），而通用规则 `.footer a` 在样式表里排在 `.social-icons a` **之后** → 源序后者胜，按钮文字被染成 `--secondary` 灰。
修法是给通用规则加排除：`.footer a:not(.social-link)`。实测验证：修前最暗像素 `RGB(107,114,128)`（= `--secondary`），修后 `RGB(20,22,26)`（= `--primary`）。

**2. 导航栏会被 menu 药丸撑高 15px。**
`.header-nav` 上是 `line-height: 60px`，`.menu a > span` 会**继承**它；一旦给 span 加 `padding: 7px 12px`，span 高度变成 74px，导航栏从 60px 涨到 75px，连带影响吸顶偏移和侧栏目录的 `top` 计算。
**给这个 span 加 padding 时必须同时显式写 `line-height`。**

**3. `--footer-height` 必须等于页脚真实高度。**
`.main` 的 `min-height: calc(100vh - header - footer)` 依赖它。页脚加了社交按钮后实际是 `153px`，而主题默认 `60px`，少算 93px → 短页面（如 `/about/`）平白多出一截滚动。改页脚内容后**记得重新测这个值**。

**4. 侧栏目录的定位含魔数。**
```css
left: calc(50% + 400px);   /* 400 = 正文半宽 370 + 间距 30 */
```
其中 370 = `--main-width: 740px` 的一半。**改 `--main-width` 必须同步这个 400**，否则目录会压到正文上或飘出屏幕。断点 `min-width: 1280px` 是按「210px 目录宽 + 30px 间距 + 留白」倒推的。

**5. 背景色雾图层会盖住页脚。**
`body::before` 是 `position: fixed; z-index: 0`，而 `.footer` 是非定位元素、绘制层级更低 → 必须给 `.main, .footer` 加 `position: relative; z-index: 1`。**新增全宽区块时注意同样的问题。**

### Hugo 模板

**6. `.TableOfContents` 会多包一层 `<ul><li><ul>`。**
即使标题全在同一级也是这样。所以：
- `nav > ul` 是**包裹层**（要抹掉缩进）
- `nav > ul > li > ul > li > ul` 才是**真正的二级**（要缩进 + 引导线）

只 reset `nav > ul` 会导致每个目录条目漏出圆点和一条多余竖线。

**7. `jsonify` 在 `<script>` 里会被转义成 JS 字符串。**
```gotemplate
var series = {{ site.Params.mainSections | jsonify }};          {{/* ❌ 得到 "[\"llm\",...]" 字符串 */}}
var series = {{ site.Params.mainSections | jsonify | safeJS }}; {{/* ✅ 得到 ["llm",...] 数组 */}}
```
这个坑很阴 —— 字符串的 `.indexOf()` 恰好也能"看起来能用"，但那是子串匹配，`seg="l"` 也会命中。

**8. 分区页没有 section 类名可用。**
`baseof.html` 只输出 `<body class="list">`，不带分区信息。所以 `extend_footer.html` 里读 URL 第一段给 `<html>` 打 `data-series`，分区页才能用上各自的系列色。系列列表由 Hugo 注入，会自动跟随 `mainSections`。

**9. `layouts/home.html` 是首页的覆盖点**，不是 `list.html`。改首页只动 `home.html`，不会影响 `/llm/` `/ai/` `/craft/` 分区页。

---

## 9. 验证方法

**视觉验证是必须的**，这个站点的改动经常「代码看着对、渲染出来错」。

### 截图

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --no-first-run \
  --user-data-dir=/tmp/cp --window-size=1440,900 --force-device-scale-factor=1 \
  --virtual-time-budget=6000 --screenshot=/tmp/out.png "http://127.0.0.1:1313/"
```

注意事项：

- **`--user-data-dir` 必须显式给**（且要可写），否则 Chrome 会崩或挂住；
- macOS 下**窗口最小宽度约 500px**，所以 `--window-size=390,...` 拿不到真正的窄屏。测移动端要用一个 390px 宽的 `<iframe>` 包住站点再截图；
- `defaultTheme: light` 之后 `--blink-settings=preferredColorScheme` **不再有效**。要模拟深色得先在一个同源页面写 `localStorage.setItem('pref-theme','dark')` 再跳转（**注意：恢复深色模式这件事只在 `:root[data-theme="dark"]` 的 CSS 还在时才需要**）。

### 像素测量

配色/对比度这类问题肉眼看不准，建议截图后量化：

```bash
sips -s format bmp shot.png --out shot.bmp      # 转 BMP
```

然后用 Python 读像素。**BMP 头里高度为负表示自上而下**，行序别搞反 —— 我犯过这个错，导致 y 轴整个翻转、误判了一轮结果。稳妥写法：

```python
bottom_up = h > 0                 # 正数高度 = 自下而上
row = (H - 1 - y) if bottom_up else y
```

背景分析有个好用的技巧：在正文栏内打 40px 方块，取每块的**中位数**当前景色（文字像素是少数，中位数≈背景），这样能算出「正文区背景亮度波动」和「正文对比度区间」这类客观指标。

### 改完必做的检查

```bash
rm -rf public && hugo 2>&1 | grep -iE "warn|error"   # 应为空
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:1313/llm/
```

---

## 10. 约定

- **优先用站点 `layouts/` 覆盖主题，而不是直接改 `themes/PaperMod/`。** 主题现在虽然内置在仓库里、可以改，但保持与上游的 diff 干净，升级时才好比对。改动要写清「理由 + 改了什么」。
- 覆盖主题的文件尽量保持**最小 diff**，方便主题升级时比对。
- 注释和提交信息用**中文**，说明「为什么」而不是「做了什么」。
- 改完样式**必须截图验证**，不要只靠读 CSS 判断。
- 主题已内置，`git submodule status` 现在应当**无输出**；如果又出现了 submodule，说明结构被改回去了。

---

## 11. 待办 / 未完成

| 项 | 状态 |
|---|---|
| **部署** | `public/` 尚未部署；`lvxinrong.com` 托管在 Cloudflare（NS: `james.ns.cloudflare.com`）。截至撰写时 apex 无 A/AAAA 记录、`www` 为 NXDOMAIN；`baseURL` 用的是 `blog.lvxinrong.com` 子域，**上线前需确认该子域已加 DNS 记录**。上线需要：部署产物 + DNS 记录 |
| 深色模式 CSS | 仍在 `custom.css` 中，当前不生效（`defaultTheme: light`）。是给未来恢复用的 |
| `/about/` 的阅读时长 | 显示「1 分钟 · 48 字」，建议加 `ShowReadingTime = false` |
| git | 部分改动尚未提交 |

### 排查线上域名的一个提醒

本机 `nslookup lvxinrong.com` 可能返回 `198.18.1.1` —— 那是代理软件 fake-IP 模式的保留网段，**是本地 DNS 劫持的假结果，不要据此判断域名状态**。要查真实记录请绕开本地 DNS，走 DoH：

```bash
curl -s 'https://dns.google/resolve?name=lvxinrong.com&type=A'
```
