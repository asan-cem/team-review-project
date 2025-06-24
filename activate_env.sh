#!/bin/bash

# 프로젝트 가상환경 자동 활성화 스크립트
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/venv"

echo "🔧 팀 리뷰 프로젝트 가상환경 활성화 중..."
echo "📁 프로젝트 경로: $PROJECT_DIR"

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 가상환경이 존재하지 않습니다. 생성 중..."
    python3 -m venv "$VENV_PATH"
    if [ $? -eq 0 ]; then
        echo "✅ 가상환경이 성공적으로 생성되었습니다."
    else
        echo "❌ 가상환경 생성에 실패했습니다."
        exit 1
    fi
fi

# 가상환경 활성화
source "$VENV_PATH/bin/activate"

# 의존성 확인 및 설치
if [ ! -f "$VENV_PATH/pyvenv.cfg" ]; then
    echo "❌ 가상환경이 손상되었습니다. 재생성 중..."
    rm -rf "$VENV_PATH"
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
fi

# requirements.txt가 있으면 의존성 설치
if [ -f "requirements.txt" ]; then
    echo "📦 의존성 패키지 확인 중..."
    pip install -r requirements.txt --quiet
    if [ $? -eq 0 ]; then
        echo "✅ 모든 의존성이 설치되었습니다."
    else
        echo "⚠️  일부 의존성 설치에 문제가 있을 수 있습니다."
    fi
fi

echo "🎉 가상환경이 활성화되었습니다!"
echo "🐍 Python 경로: $(which python)"
echo "📦 pip 경로: $(which pip)"
echo ""
echo "💡 사용법:"
echo "   - Python 실행: python main.py"
echo "   - Claude 버전: python process_with_claude.py"
echo "   - 가상환경 비활성화: deactivate"
echo "" 