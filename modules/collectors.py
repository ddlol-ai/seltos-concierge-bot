"""국토부/자동차리콜센터 및 네이버/구글 뉴스 크롤러 모듈"""

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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

    def fetch_google_news(self, query: str, category: str, limit: int = 5, max_days: int = 7) -> List[SeltosNewsItem]:
        # Google News when:7d 필터 적용
        scoped_query = f"{query} when:{max_days}d"
        encoded = urllib.parse.quote(scoped_query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
        items = []
        now = datetime.now(timezone.utc)

        try:
            req = urllib.request.Request(url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)

            for it in root.findall(".//channel/item"):
                title = self._clean_text(it.findtext("title", ""))
                link = it.findtext("link", "")
                pub_date_raw = it.findtext("pubDate", "")
                source = it.findtext("source", "구글 뉴스")

                # 발행일 파싱 및 N일 전 계산
                pub_dt = None
                days_ago = 0
                if pub_date_raw:
                    try:
                        pub_dt = parsedate_to_datetime(pub_date_raw)
                        days_ago = max(0, (now - pub_dt).days)
                    except Exception:
                        pass

                # 엄격한 날짜 필터 (지정된 일수 초과 시 스킵)
                if pub_dt and days_ago > max_days:
                    continue

                # 제목에서 출처 분리
                if " - " in title:
                    title_part, source_part = title.rsplit(" - ", 1)
                    title = title_part.strip()
                    source = source_part.strip()

                # 날짜 라벨 포맷 (예: "오늘", "1일 전", "3일 전")
                time_label = "오늘" if days_ago == 0 else f"{days_ago}일 전"

                items.append(SeltosNewsItem(
                    title=title,
                    link=link,
                    pub_date=time_label,
                    source=source,
                    category=category,
                    snippet=title
                ))
                if len(items) >= limit:
                    break
        except Exception as e:
            print(f"[수집 경고 - Google News '{query}'] {e}")

        return items

    def collect_all(self) -> List[SeltosNewsItem]:
        all_items: List[SeltosNewsItem] = []

        # 1. 셀토스 하이브리드 출고/생산/납기/신차 뉴스 (최근 7일)
        hev_items = self.fetch_google_news("기아 셀토스 하이브리드", category="NEWS", limit=4, max_days=7)
        all_items.extend(hev_items)

        # 2. 셀토스 리콜/무상수리/엔진/결함 뉴스 (최근 14일)
        recall_items = self.fetch_google_news("기아 셀토스 리콜 OR 무상수리 OR 결함", category="RECALL", limit=3, max_days=14)
        all_items.extend(recall_items)

        # 3. 옵션/OTA 내비게이션/기술 업데이트 (최근 14일)
        tech_items = self.fetch_google_news("기아 빌트인캠2 OR 드라이브와이즈 OR ccNC 업데이트", category="TECH", limit=2, max_days=14)
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
