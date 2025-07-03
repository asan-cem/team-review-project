"""
대시보드 HTML 템플릿 관리 모듈
"""
import html
from typing import Dict, Any
from dashboard_config import DashboardConfig
from dashboard_styles import DashboardStyles
from dashboard_javascript import DashboardJavaScript

class DashboardTemplates:
    """대시보드 HTML 템플릿을 관리하는 클래스"""
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
        self.styles = DashboardStyles(self.config)
        self.javascript = DashboardJavaScript(self.config)
    
    def escape_html(self, text: str) -> str:
        """HTML 이스케이프 처리"""
        return html.escape(str(text))
    
    def get_html_head(self) -> str:
        """HTML head 섹션"""
        return f"""
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>서울아산병원 협업 평가 대시보드</title>
            <script src="{self.config.JS_CONFIG['plotly_cdn']}"></script>
            {self.styles.get_all_styles()}
        </head>
        """
    
    def get_header_section(self) -> str:
        """헤더 섹션"""
        return """
        <div class="header">
            <h1>📊 서울아산병원 협업 평가 대시보드</h1>
        </div>
        """
    
    def get_hospital_yearly_section(self) -> str:
        """전체 연도별 차트 섹션"""
        return """
        <div class="section">
            <h2>[전체] 연도별 문항 점수</h2>
            <div class="filters">
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="hospital-score-header" onclick="toggleExpander('hospital-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="hospital-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="hospital-score-expander">
                            <div id="hospital-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="hospital-yearly-chart-container"></div>
        </div>
        """
    
    def get_division_yearly_section(self) -> str:
        """부문별 연도별 차트 섹션"""
        return """
        <div class="section">
            <h2>[부문별] 연도별 문항 점수</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="division-chart-filter">부문 선택</label>
                    <select id="division-chart-filter"></select>
                </div>
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="division-score-header" onclick="toggleExpander('division-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="division-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="division-score-expander">
                            <div id="division-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="division-yearly-chart-container"></div>
        </div>
        """
    
    def get_comparison_section(self) -> str:
        """연도별 부문 비교 섹션"""
        return """
        <div class="section">
            <h2>연도별 부문 비교</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="comparison-year-filter">연도 선택</label>
                    <select id="comparison-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label>부문 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="comparison-division-header" onclick="toggleExpander('comparison-division-expander')">
                            <span>부문 선택 (0개 선택됨)</span>
                            <span class="expander-arrow" id="comparison-division-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="comparison-division-expander">
                            <div id="comparison-division-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="comparison-chart-container"></div>
        </div>
        """
    
    def get_team_ranking_section(self) -> str:
        """부문별 팀 점수 순위 섹션"""
        return """
        <div class="section">
            <h2>부문별 팀 점수 순위</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="team-ranking-year-filter">연도 선택</label>
                    <select id="team-ranking-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="team-ranking-division-filter">부문 선택</label>
                    <select id="team-ranking-division-filter"></select>
                </div>
            </div>
            <div id="team-ranking-chart-container"></div>
        </div>
        """
    
    def get_detailed_analysis_section(self) -> str:
        """상세 분석 섹션"""
        return """
        <div class="section">
            <h2>상세 분석 (부서/Unit별)</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="year-filter">연도 (전체)</label>
                    <select id="year-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="department-filter">피평가부서</label>
                    <select id="department-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="unit-filter">피평가Unit</label>
                    <select id="unit-filter"></select>
                </div>
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="drilldown-score-header" onclick="toggleExpander('drilldown-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="drilldown-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="drilldown-score-expander">
                            <div id="drilldown-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="metrics-container"></div>
            <div id="drilldown-chart-container" class="mt-4"></div>
            
            <h3>협업 주관식 피드백 감정 분석</h3>
            <div id="sentiment-chart-container" class="mt-4"></div>
            
            <h3>협업 후기</h3>
            <div class="filters">
                <div class="filter-group">
                    <label>감정 분류 필터</label>
                    <div class="expander-container">
                        <div class="expander-header" id="review-sentiment-header" onclick="toggleExpander('review-sentiment-expander')">
                            <span>감정 선택 (3개 선택됨)</span>
                            <span class="expander-arrow" id="review-sentiment-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="review-sentiment-expander">
                            <div id="review-sentiment-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="reviews-table-container">
                <table id="reviews-table">
                    <thead>
                        <tr>
                            <th style="width: 100px;">연도</th>
                            <th>후기 내용</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            
            <h3>감정 강도 분석</h3>
            <div id="emotion-intensity-trend-container"></div>
            
            <div id="keyword-analysis-section">
                <h3>핵심 키워드 분석</h3>
                <div class="keyword-charts-container">
                    <div id="positive-keywords-chart" class="keyword-chart"></div>
                    <div id="negative-keywords-chart" class="keyword-chart"></div>
                </div>
                <div id="keyword-reviews-container" class="mt-4"></div>
            </div>
        </div>
        """
    
    def get_yearly_comparison_section(self) -> str:
        """연도별 부서/Unit 점수 비교 섹션"""
        return """
        <div class="section">
            <h2>연도별 부서/Unit 점수 비교</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="yearly-comparison-department-filter">피평가부서</label>
                    <select id="yearly-comparison-department-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="yearly-comparison-unit-filter">피평가Unit</label>
                    <select id="yearly-comparison-unit-filter"></select>
                </div>
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="yearly-comparison-score-header" onclick="toggleExpander('yearly-comparison-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="yearly-comparison-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="yearly-comparison-score-expander">
                            <div id="yearly-comparison-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="yearly-comparison-chart-container"></div>
        </div>
        """
    
    def get_unit_comparison_section(self) -> str:
        """부서 내 Unit 비교 섹션"""
        return """
        <div class="section">
            <h2>부서 내 Unit 비교</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="unit-comparison-department-filter">피평가부서 선택</label>
                    <select id="unit-comparison-department-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="unit-comparison-year-filter">연도 선택</label>
                    <select id="unit-comparison-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="unit-comparison-score-header" onclick="toggleExpander('unit-comparison-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="unit-comparison-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="unit-comparison-score-expander">
                            <div id="unit-comparison-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="unit-comparison-chart-container"></div>
        </div>
        """
    
    def get_footer_section(self) -> str:
        """푸터 섹션"""
        return """
        <footer class="section text-center">
            <p style="color: #6c757d; margin: 0;">
                서울아산병원 협업 평가 대시보드 | 
                생성일: <span id="generation-date"></span>
            </p>
        </footer>
        <script>
            document.getElementById('generation-date').textContent = new Date().toLocaleDateString('ko-KR');
        </script>
        """
    
    def render_dashboard(self, data_json: str) -> str:
        """전체 대시보드 HTML 렌더링"""
        # JavaScript 코드에 데이터 주입
        javascript_code = self.javascript.get_all_javascript().replace("'{data_json}'", data_json)
        
        return f"""<!DOCTYPE html>
<html lang="ko">
{self.get_html_head()}
<body>
    {self.get_header_section()}
    <div class="container">
        {self.get_hospital_yearly_section()}
        {self.get_division_yearly_section()}
        {self.get_comparison_section()}
        {self.get_team_ranking_section()}
        {self.get_detailed_analysis_section()}
        {self.get_yearly_comparison_section()}
        {self.get_unit_comparison_section()}
        {self.get_footer_section()}
    </div>
    {javascript_code}
</body>
</html>"""