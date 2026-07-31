# MoviePilot 豆瓣合集榜单

把豆瓣 `subject_collection` 榜单放进 MoviePilot 的“发现”分组里浏览。

插件不是把某一个页面截图搬过去，而是读取榜单返回的真实筛选结构。以“近期热门美剧榜”为例，左侧的大陆剧、美剧、英剧、日剧等地区会保留；选择地区后，上方只展示豆瓣为该地区实际提供的近期热门、高分经典、喜剧、悬疑等类型。没有对应榜单的组合不会凭空出现。

## 能做什么

- 展示榜单排名、海报、豆瓣评分、评分人数和条目简介
- 保留豆瓣返回的地区与类型筛选
- 支持分页和手动刷新
- 点击条目可打开豆瓣详情
- 通过 MoviePilot 原生订阅流程订阅电影或电视剧
- 缓存最后一次成功结果；豆瓣临时不可用时可继续浏览旧数据
- 支持自定义任意 `m.douban.com/subject_collection/...` 榜单作为入口

## 安装

要求 MoviePilot `2.15.1` 或更新版本。

1. 在 MoviePilot 的插件仓库设置中添加：

   ```text
   https://github.com/mercer08/moviepilot-douban-collections
   ```

2. 刷新插件市场，安装“豆瓣合集榜单”。
3. 打开插件设置，启用插件并保存。
4. 从侧栏“发现”分组进入“豆瓣榜单”。

默认入口是：

```text
https://m.douban.com/subject_collection/ECFA5DI7Q
```

设置里可以直接粘贴其他豆瓣合集榜单 URL，也可以只填 collection ID。

## 数据与隐私

插件只请求豆瓣公开的榜单元数据和条目接口，不读取或上传豆瓣 Cookie、MoviePilot 媒体库、订阅记录、账号信息或服务器地址。仓库中不包含任何部署环境配置、内网域名、IP 地址或访问凭据。

为了减少对豆瓣的请求，默认缓存 6 小时。缓存只保存在当前 MoviePilot 实例的插件数据目录中。

## 开发

后端逻辑：

```bash
python3 -m unittest discover -s tests -v
```

前端联邦组件：

```bash
cd plugins.v2/doubancollections
pnpm install --frozen-lockfile
pnpm run build
```

发布仓库会提交构建后的 `dist/assets`，MoviePilot 安装时不需要现场安装 Node.js 依赖。

## 说明

这是第三方开源插件，与豆瓣及 MoviePilot 官方无隶属关系。榜单内容、评分和图片版权归相应权利人所有；请合理设置缓存并遵守数据来源站点的使用规则。

许可证：[MIT](LICENSE)
