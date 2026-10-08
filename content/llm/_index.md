+++
title = "手搓 LLM"
description = "读《从零构建大模型》，把每一层都拆开看"

# columnKind 决定这个栏目在站内怎么被对待，两种取值的差别贯穿首页、列表页和导航：
#   serial 连载 —— 有顺序，读者会从 00 一路追下去
#   column 专栏 —— 主题抽屉，篇与篇互相独立，读者按兴趣挑
# 判据很简单：这些文章之间有先后关系吗？有就是 serial。
#
# 为什么不叫 kind：`kind` 在 Hugo 0.147.7（Cloudflare 线上用的版本）里是**保留的
# front matter 键**，写上去会让构建直接失败：
#     Error: unknown kind "column" in front matter
# 而本地 0.166 不报。别和模板里的 .Kind 搞混 —— 那个是 Page 的方法，不受影响。
columnKind = "serial"

# ongoing 连载中 | complete 已完结 | paused 暂缓。站内会把它显示成徽章。
status = "ongoing"

# 首页展示顺序，数字越小越靠前。不填 = 不上首页（沉到 /columns/）。
featured = 1

# 这里**刻意不放进度数据**。
# 曾经有过 startDate + totalWeeks 用来算「第 N 周 / 共 12 周」—— 那个 12 周是私下
# 约定，不该变成对外的公开承诺，而且「共 X 周」等于给自己套了个倒计时。
# 现在状态栏只说三件事实，全部从文章本身推出来，一个参数都不用维护：
#   已写多少篇  ← len(.RegularPages)
#   最近更新    ← 最新一篇的 date
#   在读什么书  ← 上面那个 description
+++

{{< series_status >}}
