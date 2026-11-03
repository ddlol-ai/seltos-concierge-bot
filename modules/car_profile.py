"""셀토스 오너 맞춤형 사양 및 옵션 프로필 정의 모듈"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class OwnerCarProfile:
    """차주 계약 차량 정보 및 탑재 옵션"""
    model_name: str = "기아 The New 셀토스"
    model_year: str = "2026년식"
    powertrain: str = "하이브리드 (1.6 HEV)"
    trim: str = "시그니처 (Signature)"
    expected_delivery: str = "2026-12-05"  # 12월 초 출고 예정
    contract_date: str = "2026-08-22"      # 최초 계약 체결일
    initial_wait_number: int = 30          # 최초 계약 순번
    next_check_date: str = "2026-11-16"    # 카마스터 3차 순번 확인 약속일 (한 자릿수 진입 체크)
    
    # 카마스터 대기 순번 추적 이력
    current_wait_number: int = 14  # 11월 3일 카마스터 조회 기준
    wait_history: List[Dict[str, any]] = field(default_factory=lambda: [
        {"date": "2026-08-22", "rank": 30, "desc": "최초 계약 접수 (30번)"},
        {"date": "2026-10-07", "rank": 27, "desc": "46일간 3대 소진 (-3)"},
        {"date": "2026-11-03", "rank": 14, "desc": "27일간 13대 급소진 (-13)"}
    ])
    
    # 추가 선택 옵션 목록
    options: List[Dict[str, str]] = field(default_factory=lambda: [
        {"name": "HUD 팩", "desc": "컴바이너 타입 헤드업 디스플레이, 레인센서"},
        {"name": "드라이브 와이즈", "desc": "전방 충돌방지 보조, 스마트 크루즈 컨트롤, 후측방 충돌방지, 안전 하차 경고, 고속도로 주행 보조(HDA)"},
        {"name": "모니터링 팩", "desc": "서라운드 뷰 모니터(SVM), 후측방 모니터(BVM), 원격 스마트 주차 보조(RSPA), 후방 주차 충돌방지"},
        {"name": "빌트인캠 2 플러스", "desc": "QHD 고화질 빌트인캠 2, 증강현실(AR) 내비게이션, 음성녹음 지원, 주차 충격 녹화"},
        {"name": "스타일", "desc": "프로젝션 LED 헤드램프, 프론트 LED 턴시그널, LED 리어 콤비네이션 램프, 18인치 전면가공 휠"},
        {"name": "컴포트", "desc": "운전석 메모리 시트(IMS), 운전석 이지 억세스, 동승석 파워시트, 2열 열선시트"}
    ])

    def get_days_until_delivery(self) -> int:
        """출고 예정일까지 남은 D-Day 계산"""
        try:
            target = datetime.strptime(self.expected_delivery, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (target - today).days
        except Exception:
            return 50

    def get_days_until_next_check(self) -> int:
        """다음 카마스터 연락 예정일까지 남은 D-Day 계산"""
        try:
            target = datetime.strptime(self.next_check_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (target - today).days
        except Exception:
            return 13

    def get_summary_str(self) -> str:
        opts = ", ".join([o["name"] for o in self.options])
        return f"{self.model_year} {self.model_name} {self.powertrain} {self.trim} (풀옵션 패키지: {opts})"
