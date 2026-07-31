# 豆瓣分类榜单

通过 MoviePilot V2 的标准 `DiscoverSource` 扩展位，在“探索”页增加“豆瓣分类榜单”标签。
插件把豆瓣 `subject_collection` 返回的地区和分类保留为原生筛选项，榜单条目转换为
MoviePilot `MediaInfo`，因此海报、评分、详情和订阅都由 MoviePilot 原生媒体卡片处理。

配置项：

- 启用“豆瓣分类榜单”探索标签
- 是否使用 MoviePilot 代理访问豆瓣
- 默认豆瓣榜单 ID 或 URL
- 缓存时长（0～168 小时）

插件不需要豆瓣 Cookie 或 API Key，也不注入或修改 MoviePilot 前端代码。
