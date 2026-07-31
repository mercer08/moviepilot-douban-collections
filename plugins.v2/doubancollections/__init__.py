"""MoviePilot 豆瓣分类榜单插件。"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from app import schemas
from app.core.config import settings
from app.core.event import Event, eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import DiscoverSourceEventData
from app.schemas.types import ChainEventType
from app.utils.http import RequestUtils

from .douban import (
    DEFAULT_COLLECTION_ID,
    active_category_name,
    build_filter_ui,
    media_info_payload,
    normalize_collection,
    parse_collection_id,
    resolve_collection_id,
)


class DoubanCollections(_PluginBase):
    """把豆瓣 subject_collection 分类榜单注册为 MoviePilot 原生探索源。"""

    plugin_name = "豆瓣分类榜单"
    plugin_desc = "在探索页新增豆瓣分类榜单标签，保留地区和分类筛选，并使用原生媒体卡片。"
    plugin_icon = "https://raw.githubusercontent.com/mercer08/moviepilot-douban-collections/main/icons/douban.png"
    plugin_version = "1.1.0"
    plugin_author = "mercer08"
    author_url = "https://github.com/mercer08"
    plugin_config_prefix = "doubancollections_"
    plugin_order = 30
    auth_level = 1

    DATA_KEY_CACHE = "collection_cache"
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )

    def init_plugin(self, config: dict = None) -> None:
        """读取配置并初始化持久缓存。"""
        config = config or {}
        self._cache_lock = threading.RLock()
        self._enabled = bool(config.get("enabled", False))
        self._use_proxy = bool(config.get("use_proxy", False))
        self._default_collection_id = (
            parse_collection_id(config.get("collection")) or DEFAULT_COLLECTION_ID
        )
        try:
            self._cache_hours = max(0, min(168, int(config.get("cache_hours", 6))))
        except (TypeError, ValueError):
            self._cache_hours = 6
        logger.info(
            f"DoubanCollections v{self.plugin_version} loaded: enabled={self._enabled} "
            f"default={self._default_collection_id} cache={self._cache_hours}h"
        )

    def get_state(self) -> bool:
        """返回插件是否启用。"""
        return bool(getattr(self, "_enabled", False))

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """本插件不注册远程命令。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """注册探索数据和缓存管理接口。"""
        return [
            {
                "path": "/discover",
                "endpoint": self.discover,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "探索豆瓣分类榜单",
            },
            {
                "path": "/cache/clear",
                "endpoint": self.clear_cache,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "清空豆瓣分类榜单缓存",
            },
        ]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """使用 MoviePilot 原生表单配置插件。"""
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [{
                                    "component": "VSwitch",
                                    "props": {"model": "enabled", "label": "启用探索标签"},
                                }],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [{
                                    "component": "VSwitch",
                                    "props": {"model": "use_proxy", "label": "使用 MoviePilot 代理"},
                                }],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [{
                                    "component": "VTextField",
                                    "props": {
                                        "model": "cache_hours",
                                        "label": "缓存时长（小时）",
                                        "type": "number",
                                        "min": 0,
                                        "max": 168,
                                    },
                                }],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [{
                                    "component": "VTextField",
                                    "props": {
                                        "model": "collection",
                                        "label": "默认豆瓣榜单 ID 或 URL",
                                        "placeholder": DEFAULT_COLLECTION_ID,
                                    },
                                }],
                            },
                        ],
                    }
                ],
            }
        ], {
            "enabled": False,
            "use_proxy": False,
            "collection": DEFAULT_COLLECTION_ID,
            "cache_hours": 6,
        }

    @staticmethod
    def get_page() -> None:
        """主界面由 MoviePilot 探索页原生渲染，不再提供独立页面。"""
        return None

    def stop_service(self) -> None:
        """本插件没有后台服务。"""
        pass

    def discover(
        self,
        region: str = "",
        collection_id: str = "",
        page: int = 1,
        count: int = 20,
    ) -> List[schemas.MediaInfo]:
        """返回 MoviePilot 原生 MediaInfo 列表，供探索页无限滚动。"""
        if not self.get_state():
            return []
        page = max(1, int(page or 1))
        count = max(1, min(50, int(count or 20)))
        try:
            source = self._category_snapshot()
            categories = source.get("categories") or []
            selected_id = resolve_collection_id(
                categories,
                region=region,
                requested_id=collection_id,
                fallback_id=self._default_collection_id,
            )
            payload = self._load_collection(
                selected_id,
                start=(page - 1) * count,
                count=count,
                refresh=False,
            )
            collection = payload.get("collection") or {}
            return [
                schemas.MediaInfo(**media_info_payload(item, collection))
                for item in payload.get("items") or []
                if item.get("id") and item.get("title")
            ]
        except Exception as error:
            logger.error(f"探索豆瓣分类榜单失败：{error}")
            return []

    def clear_cache(self) -> schemas.Response:
        """清空持久化榜单缓存。"""
        with self._cache_lock:
            self.save_data(self.DATA_KEY_CACHE, {})
        return schemas.Response(success=True, message="缓存已清空")

    @eventmanager.register(ChainEventType.DiscoverSource)
    def discover_source(self, event: Event) -> None:
        """通过标准 DiscoverSource 扩展位注册探索页标签。"""
        if not self.get_state() or not event or not event.event_data:
            return
        try:
            snapshot = self._category_snapshot()
            categories = snapshot.get("categories") or []
            collection = snapshot.get("collection") or {}
            current_id = collection.get("id") or self._default_collection_id
            current_region = active_category_name(categories, current_id)
            source = schemas.DiscoverMediaSource(
                name="豆瓣分类榜单",
                mediaid_prefix="douban-collections",
                api_path="plugin/DoubanCollections/discover",
                filter_params={
                    "region": current_region,
                    "collection_id": current_id,
                },
                filter_ui=build_filter_ui(categories),
            )
        except Exception as error:
            logger.warning(f"构造豆瓣分类榜单筛选失败，将使用默认榜单：{error}")
            source = schemas.DiscoverMediaSource(
                name="豆瓣分类榜单",
                mediaid_prefix="douban-collections",
                api_path="plugin/DoubanCollections/discover",
                filter_params={"region": "", "collection_id": self._default_collection_id},
                filter_ui=[],
            )
        event_data: DiscoverSourceEventData = event.event_data
        if event_data.extra_sources:
            event_data.extra_sources.append(source)
        else:
            event_data.extra_sources = [source]

    def _category_snapshot(self) -> Dict[str, Any]:
        """获取默认榜单元数据，用于构造原生筛选控件。"""
        return self._load_collection(
            self._default_collection_id,
            start=0,
            count=1,
            refresh=False,
        )

    def _load_collection(
        self,
        collection_id: str,
        start: int,
        count: int,
        refresh: bool,
    ) -> Dict[str, Any]:
        """优先返回有效缓存，远端异常时允许使用过期缓存。"""
        cache_key = f"native-v1:{collection_id}:{start}:{count}"
        with self._cache_lock:
            cache = self.get_data(self.DATA_KEY_CACHE) or {}
            cached = cache.get(cache_key)
            if not refresh and self._cache_is_fresh(cached):
                return self._mark_cache(cached["payload"], source="cache", stale=False)

        try:
            payload = self._fetch_collection(collection_id, start, count)
        except Exception:
            if cached and cached.get("payload"):
                return self._mark_cache(cached["payload"], source="cache", stale=True)
            raise

        with self._cache_lock:
            cache = self.get_data(self.DATA_KEY_CACHE) or {}
            cache[cache_key] = {"cached_at": time.time(), "payload": payload}
            self.save_data(self.DATA_KEY_CACHE, cache)
        return self._mark_cache(payload, source="remote", stale=False)

    def _fetch_collection(self, collection_id: str, start: int, count: int) -> Dict[str, Any]:
        """通过 MoviePilot 请求工具读取豆瓣元数据与榜单条目。"""
        page_url = f"https://m.douban.com/subject_collection/{collection_id}"
        api_url = f"https://m.douban.com/rexxar/api/v2/subject_collection/{collection_id}"
        proxies: Optional[dict] = None
        if getattr(self, "_use_proxy", False):
            proxies = getattr(settings, "PROXY", None)
        request = RequestUtils(
            ua=getattr(settings, "USER_AGENT", None) or self.DEFAULT_USER_AGENT,
            referer=page_url,
            proxies=proxies,
            timeout=20,
        )
        metadata = request.get_json(api_url, params={"for_mobile": 1})
        if not isinstance(metadata, dict) or not metadata.get("id"):
            raise RuntimeError("豆瓣未返回有效榜单信息")
        items_payload = request.get_json(
            f"{api_url}/items",
            params={"start": start, "count": count, "items_only": 1},
        )
        if not isinstance(items_payload, dict):
            raise RuntimeError("豆瓣未返回有效榜单条目")
        return normalize_collection(metadata, items_payload, start, count)

    def _cache_is_fresh(self, cached: Any) -> bool:
        """判断缓存是否仍处于配置的有效期内。"""
        if not isinstance(cached, dict) or not cached.get("payload"):
            return False
        cache_seconds = max(0, getattr(self, "_cache_hours", 6)) * 3600
        return cache_seconds > 0 and time.time() - float(cached.get("cached_at") or 0) < cache_seconds

    @staticmethod
    def _mark_cache(payload: Dict[str, Any], source: str, stale: bool) -> Dict[str, Any]:
        """复制响应并标记数据来源，避免修改持久化对象。"""
        result = dict(payload)
        result["source"] = source
        result["stale"] = stale
        return result
