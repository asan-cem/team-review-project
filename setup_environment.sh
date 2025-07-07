#!/bin/bash

# 환경 설정 스크립트
echo "🔧 프로젝트 환경 설정 중..."

# 현재 디렉토리 확인
PROJECT_DIR="/home/cocori2864/team-review-project"

# .bashrc에 프로젝트 설정 추가
echo ""
echo "📝 .bashrc 설정 추가 중..."

# 기존 설정 제거 (중복 방지)
grep -v "source $PROJECT_DIR/.bashrc_project" ~/.bashrc > ~/.bashrc.tmp
mv ~/.bashrc.tmp ~/.bashrc

# 새 설정 추가
echo "" >> ~/.bashrc
echo "# 서울아산병원 협업평가 대시보드 프로젝트 설정" >> ~/.bashrc
echo "source $PROJECT_DIR/.bashrc_project" >> ~/.bashrc

echo "✅ 환경 설정 완료!"
echo ""
echo "다음 명령어로 새 터미널을 시작하거나 설정을 적용하세요:"
echo "  source ~/.bashrc"
echo ""
echo "또는 새 터미널을 열면 자동으로 프로젝트 환경이 설정됩니다."
echo ""
echo "사용 가능한 명령어:"
echo "  cdproject  - 프로젝트 디렉토리로 이동"
echo "  activate   - 가상환경 활성화"
echo "  runproject - 프로젝트 실행 스크립트"
echo "  dashboard  - 대시보드 생성"
echo "  mainproc   - 메인 데이터 처리"