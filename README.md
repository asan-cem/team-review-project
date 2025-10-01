# 서울아산병원 협업평가 시스템

> AI 기반 의료진 협업 피드백 분석 및 대시보드 시스템

## 📚 프로젝트 실행을 위한 완벽 가이드 (비개발자용)

이 가이드는 서울아산병원 협업평가 시스템을 실행하기 위해 필요한 모든 도구와 기술에 대해 처음부터 차근차근 설명합니다.

### 🖥️ WSL (Windows Subsystem for Linux)란?

**WSL**은 Windows에서 Linux를 실행할 수 있게 해주는 Microsoft의 기술입니다.

#### 왜 WSL을 사용하나요?
1. **개발 환경 통일**: 많은 개발 도구들이 Linux 기반으로 만들어져 있습니다
2. **성능 향상**: Windows에서 직접 실행하는 것보다 빠른 경우가 많습니다
3. **호환성**: Python 패키지들이 Linux에서 더 잘 작동합니다
4. **편의성**: Linux 명령어를 Windows에서 그대로 사용할 수 있습니다

#### WSL 설치 방법
```powershell
# PowerShell을 관리자 권한으로 실행 후
wsl --install

# 설치 후 컴퓨터 재시작
# Ubuntu 사용자명과 비밀번호 설정
```

### 🟢 Node.js란?

**Node.js**는 JavaScript를 웹 브라우저 밖에서도 실행할 수 있게 해주는 환경입니다.

#### 왜 Node.js가 필요한가요?
1. **패키지 관리**: npm(Node Package Manager)으로 다양한 도구를 쉽게 설치할 수 있습니다
2. **개발 도구 실행**: 많은 개발 도구들이 Node.js 기반으로 작동합니다
3. **JavaScript 실행**: 서버나 컴퓨터에서 JavaScript 코드를 실행할 수 있습니다

#### Node.js 설치 및 확인
```bash
# WSL Ubuntu에서 설치
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# 설치 확인
node --version  # v20.x.x 같은 버전이 표시되면 성공
npm --version   # 10.x.x 같은 버전이 표시되면 성공
```

### 💻 VS Code (Visual Studio Code)란?

**VS Code**는 Microsoft에서 만든 무료 코드 편집기입니다.

#### 왜 VS Code를 사용하나요?
1. **사용하기 쉬움**: 초보자도 쉽게 사용할 수 있는 인터페이스
2. **강력한 기능**: 자동 완성, 오류 표시, 디버깅 등
3. **확장 프로그램**: Python, WSL 등 다양한 확장 기능
4. **무료**: 완전 무료로 모든 기능 사용 가능

#### VS Code 설치 및 설정
1. [VS Code 다운로드](https://code.visualstudio.com/)
2. 설치 후 확장 프로그램 설치:
   - Python
   - WSL
   - Pylance
   - Python Debugger

### 🐍 Python이란?

**Python**은 배우기 쉽고 강력한 프로그래밍 언어입니다.

#### 이 프로젝트에서 Python의 역할
1. **데이터 처리**: Excel 파일 읽기, 정리, 분석
2. **AI 연동**: Google Gemini API를 통한 텍스트 분석
3. **대시보드 생성**: HTML 파일 생성 및 차트 구성
4. **자동화**: 반복 작업을 자동으로 처리

#### Python 주요 라이브러리 설명
- **pandas**: Excel 같은 데이터를 다루는 도구
  - Excel 파일을 읽고 쓰기
  - 데이터 필터링, 정렬, 그룹화
  - 통계 계산 (평균, 합계 등)
- **numpy**: 숫자 계산을 빠르게 해주는 도구
- **plotly**: 인터랙티브 차트를 만드는 도구
  - 막대 그래프, 선 그래프, 파이 차트 등
  - 마우스 오버 시 정보 표시
  - 확대/축소 가능한 차트
- **google-cloud-aiplatform**: Google AI 서비스 연결
  - Gemini Pro를 사용한 텍스트 분석
  - 감정 분석 및 키워드 추출
- **openpyxl**: Excel 파일 처리 도구
- **tqdm**: 진행 상황 표시 막대
- **streamlit**: 웹 애플리케이션 만들기 (선택사항)
- **scipy, scikit-learn**: 통계 및 머신러닝 도구

### 🤖 Claude CLI란?

**Claude CLI**는 Anthropic의 AI 어시스턴트 Claude를 명령줄에서 사용할 수 있게 해주는 도구입니다.

#### Claude CLI의 장점
1. **코드 작성 도움**: AI가 코드 작성을 도와줍니다
2. **문제 해결**: 오류가 발생했을 때 해결 방법을 제시합니다
3. **학습 도구**: 코드를 설명해주고 개선점을 제안합니다

#### Claude CLI 설치
```bash
# npm을 사용한 설치
npm install -g @anthropic-ai/claude-cli

# API 키 설정 (Anthropic 웹사이트에서 발급)
claude-cli auth
```

### 🖱️ Cursor란?

**Cursor**는 AI 기능이 내장된 코드 편집기로, VS Code를 기반으로 만들어졌습니다.

#### Cursor의 특별한 기능
1. **AI 자동 완성**: 코드를 작성하면 AI가 다음 코드를 예측해서 제안합니다
2. **대화형 코딩**: 채팅창에 "이 함수를 수정해줘"라고 말하면 AI가 코드를 수정해줍니다
3. **코드 설명**: 복잡한 코드를 선택하고 "설명해줘"라고 하면 쉽게 설명해줍니다
4. **오류 수정**: 오류가 발생하면 AI가 자동으로 해결 방법을 제안합니다

#### Cursor 설치 및 사용법
1. **다운로드**: [Cursor 공식 사이트](https://cursor.sh)에서 다운로드
2. **설치**: 일반 프로그램처럼 설치 (VS Code와 별도로 설치됨)
3. **API 키 설정**: 
   - 설정(Settings) → Cursor Settings → API Key
   - OpenAI 또는 Anthropic API 키 입력

#### Cursor 주요 단축키
- `Ctrl+K`: AI에게 코드 수정 요청
- `Ctrl+L`: 새 채팅 창 열기
- `Ctrl+Shift+L`: 현재 파일 전체를 컨텍스트로 채팅
- `Tab`: AI 제안 수락
- `Esc`: AI 제안 거절

#### VS Code vs Cursor 선택 가이드
- **VS Code 추천**: 
  - 무료로 사용하고 싶을 때
  - 다양한 확장 프로그램이 필요할 때
  - 전통적인 개발 환경을 선호할 때
  
- **Cursor 추천**:
  - AI 도움을 적극적으로 받고 싶을 때
  - 코딩을 처음 배우는 경우
  - 빠르게 프로토타입을 만들 때

#### 이 프로젝트에서 Cursor 활용하기
```python
# 예시: Cursor에서 "평균 점수가 80점 이상인 부서만 필터링하는 코드 작성해줘"라고 요청
# AI가 자동으로 다음과 같은 코드를 생성합니다:

high_score_departments = df[df['평균점수'] >= 80]
print(f"우수 부서 수: {len(high_score_departments)}")
```

### 🌐 HTML과 JavaScript란?

#### HTML (HyperText Markup Language)
웹 페이지의 **구조**를 만드는 언어입니다.
```html
<!DOCTYPE html>
<html>
<head>
    <title>페이지 제목</title>
</head>
<body>
    <h1>큰 제목</h1>
    <p>문단 내용</p>
    <button>버튼</button>
</body>
</html>
```

#### JavaScript
웹 페이지에 **동작**을 추가하는 프로그래밍 언어입니다.
```javascript
// 버튼 클릭 시 알림 표시
document.querySelector('button').addEventListener('click', function() {
    alert('버튼이 클릭되었습니다!');
});

// 차트 데이터 업데이트
function updateChart(newData) {
    chart.data = newData;
    chart.update();
}
```

#### 이 프로젝트에서의 역할
- **HTML**: 대시보드의 레이아웃과 구조 정의
- **JavaScript**: 
  - Plotly.js로 인터랙티브 차트 생성
  - 사용자 상호작용 처리 (필터링, 정렬 등)
  - 데이터 동적 업데이트

## 🚀 전체 환경 설정 가이드

### 1단계: WSL 설치 및 설정
```powershell
# Windows PowerShell (관리자 권한)
wsl --install
# 재부팅 후 Ubuntu 설정
```

### 2단계: 기본 도구 설치
```bash
# WSL Ubuntu 터미널에서
sudo apt update
sudo apt install -y python3-pip python3-venv git curl

# Node.js 설치
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 3단계: VS Code 설치 및 WSL 연결
1. Windows에서 VS Code 설치
2. VS Code 실행 후 WSL 확장 설치
3. `Ctrl+Shift+P` → "WSL: New Window" 선택

### 4단계: 프로젝트 클론 및 설정
```bash
# 프로젝트 다운로드
git clone https://github.com/your-repo/team-review-project.git
cd team-review-project

# Python 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 5단계: Google Cloud 설정
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성
3. Vertex AI API 활성화
4. 서비스 계정 키 생성 및 다운로드
5. 환경 변수 설정:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
```

## 📋 프로젝트 실행 순서

### 기본 실행 과정
```bash
# 1. 가상환경 활성화 (매번 터미널 열 때마다)
source .venv/bin/activate

# 2. 데이터 전처리
python "1. data_processor.py"

# 3. AI 텍스트 분석 (선택사항, 비용 발생)
python "2. text_processor.py"

# 4. 대시보드 생성
python "3. build_dashboard_html.py"

# 5. 생성된 HTML 파일 열기
# Windows에서: 파일 탐색기에서 더블클릭
# WSL에서: explorer.exe "서울아산병원 협업평가 결과.html"
```

## 🔧 문제 해결 가이드

### 자주 발생하는 문제와 해결법

#### 1. "command not found" 오류
```bash
# Python이 없다고 나올 때
sudo apt install python3

# pip가 없다고 나올 때
sudo apt install python3-pip
```

#### 2. "Module not found" 오류
```bash
# 가상환경이 활성화되었는지 확인
which python  # .venv 경로가 나와야 함

# 패키지 재설치
pip install -r requirements.txt
```

#### 3. Google Cloud 인증 오류
```bash
# 서비스 계정 키 파일 경로 확인
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# 권한 확인
chmod 600 /path/to/your/key.json
```

#### 4. 한글 깨짐 문제
```python
# Python 파일 맨 위에 추가
# -*- coding: utf-8 -*-

# pandas 읽기 시 인코딩 지정
pd.read_excel('파일명.xlsx', encoding='utf-8')
```

## 💡 유용한 팁

### VS Code 단축키
- `Ctrl+S`: 저장
- `Ctrl+/`: 주석 처리/해제
- `F5`: 디버깅 시작
- `Ctrl+` `: 터미널 열기

### Python 디버깅
```python
# 중간에 값 확인하기
print(f"현재 데이터 개수: {len(data)}")

# 오류 발생 위치 찾기
try:
    # 문제가 될 수 있는 코드
    result = process_data(data)
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
```

### Git 기본 명령어
```bash
# 변경사항 확인
git status

# 변경사항 저장
git add .
git commit -m "변경 내용 설명"

# 원격 저장소에 업로드
git push
```

## 🔗 도구들이 함께 작동하는 방식

### 전체 시스템 구조
```
Windows 10/11
    └── WSL (Ubuntu)
        ├── Python 3.x
        │   ├── pandas (Excel 데이터 처리)
        │   ├── plotly (차트 생성)
        │   └── google-cloud-aiplatform (AI 분석)
        ├── Node.js
        │   └── npm (패키지 관리, Claude CLI 설치)
        └── VS Code (코드 편집)
```

### 데이터 처리 흐름
1. **Excel 데이터 입력** → Python pandas로 읽기
2. **데이터 정제** → 부서명 표준화, 점수 변환
3. **AI 분석** (선택) → Google Gemini로 텍스트 분석
4. **차트 생성** → Plotly로 인터랙티브 차트 만들기
5. **HTML 생성** → JavaScript 포함된 대시보드 파일
6. **결과 확인** → 웹 브라우저에서 열기

### 각 도구의 구체적인 역할

#### 1. Excel 파일 처리 과정
```python
# pandas가 Excel 파일을 읽는 방식
import pandas as pd

# Excel 파일 읽기
df = pd.read_excel('설문조사진행현황.xlsx')

# 데이터 확인
print(f"총 {len(df)}개의 응답")
print(f"부서 수: {df['부서명'].nunique()}")

# 평균 점수 계산
avg_score = df['협업점수'].mean()
```

#### 2. AI 텍스트 분석 과정
```python
# Google Gemini가 텍스트를 분석하는 방식
from vertexai.generative_models import GenerativeModel

model = GenerativeModel("gemini-pro")
response = model.generate_content(
    f"다음 피드백의 감정을 분석해주세요: {feedback_text}"
)
```

#### 3. 대시보드 생성 과정
```python
# Plotly가 차트를 만드는 방식
import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(x=부서명_리스트, y=평균점수_리스트)
])

# HTML 파일로 저장
fig.write_html("대시보드.html")
```

## 📝 실제 사용 시나리오

### 시나리오 1: 처음 설치하는 경우
```bash
# 1. WSL 터미널 열기
# 2. 프로젝트 폴더로 이동
cd ~/team-review-project

# 3. 가상환경 생성
python3 -m venv .venv

# 4. 가상환경 활성화
source .venv/bin/activate

# 5. 패키지 설치
pip install -r requirements.txt

# 6. 데이터 파일 확인
ls rawdata/

# 7. 첫 실행
python "1. data_processor.py"
```

### 시나리오 2: 매월 정기 실행
```bash
# 1. 새 데이터 파일 추가
# rawdata/ 폴더에 새 Excel 파일 복사

# 2. WSL 터미널에서
cd ~/team-review-project
source .venv/bin/activate

# 3. 데이터 처리
python "1. data_processor.py"

# 4. 대시보드 생성
python "3. build_dashboard_html.py"

# 5. 결과 확인
explorer.exe .  # Windows 탐색기 열기
# "서울아산병원 협업평가 결과.html" 더블클릭
```

### 시나리오 3: 2025년 상하반기 비교 분석
```bash
# 2025년 상하반기를 구분하여 비교 분석하고 싶을 때
python "3. build_dashboard_html_2025년 상하반기 나누기.py"

# 2025년 전체를 통합하여 연도별 추이만 보고 싶을 때
python "3. build_dashboard_html_2025년 기간 통합.py"
```

## 🎯 초보자를 위한 체크리스트

### 설치 확인 사항
- [ ] Windows 10 버전 2004 이상 또는 Windows 11
- [ ] WSL2 설치 완료
- [ ] Ubuntu 설치 및 계정 생성 완료
- [ ] VS Code 설치 완료
- [ ] Python 3.8 이상 설치 확인 (`python3 --version`)
- [ ] Node.js 설치 확인 (`node --version`)
- [ ] Git 설치 확인 (`git --version`)

### 프로젝트 준비 사항
- [ ] 프로젝트 코드 다운로드 완료
- [ ] Python 가상환경 생성 완료
- [ ] requirements.txt 패키지 설치 완료
- [ ] Google Cloud 계정 생성 (AI 분석 시)
- [ ] 서비스 계정 키 파일 저장 (AI 분석 시)

### 데이터 준비 사항
- [ ] 설문 원본 Excel 파일 준비
- [ ] 부서명 매핑 파일 확인
- [ ] 파일명 형식 확인 (한글 포함 가능)

## 🆘 도움이 필요할 때

### 1. 오류 메시지 읽는 방법
```python
# 오류 예시
FileNotFoundError: [Errno 2] No such file or directory: 'data.xlsx'
```
- **FileNotFoundError**: 파일을 찾을 수 없음
- **'data.xlsx'**: 찾으려던 파일명
- **해결**: 파일이 올바른 위치에 있는지 확인

### 2. Claude CLI로 도움 받기
```bash
# 오류 메시지 복사 후
claude "다음 Python 오류를 해결하는 방법을 알려줘: [오류 메시지]"

# 코드 설명 요청
claude "이 코드가 무엇을 하는지 설명해줘: [코드]"
```

### 3. 로그 파일 확인
```bash
# 실행 기록 확인
ls -la | grep log

# 최근 실행 내용 보기
tail -n 50 execution.log
```

---

## 프로젝트 개요

이 시스템은 서울아산병원의 부서간 협업 평가 설문 데이터를 AI로 분석하고, 인터랙티브 대시보드로 시각화합니다.

### 주요 기능
- **데이터 전처리**: 설문 원본 데이터 정제 및 표준화
- **AI 텍스트 분석**: Google Gemini를 활용한 감정 분석 및 키워드 추출
- **대시보드 생성**: 인터랙티브 HTML 대시보드 자동 생성
- **부서별 리포트**: 각 부서별 상세 분석 리포트 제공

## 프로젝트 구조

```
team-review-project/
│
├── 핵심 처리 스크립트/
│   ├── 0. setup.py                                      # 초기 환경 설정 스크립트
│   ├── 1. data_processor.py                             # 설문 데이터 전처리
│   ├── 2. text_processor.py                             # AI 텍스트 분석 (Google Vertex AI)
│   ├── 3. build_dashboard_html_2025년 기간 통합.py      # 통합 대시보드 (2022~2024년은 연도만, 2025년 통합)
│   ├── 3. build_dashboard_html_2025년 상하반기 나누기.py # 통합 대시보드 (2022~2024년은 연도만, 2025년 상하반기 구분)
│   ├── 4. team_reports_외부망접근가능한부서.py           # 외부망 접근 가능 부서 리포트 생성
│   └── 4. team_reports_외부망불가능부서(디지털).py       # 디지털정보혁신본부 등 리포트 생성
│
├── 데이터 폴더/
│   └── rawdata/                                             # 원본 데이터 및 처리 결과
│       ├── 설문조사진행현황[VCRCRIC120S]_2025_1.xlsx       # 2025년 상반기 원본 데이터
│       ├── 설문조사진행현황[VCRCRIC120S]_2025_2.xlsx       # 2025년 하반기 원본 데이터
│       ├── 부서_부문_매핑.xlsx                              # 부서-부문 매핑 테이블
│       ├── 부서명_표준화_매핑.xlsx                          # 부서명 표준화 매핑
│       ├── 1. data_processor_결과_20251001_090316.xlsx    # 전처리 결과 (2025.10.01 기준)
│       └── 2. text_processor_결과_20251001_090316.xlsx    # AI 분석 결과 (2025.10.01 기준)
│
├── 결과물 폴더/
│   ├── generated_reports/             # 생성된 부서별 리포트
│   │   ├── never delete/              # 공통 자원 폴더
│   │   │   └── plotly.min.js          # Plotly.js 라이브러리 파일
│   │   ├── reports_YYYYMMDD_HHMMSS/   # 타임스탬프별 리포트 세트
│   │   │   ├── 간호부문/              # 부문별 폴더
│   │   │   ├── 관리부문/
│   │   │   ├── 진료부문/
│   │   │   └── ...
│   │   └── standalone_reports_YYYYMMDD_HHMMSS/  # 단독 실행 HTML 보고서
│   └── 서울아산병원 협업평가 결과.html # 통합 대시보드
│
├── 기타 스크립트/
│   ├── summarize_mutual_reviews.py    # 상호 평가 요약 (보조)
│   └── update_notion_formatted.py     # Notion 포맷 업데이트 (보조)
│
└── 설정 파일/
    ├── requirements.txt               # Python 패키지 의존성
    ├── README.md                      # 프로젝트 문서 (현재 파일)
    └── .gitignore                     # Git 제외 파일

```

## 시작하기

### 1. 사전 요구사항

- Python 3.8 이상
- Google Cloud 계정 (Vertex AI API 사용)
- 최소 8GB RAM
- 인터넷 연결 (AI API 호출)

### 2. 설치 방법

```bash
# 저장소 클론
git clone https://github.com/your-repo/team-review-project.git
cd team-review-project

# 환경 설정 (가상환경 생성 및 패키지 설치)
python 0. setup.py

# 가상환경 활성화
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Google Cloud 설정

1. Google Cloud Console에서 프로젝트 생성
2. Vertex AI API 활성화
3. 서비스 계정 생성 및 키 다운로드
4. 환경변수 설정:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

## 사용 방법

### 전체 프로세스 실행

```bash
# 1단계: 데이터 전처리
python "1. data_processor.py"

# 2단계: AI 텍스트 분석 (선택사항)
python "2. text_processor.py"

# 3단계: 대시보드 생성 (두 가지 버전 중 선택)

# 옵션 A: 2025년 기간 통합 대시보드 (2025년 상반기+하반기 통합)
python "3. build_dashboard_html_2025년 기간 통합.py"

# 옵션 B: 2025년 상하반기 구분 대시보드 (상반기/하반기 개별 막대그래프)
python "3. build_dashboard_html_2025년 상하반기 나누기.py"

# 4단계: 부서별 리포트 생성 (선택사항)

# 옵션 A: 외부망 접근 가능한 부서
python "4. team_reports_외부망접근가능한부서.py"

# 옵션 B: 디지털정보혁신본부 등 외부망 불가능 부서
python "4. team_reports_외부망불가능부서(디지털).py"
```

### 각 단계별 설명

#### 1. 데이터 전처리 (data_processor.py)
- **입력**: `rawdata/설문조사진행현황[VCRCRIC120S]_*.xlsx`
- **처리**: 
  - 부서명 표준화
  - 부문 매핑
  - 점수 변환 (5점 → 100점)
  - 데이터 품질 검증
- **출력**: `rawdata/1. data_processor_결과_YYYYMMDD_HHMMSS.xlsx`

#### 2. AI 텍스트 분석 (text_processor.py)
- **입력**: data_processor 결과 파일
- **처리**:
  - 협업 후기 텍스트 분석
  - 감정 분류 (긍정/부정/중립)
  - 키워드 추출
  - 비식별화 처리
- **출력**: `rawdata/2. text_processor_결과_YYYYMMDD_HHMMSS.xlsx`
- **참고**: Google Vertex AI 비용이 발생합니다

#### 3. 통합 대시보드 생성
두 가지 버전의 대시보드 스크립트 제공:

**3-A. build_dashboard_html_2025년 기간 통합.py**
- **입력**: 전처리된 데이터 (AI 분석은 선택사항)
- **처리**: 2025년 데이터를 통합하여 하나의 막대로 표시
- **기간 표시**:
  - 2022년, 2023년, 2024년, 2025년 (상반기+하반기 통합)
- **출력**: `서울아산병원 협업평가 결과.html`
- **적합한 경우**: 연도별 추이를 간단히 비교하고 싶을 때

**3-B. build_dashboard_html_2025년 상하반기 나누기.py**
- **입력**: 전처리된 데이터 (AI 분석은 선택사항)
- **처리**: 2025년을 상반기/하반기로 구분하여 개별 막대로 표시
- **기간 표시**:
  - 2022년, 2023년, 2024년, 2025년 상반기, 2025년 하반기
- **출력**: `서울아산병원 협업평가 결과.html`
- **적합한 경우**: 2025년 상반기와 하반기를 별도로 비교 분석하고 싶을 때
- **주요 개선사항**:
  - 섹션 4 Y축을 0-100으로 고정하여 일관된 비교 가능
  - response_id 파싱으로 자동 기간 표시 생성

#### 4. 부서별 리포트 생성
두 가지 버전의 리포트 생성 스크립트 제공:

**4-A. team_reports_외부망접근가능한부서.py**
- **입력**: 전처리된 데이터
- **처리**: 외부망 접근이 가능한 부서들의 상세 분석
- **출력**: `generated_reports/reports_*/부문명/부서별HTML파일`
- **대상 부서**: 외부 CDN(Plotly.js)을 사용할 수 있는 부서
- **특징**:
  - 파일 크기가 작음 (외부 스크립트 참조)
  - 인터넷 연결 필요

**4-B. team_reports_외부망불가능부서(디지털).py**
- **입력**: 전처리된 데이터
- **처리**: 외부망 접근이 불가능한 부서들의 상세 분석 (디지털정보혁신본부 등)
- **출력**: `generated_reports/standalone_reports_*/부문명/부서별HTML파일`
- **대상 부서**: 외부 CDN 접근이 제한된 부서
- **특징**:
  - plotly.min.js를 각 HTML 파일에 임베드
  - 오프라인 환경에서도 모든 차트 기능 작동
  - 파일 크기 증가 (~600KB 추가)
  - 배포 편의성 향상

## 주요 기능 상세

### AI 분석 기능
- **감정 분석**: 8가지 세분화된 감정 분류
- **감정 강도**: 1-10점 척도
- **키워드 추출**: 주요 키워드 3-5개
- **의료 맥락**: 의료 서비스, 업무 효율, 존중/소통, 전문성
- **비식별화**: 부정적 피드백의 개인정보 자동 처리

### 대시보드 구성요소
1. **전체 병원 현황**: 종합 점수 및 추이
2. **부문별 분석**: 부문간 비교 차트
3. **부서별 순위**: 상위/하위 부서
4. **감정 분석**: 감정 분포 및 키워드 클라우드
5. **상세 피드백**: 필터링 가능한 피드백 테이블

## 데이터 파일 설명

### 입력 데이터
- **설문조사진행현황**: 연도별/차수별 설문 원본 데이터
- **부서_부문_매핑.xlsx**: 부서를 부문으로 분류하는 매핑 테이블
- **부서명_표준화_매핑.xlsx**: 변경된 부서명을 표준화하는 매핑

### 출력 데이터
- **전처리 결과**: 표준화되고 정제된 설문 데이터
- **AI 분석 결과**: 텍스트 분석이 추가된 데이터
- **HTML 대시보드**: 웹브라우저에서 볼 수 있는 인터랙티브 리포트

## 문제 해결

### 일반적인 오류 해결

1. **Google Cloud 인증 오류**
   ```bash
   # 인증 확인
   gcloud auth application-default login
   # 또는 서비스 계정 키 경로 확인
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

2. **패키지 설치 오류**
   ```bash
   # pip 업그레이드
   pip install --upgrade pip
   # 패키지 재설치
   pip install -r requirements.txt --force-reinstall
   ```

3. **메모리 부족**
   - text_processor.py의 BATCH_SIZE를 줄이기 (기본값: 10)
   - 데이터를 연도별로 나누어 처리

### 로그 파일
- 오류 발생시 콘솔 출력 확인
- AI 분석 중단시 checkpoints 폴더에서 재개 가능

## 성능 및 처리 시간

- **데이터 전처리**: 약 1-2분 (38,000건 기준)
- **AI 분석**: 약 20-40분 (텍스트 수에 따라 변동)
- **대시보드 생성**: 약 1-2분
- **부서별 리포트**: 약 5-10분
- **단독 실행 HTML 변환**: 약 1-3분 (파일 수에 따라 변동)

## 주의사항

1. **데이터 보안**: 의료 데이터는 민감정보이므로 보안 주의
2. **API 비용**: Google Vertex AI는 사용량에 따라 과금
3. **브라우저 호환성**: Chrome, Edge, Safari 최신 버전 권장
4. **파일 크기**: 생성된 HTML 파일이 클 수 있음 (10-50MB)

## 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## 문의 및 지원

- **이슈 제출**: GitHub Issues 사용
- **개선 제안**: Pull Request 환영
- **최종 업데이트**: 2025년 10월 1일

## 최근 변경사항 (2025년 10월 1일)

### 2025년 하반기 데이터 추가 및 스크립트 재구조화
- **신규 데이터**: 2025년 하반기(2025_2) 설문 데이터 추가
- **데이터 통합**: 2022년~2025년 하반기까지 전체 데이터 통합 처리
- **스크립트 재구조화**:
  - 대시보드 스크립트를 용도별로 명확히 구분
    * `3. build_dashboard_html_2025년 기간 통합.py`: 2025년 전체 통합 버전
    * `3. build_dashboard_html_2025년 상하반기 나누기.py`: 2025년 상하반기 구분 버전
  - 팀 보고서 스크립트를 접근 권한별로 구분
    * `4. team_reports_외부망접근가능한부서.py`: 외부 CDN 사용 가능
    * `4. team_reports_외부망불가능부서(디지털).py`: 오프라인 실행 가능 (plotly 임베드)

### 2025년 상하반기 구분 대시보드 주요 기능
- **기간 표시 개선**:
  - 2022~2024년: 연도만 표시 (예: "2022년", "2023년", "2024년")
  - 2025년: 상반기/하반기 구분 표시 (예: "2025년 상반기", "2025년 하반기")
  - response_id 자동 파싱으로 기간 표시 생성
- **차트 개선**:
  - 섹션 4 (소속 부문 팀별 종합 점수) Y축을 0~100으로 고정
  - 연도 선택 드롭다운 변경 시에도 Y축 범위 유지
- **집계 데이터 변경**:
  - 기존 '설문시행연도' 기준 → '기간_표시' 기준으로 변경
  - 모든 JavaScript 필터 및 차트 로직 업데이트
- **부제 업데이트**: "2025년 하반기(2025년 10월 1일 기준)"으로 변경

### 데이터 처리 개선
- 중복 제거 로직 강화
- 2025년 상반기/하반기 데이터 통합 처리 안정화
- 텍스트 분석 정확도 향상

## 최근 변경사항 (2025년 7월 31일)

### 단독 실행 HTML 보고서 기능 추가
- **신규 파일**: `4. team_reports2.py` 추가
- **주요 기능**:
  - 기존 부서별 HTML 보고서를 단독 실행 가능한 형태로 변환
  - plotly.min.js를 각 HTML 파일에 임베드하여 외부 의존성 제거
  - 오프라인 환경에서도 모든 차트 기능 정상 작동
- **디렉토리 구조**:
  - plotly.min.js 파일 위치: `generated_reports/never delete/plotly.min.js`
  - 출력 디렉토리: `generated_reports/standalone_reports_{timestamp}/`
- **실행 방법**:
  - 자동 감지: `python "4. team_reports2.py"`
  - 특정 디렉토리: `python "4. team_reports2.py" path/to/reports`
- **장점**:
  - 배포 편의성 대폭 향상 (CDN 연결 불필요)
  - 네트워크 제한 환경에서도 완전한 기능 사용 가능
  - 원본 보고서의 모든 인터랙티브 기능 보존


---

*서울아산병원 협업평가 시스템 - 더 나은 의료 협업 문화를 위하여*