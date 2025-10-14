# 프로젝트 구조

## 📁 프로젝트 디렉토리 구조

```
team-review-project/
├── src/                            # 보고서 생성 핵심 모듈
│   ├── dashboard_builder.py       # 통합 대시보드 생성기 (간소화 버전)
│   ├── department_report_builder.py # 부서별 개별 보고서 생성기 (완전판)
│   ├── config.py                  # 설정 파일
│   └── plotly.min.js              # Plotly 라이브러리 (4.4MB, 필수 유지!)
├── data_preparation/               # 데이터 준비 스크립트 (선택적 사용)
│   ├── 0. setup.py                # 프로젝트 초기 환경 설정
│   ├── 1. data_processor.py       # Google Sheets 원본 데이터 수집
│   └── 2. text_processor.py       # AI 텍스트 감정 분석
├── build_integrated.py            # 2025년 통합 대시보드 생성
├── build_split.py                 # 2025년 상하반기 분할 대시보드 생성
├── build_standalone.py            # 부서별 독립형 보고서 생성 (외부망 불가)
├── 상호평가부서추출.py              # 데이터 전처리 스크립트
├── QUICKSTART.md                  # 빠른 시작 가이드
├── PROJECT_STRUCTURE.md           # 이 파일
├── rawdata/                       # 원본 데이터
│   └── 2. text_processor_결과_*.xlsx
├── generated_reports/             # 생성된 보고서
├── 개별보고서/                     # 부서별 개별 보고서 (최신)
│   ├── [부문명]/
│   │   └── [부서명].html
│   └── ...
├── outputs/                       # 통합 대시보드 출력
│   ├── dashboard_integrated.html
│   └── dashboard_split.html
└── legacy/                        # 구버전 코드 보관 (참조용만, 현재 미사용)
    ├── 3. build_dashboard_html_2025년 기간 통합.py
    ├── 3. build_dashboard_html_2025년 상하반기 나누기.py
    └── 4. team_reports_*.py
```

## 🔧 핵심 파일 설명

### src/dashboard_builder.py (통합 대시보드)
**역할**: 간소화된 통합 대시보드 생성 엔진
- 초보자도 이해하기 쉬운 구조
- 모듈화된 차트 생성
- Plotly standalone 변환 기능 내장
- `build_integrated.py`, `build_split.py`가 이 모듈 사용

### src/department_report_builder.py (부서별 보고서)
**역할**: 부서별 개별 보고서 생성 엔진 (완전판)
- 모든 분석 기능 포함 (네트워크, 키워드 등)
- 부서별 개별 보고서 생성 기능 (`generate_all_department_reports()`)
- Plotly 인라인 포함 기능 내장 (외부망 불필요)
- `build_standalone.py`가 이 모듈 사용
- 79개 부서별 개별 HTML 생성

### data_preparation/ (데이터 준비)
**역할**: 원본 데이터 수집 및 전처리 (보고서 생성에 직접 불필요)
- `0. setup.py`: 프로젝트 초기 환경 설정 (한 번만 실행)
- `1. data_processor.py`: Google Sheets에서 원본 데이터 수집
- `2. text_processor.py`: AI 기반 텍스트 감정 분석 및 키워드 추출
- **보고서 생성 시**: 이미 처리된 `rawdata/*.xlsx` 파일만 있으면 됨
- **새 데이터 수집 시**: 이 스크립트들 사용

### build_*.py 스크립트들

#### 통합 대시보드
- `build_integrated.py`: 2025년 통합 대시보드
- `build_split.py`: 2025년 상하반기 분할 대시보드
- → `src/dashboard_builder.py` 호출

#### 부서별 개별 보고서
- `build_standalone.py`: 부서별 독립형 보고서 (외부망 불가)
- → `src/department_report_builder.py` 호출

## 📦 외부망 불가 환경 대응

### Plotly 인라인 포함
- **경로**: `src/plotly.min.js` (4.4MB)
- **방식**: `src/department_report_builder.py`가 자동으로 HTML에 임베드
- **중요**: `plotly.min.js` 파일은 절대 삭제하지 마세요!

### 독립형 보고서 생성
```bash
python build_standalone.py
```
- Plotly 라이브러리가 HTML에 자동 인라인 포함됨
- 인터넷 연결 없이도 모든 그래프 표시 가능
- 파일 크기: 약 4.4MB/파일 (Plotly 포함)
- 출력: `개별보고서/[부문명]/[부서명].html`

## 📂 legacy 폴더

**용도**: 구버전 코드 보관 (참조용)
- **상태**: 현재 미사용 (모든 기능이 src/로 이동됨)
- **내용**: 이전 버전의 대시보드 생성 스크립트들
- **삭제**: 참조용으로 유지 (필요시 삭제 가능)

## 🚀 개발 흐름

### 통합 대시보드 생성
1. `build_integrated.py` 또는 `build_split.py` 실행
2. → `src/dashboard_builder.py` 호출
3. → 출력: `outputs/dashboard_*.html`

### 부서별 독립형 보고서 생성
1. `build_standalone.py` 실행
2. → `src/department_report_builder.py` 호출
3. → `generate_all_department_reports()` 함수 실행
4. → Plotly 자동 인라인 포함 (`src/plotly.min.js`)
5. → 출력: `개별보고서/[부문명]/[부서명].html` (79개 부서)

## 💡 유지보수 가이드

### 통합 대시보드 수정 시
→ `src/dashboard_builder.py` 또는 `src/config.py` 수정

### 부서별 개별 보고서 수정 시
→ `src/department_report_builder.py` 수정

### Plotly 버전 업데이트 시
→ `src/plotly.min.js` 교체

## 📂 폴더 역할 구분

### src/ (핵심 - 보고서 생성)
- **용도**: 보고서 생성 시 직접 사용되는 핵심 모듈
- **크기**: 약 4.9MB (plotly.min.js 포함)
- **필수**: ✅ 보고서 생성 시 필수

### data_preparation/ (선택 - 데이터 수집)
- **용도**: 새로운 원본 데이터 수집 및 전처리
- **크기**: 약 100KB
- **필수**: ⚠️ 보고서 생성엔 불필요 (데이터 수집 시만 사용)

### legacy/ (참조 - 구버전 보관)
- **용도**: 이전 버전 코드 참조
- **필수**: ❌ 참조용 (필요시 삭제 가능)

## ⚠️ 주의사항

1. **plotly.min.js 삭제 금지**
   - 외부망 불가 환경에서 그래프 표시에 필수
   - 경로: `src/plotly.min.js`
   - 파일 크기: 4.4MB

2. **src/ 폴더 내 파일 역할**
   - `dashboard_builder.py`: 통합 대시보드 생성용
   - `department_report_builder.py`: 부서별 개별 보고서 생성용
   - 각각 독립적으로 작동
   - **보고서 생성 시 이 폴더만 필요**

3. **data_preparation/ 폴더**
   - 보고서 생성엔 직접 불필요
   - 새 데이터 수집/전처리 시에만 사용
   - `rawdata/*.xlsx` 파일이 이미 있으면 사용 안 해도 됨

---

작성일: 2025-10-14
버전: 3.1 (src 최적화 - 데이터 준비 스크립트 분리)
