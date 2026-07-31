"""豆瓣榜单数据清洗工具。"""

from __future__ import annotations

import json
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
    poster = str(pic.get("large") or item.get("cover_url") or pic.get("normal") or "").strip()
    # MoviePilot 2.15.1 的原生图片代理在当前网络中无法稳定访问 img9，
    # 豆瓣 CDN 的同一路径可由 img1 镜像提供。
    poster = poster.replace("://img9.doubanio.com/", "://img1.doubanio.com/", 1)
    return {
        "rank": safe_int(item.get("rank") or item.get("rank_value"), fallback_rank),
        "id": douban_id,
        "title": str(item.get("title") or "").strip(),
        "type": "movie" if media_type == "movie" else "tv",
        "year": extract_year(item.get("card_subtitle")),
        "subtitle": str(item.get("card_subtitle") or "").strip(),
        "poster": poster,
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


def active_category_name(categories: List[Dict[str, Any]], collection_id: str) -> str:
    """返回某个榜单所属的地区分类。"""
    resolved_id = parse_collection_id(collection_id)
    for category in categories or []:
        for item in category.get("items") or []:
            if item.get("id") == resolved_id:
                return str(category.get("name") or "")
    return str((categories or [{}])[0].get("name") or "")


def resolve_collection_id(
    categories: List[Dict[str, Any]],
    region: str,
    requested_id: str,
    fallback_id: str = DEFAULT_COLLECTION_ID,
) -> str:
    """按地区约束榜单 ID，地区切换时回退到该地区的首个榜单。"""
    requested = parse_collection_id(requested_id)
    normalized_fallback = parse_collection_id(fallback_id) or DEFAULT_COLLECTION_ID
    selected_region = str(region or "").strip()
    if not selected_region:
        return requested or normalized_fallback

    category = next(
        (
            item
            for item in categories or []
            if str(item.get("name") or "").strip() == selected_region
        ),
        None,
    )
    if not category:
        return requested or normalized_fallback
    category_ids = [
        item.get("id")
        for item in category.get("items") or []
        if parse_collection_id(item.get("id"))
    ]
    if requested in category_ids:
        return requested
    return str(category_ids[0] if category_ids else normalized_fallback)


def build_filter_ui(categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """用 MoviePilot 原生筛选组件呈现豆瓣的地区与分类矩阵。"""
    usable_categories = [
        category
        for category in categories or []
        if category.get("name") and category.get("items")
    ]
    if not usable_categories:
        return []

    collection_names = {
        item["id"]: item["name"]
        for category in usable_categories
        for item in category.get("items") or []
        if item.get("id") and item.get("name")
    }
    region_chips: List[Dict[str, Any]] = []
    for category in usable_categories:
        items = category.get("items") or []
        target_by_name = {
            item["name"]: item["id"]
            for item in items
            if item.get("id") and item.get("name")
        }
        first_id = str(items[0].get("id") or "")
        click_handler = (
            "function(){"
            f"const names={json.dumps(collection_names, ensure_ascii=False)};"
            f"const targets={json.dumps(target_by_name, ensure_ascii=False)};"
            f"collection_id=targets[names[collection_id]]||{json.dumps(first_id)};"
            "}"
        )
        region_chips.append({
            "component": "VChip",
            "props": {
                "filter": True,
                "tile": True,
                "value": category["name"],
                "onClick": click_handler,
            },
            "text": category["name"],
        })

    filter_rows: List[Dict[str, Any]] = [
        _filter_row("地区", "region", region_chips),
    ]
    for category in usable_categories:
        filter_chips = [
            {
                "component": "VChip",
                "props": {
                    "filter": True,
                    "tile": True,
                    "value": item["id"],
                },
                "text": item["name"],
            }
            for item in category.get("items") or []
            if item.get("id") and item.get("name")
        ]
        row = _filter_row("分类", "collection_id", filter_chips)
        region_literal = json.dumps(category["name"], ensure_ascii=False)
        row["props"]["show"] = f"{{{{region === {region_literal}}}}}"
        filter_rows.append(row)
    return filter_rows


def _filter_row(label: str, model: str, chips: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构造与官方探索扩展源一致的原生筛选行。"""
    return {
        "component": "div",
        "props": {"class": "flex justify-start items-center flex-wrap"},
        "content": [
            {
                "component": "div",
                "props": {"class": "mr-5 text-medium-emphasis"},
                "content": [{"component": "VLabel", "text": label}],
            },
            {
                "component": "VChipGroup",
                "props": {"model": model, "mandatory": True},
                "content": chips,
            },
        ],
    }


def media_info_payload(item: Dict[str, Any], collection: Dict[str, Any]) -> Dict[str, Any]:
    """把豆瓣榜单条目转换为 MoviePilot MediaInfo 字段。"""
    title = str(item.get("title") or "").strip()
    year = str(item.get("year") or "").strip()
    douban_id = str(item.get("id") or "").strip()
    media_type = "电影" if item.get("type") == "movie" else "电视剧"
    rating = item.get("rating")
    try:
        vote_average = float(rating or 0)
    except (TypeError, ValueError):
        vote_average = 0.0
    return {
        "source": "douban",
        "scrape_source": "douban",
        "mediaid_prefix": "douban",
        "media_id": douban_id,
        "douban_id": douban_id,
        "type": media_type,
        "title": title,
        "en_title": title,
        "original_title": title,
        "year": year,
        "title_year": f"{title} ({year})" if year else title,
        "poster_path": str(item.get("poster") or "").strip() or None,
        "vote_average": vote_average,
        "vote_count": safe_int(item.get("rating_count")),
        "popularity": max(0.0, 10000.0 - float(safe_int(item.get("rank")))),
        "overview": str(item.get("subtitle") or collection.get("description") or "").strip(),
        "category": str(collection.get("filter_name") or collection.get("name") or "").strip(),
        "detail_link": str(item.get("url") or "").strip() or None,
        "homepage": str(item.get("url") or "").strip() or None,
    }
