# MoviePilot 豆瓣分类榜单

把豆瓣 `subject_collection` 分类榜单接入 MoviePilot V2 的“探索”页。

安装并启用后，“探索”顶部会出现“豆瓣分类榜单”标签。页面不使用插件自建布局，筛选控件、
海报卡片、评分、详情入口和订阅操作都由 MoviePilot 原生组件负责。

## 功能

- 保留豆瓣榜单返回的地区分类：大陆剧、美剧、英剧、日剧、韩剧等
- 根据地区显示实际可用的近期热门、高分经典、喜剧、悬疑等分类
- 切换地区时优先保留同名分类；没有对应分类时回到该地区首个榜单
- 使用 MoviePilot 原生媒体卡片展示海报、类型和豆瓣评分
- 支持 MoviePilot 原生详情、搜索、订阅状态和订阅操作
- 支持分页、持久缓存和远端异常时的最后成功结果回退
- 可将任意 `m.douban.com/subject_collection/...` 地址设为默认入口

## 安装

要求 MoviePilot `2.15.1` 或更新版本。

1. 在 MoviePilot 的插件仓库设置中添加：

   ```text
   https://github.com/mercer08/moviepilot-douban-collections
   ```

2. 刷新插件市场，安装“豆瓣分类榜单”。
3. 打开插件设置，启用“探索标签”并保存。
4. 进入“探索”，选择顶部的“豆瓣分类榜单”。

默认榜单：

```text
https://m.douban.com/subject_collection/ECFA5DI7Q
```

插件不需要豆瓣 Cookie 或 API Key。

## 实现方式

插件通过 MoviePilot V2 的 `ChainEventType.DiscoverSource` 注册探索数据源，筛选项使用
`DiscoverMediaSource.filter_ui`，榜单接口返回标准 `MediaInfo` 列表。插件不会修改、注入或
替换 MoviePilot 前端文件。

豆瓣海报地址交给 MoviePilot 自带的图片代理处理。为兼容部分环境无法访问
`img9.doubanio.com` 的情况，插件会把同一路径切换到豆瓣 CDN 的 `img1` 镜像。

## 数据与隐私

插件只请求豆瓣公开的榜单元数据和条目接口，不读取或上传豆瓣 Cookie、MoviePilot 媒体库、
订阅记录、账号信息或服务器地址。仓库不包含部署环境配置、内网域名、IP 地址或访问凭据。

默认缓存 6 小时，缓存只保存在当前 MoviePilot 实例的插件数据目录中。

## 开发

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile \
  plugins.v2/doubancollections/__init__.py \
  plugins.v2/doubancollections/douban.py
```

许可证：[MIT](LICENSE)
