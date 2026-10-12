"""디스코드 웹훅 전송 및 프리미엄 오너 Embed 카드 빌더 모듈"""

from datetime import datetime
import json
import os
import urllib.request
from typing import Dict, List, Optional

from modules.car_profile import OwnerCarProfile
from modules.collectors import SeltosNewsItem
from modules.gemini_advisor import ConciergeBriefing


class DiscordSeltosNotifier:
    """셀토스 오너 전용 디스코드 웹훅 발송기"""

    KIA_LOGO = "https://img.icons8.com/color/512/kia.png"

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")

    def test_connection(self) -> bool:
        if not self.webhook_url:
            print("❌ DISCORD_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
            return False

        desc = (
            "**축하드립니다!** 셀토스 하이브리드 시그니처 오너 맞춤형 브리핑 시스템이 디스코드 채널에 성공적으로 연결되었습니다.\n\n"
            "앞으로 리콜·무상수리 통지, 12월 출고 D-Day, 옵션별 200% 활용법 및 최신 자동차 뉴스를 매일 정기 배달해 드립니다."
        )

        payload = {
            "username": "기아 셀토스 하이브리드 컨시어지",
            "avatar_url": self.KIA_LOGO,
            "embeds": [
                {
                    "title": "🚗 기아 셀토스 하이브리드 오너 컨시어지 봇 연동 완료",
                    "description": desc,
                    "color": 0x05141F,  # 기아 미드나잇 블랙
                    "fields": [
                        {"name": "🚙 내 차 사양", "value": "2026 The New 셀토스 1.6 HEV 시그니처", "inline": True},
                        {"name": "🎯 장착 옵션", "value": "HUD · 드라와 · 모니터링 · 빌캠2+ · 스타일 · 컴포트", "inline": True},
                        {"name": "📅 출고 예정", "value": "2026년 12월 초순 (대기 모드)", "inline": True},
                    ],
                    "footer": {"text": "Kia Motors Owner Concierge • Powered by Gemini AI"},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
        }
        return self._send_payload(payload)

    def send_concierge_report(
        self,
        profile: OwnerCarProfile,
        briefing: ConciergeBriefing,
        news_items: List[SeltosNewsItem],
        dry_run: bool = False
    ) -> bool:
        now_str = datetime.now().strftime("%Y년 %m월 %d일")
        d_day = profile.get_days_until_delivery()
        d_day_badge = f"D-{d_day}" if d_day > 0 else "출고 완료 🎉"

        desc = (
            f"**{briefing.greeting}**\n\n"
            f"📌 **차량 사양**: `{profile.get_summary_str()}`\n"
            f"⏳ **출고 D-Day**: `{d_day_badge}` ({profile.expected_delivery} 전후 예정)\n"
            f"> {briefing.d_day_msg}"
        )

        # Embed 1: 오너 메인 컨시어지 브리핑 카드
        main_embed = {
            "title": f"🚗 [기아 셀토스 하이브리드 오너 브리핑] • {now_str}",
            "description": desc,
            "color": 0xBB162B,  # 기아 레드 포인트
            "fields": [
                {
                    "name": "🚨 안전 점검 & 리콜/무상수리 현황",
                    "value": f"{briefing.recall_alert}",
                    "inline": False,
                },
                {
                    "name": "✨ 오늘의 옵션 200% 활용 꿀팁",
                    "value": f"{briefing.option_spotlight}",
                    "inline": False,
                },
                {
                    "name": "🔋 1.6 하이브리드 연비 & 드라이빙 가이드",
                    "value": f"{briefing.owner_guide}",
                    "inline": False,
                },
            ],
            "footer": {"text": "Kia Owner Concierge • 기아 연구소 수석 엔지니어 AI"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Embed 2: 최신 뉴스 및 업계 동향
        news_fields = []
        for it in news_items[:5]:
            icon = "🚨" if it.category == "RECALL" else ("⚡" if it.category == "TECH" else "📰")
            title_link = f"[{it.title}]({it.link})"
            news_fields.append({
                "name": f"{icon} {it.source} ({it.category})",
                "value": title_link,
                "inline": False,
            })

        news_embed = {
            "title": "📡 셀토스 & 현대기아 하이브리드 실시간 모니터링 뉴스",
            "description": "국토교통부, 자동차리콜센터 및 포털 최신 언론 보도 핫토픽 요약",
            "color": 0x1A2B49,
            "fields": news_fields if news_fields else [{"name": "공지", "value": "새로운 특이 결함이나 긴급 리콜 보도가 없습니다.", "inline": False}],
            "footer": {"text": "실시간 데이터 수집 • 자동차리콜센터 & Google News"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        payload = {
            "username": "기아 셀토스 하이브리드 컨시어지",
            "avatar_url": self.KIA_LOGO,
            "embeds": [main_embed, news_embed],
        }

        if dry_run:
            print("\n[Dry Run] 전송될 페이로드:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return True

        return self._send_payload(payload)

    def _send_payload(self, payload: Dict) -> bool:
        if not self.webhook_url:
            print("❌ DISCORD_WEBHOOK_URL이 지정되지 않았습니다.")
            return False

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status in (200, 204)
        except Exception as e:
            print(f"[디스코드 발송 실패] {e}")
            return False
