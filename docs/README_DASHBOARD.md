# 대시보드 생성 시스템

의료진 협업 피드백 데이터를 기반으로 다양한 형태의 대시보드를 생성하는 통합 시스템입니다.

## 특징

- ✅ **간단한 구조**: 3개 파일로 구성된 단순한 시스템
- ✅ **쉬운 수정**: 함수 기반 설계로 초보자도 쉽게 수정 가능
- ✅ **4가지 모드**: 통합/분할/부서별/Standalone 지원
- ✅ **빠른 실행**: 4-5초 내 대시보드 생성

## 설치

```bash
pip install pandas openpyxl plotly
```

## 사용법

### 기본 사용

```bash
# 모드 없이 실행하면 도움말 표시
python dashboard_builder.py

# 기간 통합 대시보드
python dashboard_builder.py integrated

# 상하반기 분할 대시보드
python dashboard_builder.py split

# 부서별 리포트
python dashboard_builder.py departments

# Standalone 버전 (인터넷 연결 불필요)
python dashboard_builder.py standalone
```

### 출력 결과

생성된 HTML 파일은 `outputs/` 디렉토리에 저장됩니다:
- `dashboard_integrated.html` - 기간 통합
- `dashboard_split.html` - 상하반기 분할
- `dashboard_departments.html` - 부서별 리포트
- `dashboard_standalone.html` - 독립형 (인터넷 불필요)

## 파일 구조

```
.
├── dashboard_builder.py  (600-700줄) - 핵심 로직
├── config.py             (50줄)      - 설정 관리
├── README_DASHBOARD.md                - 사용 설명서
├── rawdata/
│   └── 2. text_processor_결과_20251013_093925.xlsx
├── outputs/              - 생성된 HTML 파일
└── libs/                 - Plotly JS (Standalone용)
```

## 커스터마이징

### 새로운 모드 추가

`config.py`에 설정 추가:

```python
DASHBOARD_CONFIGS = {
    # ... 기존 설정 ...

    'my_custom': {
        'name': '내 커스텀 대시보드',
        'output_file': 'outputs/my_dashboard.html',
        'mode': 'integrated',
        'charts': ['sentiment', 'trend'],
        'description': '설명 추가'
    }
}
```

### 차트 수정

`dashboard_builder.py`의 `create_*_chart()` 함수 수정:

```python
def create_sentiment_chart(df, title="감정 분포"):
    # 여기서 차트 디자인 변경
    fig = go.Figure(...)
    # 색상, 크기, 레이아웃 등 수정
    return fig.to_html(...)
```

### HTML 스타일 변경

`build_html()` 함수의 `<style>` 섹션 수정:

```python
def build_html(charts, stats, title="대시보드"):
    html = f"""
    ...
    <style>
        /* 여기서 CSS 수정 */
        body {{ background: #새색상; }}
    </style>
    ...
    """
```

## 문제 해결

### 에러: 필수 컬럼 누락

**증상**: `ValueError: 필수 컬럼이 없습니다: ...`

**해결**: Excel 파일에 필수 컬럼이 있는지 확인:
- response_id
- 설문시행연도
- 평가_부서명
- 피평가대상 부서명
- 종합점수
- 협업 후기
- 감정_분류
- 감정_강도_점수
- 신뢰도_점수

### 에러: Plotly JS 파일 없음 (Standalone 모드)

**증상**: `⚠️ Plotly JS 파일 없음`

**해결**:
1. https://cdn.plot.ly/plotly-latest.min.js 다운로드
2. `libs/plotly-latest.min.js`에 저장

### 차트가 표시되지 않음

**증상**: HTML은 생성되지만 차트가 빈 공간

**해결**:
- 인터넷 연결 확인 (CDN 모드)
- 또는 Standalone 모드 사용

## 개발자 가이드

### 새로운 차트 타입 추가

1. `dashboard_builder.py`에 차트 함수 추가:

```python
def create_my_chart(df):
    fig = go.Figure(...)
    return fig.to_html(include_plotlyjs='cdn', full_html=False)
```

2. `config.py`에서 차트 활성화:

```python
'charts': ['sentiment', 'trend', 'my_chart']
```

3. `build_dashboard()` 함수에 차트 생성 로직 추가:

```python
if 'my_chart' in chart_types:
    charts.append(create_my_chart(df))
```

### 데이터 전처리 수정

`process_data()` 함수 수정:

```python
def process_data(df, mode='integrated'):
    # 기존 로직...

    # 새로운 처리 추가
    df['새_컬럼'] = df['기존_컬럼'].apply(lambda x: ...)

    return df
```

### 집계 함수 추가

```python
def aggregate_by_custom(df):
    """커스텀 집계"""
    # 집계 로직 구현
    return result_df
```

## 함수 목록

### Phase 1: 데이터 처리
- `load_data(file_path)` - Excel 파일 로드 및 검증
- `parse_period(response_id, mode)` - 기간 정보 추출
- `process_data(df, mode)` - 데이터 전처리
- `aggregate_by_period(df)` - 기간별 집계
- `aggregate_by_department(df)` - 부서별 집계

### Phase 2: 차트 생성
- `create_sentiment_chart(df, title)` - 감정 분포 파이 차트
- `create_trend_chart(period_df, title)` - 기간별 트렌드 라인 차트
- `create_department_chart(dept_stats, title, top_n)` - 부서별 막대 차트

### Phase 3: HTML 생성
- `build_html(charts, stats, title)` - HTML 문서 생성
- `build_dashboard(config_name)` - 메인 파이프라인
- `convert_to_standalone(html, plotly_js_path)` - CDN→독립형 변환

## 성능

- **데이터 크기**: 46,000행
- **처리 시간**: 4-5초
- **파일 크기**: 20-50 KB (CDN), 3-5 MB (Standalone)

## 라이선스

MIT License

## 변경 이력

### v1.0 (2025-01-14)
- 초기 릴리스
- 4가지 모드 지원 (integrated, split, departments, standalone)
- Phase 1-4 완료 (공통 함수, 차트, HTML, CLI)
- 총 ~700줄 (dashboard_builder.py + config.py)

## 기여

문제가 발생하면 Issue를 등록해주세요.

## 기존 파일과의 비교

### Before (현재)
```
4개 파일
- 3. build_dashboard_html_2025년 기간 통합.py (2,607줄)
- 3. build_dashboard_html_2025년 상하반기 나누기.py (2,639줄)
- 4. team_reports_외부망접근가능한부서.py (2,509줄)
- 4. team_reports_외부망불가능부서(디지털).py (145줄)

총 7,900줄
85-90% 코드 중복
수정 시 4곳 변경 필요
```

### After (리팩토링 후)
```
3개 파일
- dashboard_builder.py (600-700줄)
- config.py (50줄)
- README_DASHBOARD.md (100줄)

총 750-850줄 (89% 감소)
중복 제거
수정 시 1곳만 변경
초보자도 이해 가능
```

## 마이그레이션 가이드

### 기존 사용자를 위한 변경 사항

#### Before (기존 방식)
```bash
python "3. build_dashboard_html_2025년 기간 통합.py"
python "3. build_dashboard_html_2025년 상하반기 나누기.py"
python "4. team_reports_외부망접근가능한부서.py"
python "4. team_reports_외부망불가능부서(디지털).py"
```

#### After (새로운 방식)
```bash
python dashboard_builder.py integrated
python dashboard_builder.py split
python dashboard_builder.py departments
python dashboard_builder.py standalone
```

### 설정 변경 방법

기존 파일의 하드코딩된 값들을 `config.py`로 이동:

```python
# Before: 파일 안에 하드코딩
input_file = "rawdata/2. text_processor_결과.xlsx"
output_file = "outputs/dashboard.html"

# After: config.py에서 관리
COMMON_CONFIG = {
    'input_file': 'rawdata/2. text_processor_결과_20251013_093925.xlsx',
    'output_dir': 'outputs'
}
```
