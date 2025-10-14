# 프로젝트 구조

대시보드 빌더 프로젝트의 폴더 구조 설명

## 📂 디렉토리 구조

```
team-review-project/
├── src/                              # 새로운 리팩토링된 코드
│   ├── __init__.py                   # 패키지 초기화
│   ├── dashboard_builder.py          # 핵심 대시보드 생성 로직
│   └── config.py                     # 설정 관리 (5가지 모드)
│
├── legacy/                           # 기존 원본 스크립트 (백업)
│   ├── 0. setup.py                   # 초기 설정
│   ├── 1. data_processor.py          # 데이터 전처리
│   ├── 2. text_processor.py          # 텍스트 분석
│   ├── 3. build_dashboard_html_2025년 기간 통합.py
│   ├── 3. build_dashboard_html_2025년 상하반기 나누기.py
│   ├── 4. team_reports_외부망접근가능한부서.py
│   ├── 4. team_reports_외부망불가능부서(디지털).py
│   └── summarize_mutual_reviews.py
│
├── tests/                            # 테스트 스크립트
│   ├── test_aggregated_data.py       # 집계 함수 테스트
│   └── dashboard_builder_full.py     # 완전판 래퍼 스크립트
│
├── docs/                             # 프로젝트 문서
│   ├── README_DASHBOARD.md           # 대시보드 사용 가이드
│   ├── REFACTORING_PLAN.md           # 리팩토링 계획
│   └── deployment-troubleshooting-plan.md
│
├── outputs/                          # 생성된 대시보드 HTML
│   ├── dashboard_integrated.html     # 간소화: 기간 통합
│   ├── dashboard_split.html          # 간소화: 상하반기 분할
│   ├── dashboard_departments.html    # 간소화: 부서별 비교
│   └── dashboard_standalone.html     # 간소화: 독립형
│
├── rawdata/                          # 원본 데이터
│   └── 2. text_processor_결과_*.xlsx
│
├── libs/                             # 외부 라이브러리 (standalone용)
│   └── plotly-latest.min.js
│
├── dashboard_builder.py              # 메인 실행 스크립트 (프로젝트 루트)
├── 서울아산병원 협업평가 결과.html      # Full 모드 출력 (20MB)
├── README.md                         # 메인 README
└── PROJECT_STRUCTURE.md              # 이 파일
```

## 🎯 주요 파일 설명

### 실행 파일
- **dashboard_builder.py** (루트): 메인 실행 스크립트, src/ 모듈을 import하여 실행
- **src/dashboard_builder.py**: 실제 대시보드 생성 로직
- **src/config.py**: 5가지 모드 설정 (full, integrated, split, departments, standalone)

### 데이터 플로우
```
rawdata/
  └── 2. text_processor_결과_*.xlsx
       ↓
  [src/dashboard_builder.py]
       ├── load_data()              # Excel 로드
       ├── preprocess_data_types()  # 타입 변환
       ├── clean_data()             # 데이터 정제
       ├── calculate_aggregated_data()  # 집계
       └── build_html()             # HTML 생성
       ↓
outputs/ 또는 루트/
  └── *.html
```

## 🚀 사용법

### 기본 사용
```bash
# 프로젝트 루트에서 실행
python dashboard_builder.py [모드]

# 예시
python dashboard_builder.py full        # 원본 완전판 (20MB)
python dashboard_builder.py integrated  # 간소화 버전 (20KB)
```

### 모듈로 사용
```python
from src.dashboard_builder import build_dashboard

# 대시보드 생성
build_dashboard('full')
build_dashboard('integrated')
```

## 📊 모드 설명

| 모드 | 파일 크기 | 설명 |
|------|----------|------|
| **full** | 20 MB | 원본 대시보드의 모든 기능 (병원 전체, 부문별, 팀 순위, 네트워크, 키워드 분석) |
| **integrated** | 20 KB | 2025년 전체 기간을 통합하여 표시 |
| **split** | 20 KB | 2025년을 상하반기로 구분하여 표시 |
| **departments** | 30 KB | 모든 부서의 협업 현황 비교 |
| **standalone** | 30 KB | 인터넷 연결 없이도 볼 수 있는 독립형 |

## 🔧 개발자 가이드

### 새로운 모드 추가
1. `src/config.py`에 설정 추가
2. 필요시 `src/dashboard_builder.py`에 로직 추가
3. 테스트 실행

### 테스트 실행
```bash
# 집계 함수 테스트
python tests/test_aggregated_data.py

# 모든 모드 테스트
for mode in full integrated split departments standalone; do
    python dashboard_builder.py $mode
done
```

## 📝 변경 이력

### v2.0 (2025-01-14)
- 폴더 구조 개편
- legacy/, src/, tests/, docs/ 분리
- 모듈화 완성

### v1.0 (2025-01-14)
- 초기 리팩토링 완료
- 7,900줄 → 750줄 (90.4% 감소)
- 5가지 모드 지원
