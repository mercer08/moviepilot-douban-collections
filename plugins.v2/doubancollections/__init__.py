"""MoviePilot 豆瓣合集榜单插件。"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from app import schemas
from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.utils.http import RequestUtils

from .douban import DEFAULT_COLLECTION_ID, normalize_collection, parse_collection_id


class DoubanCollections(_PluginBase):
    """在 MoviePilot 中呈现豆瓣 subject_collection 榜单。"""

    plugin_name = "豆瓣合集榜单"
    plugin_desc = "保留豆瓣地区与类型筛选，展示海报和评分，并接入 MoviePilot 原生订阅。"
    plugin_icon = "https://raw.githubusercontent.com/mercer08/moviepilot-douban-collections/main/icons/douban.png"
    plugin_version = "1.0.0"
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
        """读取配置并初始化缓存锁。"""
        config = config or {}
        self._cache_lock = threading.RLock()
        self._enabled = bool(config.get("enabled", False))
        self._show_sidebar_nav = bool(config.get("show_sidebar_nav", True))
        self._use_proxy = bool(config.get("use_proxy", False))
        self._default_collection_id = (
            parse_collection_id(config.get("collection")) or DEFAULT_COLLECTION_ID
        )
        try:
            self._cache_hours = max(0, min(168, int(config.get("cache_hours", 6))))
        except (TypeError, ValueError):
            self._cache_hours = 6

    def get_state(self) -> bool:
        """返回插件是否启用。"""
        return bool(getattr(self, "_enabled", False))

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """本插件不注册远程命令。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """注册供 Vue 页面调用的鉴权接口。"""
        return [
            {
                "path": "/collection",
                "endpoint": self.get_collection,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "读取豆瓣合集榜单",
            },
            {
                "path": "/cache/clear",
                "endpoint": self.clear_cache,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "清空豆瓣榜单缓存",
            },
        ]

    @staticmethod
    def get_render_mode() -> Tuple[str, str]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回 Vue 配置组件使用的默认模型。"""
        return [], {
            "enabled": False,
            "show_sidebar_nav": True,
            "use_proxy": False,
            "collection": DEFAULT_COLLECTION_ID,
            "cache_hours": 6,
        }

    @staticmethod
    def get_page() -> List[dict]:
        """详情页由远程 Page 组件渲染。"""
        return []

    def get_sidebar_nav(self) -> List[Dict[str, Any]]:
        """把榜单页面注册到 MoviePilot 发现分组。"""
        if not self.get_state() or not getattr(self, "_show_sidebar_nav", True):
            return []
        return [
            {
                "nav_key": "main",
                "title": "豆瓣榜单",
                "icon": "mdi-chart-box-outline",
                "section": "discovery",
                "permission": "discovery",
                "order": 35,
            }
        ]

    def stop_service(self) -> None:
        """本插件没有后台服务，无需额外清理。"""
        pass

    def get_collection(
        self,
        collection_id: str = "",
        start: int = 0,
        count: int = 20,
        refresh: bool = False,
    ) -> schemas.Response:
        """读取一个榜单分页，并在请求失败时回退到最后一次缓存。"""
        resolved_id = parse_collection_id(collection_id) or getattr(
            self, "_default_collection_id", DEFAULT_COLLECTION_ID
        )
        start = max(0, start)
        count = max(1, min(50, count))
        try:
            payload = self._load_collection(resolved_id, start, count, refresh)
            return schemas.Response(success=True, data=payload)
        except Exception as error:
            logger.error(f"读取豆瓣榜单 {resolved_id} 失败：{error}")
            return schemas.Response(success=False, message=f"豆瓣榜单加载失败：{error}")

    def clear_cache(self) -> schemas.Response:
        """清空持久化榜单缓存。"""
        with self._cache_lock:
            self.save_data(self.DATA_KEY_CACHE, {})
        return schemas.Response(success=True, message="缓存已清空")

    def _load_collection(
        self,
        collection_id: str,
        start: int,
        count: int,
        refresh: bool,
    ) -> Dict[str, Any]:
        """优先返回有效缓存，远端异常时允许使用过期缓存。"""
        cache_key = f"{collection_id}:{start}:{count}"
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
