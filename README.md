# 서울아산병원 협업평가 시스템

> AI 기반 의료진 협업 피드백 분석 및 대시보드 시스템

**버전**: 3.2
**업데이트**: 2025-10-14

---

## 📚 목차

1. [프로젝트 소개](#-프로젝트-소개)
2. [빠른 시작](#-빠른-시작-5분)
3. [프로젝트 구조](#-프로젝트-구조)
4. [상세 가이드](#-상세-가이드)
5. [문제 해결](#-문제-해결)

---

## 🎯 프로젝트 소개

서울아산병원 협업평가 시스템은 의료진 간 협업 피드백을 AI로 분석하고 인터랙티브 대시보드를 생성하는 시스템입니다.

### 주요 기능

- ✅ **AI 감정 분석**: Google Gemini를 통한 텍스트 감정 분석
- ✅ **대시보드 생성**: 인터랙티브 HTML 대시보드
- ✅ **부서별 보고서**: 79개 부서별 개별 상세 보고서
- ✅ **외부망 대응**: 인터넷 연결 없이도 그래프 표시

### 3가지 보고서 유형

| 유형 | 파일명 | 출력 | 용도 |
|------|--------|------|------|
| 연도별 통합 | `1. build_연도별.py` | `outputs/dashboard_integrated.html` | 2025년 전체 통합 |
| 반기별 분할 | `2. build_반기별.py` | `outputs/dashboard_split.html` | 상반기/하반기 분할 |
| 부서별 개별 | `3. build_부서별.py` | `개별보고서/[부문명]/[부서명].html` | 79개 부서별 상세 |

---

## 🚀 빠른 시작 (5분)

### 전제 조건

- Python 3.8 이상
- Google Cloud 인증 파일 (`Gemini API.json`)
- 처리된 데이터 파일 (`rawdata/2. text_processor_결과_*.xlsx`)

### 실행 방법

```bash
# 1️⃣ 연도별 통합 대시보드
python "1. build_연도별.py"
# 출력: outputs/dashboard_integrated.html (약 20MB)

# 2️⃣ 반기별 분할 대시보드
python "2. build_반기별.py"
# 출력: outputs/dashboard_split.html (약 21MB)

# 3️⃣ 부서별 개별 보고서 (외부망 불가 부서용)
python "3. build_부서별.py"
# 출력: 개별보고서/[부문명]/[부서명].html (79개)
# ⚠️  약 1-2분 소요, 인터넷 연결 불필요
```

### 공통 기능 (모든 버전)

- ✅ 병원 전체 결과
- ✅ 부문별 비교
- ✅ 팀별 순위
- ✅ 협업 네트워크 분석
- ✅ 키워드 분석

---

## 📁 프로젝트 구조

### 디렉토리 구조

```
team-review-project/
├── src/                            # 보고서 생성 핵심 모듈
│   ├── dashboard_builder.py       # 통합 대시보드 생성기
│   ├── department_report_builder.py # 부서별 보고서 생성기
│   ├── config.py                  # 설정 파일
│   └── plotly.min.js              # Plotly 라이브러리 (4.4MB)
│
├── data_preparation/               # 데이터 준비 (선택)
│   ├── 0. setup.py                # 초기 환경 설정
│   ├── 1. data_processor.py       # 원본 데이터 수집
│   └── 2. text_processor.py       # AI 텍스트 분석
│
├── 1. build_연도별.py              # 연도별 통합 대시보드
├── 2. build_반기별.py              # 반기별 분할 대시보드
├── 3. build_부서별.py              # 부서별 개별 보고서
│
├── rawdata/                       # 원본 데이터
│   └── 2. text_processor_결과_*.xlsx
│
├── outputs/                       # 통합 대시보드 출력
│   ├── dashboard_integrated.html
│   └── dashboard_split.html
│
├── 개별보고서/                     # 부서별 보고서
│   ├── [부문명]/
│   │   └── [부서명].html
│
└── legacy/                        # 구버전 참조용
```

### 핵심 파일 설명

#### src/ (보고서 생성)

**dashboard_builder.py** (1,093줄)
- 역할: 통합 대시보드 생성 엔진 (간소화 버전)
- 사용: `1. build_연도별.py`, `2. build_반기별.py`
- 기능: 상하반기 분할, 기간별 트렌드, 간소화된 차트

**department_report_builder.py** (2,622줄)
- 역할: 부서별 상세 보고서 생성 엔진 (완전판)
- 사용: `3. build_부서별.py`
- 기능: 협업 네트워크, 키워드 분석, Plotly 인라인 포함

**config.py**
- 역할: 공통 설정 관리
- 내용: 파일 경로, 컬럼명, 점수 컬럼 정의

**plotly.min.js** (4.4MB)
- 역할: 외부망 불가 환경 대응
- 용도: HTML에 인라인으로 포함되어 그래프 표시
- ⚠️  **삭제 금지!**

#### data_preparation/ (데이터 수집)

**0. setup.py**
- 역할: 프로젝트 초기 환경 설정
- 실행: 한 번만 실행 (가상환경, 패키지 설치)

**1. data_processor.py**
- 역할: Google Sheets에서 원본 데이터 수집
- 기능: 부서명 매핑, 데이터 정제

**2. text_processor.py**
- 역할: AI 기반 텍스트 감정 분석
- 기능: Gemini API를 통한 감정 분석 및 키워드 추출

> **참고**: 보고서 생성 시 `data_preparation/` 폴더는 불필요합니다.
> 이미 처리된 `rawdata/*.xlsx` 파일이 있으면 바로 보고서 생성 가능합니다.

### 폴더 역할 구분

| 폴더 | 용도 | 필수 여부 |
|------|------|----------|
| **src/** | 보고서 생성 핵심 모듈 | ✅ 필수 |
| **data_preparation/** | 데이터 수집 및 전처리 | ⚠️ 선택 (데이터 수집 시만) |
| **legacy/** | 구버전 코드 참조 | ❌ 참조용 (삭제 가능) |

---

## 📖 상세 가이드

### 설치

#### 1. 필수 도구 설치

**Python 3.8+**
```bash
# Ubuntu/WSL
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version  # 확인
```

**필수 패키지**
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install pandas numpy plotly openpyxl tqdm
pip install google-cloud-aiplatform
```

#### 2. Google Cloud 인증 설정

1. Google Cloud Console에서 Gemini API 키 발급
2. `Gemini API.json` 파일을 프로젝트 루트에 저장
3. 환경 변수 설정:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="./Gemini API.json"
```

#### 3. 데이터 준비

**옵션 A: 이미 처리된 데이터가 있는 경우**
- `rawdata/2. text_processor_결과_*.xlsx` 확인
- → 바로 보고서 생성 가능!

**옵션 B: 새 데이터 수집이 필요한 경우**
```bash
# 데이터 수집
python data_preparation/1.\ data_processor.py

# AI 감정 분석
python data_preparation/2.\ text_processor.py
```

### 사용법

#### 시나리오 1: 전체 병원 통합 대시보드

```bash
python "1. build_연도별.py"
```

**출력**:
- `outputs/dashboard_integrated.html` (약 20MB)
- 2025년 전체 기간 통합
- 10-15초 소요

**사용 상황**:
- 병원 전체 협업 현황을 한눈에 보고 싶을 때
- 경영진 보고용
- 연간 협업 트렌드 분석

#### 시나리오 2: 상반기/하반기 비교

```bash
python "2. build_반기별.py"
```

**출력**:
- `outputs/dashboard_split.html` (약 21MB)
- 상반기/하반기 구분 표시
- 10-15초 소요

**사용 상황**:
- 반기별 성과 비교
- 개선 추이 확인
- 계절적 변화 분석

#### 시나리오 3: 부서별 상세 보고서 (외부망 불가)

```bash
python "3. build_부서별.py"
```

**출력**:
- `개별보고서/[부문명]/[부서명].html` (79개)
- 각 파일 약 4.4MB (Plotly 포함)
- 1-2분 소요

**출력 구조 예시**:
```
개별보고서/
├── 커뮤니케이션실/
│   ├── 고객만족팀.html
│   ├── 디자인·콘텐츠팀.html
│   └── 홍보팀.html
├── 간호부문/
│   ├── 중환자간호팀.html
│   └── ...
└── 진료부문/
    ├── 영상의학팀.html
    └── ...
```

**사용 상황**:
- 외부망 접속이 불가능한 부서 (디지털정보혁신본부 등)
- 각 부서장에게 개별 보고서 전달
- 인터넷 연결 없이 그래프 확인 필요

### 개발 흐름

#### 통합 대시보드 생성

```
1. build_연도별.py 또는 2. build_반기별.py 실행
    ↓
src/dashboard_builder.py 호출
    ↓
rawdata/*.xlsx 로드
    ↓
데이터 처리 및 집계
    ↓
차트 생성
    ↓
HTML 생성
    ↓
outputs/dashboard_*.html 출력
```

#### 부서별 보고서 생성

```
3. build_부서별.py 실행
    ↓
src/department_report_builder.py 호출
    ↓
generate_all_department_reports() 실행
    ↓
79개 부서 순회
    ↓
각 부서별 데이터 필터링
    ↓
상세 분석 (네트워크, 키워드 등)
    ↓
Plotly 자동 인라인 포함 (src/plotly.min.js)
    ↓
개별보고서/[부문명]/[부서명].html 출력
```

### 유지보수 가이드

#### 통합 대시보드 수정
→ `src/dashboard_builder.py` 또는 `src/config.py` 수정

#### 부서별 보고서 수정
→ `src/department_report_builder.py` 수정

#### Plotly 버전 업데이트
→ `src/plotly.min.js` 교체

#### 새 데이터 수집
→ `data_preparation/` 폴더의 스크립트 실행

---

## ❓ 문제 해결

### 자주 발생하는 문제

#### 1. `ModuleNotFoundError: No module named 'xxx'`

**원인**: 패키지가 설치되지 않음

**해결**:
```bash
pip install pandas numpy plotly openpyxl tqdm google-cloud-aiplatform
```

#### 2. Google Cloud 인증 오류

**원인**: `GOOGLE_APPLICATION_CREDENTIALS` 환경 변수 미설정

**해결**:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="./Gemini API.json"

# 또는 스크립트 내에서
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./Gemini API.json"
```

#### 3. 파일을 찾을 수 없음

**원인**: `rawdata/` 폴더에 데이터 파일이 없음

**해결**:
```bash
# 파일 확인
ls rawdata/2.\ text_processor_결과_*.xlsx

# 없으면 데이터 수집 실행
python data_preparation/2.\ text_processor.py
```

#### 4. 부서별 보고서에서 그래프가 안 보임

**원인**: `src/plotly.min.js` 파일이 없거나 경로가 잘못됨

**해결**:
```bash
# 파일 확인
ls -lh src/plotly.min.js

# 파일이 없으면 다운로드
# https://cdn.plot.ly/plotly-2.26.0.min.js
```

#### 5. 파일명에 공백이 있어서 실행 안 됨

**해결**:
```bash
# 따옴표로 감싸기
python "1. build_연도별.py"
python "2. build_반기별.py"
python "3. build_부서별.py"
```

### 성능 최적화

#### 메모리 부족 시

**증상**: `MemoryError` 또는 프로세스 중단

**해결**:
```python
# 데이터 청크 단위로 처리
df = pd.read_excel(file, chunksize=1000)

# 불필요한 컬럼 제거
df = df[['필요한', '컬럼만']]
```

#### 느린 실행 속도

**해결**:
```python
# 병렬 처리 활성화
from concurrent.futures import ThreadPoolExecutor

# 캐싱 활성화
@functools.lru_cache(maxsize=128)
def expensive_function():
    ...
```

---

## 📞 지원 및 문의

### 프로젝트 정보

- **프로젝트**: 서울아산병원 협업평가 시스템
- **버전**: 3.2
- **최종 업데이트**: 2025-10-14
- **Python 버전**: 3.8+

### 기술 스택

- **언어**: Python 3.8+
- **데이터 처리**: pandas, numpy
- **시각화**: plotly
- **AI**: Google Gemini (Vertex AI)
- **환경**: WSL2 (Ubuntu), VS Code

---

## 📝 변경 이력

### v3.2 (2025-10-14)
- 프로젝트 구조 최적화
- `data_preparation/` 폴더 분리
- `plotly.min.js` 경로 변경 (`src/`로 이동)
- 빌드 스크립트 한글화 (`1. build_연도별.py` 등)
- 문서 통합 (README.md)

### v3.1 (2025-10-14)
- `src/department_report_builder.py` 추가
- legacy 폴더를 참조용으로 변경

### v3.0 (2025-10-14)
- src 구조로 통합
- 모든 기능을 src 폴더로 이동

---

## 📄 라이선스

이 프로젝트는 서울아산병원 내부용으로 제작되었습니다.

---

**작성**: Claude AI
**유지보수**: 서울아산병원
