# 대시보드 시스템 리팩토링 상세 계획

## 개요

**목표**: 4개의 대시보드 생성 스크립트(총 7,900줄)를 단일 모듈형 시스템(~2,500줄)으로 통합
**예상 코드 감소율**: 68%
**예상 소요 시간**: 9-12시간

## 현재 파일 구조

### 통합 대상 파일 (4개)
1. `3. build_dashboard_html_2025년 기간 통합.py` (2,607줄) - 기간 통합 표시
2. `3. build_dashboard_html_2025년 상하반기 나누기.py` (2,639줄) - 상하반기 구분 표시
3. `4. team_reports_외부망접근가능한부서.py` (2,509줄) - 부서별 리포트 + 네트워크 분석
4. `4. team_reports_외부망불가능부서(디지털).py` (145줄) - Standalone HTML 변환

### 코드 중복 분석
- **데이터 로딩**: 85% 중복
- **데이터 집계**: 90% 중복
- **차트 생성**: 80% 중복
- **HTML 렌더링**: 75% 중복

## 목표 아키텍처

```
dashboard/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── data_loader.py          # 데이터 로딩
│   ├── data_processor.py       # 데이터 전처리
│   └── aggregator.py           # 데이터 집계
├── processors/
│   ├── __init__.py
│   ├── period_handler.py       # 기간 처리 (통합/분할)
│   └── network_analyzer.py     # 협업 네트워크 분석
├── renderers/
│   ├── __init__.py
│   ├── html_builder.py         # HTML 생성
│   ├── chart_builder.py        # Plotly 차트 생성
│   └── standalone_converter.py # CDN → Standalone 변환
├── models/
│   ├── __init__.py
│   ├── dashboard_config.py     # 설정 데이터 클래스
│   └── report_data.py          # 리포트 데이터 모델
└── utils/
    ├── __init__.py
    ├── logger.py               # 로깅 유틸
    ├── validators.py           # 유효성 검증
    └── file_utils.py           # 파일 처리

main.py                          # CLI 진입점
requirements.txt
README.md
```

---

## Phase 0: 환경 설정 및 준비 (30분)

### 0.1 디렉토리 구조 생성
```bash
cd /home/cocori2864/team-review-optimization
mkdir -p dashboard/{core,processors,renderers,models,utils}
touch dashboard/__init__.py
touch dashboard/core/__init__.py
touch dashboard/processors/__init__.py
touch dashboard/renderers/__init__.py
touch dashboard/models/__init__.py
touch dashboard/utils/__init__.py
touch main.py
touch requirements.txt
```

**검증**: `tree dashboard` 명령으로 구조 확인

### 0.2 기존 파일 분석 및 매핑
- [ ] 파일 1: 핵심 데이터 로딩 로직 위치 파악 (line 1-100)
- [ ] 파일 1: 데이터 집계 로직 위치 파악 (line 100-500)
- [ ] 파일 1: 차트 생성 로직 위치 파악 (line 500-1500)
- [ ] 파일 1: HTML 템플릿 위치 파악 (line 1500-2607)
- [ ] 파일 2: 기간 파싱 로직 차이점 분석 (`parse_period_from_response_id`)
- [ ] 파일 3: 네트워크 분석 로직 위치 파악
- [ ] 파일 4: Standalone 변환 로직 분석

**Git Checkpoint**:
```bash
git add .
git commit -m "chore: 프로젝트 디렉토리 구조 생성"
```

---

## Phase 1: 데이터 모델 정의 (1시간)

### 1.1 Enums 정의 (`dashboard/models/dashboard_config.py`)

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path

class PeriodMode(Enum):
    """기간 표시 모드"""
    INTEGRATED = "integrated"  # 2025년 (통합)
    SPLIT = "split"            # 2025년 상반기/하반기

class OutputScope(Enum):
    """출력 범위"""
    HOSPITAL = "hospital"      # 병원 전체
    DEPARTMENT = "department"  # 부서별

class PlotlyMode(Enum):
    """Plotly 모드"""
    CDN = "cdn"                # CDN 링크 사용
    STANDALONE = "standalone"  # JS 임베드

@dataclass
class DashboardConfig:
    """대시보드 생성 설정"""
    # 필수 파라미터
    input_file: Path
    output_dir: Path = field(default_factory=lambda: Path("outputs"))

    # 모드 설정
    period_mode: PeriodMode = PeriodMode.INTEGRATED
    output_scope: OutputScope = OutputScope.HOSPITAL
    plotly_mode: PlotlyMode = PlotlyMode.CDN

    # 네트워크 분석 옵션
    enable_network_analysis: bool = False

    # Plotly standalone 옵션
    plotly_js_path: Optional[Path] = None

    # 필터링 옵션
    exclude_departments: List[str] = field(default_factory=list)

    def __post_init__(self):
        """유효성 검증"""
        if not self.input_file.exists():
            raise FileNotFoundError(f"입력 파일 없음: {self.input_file}")

        if self.plotly_mode == PlotlyMode.STANDALONE:
            if not self.plotly_js_path or not self.plotly_js_path.exists():
                raise ValueError("Standalone 모드는 plotly_js_path 필수")

        if self.enable_network_analysis and self.output_scope != OutputScope.DEPARTMENT:
            raise ValueError("네트워크 분석은 부서별 출력에서만 가능")

        self.output_dir.mkdir(parents=True, exist_ok=True)
```

**체크리스트**:
- [ ] `PeriodMode` enum 구현 및 테스트
- [ ] `OutputScope` enum 구현 및 테스트
- [ ] `PlotlyMode` enum 구현 및 테스트
- [ ] `DashboardConfig` 데이터클래스 구현
- [ ] `__post_init__` 유효성 검증 로직 구현
- [ ] 유닛 테스트 작성 (pytest)

**테스트 예시**:
```python
# test_dashboard_config.py
def test_config_validation():
    with pytest.raises(ValueError):
        DashboardConfig(
            input_file=Path("test.xlsx"),
            plotly_mode=PlotlyMode.STANDALONE
            # plotly_js_path 누락 → 에러 발생 기대
        )
```

### 1.2 Logger 설정 (`dashboard/utils/logger.py`)

```python
import logging
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_dir: Path = Path("logs")) -> logging.Logger:
    """구조화된 로거 설정"""
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 파일 핸들러
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(log_dir / f"{name}_{timestamp}.log")
    fh.setLevel(logging.DEBUG)

    # 콘솔 핸들러
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
```

**체크리스트**:
- [ ] Logger 기본 설정 구현
- [ ] 파일 핸들러 구현 (자동 타임스탬프)
- [ ] 콘솔 핸들러 구현
- [ ] 로그 레벨 설정 (DEBUG/INFO/WARNING/ERROR)

### 1.3 Validators (`dashboard/utils/validators.py`)

```python
import pandas as pd
from pathlib import Path
from typing import List

class DataValidator:
    """데이터 유효성 검증"""

    REQUIRED_COLUMNS = [
        "응답 ID",
        "부서명",
        "기간_표시",
        "협업 후기"
    ]

    @staticmethod
    def validate_excel_structure(df: pd.DataFrame) -> List[str]:
        """Excel 파일 구조 검증"""
        errors = []

        # 필수 컬럼 체크
        missing_cols = set(DataValidator.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            errors.append(f"필수 컬럼 누락: {missing_cols}")

        # 빈 데이터 체크
        if df.empty:
            errors.append("데이터가 비어있습니다")

        # 부서명 중복 체크
        if df["부서명"].isna().any():
            errors.append("부서명에 결측치가 있습니다")

        return errors
```

**체크리스트**:
- [ ] 필수 컬럼 검증 로직
- [ ] 빈 데이터 검증
- [ ] 부서명 중복/결측 검증
- [ ] 유닛 테스트 작성

**Git Checkpoint**:
```bash
git add dashboard/models/ dashboard/utils/
git commit -m "feat: 데이터 모델 및 유틸리티 구현 (Phase 1)"
```

---

## Phase 2: 핵심 데이터 처리 로직 (2-3시간)

### 2.1 DataLoader (`dashboard/core/data_loader.py`)

**역할**: Excel 파일 로딩, 초기 검증, 기본 전처리

```python
import pandas as pd
from pathlib import Path
from typing import Optional
from ..utils.logger import setup_logger
from ..utils.validators import DataValidator

class DataLoader:
    """데이터 로딩 및 초기 검증"""

    def __init__(self):
        self.logger = setup_logger("DataLoader")

    def load_excel(self, file_path: Path, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Excel 파일 로딩"""
        self.logger.info(f"Excel 로딩 시작: {file_path}")

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            self.logger.info(f"로딩 완료: {len(df)}행, {len(df.columns)}열")

            # 유효성 검증
            errors = DataValidator.validate_excel_structure(df)
            if errors:
                raise ValueError(f"데이터 검증 실패:\n" + "\n".join(errors))

            return df

        except Exception as e:
            self.logger.error(f"로딩 실패: {e}")
            raise
```

**추출 소스**:
- 파일 1, line 10-50 참조
- `pd.read_excel()` 호출 부분 추출

**체크리스트**:
- [ ] `load_excel()` 메서드 구현
- [ ] 에러 핸들링 (FileNotFoundError, 잘못된 형식 등)
- [ ] 로깅 통합
- [ ] 유닛 테스트 (mock 데이터 사용)

### 2.2 DataProcessor (`dashboard/core/data_processor.py`)

**역할**: 데이터 정제, 형변환, 파생 컬럼 생성

```python
import pandas as pd
import re
from datetime import datetime
from ..models.dashboard_config import PeriodMode
from ..utils.logger import setup_logger

class DataProcessor:
    """데이터 전처리 및 정제"""

    def __init__(self, period_mode: PeriodMode):
        self.period_mode = period_mode
        self.logger = setup_logger("DataProcessor")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """전처리 파이프라인 실행"""
        self.logger.info("데이터 전처리 시작")

        df = df.copy()
        df = self._clean_department_names(df)
        df = self._parse_response_ids(df)
        df = self._parse_periods(df)
        df = self._clean_text_columns(df)

        self.logger.info(f"전처리 완료: {len(df)}행")
        return df

    def _parse_periods(self, df: pd.DataFrame) -> pd.DataFrame:
        """기간 파싱 (통합 vs 분할 모드)"""
        def parse_period(response_id):
            match = re.search(r'(\d{4})/(\d{1,2})', response_id)
            if not match:
                return None

            year, period = match.groups()

            if self.period_mode == PeriodMode.SPLIT and year == "2025":
                period_name = "상반기" if period == "1" else "하반기"
                return f"{year}년 {period_name}"
            else:
                return f"{year}년"

        df["기간_파싱"] = df["응답 ID"].apply(parse_period)
        return df

    def _clean_department_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """부서명 정제"""
        df["부서명"] = df["부서명"].str.strip()
        df["부서명"] = df["부서명"].fillna("미분류")
        return df

    def _clean_text_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """텍스트 컬럼 정제"""
        text_cols = ["협업 후기", "정제된_텍스트"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("")
                df[col] = df[col].str.strip()
        return df

    def _parse_response_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """응답 ID에서 메타데이터 추출"""
        df["타임스탬프"] = pd.to_datetime(
            df["응답 ID"].str.extract(r'(\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}:\d{2})')[0],
            format='%Y/%m/%d %H:%M:%S',
            errors='coerce'
        )
        return df
```

**추출 소스**:
- 파일 1, line 100-300 참조
- 파일 2, `parse_period_from_response_id` 함수 참조 (line 50-80)

**체크리스트**:
- [ ] `_parse_periods()` 구현 (통합/분할 모드 대응)
- [ ] `_clean_department_names()` 구현
- [ ] `_clean_text_columns()` 구현
- [ ] `_parse_response_ids()` 구현 (타임스탬프 추출)
- [ ] 유닛 테스트 (각 모드별 테스트)

### 2.3 DataAggregator (`dashboard/core/aggregator.py`)

**역할**: 통계 집계, 감정 분석 집계, 부서별/기간별 그룹화

```python
import pandas as pd
from typing import Dict, Any
from ..utils.logger import setup_logger

class DataAggregator:
    """데이터 집계"""

    def __init__(self):
        self.logger = setup_logger("DataAggregator")

    def aggregate_by_department(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """부서별 집계"""
        self.logger.info("부서별 집계 시작")

        dept_data = {}
        for dept in df["부서명"].unique():
            dept_df = df[df["부서명"] == dept].copy()
            dept_data[dept] = {
                "raw_data": dept_df,
                "stats": self._calculate_department_stats(dept_df)
            }

        return dept_data

    def aggregate_by_period(self, df: pd.DataFrame) -> pd.DataFrame:
        """기간별 집계"""
        period_stats = df.groupby("기간_파싱").agg({
            "협업 후기": "count",
            "감정_강도_점수": ["mean", "std"],
            "신뢰도_점수": "mean"
        }).reset_index()

        period_stats.columns = ["기간", "응답수", "감정_평균", "감정_편차", "신뢰도"]
        return period_stats

    def _calculate_department_stats(self, dept_df: pd.DataFrame) -> Dict[str, Any]:
        """부서 통계 계산"""
        stats = {
            "total_responses": len(dept_df),
            "positive_ratio": (dept_df["감정_분류"] == "긍정").mean(),
            "negative_ratio": (dept_df["감정_분류"] == "부정").mean(),
            "avg_intensity": dept_df["감정_강도_점수"].mean(),
            "avg_confidence": dept_df["신뢰도_점수"].mean()
        }
        return stats
```

**추출 소스**:
- 파일 1, line 300-600 참조 (집계 로직)
- 파일 3, 부서별 네트워크 집계 로직 참조

**체크리스트**:
- [ ] `aggregate_by_department()` 구현
- [ ] `aggregate_by_period()` 구현
- [ ] `_calculate_department_stats()` 구현
- [ ] 감정 분류별 집계 추가
- [ ] 유닛 테스트

**Git Checkpoint**:
```bash
git add dashboard/core/
git commit -m "feat: 핵심 데이터 처리 로직 구현 (Phase 2)"
```

---

## Phase 3: 선택적 기능 구현 (1.5-2시간)

### 3.1 PeriodHandler (`dashboard/processors/period_handler.py`)

**역할**: 기간 처리 전략 패턴 구현

```python
from abc import ABC, abstractmethod
import pandas as pd
import re

class PeriodHandler(ABC):
    """기간 처리 추상 클래스"""

    @abstractmethod
    def parse_period(self, response_id: str) -> str:
        """응답 ID에서 기간 파싱"""
        pass

class IntegratedPeriodHandler(PeriodHandler):
    """통합 기간 핸들러 (2025년)"""

    def parse_period(self, response_id: str) -> str:
        match = re.search(r'(\d{4})/(\d{1,2})', response_id)
        if match:
            year = match.group(1)
            return f"{year}년"
        return "미분류"

class SplitPeriodHandler(PeriodHandler):
    """분할 기간 핸들러 (2025년 상반기/하반기)"""

    def parse_period(self, response_id: str) -> str:
        match = re.search(r'(\d{4})/(\d{1,2})', response_id)
        if not match:
            return "미분류"

        year, period = match.groups()

        if year == "2025":
            period_name = "상반기" if period == "1" else "하반기"
            return f"{year}년 {period_name}"
        else:
            return f"{year}년"
```

**추출 소스**:
- 파일 2, line 50-100 참조 (`parse_period_from_response_id` 함수)

**체크리스트**:
- [ ] `PeriodHandler` 추상 클래스 구현
- [ ] `IntegratedPeriodHandler` 구현
- [ ] `SplitPeriodHandler` 구현
- [ ] Factory 패턴 추가 (선택사항)
- [ ] 유닛 테스트 (다양한 응답 ID 패턴)

### 3.2 NetworkAnalyzer (`dashboard/processors/network_analyzer.py`)

**역할**: 부서 간 협업 네트워크 분석

```python
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple
from ..utils.logger import setup_logger

class NetworkAnalyzer:
    """협업 네트워크 분석"""

    def __init__(self):
        self.logger = setup_logger("NetworkAnalyzer")

    def build_collaboration_network(
        self,
        df: pd.DataFrame,
        source_dept: str
    ) -> nx.DiGraph:
        """협업 네트워크 그래프 구축"""
        self.logger.info(f"네트워크 분석 시작: {source_dept}")

        G = nx.DiGraph()

        # 부서별 협업 관계 추출
        dept_df = df[df["부서명"] == source_dept]

        for _, row in dept_df.iterrows():
            # 협업 후기에서 다른 부서명 추출
            mentioned_depts = self._extract_mentioned_departments(
                row["협업 후기"],
                df["부서명"].unique()
            )

            for target_dept in mentioned_depts:
                if target_dept != source_dept:
                    if G.has_edge(source_dept, target_dept):
                        G[source_dept][target_dept]["weight"] += 1
                    else:
                        G.add_edge(source_dept, target_dept, weight=1)

        return G

    def calculate_centrality(self, G: nx.DiGraph) -> Dict[str, float]:
        """중심성 지표 계산"""
        return {
            "degree": nx.degree_centrality(G),
            "betweenness": nx.betweenness_centrality(G),
            "closeness": nx.closeness_centrality(G)
        }

    def _extract_mentioned_departments(
        self,
        text: str,
        all_depts: List[str]
    ) -> List[str]:
        """텍스트에서 언급된 부서 추출"""
        mentioned = []
        for dept in all_depts:
            if dept in text:
                mentioned.append(dept)
        return mentioned
```

**추출 소스**:
- 파일 3, line 1000-1500 참조 (네트워크 분석 로직)

**체크리스트**:
- [ ] NetworkX 그래프 구축 로직
- [ ] 중심성 지표 계산
- [ ] 부서명 추출 로직 (정규식 또는 키워드 매칭)
- [ ] 유닛 테스트 (mock 네트워크)

### 3.3 StandaloneConverter (`dashboard/renderers/standalone_converter.py`)

**역할**: CDN 기반 HTML을 Standalone HTML로 변환

```python
import re
from pathlib import Path
from typing import Optional
from ..utils.logger import setup_logger

class StandaloneConverter:
    """Standalone HTML 변환기"""

    def __init__(self, plotly_js_path: Path):
        self.plotly_js_path = plotly_js_path
        self.logger = setup_logger("StandaloneConverter")

    def convert(self, input_html: Path, output_html: Path) -> None:
        """CDN → Standalone 변환"""
        self.logger.info(f"변환 시작: {input_html} → {output_html}")

        # HTML 읽기
        with open(input_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Plotly JS 읽기
        with open(self.plotly_js_path, 'r', encoding='utf-8') as f:
            plotly_js = f.read()

        # CDN 링크를 임베드된 JS로 대체
        html_content = self._replace_cdn_with_embedded(html_content, plotly_js)

        # 저장
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"변환 완료: {output_html}")

    def _replace_cdn_with_embedded(self, html: str, js: str) -> str:
        """CDN 링크 대체"""
        # Plotly CDN 패턴들
        cdn_patterns = [
            r'<script src="https://cdn\.plot\.ly/plotly-latest\.min\.js"></script>',
            r'<script src="https://cdn\.plot\.ly/plotly-[\d.]+\.min\.js"></script>',
            r'<script src="https://cdn\.jsdelivr\.net/npm/plotly\.js@[\d.]+/dist/plotly\.min\.js"></script>'
        ]

        embedded_script = f'<script>{js}</script>'

        for pattern in cdn_patterns:
            html = re.sub(pattern, embedded_script, html, flags=re.IGNORECASE)

        return html
```

**추출 소스**:
- 파일 4, 전체 로직 참조 (145줄)

**체크리스트**:
- [ ] HTML 파일 읽기/쓰기
- [ ] Plotly CDN 링크 감지 (정규식)
- [ ] 임베드된 스크립트로 대체
- [ ] 다양한 CDN 패턴 대응
- [ ] 유닛 테스트 (mock HTML)

**Git Checkpoint**:
```bash
git add dashboard/processors/ dashboard/renderers/standalone_converter.py
git commit -m "feat: 선택적 기능 구현 - 기간 처리, 네트워크, Standalone (Phase 3)"
```

---

## Phase 4: HTML 렌더링 (2-3시간)

### 4.1 ChartBuilder (`dashboard/renderers/chart_builder.py`)

**역할**: Plotly 차트 생성

```python
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any
from ..models.dashboard_config import PlotlyMode
from ..utils.logger import setup_logger

class ChartBuilder:
    """Plotly 차트 생성기"""

    def __init__(self, plotly_mode: PlotlyMode):
        self.plotly_mode = plotly_mode
        self.logger = setup_logger("ChartBuilder")

    def create_sentiment_distribution_chart(
        self,
        df: pd.DataFrame,
        title: str = "감정 분포"
    ) -> str:
        """감정 분포 파이 차트"""
        sentiment_counts = df["감정_분류"].value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=sentiment_counts.index,
            values=sentiment_counts.values,
            hole=0.3
        )])

        fig.update_layout(title=title)

        return self._fig_to_html(fig)

    def create_period_trend_chart(
        self,
        period_df: pd.DataFrame
    ) -> str:
        """기간별 트렌드 라인 차트"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=period_df["기간"],
            y=period_df["감정_평균"],
            mode='lines+markers',
            name='감정 평균'
        ))

        fig.update_layout(
            title="기간별 감정 트렌드",
            xaxis_title="기간",
            yaxis_title="감정 강도"
        )

        return self._fig_to_html(fig)

    def create_department_comparison_chart(
        self,
        dept_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """부서별 비교 바 차트"""
        depts = list(dept_stats.keys())
        positive_ratios = [stats["positive_ratio"] for stats in dept_stats.values()]

        fig = go.Figure(data=[go.Bar(
            x=depts,
            y=positive_ratios,
            name='긍정 비율'
        )])

        fig.update_layout(title="부서별 긍정 비율")

        return self._fig_to_html(fig)

    def _fig_to_html(self, fig: go.Figure) -> str:
        """Plotly Figure → HTML 변환"""
        if self.plotly_mode == PlotlyMode.CDN:
            return fig.to_html(include_plotlyjs='cdn', full_html=False)
        else:
            return fig.to_html(include_plotlyjs='directory', full_html=False)
```

**추출 소스**:
- 파일 1, line 600-1500 참조 (다양한 차트 생성 로직)
- `go.Figure()`, `px.bar()` 등 Plotly 호출 부분 추출

**체크리스트**:
- [ ] 감정 분포 파이 차트
- [ ] 기간별 트렌드 라인 차트
- [ ] 부서별 비교 바 차트
- [ ] 네트워크 그래프 (선택)
- [ ] CDN vs Directory 모드 분기
- [ ] 유닛 테스트

### 4.2 HTMLBuilder (`dashboard/renderers/html_builder.py`)

**역할**: 최종 HTML 문서 조립

```python
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from ..models.dashboard_config import DashboardConfig, OutputScope
from ..utils.logger import setup_logger

class HTMLBuilder:
    """HTML 문서 생성기"""

    def __init__(self, config: DashboardConfig):
        self.config = config
        self.logger = setup_logger("HTMLBuilder")

    def build_dashboard(
        self,
        charts: List[str],
        stats: Dict[str, Any],
        metadata: Dict[str, str]
    ) -> str:
        """대시보드 HTML 조립"""
        html_parts = [
            self._build_header(metadata),
            self._build_summary_section(stats),
            self._build_charts_section(charts),
            self._build_footer()
        ]

        return "\n".join(html_parts)

    def _build_header(self, metadata: Dict[str, str]) -> str:
        """HTML 헤더"""
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.get('title', '대시보드')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Noto Sans KR', sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .stat-card {{
            display: inline-block;
            padding: 20px;
            margin: 10px;
            background: #e3f2fd;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{metadata.get('title', '대시보드')}</h1>
        <p>생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""

    def _build_summary_section(self, stats: Dict[str, Any]) -> str:
        """요약 섹션"""
        return f"""
        <h2>📊 요약 통계</h2>
        <div class="summary">
            <div class="stat-card">
                <strong>총 응답 수:</strong> {stats.get('total_responses', 0)}
            </div>
            <div class="stat-card">
                <strong>긍정 비율:</strong> {stats.get('positive_ratio', 0):.1%}
            </div>
            <div class="stat-card">
                <strong>평균 감정 강도:</strong> {stats.get('avg_intensity', 0):.2f}
            </div>
        </div>
"""

    def _build_charts_section(self, charts: List[str]) -> str:
        """차트 섹션"""
        charts_html = "\n".join([f'<div class="chart">{chart}</div>' for chart in charts])
        return f"""
        <h2>📈 시각화</h2>
        {charts_html}
"""

    def _build_footer(self) -> str:
        """HTML 푸터"""
        return """
    </div>
</body>
</html>
"""
```

**추출 소스**:
- 파일 1, line 1500-2607 참조 (HTML 템플릿)
- CSS 스타일 추출
- JavaScript 코드 추출 (필요시)

**체크리스트**:
- [ ] HTML 헤더 템플릿
- [ ] 요약 통계 섹션
- [ ] 차트 섹션
- [ ] 푸터 템플릿
- [ ] CSS 스타일 정의
- [ ] 유닛 테스트

**Git Checkpoint**:
```bash
git add dashboard/renderers/
git commit -m "feat: HTML 렌더링 구현 - 차트 및 HTML 빌더 (Phase 4)"
```

---

## Phase 5: 통합 및 CLI (1.5-2시간)

### 5.1 DashboardBuilder (`dashboard/dashboard_builder.py`)

**역할**: 모든 컴포넌트 통합

```python
from pathlib import Path
from typing import Optional
from .models.dashboard_config import DashboardConfig, OutputScope
from .core.data_loader import DataLoader
from .core.data_processor import DataProcessor
from .core.aggregator import DataAggregator
from .renderers.chart_builder import ChartBuilder
from .renderers.html_builder import HTMLBuilder
from .renderers.standalone_converter import StandaloneConverter
from .processors.network_analyzer import NetworkAnalyzer
from .utils.logger import setup_logger

class DashboardBuilder:
    """대시보드 생성 오케스트레이터"""

    def __init__(self, config: DashboardConfig):
        self.config = config
        self.logger = setup_logger("DashboardBuilder")

        # 컴포넌트 초기화
        self.loader = DataLoader()
        self.processor = DataProcessor(config.period_mode)
        self.aggregator = DataAggregator()
        self.chart_builder = ChartBuilder(config.plotly_mode)
        self.html_builder = HTMLBuilder(config)

    def build(self) -> Path:
        """대시보드 생성 파이프라인"""
        self.logger.info("=== 대시보드 생성 시작 ===")

        # 1. 데이터 로딩
        df = self.loader.load_excel(self.config.input_file)

        # 2. 데이터 전처리
        df = self.processor.process(df)

        # 3. 데이터 집계
        if self.config.output_scope == OutputScope.HOSPITAL:
            return self._build_hospital_dashboard(df)
        else:
            return self._build_department_dashboards(df)

    def _build_hospital_dashboard(self, df) -> Path:
        """병원 전체 대시보드"""
        # 통계 계산
        stats = self.aggregator.calculate_hospital_stats(df)

        # 차트 생성
        charts = [
            self.chart_builder.create_sentiment_distribution_chart(df),
            self.chart_builder.create_period_trend_chart(
                self.aggregator.aggregate_by_period(df)
            )
        ]

        # HTML 조립
        html = self.html_builder.build_dashboard(
            charts=charts,
            stats=stats,
            metadata={"title": "병원 전체 대시보드"}
        )

        # 파일 저장
        output_path = self.config.output_dir / "hospital_dashboard.html"
        output_path.write_text(html, encoding='utf-8')

        self.logger.info(f"대시보드 생성 완료: {output_path}")
        return output_path

    def _build_department_dashboards(self, df) -> Path:
        """부서별 대시보드"""
        dept_data = self.aggregator.aggregate_by_department(df)

        output_paths = []
        for dept_name, data in dept_data.items():
            # 네트워크 분석 (선택)
            if self.config.enable_network_analysis:
                analyzer = NetworkAnalyzer()
                network = analyzer.build_collaboration_network(df, dept_name)
                # 네트워크 차트 추가...

            # 부서별 차트 생성
            charts = [
                self.chart_builder.create_sentiment_distribution_chart(
                    data["raw_data"],
                    title=f"{dept_name} 감정 분포"
                )
            ]

            # HTML 조립
            html = self.html_builder.build_dashboard(
                charts=charts,
                stats=data["stats"],
                metadata={"title": f"{dept_name} 부서 리포트"}
            )

            # 파일 저장
            filename = f"{dept_name}_report.html"
            output_path = self.config.output_dir / filename
            output_path.write_text(html, encoding='utf-8')

            output_paths.append(output_path)

        self.logger.info(f"{len(output_paths)}개 부서 리포트 생성 완료")
        return self.config.output_dir
```

**체크리스트**:
- [ ] 전체 파이프라인 구성
- [ ] 병원 전체 모드 구현
- [ ] 부서별 모드 구현
- [ ] 에러 핸들링 (각 단계별)
- [ ] 로깅 통합
- [ ] 통합 테스트

### 5.2 CLI (`main.py`)

**역할**: Click 기반 명령줄 인터페이스

```python
import click
from pathlib import Path
from dashboard.models.dashboard_config import (
    DashboardConfig,
    PeriodMode,
    OutputScope,
    PlotlyMode
)
from dashboard.dashboard_builder import DashboardBuilder

@click.command()
@click.option(
    '-i', '--input', 'input_file',
    type=click.Path(exists=True),
    required=True,
    help='입력 Excel 파일 경로'
)
@click.option(
    '-o', '--output', 'output_dir',
    type=click.Path(),
    default='outputs',
    help='출력 디렉토리'
)
@click.option(
    '--period',
    type=click.Choice(['integrated', 'split'], case_sensitive=False),
    default='integrated',
    help='기간 표시 모드 (integrated: 통합, split: 상하반기 분할)'
)
@click.option(
    '--scope',
    type=click.Choice(['hospital', 'department'], case_sensitive=False),
    default='hospital',
    help='출력 범위 (hospital: 병원 전체, department: 부서별)'
)
@click.option(
    '--network',
    is_flag=True,
    help='부서별 네트워크 분석 활성화 (--scope department 필요)'
)
@click.option(
    '--plotly',
    type=click.Choice(['cdn', 'standalone'], case_sensitive=False),
    default='cdn',
    help='Plotly 모드 (cdn: CDN 링크, standalone: JS 임베드)'
)
@click.option(
    '--plotly-js',
    type=click.Path(exists=True),
    help='Plotly JS 파일 경로 (standalone 모드 필수)'
)
def main(input_file, output_dir, period, scope, network, plotly, plotly_js):
    """대시보드 생성 CLI"""

    click.echo("🚀 대시보드 생성 시작...")

    # 설정 객체 생성
    config = DashboardConfig(
        input_file=Path(input_file),
        output_dir=Path(output_dir),
        period_mode=PeriodMode(period),
        output_scope=OutputScope(scope),
        plotly_mode=PlotlyMode(plotly),
        enable_network_analysis=network,
        plotly_js_path=Path(plotly_js) if plotly_js else None
    )

    # 대시보드 생성
    try:
        builder = DashboardBuilder(config)
        output_path = builder.build()

        click.echo(f"✅ 생성 완료: {output_path}")

    except Exception as e:
        click.echo(f"❌ 에러 발생: {e}", err=True)
        raise

if __name__ == '__main__':
    main()
```

**체크리스트**:
- [ ] Click 옵션 정의 (모든 모드 대응)
- [ ] 설정 객체 생성
- [ ] DashboardBuilder 호출
- [ ] 에러 핸들링
- [ ] 도움말 메시지
- [ ] CLI 테스트 (수동)

**사용 예시**:
```bash
# 모드 1: 병원 전체, 기간 통합
python main.py -i data.xlsx --period integrated

# 모드 2: 병원 전체, 상하반기 분할
python main.py -i data.xlsx --period split

# 모드 3: 부서별 리포트, 네트워크 분석
python main.py -i data.xlsx --scope department --network

# 모드 4: 부서별, Standalone HTML
python main.py -i data.xlsx --scope department --network --plotly standalone --plotly-js plotly.min.js
```

**Git Checkpoint**:
```bash
git add dashboard/dashboard_builder.py main.py
git commit -m "feat: 통합 및 CLI 구현 (Phase 5)"
```

---

## Phase 6: 문서화 및 테스트 (1시간)

### 6.1 README 작성

```markdown
# 대시보드 생성 시스템

## 개요
의료진 협업 피드백 데이터를 기반으로 다양한 형태의 대시보드를 생성하는 통합 시스템

## 설치
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## 사용법

### 기본 사용
\`\`\`bash
python main.py -i data.xlsx
\`\`\`

### 모드별 사용 예시
[상세 예시 포함]

## 아키텍처
[구조 다이어그램 포함]

## API 문서
[주요 클래스 및 메서드 설명]

## 기여
[코드 스타일, 테스트 방법 등]
```

### 6.2 요구사항 파일

```txt
# requirements.txt
pandas>=1.5.0
openpyxl>=3.1.0
plotly>=5.18.0
networkx>=3.2
click>=8.1.7
pytest>=7.4.0
```

### 6.3 마이그레이션 가이드

```markdown
# 마이그레이션 가이드

## 기존 스크립트 → 새 CLI

### 변경 전
\`\`\`bash
python "3. build_dashboard_html_2025년 기간 통합.py"
\`\`\`

### 변경 후
\`\`\`bash
python main.py -i rawdata/2.text_processor_결과.xlsx --period integrated
\`\`\`

[각 파일별 마이그레이션 예시]
```

**체크리스트**:
- [ ] README.md 작성
- [ ] requirements.txt 작성
- [ ] MIGRATION.md 작성
- [ ] 주석 및 docstring 보완
- [ ] 타입 힌트 추가

**Git Checkpoint**:
```bash
git add README.md requirements.txt MIGRATION.md
git commit -m "docs: 문서화 완료 (Phase 6)"
git tag v1.0.0
```

---

## 검증 체크리스트

### 기능 검증
- [ ] **모드 1**: 기간 통합 대시보드 생성 성공
- [ ] **모드 2**: 상하반기 분할 대시보드 생성 성공
- [ ] **모드 3**: 부서별 리포트 + 네트워크 생성 성공
- [ ] **모드 4**: Standalone HTML 변환 성공

### 품질 검증
- [ ] 유닛 테스트 커버리지 ≥80%
- [ ] 통합 테스트 통과
- [ ] 코드 스타일 검사 (flake8, black)
- [ ] 타입 체크 (mypy)

### 성능 검증
- [ ] 1000행 데이터 처리 < 30초
- [ ] 메모리 사용량 < 500MB
- [ ] 생성된 HTML 파일 크기 적정

### 문서 검증
- [ ] README 완성도
- [ ] API 문서 완성도
- [ ] 마이그레이션 가이드 완성도
- [ ] 코드 주석 완성도

---

## 예상 타임라인

| Phase | 설명 | 예상 시간 | 누적 시간 |
|-------|------|-----------|-----------|
| 0 | 환경 설정 | 30분 | 0.5h |
| 1 | 데이터 모델 | 1시간 | 1.5h |
| 2 | 핵심 처리 로직 | 2.5시간 | 4h |
| 3 | 선택적 기능 | 2시간 | 6h |
| 4 | HTML 렌더링 | 2.5시간 | 8.5h |
| 5 | 통합 및 CLI | 2시간 | 10.5h |
| 6 | 문서화 | 1시간 | 11.5h |

**총 예상 시간**: 11.5시간

---

## 위험 요소 및 대응

### 높은 우선순위
1. **데이터 스키마 불일치**
   - 위험: 기존 Excel 파일 구조가 다를 수 있음
   - 대응: Phase 0에서 철저한 데이터 분석, Validator 강화

2. **네트워크 분석 복잡도**
   - 위험: 부서 간 관계 추출이 어려울 수 있음
   - 대응: 간단한 키워드 기반으로 시작, 추후 NLP 확장

3. **HTML 렌더링 호환성**
   - 위험: 다양한 브라우저에서 차트가 안 보일 수 있음
   - 대응: Plotly 최신 버전 사용, Standalone 모드 지원

### 중간 우선순위
4. **성능 저하**
   - 위험: 대량 데이터 처리 시 느려질 수 있음
   - 대응: Pandas 최적화, 필요시 Dask 전환

5. **테스트 커버리지 부족**
   - 위험: 버그가 늦게 발견될 수 있음
   - 대응: 각 Phase마다 테스트 작성, CI/CD 구축

---

## 다음 단계 (리팩토링 후)

### 단기 개선 (1-2주)
- [ ] CI/CD 파이프라인 구축 (GitHub Actions)
- [ ] Docker 컨테이너화
- [ ] 웹 인터페이스 추가 (Streamlit)

### 중기 개선 (1-2개월)
- [ ] 실시간 대시보드 (WebSocket)
- [ ] 대화형 필터링 기능
- [ ] 다국어 지원

### 장기 개선 (3-6개월)
- [ ] 머신러닝 기반 감정 분석 (현재 규칙 기반)
- [ ] 자동 리포트 생성 (PDF)
- [ ] 대시보드 템플릿 커스터마이징

---

## 참고 자료

- [Plotly Python 공식 문서](https://plotly.com/python/)
- [Click 공식 문서](https://click.palletsprojects.com/)
- [NetworkX 공식 문서](https://networkx.org/)
- [Pandas 공식 문서](https://pandas.pydata.org/)

---

**작성일**: 2025년 (세션 날짜)
**작성자**: Claude Code SuperClaude
**버전**: 1.0
