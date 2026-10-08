+++
title = "工程手记"
description = "一线工程实践里的判断、取舍与踩坑"

# columnKind 决定这个栏目在站内怎么被对待，两种取值的差别贯穿首页、列表页和导航：
#   serial 连载 —— 有顺序、有承诺，读者会从 00 一路追下去
#   column 专栏 —— 主题抽屉，篇与篇互相独立，读者按兴趣挑
# 判据很简单：这些文章之间有先后关系吗？没有就是 column。
#
# 为什么不叫 kind：`kind` 在 Hugo 0.147.7（Cloudflare 线上用的版本）里是**保留的
# front matter 键**，写上去会让构建直接失败：
#     Error: unknown kind "column" in front matter
# 而本地 0.166 不报。别和模板里的 .Kind 搞混 —— 那个是 Page 的方法，不受影响。
columnKind = "column"

# 首页展示顺序，数字越小越靠前。不填 = 不上首页（沉到 /columns/）。
featured = 3
+++
