"""기아 셀토스 하이브리드 컨시어지 봇 메인 실행 스크립트"""

import argparse
from datetime import datetime
import os
import sys

def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

from modules.car_profile import OwnerCarProfile
from modules.collectors import SeltosInfoCollector
from modules.gemini_advisor import GeminiSeltosAdvisor
from notifier import DiscordSeltosNotifier


def print_banner():
    print("=" * 65)
    print("   🚗 기아 셀토스 하이브리드 시그니처 오너 전담 컨시어지 봇")
    print("=" * 65)


def run_concierge(dry_run: bool = False) -> bool:
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 오너 사양 로드 및 정보 수집 시작...")

    profile = OwnerCarProfile()
    print(f"🚙 등록 차량: {profile.get_summary_str()}")
    print(f"⏳ 출고 D-Day: {profile.get_days_until_delivery()}일 남음 (예정: {profile.expected_delivery})")

    collector = SeltosInfoCollector()
    news_items = collector.collect_all()
    print(f"📡 수집된 셀토스/하이브리드 관련 뉴스: {len(news_items)}건")

    print("\n🤖 Gemini AI 수석 컨시어지 브리핑 생성 중...")
    advisor = GeminiSeltosAdvisor()
    briefing = advisor.generate_briefing(profile, news_items)
    print(f"✨ [인사말] {briefing.greeting}")
    print(f"✨ [출고팁] {briefing.d_day_msg}")
    print(f"✨ [옵션팁] {briefing.option_spotlight}")

    notifier = DiscordSeltosNotifier()
    print("\n📬 디스코드 채널로 브리핑 전송 중...")
    success = notifier.send_concierge_report(profile, briefing, news_items, dry_run=dry_run)

    if success:
        print("✅ 디스코드 오너 브리핑 발송 완료!")
    else:
        print("❌ 디스코드 브리핑 발송 실패.")

    return success


def main():
    parser = argparse.ArgumentParser(description="기아 셀토스 하이브리드 컨시어지 봇")
    parser.add_argument("--test", action="store_true", help="디스코드 웹훅 연동 테스트 카드를 전송합니다.")
    parser.add_argument("--dry-run", action="store_true", help="디스코드 발송 없이 로컬에서만 실행합니다.")
    args = parser.parse_args()

    print_banner()

    if args.test:
        print("\n🧪 [디스코드 웹훅 연동 테스트]")
        notifier = DiscordSeltosNotifier()
        if notifier.test_connection():
            print("✅ 디스코드 웹훅 연결 성공! 채널에서 확인해 보세요.")
        else:
            print("❌ 디스코드 웹훅 연결 실패.")
        return

    run_concierge(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
