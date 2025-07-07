# 서울아산병원 협업평가 대시보드 - 환경 설정 가이드

## 🚀 빠른 시작

### 1. 환경 설정 (최초 1회만)
```bash
cd /home/cocori2864/team-review-project
./setup_environment.sh
source ~/.bashrc
```

### 2. 프로젝트 실행
```bash
runproject
```

## 📋 제공되는 스크립트

### 환경 설정 스크립트
- `setup_environment.sh`: 터미널 환경 설정 (최초 1회)
- `activate_venv.sh`: 가상환경만 활성화
- `run_project.sh`: 프로젝트 실행 환경 준비

### 편의 명령어 (환경 설정 후 사용 가능)
- `cdproject`: 프로젝트 디렉토리로 이동
- `activate`: 가상환경 활성화
- `runproject`: 프로젝트 실행 스크립트
- `dashboard`: 대시보드 HTML 생성
- `mainproc`: 메인 데이터 처리

## 🔧 수동 실행

가상환경 활성화가 필요한 경우:
```bash
cd /home/cocori2864/team-review-project
source .venv/bin/activate
```

개별 스크립트 실행:
```bash
python main.py                          # 메인 데이터 처리
python summarize_mutual_reviews.py      # 상호 리뷰 요약
python build_dashboard_html_v2.py       # 대시보드 v2.0 생성
python build_dashboard_html.py          # 기본 대시보드 생성
```

## 🆘 문제 해결

### 가상환경이 활성화되지 않는 경우
```bash
cd /home/cocori2864/team-review-project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 의존성 설치 문제
```bash
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 📁 파일 구조
```
team-review-project/
├── .venv/                              # 가상환경
├── setup_environment.sh               # 환경 설정
├── run_project.sh                      # 프로젝트 실행
├── activate_venv.sh                    # 가상환경 활성화
├── .bashrc_project                     # 프로젝트 bashrc 설정
├── requirements.txt                    # 의존성 목록
├── main.py                            # 메인 데이터 처리
├── build_dashboard_html_v2.py         # 대시보드 v2.0 생성
└── ...
```