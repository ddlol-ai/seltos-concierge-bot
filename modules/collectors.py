"""국토부/자동차리콜센터 및 네이버/구글 뉴스 크롤러 모듈"""

from dataclasses import dataclass
from datetime import datetime
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Optional


@dataclass
class SeltosNewsItem:
    title: str
    link: str
    pub_date: str
    source: str
    category: str  # "RECALL" (리콜/결함), "NEWS" (출고/뉴스), "TECH" (옵션/하이브리드)
    snippet: str = ""


class SeltosInfoCollector:
    """셀토스 하이브리드 관련 뉴스 및 리콜 정보 수집기"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def _clean_text(self, text: str) -> str:
        clean = re.sub(r"<.*?>", "", text)
        clean = clean.replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        return clean.strip()

    def fetch_google_news(self, query: str, category: str, limit: int = 5) -> List[SeltosNewsItem]:
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
        items = []

        try:
            req = urllib.request.Request(url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)

            for it in root.findall(".//channel/item")[:limit]:
                title = self._clean_text(it.findtext("title", ""))
                link = it.findtext("link", "")
                pub_date = it.findtext("pubDate", "")
                source = it.findtext("source", "구글 뉴스")

                # 제목에서 출처 분리 (예: '... - 중앙일보')
                if " - " in title:
                    title_part, source_part = title.rsplit(" - ", 1)
                    title = title_part.strip()
                    source = source_part.strip()

                items.append(SeltosNewsItem(
                    title=title,
                    link=link,
                    pub_date=pub_date,
                    source=source,
                    category=category,
                    snippet=title
                ))
        except Exception as e:
            print(f"[수집 경고 - Google News '{query}'] {e}")

        return items

    def collect_all(self) -> List[SeltosNewsItem]:
        all_items: List[SeltosNewsItem] = []

        # 1. 리콜 및 무상수리 / 결함 관련
        recall_items = self.fetch_google_news("기아 셀토스 리콜 OR 무상수리 OR 결함", category="RECALL", limit=4)
        all_items.extend(recall_items)

        # 2. 하이브리드 및 납기/출고 대기 관련
        delivery_items = self.fetch_google_news("기아 셀토스 하이브리드 출고 OR 납기 OR 페이스리프트", category="NEWS", limit=4)
        all_items.extend(delivery_items)

        # 3. 옵션/신기술/기아 OTA 소프트웨어 관련
        tech_items = self.fetch_google_news("기아 빌트인캠2 OR 드라이브와이즈 OR ccNC 내비게이션 업데이트", category="TECH", limit=3)
        all_items.extend(tech_items)

        # 중복 제목 제거
        seen_titles = set()
        deduped = []
        for it in all_items:
            norm_title = re.sub(r"\s+", "", it.title)
            if norm_title not in seen_titles and len(norm_title) > 5:
                seen_titles.add(norm_title)
                deduped.append(it)

        return deduped
