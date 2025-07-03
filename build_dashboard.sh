#!/bin/bash

# 대시보드 빌드 편의 스크립트

echo "🏥 서울아산병원 협업평가 대시보드 생성기"
echo "=========================================="
echo ""
echo "사용할 버전을 선택하세요:"
echo "1) 기존 버전 (빠름, 기본 기능)"
echo "2) 개선된 버전 (안전함, 고급 기능)"
echo "3) 개선된 버전 (상세 로그)"
echo "4) 두 버전 모두 실행하여 비교"
echo ""

read -p "선택 (1-4): " choice

case $choice in
    1)
        echo "🚀 기존 버전으로 대시보드 생성 중..."
        python build_dashboard_html.py
        ;;
    2)
        echo "🔒 개선된 버전으로 대시보드 생성 중..."
        python build_dashboard_html_improved.py
        ;;
    3)
        echo "📋 개선된 버전 (상세 로그)으로 대시보드 생성 중..."
        python build_dashboard_html_improved.py --verbose
        ;;
    4)
        echo "⚖️ 두 버전 비교 실행 중..."
        echo ""
        echo "=== 기존 버전 ==="
        time python build_dashboard_html.py
        echo ""
        echo "=== 개선된 버전 ==="
        time python build_dashboard_html_improved.py
        echo ""
        echo "📊 비교 완료!"
        ;;
    *)
        echo "❌ 잘못된 선택입니다. 1-4 중에서 선택해주세요."
        exit 1
        ;;
esac

echo ""
echo "✅ 작업 완료!"
echo "📁 생성된 파일: 서울아산병원 협업평가 대시보드.html"