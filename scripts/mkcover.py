#!/usr/bin/env python3
"""生成文章封面图（1200x630），并可写入 front matter 的 [cover] 段。

为什么是本地脚本而不是 Hugo 模板：
    要在图里渲染中文，Hugo 的 images.Text 需要一个 CJK 字体文件；而 Cloudflare 的
    Linux 构建环境没有中文字体，把字体提交进仓库又是 10MB+。所以改成「本地生成、
    提交产物」——脚本跑一次几秒钟，封面本身每个约 30-60KB。

用法：
    python3 scripts/mkcover.py                    # 生成缺失的封面
    python3 scripts/mkcover.py --force            # 全部重新生成
    python3 scripts/mkcover.py --write-frontmatter  # 同时写 front matter 的 [cover]
    python3 scripts/mkcover.py --only llm-01-ch02   # 只处理某一篇

放在 assets/covers/ 而不是 static/ —— 主题的 cover.html 会用
resources.ByType "image" 去 assets/ 找图，找到后自动生成响应式尺寸。
"""
import argparse
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COVER_DIR = ROOT / "assets" / "covers"

# 系列 -> (显示名, 主色, 辅色)。色值与 assets/css/extended/custom.css 的 --series-* 一致。
SERIES = {
    "llm":   ("手搓 LLM", "#1f6fe0", "#5ea4ff"),
    "ai":    ("AI 随想",  "#7c4ddb", "#a78bfa"),
    "craft": ("工程手记", "#0e8f9c", "#3fc9d6"),
}
FONT = "PingFang SC, Hiragino Sans GB, Heiti SC, sans-serif"
CLOSERS = "。，、；：？！」』）》〉…—·"   # 不让这些跑到行首


def char_width(ch):
    """全角算 1，拉丁/数字算 0.55。用于估算折行位置。"""
    return 1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.55


def _greedy(text, limit):
    lines, cur, w = [], "", 0.0
    for ch in text:
        cw = char_width(ch)
        if w + cw > limit and cur and ch not in CLOSERS:
            lines.append(cur)
            cur, w = ch, cw
        else:
            cur += ch
            w += cw
    if cur:
        lines.append(cur)
    return lines


def wrap(text, limit=15.0):
    """两步折行：先用 limit 拿到「最少行数」，再尝试按行数均分。

    只有均分不增加行数时才采用。单纯贪心会留下孤字行：
      生产排查，不该是『老师傅』的手艺
        贪心 → 「生产排查，不该是『老师傅』的手」+「艺」   ← 孤字
        均分 → 「生产排查，不该是」+「『老师傅』的手艺」   ← 采用
    而单纯均分又会把「手搓 LLM 笔记…」从 2 行撑到 3 行，所以要带条件。
    """
    total = sum(char_width(c) for c in text)
    if total <= limit:
        return [text]
    base = _greedy(text, limit)
    balanced = _greedy(text, total / len(base))
    return balanced if len(balanced) == len(base) else base


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(title, key):
    name, c1, c2 = SERIES[key]
    lines = wrap(title)
    size, lh = 62, 84
    top = 330 - (len(lines) - 1) * lh / 2
    tspans = "\n".join(
        f'  <text x="94" y="{top + i * lh:.0f}" font-family="{FONT}" '
        f'font-size="{size}" font-weight="700" fill="#14161a">{esc(l)}</text>'
        for i, l in enumerate(lines)
    )
    rule_y = top + (len(lines) - 1) * lh + 62
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.25" y2="1">
      <stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f3f4f8"/>
    </linearGradient>
    <radialGradient id="g1" cx="0.07" cy="0.1" r="0.7">
      <stop offset="0%" stop-color="{c1}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g2" cx="0.95" cy="0.92" r="0.62">
      <stop offset="0%" stop-color="{c2}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{c2}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect width="1200" height="630" fill="url(#g1)"/>
  <rect width="1200" height="630" fill="url(#g2)"/>

  <circle cx="101" cy="104" r="7" fill="{c1}"/>
  <text x="121" y="113" font-family="{FONT}" font-size="26" font-weight="600"
        letter-spacing="1" fill="{c1}">{esc(name)}</text>

{tspans}

  <rect x="94" y="{rule_y:.0f}" width="64" height="5" rx="2.5" fill="{c1}"/>

  <text x="94" y="548" font-family="{FONT}" font-size="23" fill="#9aa0aa">吕炘嵘的博客</text>
</svg>'''


def read_front_matter(path):
    """返回 (front matter 字符串, title, slug)。只处理 TOML(+++) 格式。"""
    src = path.read_text(encoding="utf-8")
    m = re.match(r"^\+\+\+\r?\n(.*?)\r?\n\+\+\+", src, re.S)
    if not m:
        return None, None, None, src
    fm = m.group(1)
    title = (re.search(r'^title\s*=\s*"(.*?)"', fm, re.M) or [None, None])[1]
    slug = (re.search(r'^slug\s*=\s*"(.*?)"', fm, re.M) or [None, None])[1]
    return fm, title, slug, src


def generate(title, key, out_path, force=False):
    if out_path.exists() and not force:
        return False
    svg = build_svg(title, key)
    tmp_svg = out_path.with_suffix(".svg")
    tmp_svg.write_text(svg, encoding="utf-8")
    subprocess.run(
        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90",
         str(tmp_svg), "--out", str(out_path)],
        capture_output=True, check=True,
    )
    tmp_svg.unlink()
    return True


def write_cover_frontmatter(path, slug, title):
    """在 +++ 之前插入 [cover] 段。已存在则跳过。"""
    fm, _t, _s, src = read_front_matter(path)
    if fm is None:
        return False
    if re.search(r"^\[cover\]", fm, re.M):
        return False
    # 两个都 hidden：封面只作 OG 分享卡（og:image），不在页面里显示。
    # 为什么列表页也不显示 —— 实测封面占卡片高度 65%，加上封面里的标题与
    # 卡片标题重复，一屏只能看 1.6 张卡片（原先 6 张）。文字博客的列表页
    # 价值在快速扫读，把为社交分享设计的图塞进列表是负收益。
    # 详见 Agent.md「文章封面图 → 展示策略」。
    block = (f'\n[cover]\n    image = "covers/{slug}.jpg"\n'
             f'    alt = "{title}"\n'
             f'    hiddenInList = true\n    hiddenInSingle = true\n')
    new = src.replace("\n+++", block + "+++", 1)
    path.write_text(new, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="已存在的封面也重新生成")
    ap.add_argument("--write-frontmatter", action="store_true",
                    help="同时往文章的 front matter 写入 [cover] 段")
    ap.add_argument("--only", metavar="SLUG", help="只处理指定 slug")
    args = ap.parse_args()

    COVER_DIR.mkdir(parents=True, exist_ok=True)
    posts = sorted(p for p in (ROOT / "content").glob("*/*.md")
                   if p.name != "_index.md" and not p.name.startswith("_"))

    made = skipped = fm_written = 0
    for p in posts:
        section = p.parent.name
        if section not in SERIES:
            print(f"  ! 跳过（未知分区 {section}）: {p.name}")
            continue
        fm, title, slug, _src = read_front_matter(p)
        if not title or not slug:
            print(f"  ! 跳过（缺 title 或 slug）: {p.name}")
            continue
        if args.only and slug != args.only:
            continue

        out = COVER_DIR / f"{slug}.jpg"
        if generate(title, section, out, force=args.force):
            print(f"  ✓ 生成 {section:5s} {slug:26s} {out.stat().st_size // 1024} KB")
            made += 1
        else:
            print(f"  · 已存在 {slug}")
            skipped += 1

        if args.write_frontmatter and write_cover_frontmatter(p, slug, title):
            fm_written += 1

    print(f"\n  生成 {made}，跳过 {skipped}" +
          (f"，写入 front matter {fm_written} 篇" if args.write_frontmatter else ""))
    if skipped and not args.force:
        print("  （要重新生成加 --force）")


if __name__ == "__main__":
    sys.exit(main())
