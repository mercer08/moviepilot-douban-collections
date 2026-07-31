"""豆瓣榜单数据清洗测试。"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "plugins.v2"
    / "doubancollections"
    / "douban.py"
)
SPEC = importlib.util.spec_from_file_location("doubancollections_douban", MODULE_PATH)
douban = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(douban)


CATEGORIES = [
    {
        "name": "大陆剧",
        "items": [
            {"id": "MAINLANDHOT", "name": "近期热门"},
            {"id": "MAINLANDCOMEDY", "name": "喜剧"},
        ],
    },
    {
        "name": "美剧",
        "items": [
            {"id": "ECFA5DI7Q", "name": "近期热门"},
            {"id": "USCOMEDY", "name": "喜剧"},
        ],
    },
]


class DoubanHelpersTest(unittest.TestCase):
    """验证榜单 ID 解析和数据清洗。"""

    def test_parse_collection_id_accepts_id_and_mobile_url(self) -> None:
        """榜单 ID 和移动版地址都应解析为同一个 ID。"""
        self.assertEqual(douban.parse_collection_id("ECFA5DI7Q"), "ECFA5DI7Q")
        self.assertEqual(
            douban.parse_collection_id(
                "https://m.douban.com/subject_collection/ECFA5DI7Q?from=test"
            ),
            "ECFA5DI7Q",
        )

    def test_parse_collection_id_rejects_unrelated_url(self) -> None:
        """非榜单地址不能被当作 collection ID 使用。"""
        self.assertEqual(douban.parse_collection_id("https://example.com/ECFA5DI7Q"), "")
        self.assertEqual(douban.parse_collection_id("../../etc/passwd"), "")

    def test_normalize_collection_keeps_sparse_filter_matrix(self) -> None:
        """不同地区各自的真实类型组合应原样保留。"""
        metadata = {
        "id": "ECFA5DI7Q",
        "name": "近期热门美剧榜",
        "short_name": "美剧",
        "medium_name": "近期热门",
        "total": 1,
        "n_followers": 36531,
        "updated_at": "2026-07-25 03:01:06",
        "cover_url": "https://img.example/cover.jpg",
        "header_bg_image": "https://img.example/backdrop.jpg",
        "category_tabs": [
            {
                "category": "美剧",
                "items": [
                    {"id": "ECFA5DI7Q", "name": "近期热门", "current": True},
                    {"id": "ECVACWVGI", "name": "高分经典", "current": False},
                ],
            },
            {
                "category": "英剧",
                "items": [
                    {"id": "ECVACXBWI", "name": "高分经典", "current": False},
                ],
            },
        ],
        }
        items_payload = {
        "start": 0,
        "total": 1,
        "subject_collection_items": [
            {
                "rank": 1,
                "id": "37061179",
                "title": "校园之外 第一季",
                "type": "tv",
                "card_subtitle": "2026 / 美国 / 剧情 爱情 运动",
                "pic": {"large": "https://img.example/poster.jpg"},
                "rating": {"value": 8.4, "count": 93897},
                "url": "https://movie.douban.com/subject/37061179/",
            }
        ],
        }

        result = douban.normalize_collection(metadata, items_payload, 0, 20)

        self.assertEqual([category["name"] for category in result["categories"]], ["美剧", "英剧"])
        self.assertEqual([item["name"] for item in result["categories"][1]["items"]], ["高分经典"])
        self.assertEqual(result["items"][0]["year"], "2026")
        self.assertEqual(result["items"][0]["rating"], 8.4)
        self.assertEqual(result["items"][0]["type"], "tv")

    def test_normalize_item_falls_back_to_generated_douban_url(self) -> None:
        """条目未提供网页地址时应生成固定豆瓣域名链接。"""
        result = douban.normalize_item({"id": "1292052", "title": "肖申克的救赎"}, 1)
        self.assertEqual(result["url"], "https://movie.douban.com/subject/1292052/")

    def test_resolve_collection_switches_to_selected_region(self) -> None:
        """地区变化后，旧地区的榜单 ID 应切换到新地区首项。"""
        self.assertEqual(
            douban.resolve_collection_id(
                CATEGORIES,
                region="大陆剧",
                requested_id="ECFA5DI7Q",
                fallback_id="ECFA5DI7Q",
            ),
            "MAINLANDHOT",
        )

    def test_filter_ui_uses_moviepilot_native_components(self) -> None:
        """探索筛选只应由 MoviePilot 的原生渲染组件组成。"""
        ui = douban.build_filter_ui(CATEGORIES)
        self.assertEqual(ui[0]["content"][0]["content"][0]["text"], "地区")
        self.assertEqual(ui[2]["props"]["show"], '{{region === "美剧"}}')
        components = []

        def collect(nodes):
            for node in nodes:
                components.append(node["component"])
                collect(node.get("content") or [])

        collect(ui)
        self.assertTrue(set(components) <= {"div", "VLabel", "VChipGroup", "VChip"})

    def test_media_payload_exposes_native_card_fields(self) -> None:
        """海报与评分必须使用 MediaInfo 的原生字段名。"""
        payload = douban.media_info_payload(
            {
                "rank": 1,
                "id": "1292052",
                "title": "肖申克的救赎",
                "type": "movie",
                "year": "1994",
                "poster": "https://img1.doubanio.com/view/photo/l/public/p480747492.webp",
                "rating": 9.7,
                "rating_count": 3000000,
            },
            {"name": "豆瓣电影 Top 250", "filter_name": "高分经典"},
        )
        self.assertEqual(payload["mediaid_prefix"], "douban")
        self.assertEqual(payload["douban_id"], "1292052")
        self.assertTrue(payload["poster_path"].startswith("https://img1.doubanio.com/"))
        self.assertEqual(payload["vote_average"], 9.7)

    def test_img9_poster_uses_compatible_cdn_mirror(self) -> None:
        """img9 路径应改写为当前 MoviePilot 图片代理可访问的镜像。"""
        item = douban.normalize_item({
            "id": "37061179",
            "title": "校园之外 第一季",
            "type": "tv",
            "pic": {
                "large": "https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2932988314.jpg"
            },
        })
        self.assertEqual(
            item["poster"],
            "https://img1.doubanio.com/view/photo/m_ratio_poster/public/p2932988314.jpg",
        )


if __name__ == "__main__":
    unittest.main()
