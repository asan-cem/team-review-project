# 대시보드 시스템 리팩토링 계획 (간소화 버전)

## 개요

**목표**: 4개의 대시보드 생성 스크립트를 단순하고 유지보수 가능한 시스템으로 통합
**설계 원칙**: KISS (Keep It Simple, Stupid) - 코딩 초보도 쉽게 이해하고 수정 가능
**예상 소요 시간**: 4시간
**최종 구조**: 3개 파일 (총 ~700줄)

---

## 현재 상황

### 통합 대상 파일 (4개)
1. `3. build_dashboard_html_2025년 기간 통합.py` (2,607줄)
2. `3. build_dashboard_html_2025년 상하반기 나누기.py` (2,639줄)
3. `4. team_reports_외부망접근가능한부서.py` (2,509줄)
4. `4. team_reports_외부망불가능부서(디지털).py` (145줄)

### 문제점
- 85-90% 코드 중복
- 수정사항을 4곳에 반영해야 함
- 일관성 유지 어려움

---

## 목표 구조 (간소화)

```
project/
├── dashboard_builder.py  (600-700줄)  ← 모든 핵심 로직
├── config.py             (50줄)       ← 설정만 관리
└── README.md             (100줄)      ← 사용법 설명
```

**설계 철학**:
- ✅ 단일 파일에 모든 로직 (흐름 이해 쉬움)
- ✅ 함수 기반 설계 (클래스 복잡도 제거)
- ✅ dict 기반 설정 (간단명료)
- ✅ 최소 의존성 (pandas, plotly만)
- ✅ print()로 로깅 (별도 로거 불필요)

**제거할 것**:
- ❌ 추상 베이스 클래스 (ABC)
- ❌ 전략 패턴
- ❌ Click CLI 프레임워크
- ❌ 복잡한 validators
- ❌ 유닛테스트 인프라
- ❌ 다층 디렉토리 구조

---

## Phase 1: 공통 함수 추출 (1.5시간)

### 1.1 데이터 로딩 함수

**목표**: 4개 파일의 Excel 로딩 부분을 하나로 통합

```python
def load_data(file_path):
    """Excel 파일 로드 및 기본 검증"""
    print(f"📂 데이터 로드: {file_path}")
    df = pd.read_excel(file_path)

    # 필수 컬럼 확인
    required_cols = ['response_id', '부서명', '협업 후기', '감정_분류']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")

    print(f"✅ {len(df)}행 로드 완료")
    return df
```

**작업 내역**:
- [ ] 기존 파일 1에서 데이터 로드 코드 복사 (line 10-50)
- [ ] 필수 컬럼 체크 로직 추가
- [ ] 에러 메시지 개선

**추출 소스**: 파일 1, line 10-50

---

### 1.2 기간 파싱 함수

**목표**: 통합/분할 모드를 지원하는 단일 함수

```python
def parse_period(response_id, mode='integrated'):
    """
    기간 파싱

    Args:
        response_id: "2025/1/123" 형식
        mode: 'integrated' (2025년) 또는 'split' (2025년 상반기)

    Returns:
        파싱된 기간 문자열
    """
    match = re.search(r'(\d{4})/(\d{1,2})', response_id)
    if not match:
        return '미분류'

    year, period = match.groups()

    # 분할 모드이고 2025년인 경우만 상하반기 구분
    if mode == 'split' and year == '2025':
        half = '상반기' if period == '1' else '하반기'
        return f"{year}년 {half}"
    else:
        return f"{year}년"
```

**작업 내역**:
- [ ] 파일 2의 `parse_period_from_response_id` 복사 (line 50-80)
- [ ] mode 파라미터로 통합/분할 처리
- [ ] if/else로 간단하게 구현 (전략 패턴 불필요)

**추출 소스**: 파일 2, line 50-80

---

### 1.3 데이터 전처리 함수

**목표**: 부서명 정제, 텍스트 정제, 기간 파싱 통합

```python
def process_data(df, mode='integrated'):
    """
    데이터 전처리

    Args:
        df: 원본 데이터프레임
        mode: 기간 표시 모드

    Returns:
        전처리된 데이터프레임
    """
    print(f"⚙️ 데이터 처리 (모드: {mode})")
    df = df.copy()

    # 부서명 정제
    df['부서명'] = df['부서명'].str.strip().fillna('미분류')

    # 기간 파싱
    df['기간'] = df['response_id'].apply(lambda x: parse_period(x, mode))

    # 텍스트 정제
    text_cols = ['협업 후기', '정제된_텍스트']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').str.strip()

    print(f"✅ 처리 완료: {len(df)}행")
    return df
```

**작업 내역**:
- [ ] 파일 1의 데이터 정제 로직 추출 (line 100-200)
- [ ] parse_period 함수 호출
- [ ] 간단한 파이프라인으로 구성

**추출 소스**: 파일 1, line 100-200

---

### 1.4 집계 함수

**목표**: 기간별/부서별 집계를 간단하게

```python
def aggregate_by_period(df):
    """기간별 집계"""
    return df.groupby('기간').agg({
        '협업 후기': 'count',
        '감정_강도_점수': ['mean', 'std'],
        '신뢰도_점수': 'mean'
    }).reset_index()


def aggregate_by_department(df):
    """부서별 집계"""
    dept_stats = []

    for dept in df['부서명'].unique():
        dept_df = df[df['부서명'] == dept]

        stats = {
            '부서명': dept,
            '총_응답수': len(dept_df),
            '긍정_비율': (dept_df['감정_분류'] == '긍정').mean() * 100,
            '평균_감정강도': dept_df['감정_강도_점수'].mean(),
            '평균_신뢰도': dept_df['신뢰도_점수'].mean()
        }
        dept_stats.append(stats)

    return pd.DataFrame(dept_stats)
```

**작업 내역**:
- [ ] 파일 1의 집계 로직 추출 (line 300-500)
- [ ] 간단한 groupby와 for loop로 구현
- [ ] 복잡한 aggregator 클래스 대신 함수 사용

**추출 소스**: 파일 1, line 300-500

---

## Phase 2: 차트 생성 통합 (1시간)

### 2.1 감정 분포 차트

```python
def create_sentiment_chart(df, title="감정 분포"):
    """감정 분포 파이 차트"""
    counts = df['감정_분류'].value_counts()

    fig = go.Figure(data=[go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.3,
        marker=dict(colors=['#27ae60', '#e74c3c', '#95a5a6'])
    )])

    fig.update_layout(
        title=title,
        height=400,
        showlegend=True
    )

    return fig.to_html(include_plotlyjs='cdn', full_html=False)
```

**작업 내역**:
- [ ] 파일 1의 파이 차트 코드 추출 (line 600-700)
- [ ] 색상 일관성 적용
- [ ] CDN 방식으로 통일

**추출 소스**: 파일 1, line 600-700

---

### 2.2 기간별 트렌드 차트

```python
def create_trend_chart(period_df):
    """기간별 트렌드 라인 차트"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=period_df['기간'],
        y=period_df['감정_강도_점수']['mean'],
        mode='lines+markers',
        name='감정 평균',
        line=dict(color='#3498db', width=3),
        marker=dict(size=10)
    ))

    fig.update_layout(
        title="기간별 감정 트렌드",
        xaxis_title="기간",
        yaxis_title="감정 강도",
        height=400,
        hovermode='x unified'
    )

    return fig.to_html(include_plotlyjs='cdn', full_html=False)
```

**작업 내역**:
- [ ] 파일 1의 라인 차트 코드 추출 (line 800-900)
- [ ] 호버 효과 개선
- [ ] x축 레이블 자동 정렬

**추출 소스**: 파일 1, line 800-900

---

### 2.3 부서별 비교 차트

```python
def create_department_chart(dept_stats):
    """부서별 긍정 비율 바 차트"""
    # 긍정 비율 기준 정렬
    dept_stats = dept_stats.sort_values('긍정_비율', ascending=True)

    fig = go.Figure(data=[go.Bar(
        x=dept_stats['긍정_비율'],
        y=dept_stats['부서명'],
        orientation='h',
        marker=dict(
            color=dept_stats['긍정_비율'],
            colorscale='RdYlGn',
            showscale=True
        )
    )])

    fig.update_layout(
        title="부서별 긍정 비율",
        xaxis_title="긍정 비율 (%)",
        yaxis_title="부서명",
        height=max(400, len(dept_stats) * 25),  # 동적 높이
        showlegend=False
    )

    return fig.to_html(include_plotlyjs='cdn', full_html=False)
```

**작업 내역**:
- [ ] 파일 3의 부서별 차트 코드 추출 (line 1200-1400)
- [ ] 가로 막대 그래프로 변경 (부서명 가독성)
- [ ] 색상 그라데이션 적용

**추출 소스**: 파일 3, line 1200-1400

---

## Phase 3: HTML 생성 및 설정 (1시간)

### 3.1 HTML 빌더 함수

```python
def build_html(charts, stats, title="대시보드"):
    """
    HTML 문서 생성

    Args:
        charts: Plotly HTML 차트 리스트
        stats: 통계 딕셔너리 {'total': 1000, 'positive_pct': 75.5, ...}
        title: 대시보드 제목

    Returns:
        완성된 HTML 문자열
    """
    from datetime import datetime

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header p {{
            opacity: 0.9;
            font-size: 0.95em;
        }}

        .content {{
            padding: 40px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }}

        .stat-card strong {{
            display: block;
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .section-title {{
            font-size: 1.8em;
            color: #2c3e50;
            margin: 40px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .chart {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #ecf0f1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <p>생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
        </div>

        <div class="content">
            <h2 class="section-title">📈 요약 통계</h2>
            <div class="summary">
                <div class="stat-card">
                    <strong>총 응답 수</strong>
                    <div class="value">{stats.get('total', 0):,}</div>
                </div>
                <div class="stat-card">
                    <strong>긍정 비율</strong>
                    <div class="value">{stats.get('positive_pct', 0):.1f}%</div>
                </div>
                <div class="stat-card">
                    <strong>평균 감정 강도</strong>
                    <div class="value">{stats.get('avg_intensity', 0):.2f}</div>
                </div>
            </div>

            <h2 class="section-title">📊 시각화</h2>
            {''.join([f'<div class="chart">{chart}</div>' for chart in charts])}
        </div>

        <div class="footer">
            <p>🤖 Dashboard Builder v1.0 | 의료진 협업 피드백 분석 시스템</p>
        </div>
    </div>
</body>
</html>
    """

    return html
```

**작업 내역**:
- [ ] 파일 1의 HTML 템플릿 추출 (line 1500-2000)
- [ ] 반응형 CSS 적용
- [ ] 그라데이션 및 현대적 디자인

**추출 소스**: 파일 1, line 1500-2607

---

### 3.2 설정 파일 작성 (config.py)

```python
"""
대시보드 설정
각 모드별 설정을 딕셔너리로 관리
"""

# 공통 설정
COMMON_CONFIG = {
    'input_file': 'rawdata/2. text_processor_결과_20251013_093925.xlsx',
    'output_dir': 'outputs'
}

# 각 모드별 설정
DASHBOARD_CONFIGS = {
    # 모드 1: 기간 통합 (2025년으로 통합)
    'integrated': {
        'name': '2025년 통합 대시보드',
        'output_file': 'outputs/dashboard_integrated.html',
        'mode': 'integrated',
        'charts': ['sentiment', 'trend'],  # 표시할 차트
        'description': '2025년 전체 기간을 하나로 통합하여 표시'
    },

    # 모드 2: 상하반기 분할 (2025년 상반기/하반기)
    'split': {
        'name': '2025년 상하반기 대시보드',
        'output_file': 'outputs/dashboard_split.html',
        'mode': 'split',
        'charts': ['sentiment', 'trend'],
        'description': '2025년을 상반기/하반기로 구분하여 표시'
    },

    # 모드 3: 부서별 리포트
    'departments': {
        'name': '부서별 협업 리포트',
        'output_file': 'outputs/dashboard_departments.html',
        'mode': 'integrated',
        'charts': ['sentiment', 'trend', 'departments'],
        'description': '모든 부서의 협업 현황을 비교 분석'
    },

    # 모드 4: Standalone (외부망 불가 부서용)
    'standalone': {
        'name': 'Standalone 부서별 리포트',
        'output_file': 'outputs/dashboard_standalone.html',
        'mode': 'integrated',
        'charts': ['sentiment', 'trend', 'departments'],
        'plotly_mode': 'standalone',  # CDN 대신 JS 임베드
        'description': '인터넷 연결 없이도 볼 수 있는 독립형 대시보드'
    }
}

# Plotly standalone 설정
PLOTLY_JS_PATH = 'libs/plotly-latest.min.js'
```

**작업 내역**:
- [ ] 4개 파일의 설정 부분 추출
- [ ] dict 형태로 정리
- [ ] 주석으로 설명 추가

---

### 3.3 메인 로직 구현

```python
def build_dashboard(config_name):
    """
    대시보드 생성 메인 함수

    Args:
        config_name: 설정 이름 ('integrated', 'split', 'departments', 'standalone')
    """
    from config import DASHBOARD_CONFIGS, COMMON_CONFIG, PLOTLY_JS_PATH
    from pathlib import Path

    # 설정 가져오기
    if config_name not in DASHBOARD_CONFIGS:
        raise ValueError(f"알 수 없는 설정: {config_name}")

    config = {**COMMON_CONFIG, **DASHBOARD_CONFIGS[config_name]}

    print(f"\n{'='*60}")
    print(f"🚀 대시보드 생성: {config['name']}")
    print(f"{'='*60}\n")

    # 1. 데이터 로드
    df = load_data(config['input_file'])

    # 2. 데이터 처리
    df = process_data(df, mode=config.get('mode', 'integrated'))

    # 3. 통계 계산
    stats = {
        'total': len(df),
        'positive_pct': (df['감정_분류'] == '긍정').mean() * 100,
        'avg_intensity': df['감정_강도_점수'].mean()
    }

    # 4. 차트 생성
    charts = []
    chart_types = config.get('charts', ['sentiment', 'trend'])

    if 'sentiment' in chart_types:
        print("📊 감정 분포 차트 생성...")
        charts.append(create_sentiment_chart(df))

    if 'trend' in chart_types:
        print("📈 기간별 트렌드 차트 생성...")
        period_df = aggregate_by_period(df)
        charts.append(create_trend_chart(period_df))

    if 'departments' in chart_types:
        print("🏢 부서별 비교 차트 생성...")
        dept_df = aggregate_by_department(df)
        charts.append(create_department_chart(dept_df))

    # 5. HTML 생성
    print("🔨 HTML 문서 생성...")
    html = build_html(charts, stats, title=config['name'])

    # 6. Standalone 모드 처리 (필요시)
    if config.get('plotly_mode') == 'standalone':
        print("🔄 Standalone 모드로 변환...")
        html = convert_to_standalone(html, PLOTLY_JS_PATH)

    # 7. 파일 저장
    output_path = Path(config['output_file'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')

    file_size = output_path.stat().st_size / 1024
    print(f"\n✅ 완료: {output_path}")
    print(f"   파일 크기: {file_size:.1f} KB")
    print(f"   설명: {config.get('description', '')}\n")

    return output_path


def convert_to_standalone(html, plotly_js_path):
    """
    CDN 기반 HTML을 Standalone으로 변환

    Args:
        html: 원본 HTML
        plotly_js_path: Plotly JS 파일 경로

    Returns:
        변환된 HTML
    """
    import re
    from pathlib import Path

    # Plotly JS 읽기
    js_path = Path(plotly_js_path)
    if not js_path.exists():
        print(f"⚠️ Plotly JS 파일 없음: {plotly_js_path}")
        print("   CDN 모드로 유지합니다.")
        return html

    with open(js_path, 'r', encoding='utf-8') as f:
        plotly_js = f.read()

    # CDN 링크를 임베드된 JS로 대체
    cdn_patterns = [
        r'<script src="https://cdn\.plot\.ly/plotly-latest\.min\.js"></script>',
        r'<script src="https://cdn\.plot\.ly/plotly-[\d.]+\.min\.js"></script>',
    ]

    embedded_script = f'<script>{plotly_js}</script>'

    for pattern in cdn_patterns:
        html = re.sub(pattern, embedded_script, html, flags=re.IGNORECASE)

    return html
```

**작업 내역**:
- [ ] 전체 파이프라인 구성
- [ ] 설정 기반 차트 선택
- [ ] Standalone 변환 로직 추가 (파일 4 참고)
- [ ] 진행 상황 출력

---

## Phase 4: 실행 스크립트 및 문서 (30분)

### 4.1 실행 스크립트 (dashboard_builder.py 하단)

```python
if __name__ == "__main__":
    import sys
    from config import DASHBOARD_CONFIGS

    # CLI 인자 처리
    if len(sys.argv) < 2:
        print("=" * 60)
        print("📊 대시보드 빌더")
        print("=" * 60)
        print("\n사용법: python dashboard_builder.py [모드]\n")
        print("사용 가능한 모드:")
        for key, config in DASHBOARD_CONFIGS.items():
            print(f"  • {key:15} - {config['description']}")
        print("\n예시:")
        print("  python dashboard_builder.py integrated")
        print("  python dashboard_builder.py split")
        print("  python dashboard_builder.py departments")
        print()
        sys.exit(0)

    mode = sys.argv[1]

    # 대시보드 생성
    try:
        build_dashboard(mode)
        print("✨ 모든 작업이 완료되었습니다!\n")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

**작업 내역**:
- [ ] 간단한 CLI 구현 (argparse 불필요)
- [ ] 도움말 자동 생성
- [ ] 에러 핸들링

---

### 4.2 README.md 작성

```markdown
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
├── README.md                         - 사용 설명서
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

**증상**: `ValueError: 필수 컬럼 누락: ...`

**해결**: Excel 파일에 필수 컬럼이 있는지 확인:
- response_id
- 부서명
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

## 라이선스

MIT License

## 문의

문제가 발생하면 Issue를 등록해주세요.
```

**작업 내역**:
- [ ] 설치 방법
- [ ] 사용법 (모든 모드)
- [ ] 커스터마이징 가이드
- [ ] 문제 해결 섹션
- [ ] 개발자 가이드

---

## 테스트 체크리스트

### 기능 테스트
- [ ] **integrated 모드**: 2025년 통합 대시보드 생성 확인
- [ ] **split 모드**: 2025년 상하반기 분할 확인
- [ ] **departments 모드**: 모든 부서 차트 표시 확인
- [ ] **standalone 모드**: 인터넷 없이 차트 표시 확인

### 데이터 테스트
- [ ] 1000행 데이터로 테스트
- [ ] 빈 데이터 처리 확인
- [ ] 잘못된 컬럼명 처리 확인

### 출력 테스트
- [ ] HTML 파일 생성 확인
- [ ] 파일 크기 적정성 (< 5MB)
- [ ] 브라우저에서 정상 표시 확인
- [ ] 반응형 디자인 확인 (모바일)

### 성능 테스트
- [ ] 10,000행 데이터: < 10초
- [ ] 50,000행 데이터: < 30초

---

## 예상 타임라인

| Phase | 작업 내용 | 예상 시간 | 누적 시간 |
|-------|----------|-----------|-----------|
| 1 | 공통 함수 추출 | 1.5시간 | 1.5h |
| 2 | 차트 생성 통합 | 1시간 | 2.5h |
| 3 | HTML 생성 및 설정 | 1시간 | 3.5h |
| 4 | 실행 스크립트 및 문서 | 30분 | 4h |

**총 예상 시간**: 4시간

---

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
- README.md (100줄)

총 750-850줄 (89% 감소)
중복 제거
수정 시 1곳만 변경
초보자도 이해 가능
```

---

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

---

## 다음 단계 (선택사항)

리팩토링 완료 후 추가할 수 있는 기능들 (우선순위 낮음):

### 단기 개선 (1-2주)
- [ ] 배치 실행 스크립트 (모든 모드 한번에 생성)
- [ ] 진행 상황 프로그레스 바
- [ ] 로그 파일 저장 기능

### 중기 개선 (1-2개월)
- [ ] 웹 인터페이스 (Streamlit)
- [ ] 대화형 필터링
- [ ] PDF 내보내기

### 장기 개선 (3-6개월)
- [ ] 자동 스케줄링
- [ ] 이메일 리포트 발송
- [ ] 대시보드 템플릿 커스터마이징 UI

---

## 참고 자료

- [Pandas 공식 문서](https://pandas.pydata.org/)
- [Plotly Python 문서](https://plotly.com/python/)
- [Python 정규표현식](https://docs.python.org/3/library/re.html)

---

**작성일**: 2025-01-14
**버전**: 1.0 (간소화 버전)
**설계 원칙**: KISS - Keep It Simple, Stupid
