#!/usr/bin/env python3
"""文章体检：在提交前发现几类「不报错但渲染结果不对」的问题。

用法：
    python3 scripts/check-content.py            # 检查全部文章
    python3 scripts/check-content.py <文件>...   # 只检查指定文件

设计取舍：这里只查「构建不会报错、但页面上明显不对」的问题。
front matter 语法错误、模板错误那些 Hugo 自己会拦住，不在此列。
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLOSERS = "。，、；：？！）」』》〉…—·"
# 汉字 + 中文标点：直引号只要碰到这些字符，typographer 的方向判断就不可信
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef]")


def _is_punct(ch):
    return bool(ch) and unicodedata.category(ch).startswith("P")


def check_bold(lines):
    """中文标点导致的加粗失效。

    CommonMark 规定闭合的 ** 必须满足 right-flanking：不能「前一个字符是标点、
    后一个字符既不是空白也不是标点」。中文标点属于 Unicode P* 类别，所以
    `**……。**它们` 里的 ** 不被认作闭合符，页面上会原样显示两个星号。
    """
    out = []
    for ln, line in enumerate(lines, 1):
        for m in re.finditer(r"\*\*(.+?)\*\*", line):
            inner = m.group(1)
            if not inner:
                continue
            nxt = line[m.end()] if m.end() < len(line) else ""
            if _is_punct(inner[-1]) and nxt and not nxt.isspace() and not _is_punct(nxt):
                out.append((ln, f"加粗失效：{m.group(0)[:44]}",
                            "把结尾的标点挪到 ** 外面：**……文字**。后面"))
    return out


def check_quotes(lines):
    """直引号贴近中文时，typographer 会猜错方向。

    Goldmark 按拉丁文 flanking 规则判断引号开合，中文没有空格，于是同一份源文件
    里同一个 `"` 转不转、转成哪个方向全看它左右碰巧是什么字符：
      `停留在"知道名词"的水平` —— 两侧都是汉字，既非左翼也非右翼 → 原样输出 &quot;
      `经验？"如果遭到拒绝`   —— 引号前是全角标点 → 被判成左翼，收尾引号变开引号
    散文里一律把方向写死成 “ ” ‘ ’。front matter（TOML 语法引号）、代码围栏、
    行内代码不检查；`O'Reilly` 这类拉丁词内撇号两侧是字母，不会误报。
    """
    out = []
    start = 0
    if lines and lines[0].strip() == "+++":
        for i in range(1, len(lines)):
            if lines[i].strip() == "+++":
                start = i + 1
                break
    in_fence = False
    for ln, line in enumerate(lines, 1):
        if ln <= start:
            continue
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        text = re.sub(r"`[^`\n]*`", "", line)
        for m in re.finditer(r"[\"']", text):
            i = m.start()
            before = text[i - 1] if i else ""
            after = text[i + 1] if i + 1 < len(text) else ""
            if CJK_RE.match(before) or CJK_RE.match(after):
                snippet = text[max(0, i - 10):i + 11].strip()
                out.append((ln, f"直引号贴近中文：…{snippet}…",
                            '改成 “ ” 或 ‘ ’：方向写死，别让 typographer 猜'))
                break          # 一行报一次，避免刷屏
    return out


def check_code_fence(lines):
    """代码围栏必须成对，否则后面全被当成代码。"""
    n = sum(1 for l in lines if l.startswith("```"))
    if n % 2:
        return [(0, f"代码围栏 ``` 出现 {n} 次（奇数）", "有未闭合的代码块，检查 ``` 是否配对")]
    return []


def check_front_matter(path, lines):
    """Hugo 不报错、但会影响 URL 或分享卡片的缺失项。"""
    out = []
    src = "\n".join(lines)
    m = re.match(r"^\+\+\+\n(.*?)\n\+\+\+", src, re.S)
    if not m:
        return [(0, "没有 TOML front matter（+++ … +++）", "确认文件开头是 +++")]
    fm = m.group(1)
    if not re.search(r"^slug\s*=", fm, re.M):
        out.append((0, "缺 slug", "中文标题会变成百分号编码的长 URL，分享不便。加 slug = \"英文短名\""))
    if not re.search(r"^\[cover\]", fm, re.M):
        out.append((0, "缺 [cover] 段", "没有分享卡片。跑 python3 scripts/mkcover.py --write-frontmatter"))
    if not re.search(r"^date\s*=", fm, re.M):
        out.append((0, "缺 date", "Hugo 会用文件时间，且未来日期会静默不构建"))
    return out


def main():
    args = sys.argv[1:]
    if args:
        files = [Path(a) for a in args]
    else:
        files = sorted(p for p in (ROOT / "content").glob("*/*.md")
                       if p.name != "_index.md" and not p.name.startswith("_"))

    total = 0
    for f in files:
        lines = f.read_text(encoding="utf-8").split("\n")
        issues = (check_bold(lines) + check_quotes(lines) + check_code_fence(lines)
                  + check_front_matter(f, lines))
        if issues:
            total += len(issues)
            try:
                shown = f.relative_to(ROOT)
            except ValueError:
                shown = f          # 传进来的仓库外文件，原样显示
            print(f"\n{shown}")
            for ln, what, how in issues:
                loc = f"L{ln} " if ln else ""
                print(f"  ✗ {loc}{what}")
                print(f"      → {how}")

    if total:
        print(f"\n共 {total} 个问题。修完再提交。")
        return 1
    print(f"✓ {len(files)} 篇文章，未发现问题")
    return 0


if __name__ == "__main__":
    sys.exit(main())
