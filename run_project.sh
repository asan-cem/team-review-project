#!/bin/bash

# 프로젝트 실행 스크립트
echo "🚀 서울아산병원 협업평가 대시보드 프로젝트 실행"
echo "==============================================="

# 프로젝트 디렉토리로 이동
cd /home/cocori2864/team-review-project

# 가상환경 활성화
echo "📦 가상환경 활성화 중..."
source .venv/bin/activate

# 의존성 설치 확인
echo "📋 의존성 설치 확인 중..."
pip install -r requirements.txt

echo ""
echo "✅ 준비 완료! 다음 명령어로 각 스크립트를 실행할 수 있습니다:"
echo ""
echo "1. 메인 데이터 처리:"
echo "   python main.py"
echo ""
echo "2. 상호 리뷰 요약:"
echo "   python summarize_mutual_reviews.py"
echo ""
echo "3. 대시보드 HTML 생성:"
echo "   python build_dashboard_html_v2.py"
echo ""
echo "4. 기본 대시보드 생성:"
echo "   python build_dashboard_html.py"
echo ""
echo "현재 활성화된 Python 환경:"
echo "Python 경로: $(which python)"
echo "Python 버전: $(python --version)"
echo ""

# 셸 시작
exec bash