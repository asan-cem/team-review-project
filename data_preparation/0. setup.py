#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로젝트 자동 설정 스크립트

이 스크립트는 새로운 개발자가 프로젝트를 클론한 후 
자동으로 환경을 설정할 수 있도록 도와줍니다.

사용법:
    python setup.py

기능:
- 가상환경 생성 및 활성화
- 필요한 패키지 설치
- Google Cloud 인증 안내
- 프로젝트 구조 확인

작성자: Claude AI
작성일: 2025년 7월 10일
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, shell=False):
    """명령어 실행 및 결과 반환"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def print_step(step_num, description):
    """단계별 진행상황 출력"""
    print(f"\n{'='*60}")
    print(f"📋 단계 {step_num}: {description}")
    print('='*60)

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} 확인됨")
        return True
    else:
        print(f"❌ Python 3.8 이상이 필요합니다. 현재 버전: {version.major}.{version.minor}.{version.micro}")
        return False

def create_virtual_environment():
    """가상환경 생성"""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("✅ 가상환경이 이미 존재합니다.")
        return True
    
    print("🔧 가상환경 생성 중...")
    success, output = run_command([sys.executable, "-m", "venv", ".venv"])
    
    if success:
        print("✅ 가상환경 생성 완료")
        return True
    else:
        print(f"❌ 가상환경 생성 실패: {output}")
        return False

def get_activation_command():
    """운영체제별 가상환경 활성화 명령어 반환"""
    if platform.system() == "Windows":
        return ".venv\\Scripts\\activate"
    else:
        return "source .venv/bin/activate"

def install_requirements():
    """패키지 설치"""
    print("📦 필요한 패키지 설치 중...")
    
    # 가상환경의 pip 경로 찾기
    if platform.system() == "Windows":
        pip_path = ".venv\\Scripts\\pip"
    else:
        pip_path = ".venv/bin/pip"
    
    # requirements.txt 설치
    success, output = run_command([pip_path, "install", "-r", "requirements.txt"])
    
    if success:
        print("✅ 패키지 설치 완료")
        return True
    else:
        print(f"❌ 패키지 설치 실패: {output}")
        return False

def check_project_structure():
    """프로젝트 구조 확인"""
    required_files = [
        "1. data_processor.py",
        "2. text_processor.py", 
        "3. build_dashboard_html.py",
        "requirements.txt",
        "rawdata/"
    ]
    
    print("📁 프로젝트 구조 확인 중...")
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 누락된 파일/폴더:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ 프로젝트 구조 확인 완료")
        return True

def print_usage_guide():
    """사용법 안내"""
    activation_cmd = get_activation_command()
    
    print(f"""
{'='*60}
🎉 설정 완료! 이제 다음과 같이 사용하세요:
{'='*60}

1️⃣ 가상환경 활성화:
   {activation_cmd}

2️⃣ Google Cloud 인증 설정:
   - Google Cloud Console에서 서비스 계정 키 다운로드
   - 환경변수 설정: export GOOGLE_APPLICATION_CREDENTIALS="키파일경로"

3️⃣ 데이터 처리 실행:
   python "1. data_processor.py"          # 데이터 전처리
   python "2. text_processor.py"          # AI 텍스트 분석  
   python "3. build_dashboard_html.py"    # 대시보드 생성

4️⃣ rawdata 폴더에 원본 데이터 파일 배치:
   - 설문조사진행현황[VCRCRIC120S]_YYYY_H.xlsx 형식

📚 자세한 사용법은 각 파일 상단의 주석을 참조하세요.

{'='*60}
""")

def main():
    """메인 실행 함수"""
    print("🚀 서울아산병원 협업평가 시스템 자동 설정을 시작합니다...")
    
    # 1단계: Python 버전 확인
    print_step(1, "Python 버전 확인")
    if not check_python_version():
        sys.exit(1)
    
    # 2단계: 프로젝트 구조 확인
    print_step(2, "프로젝트 구조 확인") 
    if not check_project_structure():
        print("❌ 프로젝트 구조에 문제가 있습니다. 파일을 확인하세요.")
        sys.exit(1)
    
    # 3단계: 가상환경 생성
    print_step(3, "가상환경 생성")
    if not create_virtual_environment():
        sys.exit(1)
    
    # 4단계: 패키지 설치
    print_step(4, "패키지 설치")
    if not install_requirements():
        sys.exit(1)
    
    # 5단계: 사용법 안내
    print_step(5, "설정 완료 및 사용법 안내")
    print_usage_guide()

if __name__ == "__main__":
    main()