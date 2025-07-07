#!/bin/bash

# 가상환경 활성화 스크립트
echo "가상환경 활성화 중..."

# 프로젝트 디렉토리로 이동
cd /home/cocori2864/team-review-project

# 가상환경 활성화
source .venv/bin/activate

# 활성화 확인
echo "가상환경이 활성화되었습니다."
echo "Python 경로: $(which python)"
echo "Python 버전: $(python --version)"

# 셸 시작
exec bash