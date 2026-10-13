"""Gemini AI 오너 전담 수석 컨시어지 어드바이저 모듈"""

from dataclasses import dataclass
import json
import os
import time
import urllib.request
from typing import List, Optional

from modules.car_profile import OwnerCarProfile
from modules.collectors import SeltosNewsItem


@dataclass
class ConciergeBriefing:
    greeting: str
    d_day_msg: str
    recall_alert: str
    option_spotlight: str
    owner_guide: str


class GeminiSeltosAdvisor:
    """기아 수석 인스트럭터 & 오너 전담 컨시어지 AI"""

    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
    MODELS = ["gemini-flash-latest", "gemini-flash-lite-latest"]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 15 and not self.api_key.startswith("your_"))

    def generate_briefing(self, profile: OwnerCarProfile, news_items: List[SeltosNewsItem]) -> ConciergeBriefing:
        d_day = profile.get_days_until_delivery()
        opts_str = ", ".join([f"{o['name']}({o['desc']})" for o in profile.options])
        news_text = "\n".join([f"[{it.category}] ({it.source}) {it.title}" for it in news_items[:8]])

        if not self.is_configured:
            return self._fallback_briefing(profile, d_day)

        prompt = f"""
당신은 기아자동차 연구소 수석 엔지니어이자, 예비 차주를 1:1로 밀착 케어하는 최고급 '기아 셀토스 하이브리드 오너 전담 컨시어지'입니다.
차주님은 2026년식 기아 The New 셀토스 1.6 하이브리드 시그니처 트림 풀옵션을 계약하셨고 12월 초 출고를 손꼽아 기다리고 계십니다.

[차주 차량 스펙]
- 모델: {profile.model_year} {profile.model_name} {profile.powertrain} {profile.trim}
- 출고 예정일: {profile.expected_delivery} (약 {d_day}일 남음)
- 장착 옵션: {opts_str}

[오늘 감지된 기아차 / 셀토스 / 현대기아 하이브리드 관련 뉴스]
{news_text}

[작성 지침 - 전문적이고 신뢰감 넘치며 친절한 어조로 아래 JSON 형식에 맞추어 한국어로 작성할 것]
1. greeting: 차주님께 전하는 따뜻하고 에너지 넘치는 인사말 1문장 (셀토스 오너십 강조).
2. d_day_msg: 12월 초 출고 D-Day({d_day}일)와 관련된 격려 및 신차 검수/출고 준비 팁 1문장.
3. recall_alert: 수집된 뉴스 중 리콜/무상수리/엔진오일 이슈가 있으면 핵심 안내, 특별한 이슈가 없으면 현재 파워트레인 정상 상태 및 정기점검 권고 사항 2문장.
4. option_spotlight: 차주가 선택한 6대 옵션(HUD팩, 드라이브와이즈, 모니터링팩, 빌트인캠2플러스, 스타일, 컴포트) 중 오늘의 원픽 1개를 골라 200% 활용하는 꿀팁 2문장 (실제 버튼 조작이나 주행 상황 예시 포함).
5. owner_guide: 1.6 하이브리드 엔진 특성(회생제동 단계 조절, 겨울철 배터리 관리, 연비 주행법 등)에 대한 프로 드라이빙 조언 2문장.

응답은 오직 올바른 JSON 형식이어야 합니다:
{{
  "greeting": "...",
  "d_day_msg": "...",
  "recall_alert": "...",
  "option_spotlight": "...",
  "owner_guide": "..."
}}
"""

        for model_name in self.MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            for attempt in range(1, 3):
                try:
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "responseMimeType": "application/json",
                        },
                    }
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json; charset=utf-8"},
                    )
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        resp_json = json.loads(resp.read().decode("utf-8"))

                    candidates = resp_json.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if text:
                            res = json.loads(text)
                            return ConciergeBriefing(
                                greeting=res.get("greeting", "셀토스 하이브리드 오너님, 즐거운 하루 되세요!"),
                                d_day_msg=res.get("d_day_msg", f"12월 초 신차 출고까지 약 {d_day}일 남았습니다. 완벽한 출고 검수를 함께 준비합니다."),
                                recall_alert=res.get("recall_alert", "현재 셀토스 하이브리드 파워트레인 대상 긴급 리콜 이슈는 발견되지 않았습니다."),
                                option_spotlight=res.get("option_spotlight", "빌트인캠 2 플러스의 주차 녹화와 증강현실 내비게이션으로 안전하고 쾌적한 드라이빙을 누려보세요."),
                                owner_guide=res.get("owner_guide", "스마트 회생제동 모드를 활용하시면 브레이크 패드 마모를 줄이고 도심 연비를 극대화할 수 있습니다.")
                            )
                    break
                except Exception as e:
                    print(f"[Gemini 어드바이저 오류 {model_name} (시도 {attempt}/2)] {e}")
                    if attempt < 2:
                        time.sleep(attempt * 2)

        return self._fallback_briefing(profile, d_day)

    def _fallback_briefing(self, profile: OwnerCarProfile, d_day: int) -> ConciergeBriefing:
        return ConciergeBriefing(
            greeting="셀토스 하이브리드 시그니처 예비 차주님, 오늘의 차량 리포트를 전달해 드립니다!",
            d_day_msg=f"12월 초 출고까지 약 {d_day}일 남았습니다! 틴팅(선팅) 농도와 신차 검수 체크리스트를 미리 구상해 보세요.",
            recall_alert="현재 셀토스 1.6 하이브리드 및 드라이브 와이즈 모듈 관련 신규 긴급 리콜은 접수되지 않았습니다.",
            option_spotlight="[모니터링 팩 & HUD 팩] 좁은 주차공간에서는 원격 스마트 주차 보조(RSPA)와 360도 서라운드 뷰를 활용해 휠 긁힘 없이 안전하게 주차하세요.",
            owner_guide="1.6 HEV 파워트레인은 패들 시프트를 이용해 회생제동 감도를 AUTO로 설정하면 도심 실연비 20km/L 이상을 가볍게 달성할 수 있습니다."
        )
