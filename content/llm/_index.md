+++
title = "手搓 LLM"
description = "从零实现一个大模型，把每一层都拆开看"

# columnKind 决定这个栏目在站内怎么被对待，两种取值的差别贯穿首页、列表页和导航：
#   serial 连载 —— 有顺序、有承诺，读者会从 00 一路追下去
#   column 专栏 —— 主题抽屉，篇与篇互相独立，读者按兴趣挑
# 判据很简单：这些文章之间有先后关系吗？有就是 serial。
#
# 为什么不叫 kind：`kind` 在 Hugo 0.147.7（Cloudflare 线上用的版本）里是**保留的
# front matter 键**，写上去会让构建直接失败：
#     Error: unknown kind "column" in front matter
# 而本地 0.166 不报。别和模板里的 .Kind 搞混 —— 那个是 Page 的方法，不受影响。
columnKind = "serial"

# ongoing 连载中 | complete 已完结 | paused 暂缓。首页卡片会把它显示成徽章。
status = "ongoing"

# 首页展示顺序，数字越小越靠前。不填 = 不上首页（沉到 /columns/）。
featured = 1

# ---------- 进度条（只有连载需要）----------
# 这两个参数一设，首页 Hero、栏目页头部、栏目卡片三处的进度条全部自动算出来，
# 不需要手写任何数字。当前第几周由构建时间推出，每次部署刷新一次。
# 立项书里写的是「周期 12 周」，立项日期 2026-09 月 —— 这里用立项书发布那天。
startDate = 2026-09-21
totalWeeks = 12
+++

{{< series_progress >}}
