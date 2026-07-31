"""豆瓣榜单数据清洗工具。"""

from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urlparse


DEFAULT_COLLECTION_ID = "ECFA5DI7Q"
COLLECTION_ID_PATTERN = re.compile(r"^[A-Z0-9]{6,32}$")


def parse_collection_id(value: Any) -> str:
    """从榜单 ID 或豆瓣榜单 URL 中提取并校验 collection ID。"""
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" in raw:
        path_parts = [part for part in urlparse(raw).path.split("/") if part]
        try:
            index = path_parts.index("subject_collection")
            raw = path_parts[index + 1]
        except (ValueError, IndexError):
            return ""
    raw = raw.strip("/").upper()
    return raw if COLLECTION_ID_PATTERN.fullmatch(raw) else ""


def safe_int(value: Any, default: int = 0) -> int:
    """将接口字段安全转换为整数。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def extract_year(card_subtitle: Any) -> str:
    """从豆瓣卡片副标题中提取首个四位年份。"""
    match = re.search(r"(?:^|\D)((?:19|20)\d{2})(?:\D|$)", str(card_subtitle or ""))
    return match.group(1) if match else ""


def normalize_item(item: Dict[str, Any], fallback_rank: int = 0) -> Dict[str, Any]:
    """把豆瓣条目转换为前端稳定使用的最小字段集合。"""
    rating = item.get("rating") or {}
    pic = item.get("pic") or {}
    douban_id = str(item.get("id") or "").strip()
    media_type = str(item.get("type") or item.get("subtype") or "tv").lower()
    return {
        "rank": safe_int(item.get("rank") or item.get("rank_value"), fallback_rank),
        "id": douban_id,
        "title": str(item.get("title") or "").strip(),
        "type": "movie" if media_type == "movie" else "tv",
        "year": extract_year(item.get("card_subtitle")),
        "subtitle": str(item.get("card_subtitle") or "").strip(),
        "poster": str(pic.get("large") or item.get("cover_url") or pic.get("normal") or "").strip(),
        "rating": rating.get("value"),
        "rating_count": safe_int(rating.get("count")),
        "url": str(item.get("url") or f"https://movie.douban.com/subject/{douban_id}/").strip(),
    }


def normalize_categories(category_tabs: Any) -> List[Dict[str, Any]]:
    """保留豆瓣返回的地区与类型筛选矩阵。"""
    categories: List[Dict[str, Any]] = []
    for category in category_tabs or []:
        if not isinstance(category, dict):
            continue
        items = []
        for item in category.get("items") or []:
            if not isinstance(item, dict):
                continue
            collection_id = parse_collection_id(item.get("id"))
            name = str(item.get("name") or "").strip()
            if collection_id and name:
                items.append({
                    "id": collection_id,
                    "name": name,
                    "current": bool(item.get("current")),
                })
        name = str(category.get("category") or "").strip()
        if name and items:
            categories.append({"name": name, "items": items})
    return categories


def normalize_collection(
    metadata: Dict[str, Any],
    items_payload: Dict[str, Any],
    start: int,
    count: int,
) -> Dict[str, Any]:
    """合并榜单元数据和分页条目，生成插件 API 响应。"""
    raw_items = items_payload.get("subject_collection_items") or items_payload.get("items") or []
    items = [
        normalize_item(item, fallback_rank=start + index + 1)
        for index, item in enumerate(raw_items)
        if isinstance(item, dict)
    ]
    collection_id = parse_collection_id(metadata.get("id"))
    return {
        "collection": {
            "id": collection_id,
            "name": str(metadata.get("name") or metadata.get("title") or "豆瓣榜单").strip(),
            "short_name": str(metadata.get("short_name") or "").strip(),
            "filter_name": str(metadata.get("medium_name") or "").strip(),
            "description": str(metadata.get("description") or "").strip(),
            "total": safe_int(items_payload.get("total"), safe_int(metadata.get("total"))),
            "followers": safe_int(metadata.get("n_followers")),
            "updated_at": str(metadata.get("updated_at") or "").strip(),
            "cover": str(metadata.get("cover_url") or "").strip(),
            "backdrop": str(metadata.get("header_bg_image") or metadata.get("cover_url") or "").strip(),
            "url": f"https://m.douban.com/subject_collection/{collection_id}",
        },
        "categories": normalize_categories(metadata.get("category_tabs")),
        "items": items,
        "start": safe_int(items_payload.get("start"), start),
        "count": len(items),
    }
