import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import ast

# --- 1. 데이터 로드 및 전처리 ---
def safe_literal_eval(s):
    """문자열을 안전하게 파이썬 리터럴로 변환. 실패 시 빈 리스트 반환."""
    if isinstance(s, str) and s.startswith('[') and s.endswith(']'):
        try:
            return ast.literal_eval(s)
        except (ValueError, SyntaxError):
            return []
    return []

def load_data():
    """데이터 로드 및 기본 전처리"""
    df = pd.read_excel("설문조사_전처리데이터_20250620_0731_processed.xlsx")
    df.columns = [
        'response_id', '설문연도', '평가부서', '평가부서_원본', '평가Unit', '평가부문',
        '피평가부서', '피평가부서_원본', '피평가Unit', '피평가부문',
        '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수',
        '극단값', '결측값', '협업내용', '협업내용상세', '협업후기', '정제된_텍스트', 
        '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]
    df['설문연도'] = df['설문연도'].astype(str)
    
    score_cols = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수']
    for col in score_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # '미분류' 값을 결측값으로 처리하여 점수 계산에서 제외 (데이터 감소율: 1.2%)
    df = df[(df['평가부문'] != '미분류') & (df['피평가부문'] != '미분류')]
    
    df.dropna(subset=['종합 점수'], inplace=True)
    
    for col in ['피평가부문', '피평가부서', '피평가Unit', '정제된_텍스트']:
        df[col] = df[col].fillna('N/A')
        
    # 핵심_키워드 컬럼을 문자열에서 리스트로 변환
    df['핵심_키워드'] = df['핵심_키워드'].apply(safe_literal_eval)
        
    return df

# --- 2. 개선된 HTML 생성 ---
def build_html_v2(data_json):
    """개선된 구조와 번호 체계를 적용한 대화형 HTML 생성"""
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>서울아산병원 협업 평가 대시보드 v2.0</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; color: #343a40; font-size: 16px;}}
        .container {{ max-width: 1400px; margin: auto; padding: 20px; }}
        .header {{ background: linear-gradient(90deg, #4a69bd, #6a89cc); color: white; padding: 25px; text-align: center; border-radius: 0 0 10px 10px; }}
        
        /* 자동 번호 매기기 CSS */
        .container {{ counter-reset: section-counter; }}
        .section {{ counter-reset: subsection-counter; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 30px; }}
        .section h2::before {{ counter-increment: section-counter; content: counter(section-counter) ". "; color: #4a69bd; font-weight: bold; }}
        .section h3::before {{ counter-increment: subsection-counter; content: counter(section-counter) "." counter(subsection-counter) " "; color: #6a89cc; font-weight: bold; }}
        
        h1, h2, h3 {{ margin: 0; padding: 0; }}
        h2 {{ color: #4a69bd; border-bottom: 3px solid #6a89cc; padding-bottom: 10px; margin-top: 20px; margin-bottom: 20px; }}
        h3 {{ color: #555; margin-top: 30px; margin-bottom: 15px;}}
        
        /* 파트 구분 스타일 */
        .part-divider {{ background: linear-gradient(90deg, #e9ecef, #6c757d, #e9ecef); height: 3px; margin: 40px 0; border-radius: 2px; }}
        .part-title {{ text-align: center; color: #6c757d; font-size: 1.2em; font-weight: bold; margin: 30px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 5px solid #6a89cc; }}
        
        .filters, .trend-filters {{ display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-end; margin-bottom: 20px;}}
        .filter-group {{ display: flex; flex-direction: column; }}
        .filter-group label {{ margin-bottom: 5px; font-weight: bold; font-size: 0.9em; }}
        .filter-group select, .filter-group input {{ padding: 8px; border-radius: 5px; border: 1px solid #ced4da; min-width: 200px; }}
        .expander-container {{ border: 1px solid #ced4da; border-radius: 5px; background-color: white; min-width: 200px; max-width: 280px; position: relative; }}
        .expander-header {{ padding: 6px 8px; background-color: #f8f9fa; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-radius: 5px; user-select: none; font-size: 13px; }}
        .expander-header:hover {{ background-color: #e9ecef; }}
        .expander-arrow {{ transition: transform 0.3s ease; font-size: 11px; }}
        .expander-arrow.expanded {{ transform: rotate(180deg); }}
        .expander-content {{ padding: 4px; display: none; max-height: 200px; overflow-y: auto; position: absolute; top: 100%; left: 0; width: 100%; background-color: white; border: 1px solid #ced4da; border-top: none; border-radius: 0 0 5px 5px; z-index: 1000; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .expander-content.expanded {{ display: block; }}
        .checkbox-item {{ display: flex; align-items: center; padding: 2px 0; height: auto; min-height: unset; }}
        .checkbox-item input[type="checkbox"] {{ width: 16px; height: 16px; min-width: 16px; min-height: 16px; margin-right: 6px; box-sizing: border-box; }}
        .checkbox-item:hover {{ background-color: #f8f9fa; }}
        .checkbox-item label {{ cursor: pointer; font-weight: normal; font-size: 13px; line-height: 1.1; margin: 0; }}
        #metrics-container {{ display: flex; gap: 30px; margin-top: 20px; text-align: center; justify-content: center; }}
        .metric {{ background-color: #e9ecef; padding: 15px; border-radius: 8px; flex-grow: 1; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #4a69bd; }}
        .metric-label {{ font-size: 0.9em; color: #6c757d; }}
        #reviews-table-container, #keyword-reviews-table-container {{ max-height: 400px; overflow-y: auto; margin-top: 20px; border: 1px solid #dee2e6; border-radius: 5px; }}
        #reviews-table, #keyword-reviews-table {{ width: 100%; border-collapse: collapse; }}
        #reviews-table th, #reviews-table td, #keyword-reviews-table th, #keyword-reviews-table td {{ padding: 12px; border-bottom: 1px solid #dee2e6; text-align: left; }}
        #reviews-table th, #keyword-reviews-table th {{ background-color: #f8f9fa; position: sticky; top: 0; }}
        #reviews-table tr:last-child td, #keyword-reviews-table tr:last-child td {{ border-bottom: none; }}
        .keyword-charts-container {{ display: flex; gap: 20px; }}
        .keyword-chart {{ flex: 1; }}
        
        /* 차트 컨테이너 스타일 개선 */
        .chart-container {{ margin: 20px 0; }}
        .subsection {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 서울아산병원 협업 평가 대시보드 v2.0</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">개선된 구조로 더 직관적인 데이터 탐색</p>
    </div>
    <div class="container">
        
        <!-- Part 1: 전체 현황 (Overview) -->
        <div class="part-title">📈 Part 1: 전체 현황 (Overview)</div>
        
        <div class="section">
            <h2>[전체] 연도별 문항 점수</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">병원 전체의 기본 트렌드를 파악합니다.</p>
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
            <div id="hospital-yearly-chart-container" class="chart-container"></div>
        </div>

        <div class="section">
            <h2>[부문별] 연도별 문항 점수</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">부문별 성과 트렌드를 분석합니다.</p>
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
            <div id="division-yearly-chart-container" class="chart-container"></div>
        </div>

        <div class="section">
            <h2>연도별 부문 비교</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">특정 연도의 부문간 상대적 성과를 비교합니다.</p>
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
            <div id="comparison-chart-container" class="chart-container"></div>
        </div>

        <div class="part-divider"></div>
        
        <!-- Part 2: 성과 분석 (Performance) -->
        <div class="part-title">🏆 Part 2: 성과 분석 (Performance)</div>
        
        <div class="section">
            <h2>부문별 팀 점수 순위</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">우수 및 개선이 필요한 부서를 식별합니다.</p>
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
            <div id="team-ranking-chart-container" class="chart-container"></div>
        </div>

        <div class="part-divider"></div>
        
        <!-- Part 3: 상세 분석 (Deep Dive) -->
        <div class="part-title">🔍 Part 3: 상세 분석 (Deep Dive)</div>
        
        <div class="section">
            <h2>부서/Unit 상세 분석</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">특정 부서나 Unit의 상세한 성과와 피드백을 분석합니다.</p>
            
            <!-- 공통 필터 -->
            <div class="filters">
                <div class="filter-group"><label for="year-filter">연도 (전체)</label><select id="year-filter"></select></div>
                <div class="filter-group"><label for="department-filter">부서</label><select id="department-filter"></select></div>
                <div class="filter-group"><label for="unit-filter">Unit</label><select id="unit-filter"></select></div>
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
            
            <!-- 5.1 기본 지표 및 점수 트렌드 -->
            <div class="subsection">
                <h3>기본 지표 및 점수 트렌드</h3>
                <div id="metrics-container"></div>
                <div id="drilldown-chart-container" class="chart-container"></div>
                <div id="yearly-comparison-chart-container" class="chart-container"></div>
            </div>
            
            <!-- 5.2 감정 분석 -->
            <div class="subsection">
                <h3>협업 주관식 피드백 감정 분석</h3>
                <div id="sentiment-chart-container" class="chart-container"></div>
            </div>
            
            <!-- 5.3 감정 강도 -->
            <div class="subsection">
                <h3>감정 강도 분석</h3>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #6a89cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 이 차트는 무엇인가요?</strong><br>
                        협업 후기의 감정이 얼마나 강한지를 1점(매우 약함)부터 10점(매우 강함)까지 수치로 나타낸 것입니다.<br><br>
                        <strong>💡 해석 방법:</strong><br>
                        • <span style="color: #28a745;"><strong>높은 점수(7-10점)</strong></span>: 매우 만족하거나 매우 불만족한 강한 감정<br>
                        • <span style="color: #ffc107;"><strong>중간 점수(4-6점)</strong></span>: 보통 수준의 감정<br>
                        • <span style="color: #6c757d;"><strong>낮은 점수(1-3점)</strong></span>: 담담하고 객관적인 평가<br><br>
                        <em>예시: "정말 훌륭한 협업이었다"(9점) vs "괜찮은 협업이었다"(5점)</em>
                    </p>
                </div>
                <div id="emotion-intensity-trend-container" class="chart-container"></div>
            </div>

            <!-- 5.4 키워드 분석 -->
            <div class="subsection">
                <h3>핵심 키워드 분석</h3>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #6a89cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 이 차트는 무엇인가요?</strong><br>
                        협업 후기에서 자주 언급되는 단어들을 긍정/부정으로 분류하여 상위 10개를 보여줍니다.<br><br>
                        <strong>💡 활용 방법:</strong><br>
                        • <span style="color: #28a745;"><strong>긍정 키워드</strong></span>: 어떤 부분에서 만족하고 있는지 파악<br>
                        • <span style="color: #dc3545;"><strong>부정 키워드</strong></span>: 개선이 필요한 부분을 빠르게 확인<br>
                        • <strong>막대 클릭</strong>: 해당 키워드가 포함된 실제 후기 내용을 확인할 수 있습니다<br><br>
                        <em>예시: "신속한" 키워드 클릭 → "신속한 응답으로 업무가 원활했다" 등의 후기 표시</em>
                    </p>
                </div>
                <div class="keyword-charts-container">
                    <div id="positive-keywords-chart" class="keyword-chart"></div>
                    <div id="negative-keywords-chart" class="keyword-chart"></div>
                </div>
                <div id="keyword-reviews-container"></div>
            </div>
            
            <!-- 5.5 협업 후기 -->
            <div class="subsection">
                <h3>협업 후기</h3>
                <div class="filters">
                    <div class="filter-group">
                        <label>감정 분류 필터</label>
                        <div class="expander-container">
                            <div class="expander-header" id="review-sentiment-header" onclick="toggleExpander('review-sentiment-expander')">
                                <span>감정 선택 (4개 선택됨)</span>
                                <span class="expander-arrow" id="review-sentiment-arrow">▼</span>
                            </div>
                            <div class="expander-content" id="review-sentiment-expander">
                                <div id="review-sentiment-filter"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div id="reviews-table-container"><table id="reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody></tbody></table></div>
            </div>
        </div>

        <div class="part-divider"></div>
        
        <!-- Part 4: 협업 네트워크 분석 (Collaboration Network Analysis) -->
        <div class="part-title">🔗 Part 4: 협업 네트워크 분석 (Collaboration Network Analysis)</div>
        
        <div class="section">
            <h2>협업 네트워크 분석</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">🔍 부서/Unit간 협업 관계와 중요성을 종합적으로 분석합니다.</p>
            
            <!-- 공통 필터 -->
            <div class="filters">
                <div class="filter-group">
                    <label for="network-division-filter">연도 (전체)</label>
                    <select id="network-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="network-division-filter">부문</label>
                    <select id="network-division-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="network-department-filter">부서</label>
                    <select id="network-department-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="network-unit-filter">Unit</label>
                    <select id="network-unit-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="min-collaboration-filter">최소 협업 횟수</label>
                    <select id="min-collaboration-filter">
                        <option value="5">5회 이상</option>
                        <option value="10" selected>10회 이상</option>
                        <option value="30">30회 이상</option>
                    </select>
                </div>
            </div>
            
            <!-- 2.1 협업 빈도 TOP 파트너 -->
            <div class="subsection">
                <h3>협업 빈도 TOP 파트너</h3>
                <div style="background: #e8f4fd; padding: 15px; border-left: 4px solid #0066cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 이 차트는 무엇인가요?</strong><br>
                        선택한 부서/Unit과 가장 많이 협업하는 상위 10개 파트너를 보여줍니다.<br><br>
                        <strong>💡 활용 방법:</strong><br>
                        • <span style="color: #28a745;"><strong>주요 협업 식별</strong></span>: 업무 연계가 가장 많은 부서 파악<br>
                        • <span style="color: #007bff;"><strong>네트워크 중심성</strong></span>: 협업 허브 역할 부서 확인<br>
                        • <span style="color: #6c757d;"><strong>업무 의존도</strong></span>: 업무 연계가 높은 관계 분석
                    </p>
                </div>
                <div id="collaboration-frequency-chart-container" class="chart-container"></div>
            </div>

            <!-- 2.2 협업 관계 현황 -->
            <div class="subsection">
                <h3>협업 관계 현황</h3>
                <div style="background: #e8f4fd; padding: 15px; border-left: 4px solid #0066cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 관계 분류 기준:</strong><br>
                        • <span style="color: #28a745;"><strong>우수 (75점 이상)</strong></span>: 매우 공정적인 협업 관계<br>
                        • <span style="color: #ffc107;"><strong>양호 (60-74점)</strong></span>: 안정적인 협업 관계<br>
                        • <span style="color: #fd7e14;"><strong>주의 (50-59점)</strong></span>: 개선이 필요한 관계<br>
                        • <span style="color: #dc3545;"><strong>문제 (50점 미만)</strong></span>: 시급한 개선이 필요한 관계
                    </p>
                </div>
                <div id="collaboration-status-chart-container" class="chart-container"></div>
            </div>

            <!-- 2.3 협업 관계 변화 트렌드 -->
            <div class="subsection">
                <h3>협업 관계 변화 트렌드</h3>
                <div style="background: #e8f4fd; padding: 15px; border-left: 4px solid #0066cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📈 개선도 파악 기준:</strong><br>
                        • <span style="color: #28a745;"><strong>연평균 +3점 이상 증가</strong></span>: 눈에 띄는 개선<br>
                        • <span style="color: #ffc107;"><strong>연평균 +2점 이상 증가</strong></span>: 안정적 개선<br>
                        • <span style="color: #6c757d;"><strong>연평균 -3점 이상 감소</strong></span>: 악화 추세<br>
                        • <span style="color: #dc3545;"><strong>연평균 -5점 이상 감소</strong></span>: 악화 주의 감수
                    </p>
                </div>
                <div id="collaboration-trend-chart-container" class="chart-container"></div>
            </div>

            <!-- 2.4 협업 후기 -->
            <div class="subsection">
                <h3>협업 후기</h3>
                <div style="background: #e8f4fd; padding: 15px; border-left: 4px solid #0066cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>🔍 텍터링된 협업 후기:</strong><br>
                        선택한 부서/Unit과 관련된 실제 협업 후기를 확인할 수 있습니다.<br>
                        감정 분류별로 필터링하여 구체적인 피드백 내용을 파악하세요.
                    </p>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <label>감정 분류 필터</label>
                        <select id="network-sentiment-filter">
                            <option value="전체">전체 (긍정+부정+중립)</option>
                            <option value="긍정">긍정</option>
                            <option value="부정">부정</option>
                            <option value="중립">중립</option>
                        </select>
                    </div>
                </div>
                <div id="network-reviews-table-container">
                    <table id="network-reviews-table">
                        <thead>
                            <tr>
                                <th style="width: 80px;">연도</th>
                                <th style="width: 120px;">협업 파트너</th>
                                <th>후기 내용</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>부서 내 Unit 비교</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">같은 부서 내 Unit간 비교분석을 수행합니다.</p>
            <div class="filters">
                <div class="filter-group">
                    <label for="unit-comparison-department-filter">부서 선택</label>
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
            <div id="unit-comparison-chart-container" class="chart-container"></div>
        </div>
    </div>
    <script>
        const rawData = {data_json};
        const scoreCols = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수'];
        const allYears = [...new Set(rawData.map(item => item['설문연도']))].sort();
        const allDivisions = [...new Set(rawData.map(item => item['피평가부문']))].filter(d => d && d !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
        const layoutFont = {{ size: 14 }};

        const departmentUnitMap = rawData.reduce((acc, item) => {{
            const dept = item['피평가부서'];
            const unit = item['피평가Unit'];
            if (dept && dept !== 'N/A' && unit && unit !== 'N/A') {{
                if (!acc[dept]) {{ acc[dept] = new Set(); }}
                acc[dept].add(unit);
            }}
            return acc;
        }}, {{}});
        for (const dept in departmentUnitMap) {{
            departmentUnitMap[dept] = [...departmentUnitMap[dept]].sort((a, b) => String(a).localeCompare(String(b), 'ko'));
        }}

        function populateFilters() {{
            const filters = {{ 'year-filter': '설문연도', 'department-filter': '피평가부서', 'unit-filter': '피평가Unit' }};
            for (const [elementId, dataCol] of Object.entries(filters)) {{
                const select = document.getElementById(elementId);
                const values = [...new Set(rawData.map(item => item[dataCol]))].sort((a, b) => String(a).localeCompare(String(b), 'ko'));
                const options = ['전체', ...values];
                select.innerHTML = options.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
                select.addEventListener('change', updateDashboard);
            }}
            document.getElementById('department-filter').addEventListener('change', updateUnitFilter);
        }}

        function updateUnitFilter() {{
            const deptSelect = document.getElementById('department-filter');
            const unitSelect = document.getElementById('unit-filter');
            const selectedDept = deptSelect.value;

            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept])
                ? allUnits
                : departmentUnitMap[selectedDept];

            unitSelect.innerHTML = ['전체', ...units].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            unitSelect.value = '전체';
        }}

        function setupDivisionChart() {{
            const select = document.getElementById('division-chart-filter');
            select.innerHTML = allDivisions.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            select.addEventListener('change', updateDivisionYearlyChart);
            createCheckboxFilter('division-score-filter', scoreCols, 'division-score', updateDivisionYearlyChart);
        }}
        
        function setupComparisonChart() {{
            const yearSelect = document.getElementById('comparison-year-filter');
            yearSelect.innerHTML = allYears.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1]; // Default to last year
            yearSelect.addEventListener('change', updateYearlyDivisionComparisonChart);
            createCheckboxFilter('comparison-division-filter', allDivisions, 'comparison-division', updateYearlyDivisionComparisonChart, true);
        }}

        function getFilteredData() {{
            let filteredData = [...rawData];
            const filters = {{ 'year-filter': '설문연도', 'department-filter': '피평가부서', 'unit-filter': '피평가Unit' }};
            for (const [elementId, dataCol] of Object.entries(filters)) {{
                const selectedValue = document.getElementById(elementId).value;
                if (selectedValue !== '전체') {{ filteredData = filteredData.filter(item => item[dataCol] == selectedValue); }}
            }}
            return filteredData;
        }}

        function updateDashboard() {{
            const filteredData = getFilteredData();
            updateMetrics(filteredData);
            updateDrilldownChart(filteredData);
            updateSentimentChart(filteredData);
            updateReviewsTable(filteredData);
            updateEmotionIntensityTrend();
            updateKeywordAnalysis(filteredData);
            updateYearlyComparisonChart();
        }}
        
        function calculateAverages(data) {{
            const averages = {{}};
            scoreCols.forEach(col => {{
                const total = data.reduce((sum, item) => sum + (item[col] || 0), 0);
                averages[col] = data.length > 0 ? (total / data.length) : 0;
            }});
            return averages;
        }}

        function updateMetrics(data) {{
            const container = document.getElementById('metrics-container');
            if (data.length === 0) {{ container.innerHTML = "<p style='text-align:center;'>선택된 조건에 해당하는 데이터가 없습니다.</p>"; return; }}
            const averages = calculateAverages(data);
            container.innerHTML = `<div class="metric"><div class="metric-value">${{data.length}}</div><div class="metric-label">응답 수</div></div><div class="metric"><div class="metric-value">${{averages['종합 점수'].toFixed(1)}}</div><div class="metric-label">종합 점수</div></div>`;
        }}
        
        function updateDrilldownChart(data) {{
            const container = document.getElementById('drilldown-chart-container');
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);

            if (data.length === 0 || selectedScores.length === 0) {{ 
                const message = data.length > 0 ? '표시할 문항을 선택해주세요.' : '';
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: message, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const averages = calculateAverages(data);
            const chartData = [{{ x: selectedScores, y: selectedScores.map(col => averages[col].toFixed(1)), type: 'bar', text: selectedScores.map(col => averages[col].toFixed(1)), textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: '#6a89cc' }}, hovertemplate: '%{{x}}: %{{y}}<extra></extra>' }}];
            const selectedYear = document.getElementById('year-filter').value;
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            
            // 제목 생성
            let titleParts = [];
            if (selectedDept !== '전체') {{ titleParts.push(selectedDept); }}
            if (selectedUnit !== '전체') {{ titleParts.push(selectedUnit); }}
            
            const titlePrefix = titleParts.length > 0 ? titleParts.join(' > ') : '부서, Unit';
            const yearSuffix = selectedYear === '전체' ? ' (전체 연도)' : ` (${{selectedYear}})`;
            const title = `<b>${{titlePrefix}} 문항 점수${{yearSuffix}}</b>`;
            const layout = {{ title: title, yaxis: {{ title: '점수', range: [0, 100] }}, font: layoutFont, hovermode: 'closest' }};
            Plotly.react(container, chartData, layout);
        }}
        
        function updateHospitalYearlyChart() {{
            const container = document.getElementById('hospital-yearly-chart-container');
            const selectedScores = Array.from(document.querySelectorAll('input[name="hospital-score"]:checked')).map(cb => cb.value);
            
            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const years = allYears;
            const traces = [];

            selectedScores.forEach(col => {{
                const y_values = years.map(year => calculateAverages(rawData.filter(d => d['설문연도'] === year))[col].toFixed(1));
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            
            const yearly_counts = years.map(year => rawData.filter(d => d['설문연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}명`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}명<br>연도: %{{x}}<extra></extra>' }});

            const layout = {{
                title: '<b>[전체] 연도별 문항 점수</b>',
                barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont,
                hovermode: 'closest'
            }};
            Plotly.react(container, traces, layout);
        }}

        function updateDivisionYearlyChart() {{
            const container = document.getElementById('division-yearly-chart-container');
            const selectedDivision = document.getElementById('division-chart-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="division-score"]:checked')).map(cb => cb.value);

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const divisionData = rawData.filter(item => item['피평가부문'] === selectedDivision);
            const years = [...new Set(divisionData.map(item => item['설문연도']))].sort();
            const traces = [];

            selectedScores.forEach(col => {{
                const y_values = years.map(year => calculateAverages(divisionData.filter(d => d['설문연도'] === year))[col].toFixed(1));
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            
            const yearly_counts = years.map(year => divisionData.filter(d => d['설문연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}명`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}명<br>연도: %{{x}}<extra></extra>' }});

            const layout = {{
                title: `<b>[${{selectedDivision}}] 연도별 문항 점수</b>`,
                barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont,
                hovermode: 'closest'
            }};
            Plotly.react(container, traces, layout);
        }}

        function updateYearlyDivisionComparisonChart() {{
            const container = document.getElementById('comparison-chart-container');
            const selectedYear = document.getElementById('comparison-year-filter').value;
            const selectedDivisions = Array.from(document.querySelectorAll('input[name="comparison-division"]:checked')).map(cb => cb.value);

            let yearData = rawData.filter(item => item['설문연도'] === selectedYear);

            if (selectedDivisions.length > 0) {{
                yearData = yearData.filter(item => selectedDivisions.includes(item['피평가부문']));
            }} else {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '비교할 부문을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const divisionScores = {{}};
            yearData.forEach(item => {{
                const division = item['피평가부문'];
                if (division === 'N/A') return;
                if (!divisionScores[division]) {{ divisionScores[division] = {{ sum: 0, count: 0 }}; }}
                divisionScores[division].sum += item['종합 점수'] || 0;
                divisionScores[division].count++;
            }});

            const divisions = Object.keys(divisionScores).sort((a,b) => a.localeCompare(b, 'ko'));
            const avgScores = divisions.map(div => (divisionScores[div].sum / divisionScores[div].count).toFixed(1));

            const trace = [{{ x: divisions, y: avgScores, type: 'bar', text: avgScores, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{x}}: %{{y}}<extra></extra>' }}];
            const layout = {{
                title: `<b>${{selectedYear}} 부문별 점수 비교</b>`,
                yaxis: {{ title: '점수', range: [0, 100] }},
                font: layoutFont,
                height: 500,
                barmode: 'group',
                hovermode: 'closest'
            }};
            Plotly.react(container, trace, layout);
        }}

        function updateSentimentChart(data) {{
            const container = document.getElementById('sentiment-chart-container');
            
            if (data.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 감정 분류가 있는 데이터만 필터링
            const validSentimentData = data.filter(item => {{
                const sentiment = item['감정_분류'];
                return sentiment && sentiment !== 'N/A' && sentiment !== '알 수 없음';
            }});

            if (validSentimentData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '감정 분류 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 감정 분류별 집계 (알 수 없음 제외)
            const sentimentCounts = {{}};
            validSentimentData.forEach(item => {{
                const sentiment = item['감정_분류'];
                sentimentCounts[sentiment] = (sentimentCounts[sentiment] || 0) + 1;
            }});

            // 원하는 순서로 감정 분류 고정
            const desiredOrder = ['긍정', '부정', '중립'];
            const sentiments = desiredOrder.filter(sentiment => sentimentCounts[sentiment] > 0);
            const counts = sentiments.map(sentiment => sentimentCounts[sentiment]);
            const total = counts.reduce((sum, count) => sum + count, 0);
            const percentages = counts.map(count => ((count / total) * 100).toFixed(1));

            // 색상 매핑
            const colorMap = {{
                '긍정': '#2E8B57',
                '부정': '#DC143C', 
                '중립': '#4682B4',
                '알 수 없음': '#808080'
            }};
            const colors = sentiments.map(sentiment => colorMap[sentiment] || '#808080');

            const trace = {{
                x: sentiments,
                y: counts,
                type: 'bar',
                text: counts.map((count, idx) => `${{count}}건 (${{percentages[idx]}}%)`),
                textposition: 'outside',
                textfont: {{ size: 12 }},
                marker: {{ color: colors }},
                hovertemplate: '%{{x}}: %{{y}}건 (%{{text}})<extra></extra>'
            }};

            const layout = {{
                title: '<b>감정 분류별 응답 분포</b>',
                height: 400,
                xaxis: {{ title: '감정 분류' }},
                yaxis: {{ title: '응답 수', rangemode: 'tozero', range: [0, Math.max(...counts) * 1.15] }},
                font: layoutFont,
                hovermode: 'closest',
                showlegend: false
            }};

            Plotly.react(container, [trace], layout);
        }}

        function updateEmotionIntensityTrend() {{
            const container = document.getElementById('emotion-intensity-trend-container');
            
            // 상세 분석 섹션의 부서/Unit 필터만 사용 (연도는 무시하여 전체 트렌드 표시)
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            
            // 감정 강도 데이터가 있는 항목만 필터링 (0도 유효한 값으로 처리)
            let targetData = rawData.filter(item => {{
                const intensity = item['감정_강도_점수'];
                return intensity !== null && intensity !== undefined && intensity !== '' && !isNaN(parseFloat(intensity));
            }});
            
            // 부서 필터 적용
            if (selectedDept !== '전체') {{
                targetData = targetData.filter(item => item['피평가부서'] === selectedDept);
            }}
            
            // Unit 필터 적용
            if (selectedUnit !== '전체') {{
                targetData = targetData.filter(item => item['피평가Unit'] === selectedUnit);
            }}
            
            if (targetData.length === 0) {{
                let message = '감정 강도 데이터가 없습니다.';
                if (selectedDept !== '전체' || selectedUnit !== '전체') {{
                    message = '선택된 부서/Unit에 해당하는 감정 강도 데이터가 없습니다.';
                }}
                
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: message, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const yearlyData = {{}};
            targetData.forEach(item => {{
                const year = item['설문연도'];
                const intensity = parseFloat(item['감정_강도_점수']);
                const sentiment = item['감정_분류'] || '알 수 없음';
                
                if (!yearlyData[year]) {{
                    yearlyData[year] = {{
                        intensities: [],
                        sentiments: {{ '긍정': [], '부정': [], '중립': [], '알 수 없음': [] }}
                    }};
                }}
                
                yearlyData[year].intensities.push(intensity);
                if (yearlyData[year].sentiments[sentiment]) {{
                    yearlyData[year].sentiments[sentiment].push(intensity);
                }}
            }});
            
            const years = Object.keys(yearlyData).sort();
            
            if (years.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '표시할 연도별 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const traces = [];
            
            const overallAvg = years.map(year => {{
                const intensities = yearlyData[year].intensities;
                return (intensities.reduce((sum, val) => sum + val, 0) / intensities.length).toFixed(2);
            }});
            
            traces.push({{
                x: years,
                y: overallAvg,
                type: 'scatter',
                mode: 'lines+markers',
                name: '전체 평균',
                line: {{ color: '#1f77b4', width: 3 }},
                marker: {{ size: 8 }},
                hovertemplate: '연도: %{{x}}<br>전체 평균 강도: %{{y}}<extra></extra>'
            }});
            
            const sentimentColors = {{ '긍정': '#28a745', '부정': '#dc3545', '중립': '#6c757d' }};
            
            Object.entries(sentimentColors).forEach(([sentiment, color]) => {{
                const sentimentAvg = years.map(year => {{
                    const sentimentIntensities = yearlyData[year].sentiments[sentiment];
                    if (sentimentIntensities.length === 0) return null;
                    return (sentimentIntensities.reduce((sum, val) => sum + val, 0) / sentimentIntensities.length).toFixed(2);
                }});
                
                if (sentimentAvg.some(val => val !== null)) {{
                    traces.push({{
                        x: years,
                        y: sentimentAvg,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: `${{sentiment}} 평균`,
                        line: {{ color: color, width: 2, dash: 'dot' }},
                        marker: {{ size: 6 }},
                        connectgaps: false,
                        hovertemplate: `연도: %{{x}}<br>${{sentiment}} 평균 강도: %{{y}}<extra></extra>`
                    }});
                }}
            }});
            
            let titleParts = [];
            if (selectedDept !== '전체') {{ titleParts.push(selectedDept); }}
            if (selectedUnit !== '전체') {{ titleParts.push(selectedUnit); }}
            
            const titlePrefix = titleParts.length > 0 ? titleParts.join(' > ') : '전체';
            const title = `<b>${{titlePrefix}} 연도별 감정 강도 트렌드</b>`;
            
            const layout = {{
                title: title,
                height: 400,
                xaxis: {{ title: '연도', type: 'category' }},
                yaxis: {{ title: '평균 감정 강도', range: [1, 10] }},
                font: layoutFont,
                hovermode: 'x unified',
                showlegend: true,
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }}
            }};
            
            Plotly.react(container, traces, layout);
        }}

        function updateReviewsTable(data = null) {{
            const tbody = document.querySelector("#reviews-table tbody");
            
            if (data === null) {{ data = getFilteredData(); }}
            
            const selectedSentiments = Array.from(document.querySelectorAll('input[name="review-sentiment"]:checked')).map(cb => cb.value);
            
            let filteredData = data;
            if (selectedSentiments.length > 0 && !selectedSentiments.includes('전체')) {{
                filteredData = data.filter(item => selectedSentiments.includes(item['감정_분류']));
            }}
            
            const reviews = filteredData.map(item => ({{ 
                year: item['설문연도'], 
                review: item['정제된_텍스트'],
                sentiment: item['감정_분류'] || '알 수 없음'
            }})).filter(r => r.review && r.review !== 'N/A')
            .sort((a, b) => b.year - a.year);
            
            tbody.innerHTML = (reviews.length > 0) ? 
                reviews.map(r => `<tr><td>${{r.year}}</td><td>${{r.review}} <span style="color: #666; font-size: 0.9em;">[${{r.sentiment}}]</span></td></tr>`).join('') : 
                '<tr><td colspan="2">해당 조건의 후기가 없습니다.</td></tr>';
        }}

        function updateKeywordAnalysis(data) {{
            const positiveCounts = {{}};
            const negativeCounts = {{}};

            data.forEach(item => {{
                const keywords = item['핵심_키워드'];
                if (keywords && Array.isArray(keywords) && keywords.length > 0) {{
                    const sentiment = item['감정_분류'];
                    keywords.forEach(kw => {{
                        if (sentiment === '긍정') {{
                            positiveCounts[kw] = (positiveCounts[kw] || 0) + 1;
                        }} else if (sentiment === '부정') {{
                            negativeCounts[kw] = (negativeCounts[kw] || 0) + 1;
                        }}
                    }});
                }}
            }});

            const topPositive = Object.entries(positiveCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
            const topNegative = Object.entries(negativeCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);

            const posChartContainer = document.getElementById('positive-keywords-chart');
            const negChartContainer = document.getElementById('negative-keywords-chart');

            plotKeywordChart(posChartContainer, '긍정 키워드 Top 10', topPositive, '긍정');
            plotKeywordChart(negChartContainer, '부정 키워드 Top 10', topNegative, '부정');
            
            displayKeywordReviews(null, null, true);
        }}

        function plotKeywordChart(container, title, data, sentiment) {{
            if (data.length === 0) {{
                Plotly.react(container, [], {{ title: `<b>${{title}}</b>`, height: 400, annotations: [{{ text: '데이터 없음', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false }}] }});
                return;
            }}

            const trace = {{
                y: data.map(d => d[0]).reverse(),
                x: data.map(d => d[1]).reverse(),
                type: 'bar',
                orientation: 'h',
                marker: {{ color: sentiment === '긍정' ? '#28a745' : '#dc3545' }},
                hovertemplate: '언급 횟수: %{{x}}<extra></extra>'
            }};

            const layout = {{
                title: `<b>${{title}}</b>`,
                height: 400,
                margin: {{ l: 150 }},
                xaxis: {{ title: '언급 횟수' }},
                yaxis: {{ automargin: true }}
            }};

            Plotly.react(container, [trace], layout);
            container.removeAllListeners('plotly_click');
            container.on('plotly_click', (eventData) => {{
                const keyword = eventData.points[0].y;
                displayKeywordReviews(keyword, sentiment);
            }});
        }}

        function displayKeywordReviews(keyword, sentiment, isInitial = false) {{
            const container = document.getElementById('keyword-reviews-container');
            
            if (isInitial) {{
                container.innerHTML = `<h4>관련 리뷰</h4><p>위 그래프의 막대를 클릭하면 관련 리뷰를 확인할 수 있습니다.</p><div id="keyword-reviews-table-container"><table id="keyword-reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody><tr><td colspan="2" style="text-align:center;"></td></tr></tbody></table></div>`;
                return;
            }}

            const filteredData = getFilteredData();
            
            const reviews = filteredData.filter(item => 
                item['감정_분류'] === sentiment && 
                Array.isArray(item['핵심_키워드']) && 
                item['핵심_키워드'].includes(keyword)
            );

            let content = `<h4>'${{keyword}}' (${{sentiment}}) 관련 리뷰 (${{reviews.length}}건)</h4>`;
            if (reviews.length > 0) {{
                content += `<div id="keyword-reviews-table-container"><table id="keyword-reviews-table">
                    <thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody>`;
                content += reviews.map(r => `<tr><td>${{r['설문연도']}}</td><td>${{r['정제된_텍스트']}}</td></tr>`).join('');
                content += `</tbody></table></div>`;
            }} else {{
                content += '<p>관련 리뷰가 없습니다.</p>';
            }}
            container.innerHTML = content;
        }}

        function setupTeamRankingChart() {{
            const yearSelect = document.getElementById('team-ranking-year-filter');
            const divisionSelect = document.getElementById('team-ranking-division-filter');
            
            yearSelect.innerHTML = allYears.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1];
            
            divisionSelect.innerHTML = ['부문을 선택하세요', ...allDivisions].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            yearSelect.addEventListener('change', updateTeamRankingChart);
            divisionSelect.addEventListener('change', updateTeamRankingChart);
        }}

        function updateTeamRankingChart() {{
            const container = document.getElementById('team-ranking-chart-container');
            const selectedYear = document.getElementById('team-ranking-year-filter').value;
            const selectedDivision = document.getElementById('team-ranking-division-filter').value;

            let yearData = rawData.filter(item => item['설문연도'] === selectedYear);

            if (selectedDivision !== '부문을 선택하세요') {{
                yearData = yearData.filter(item => item['피평가부문'] === selectedDivision);
            }}

            const teamScores = {{}};
            yearData.forEach(item => {{
                const department = item['피평가부서'];
                const division = item['피평가부문'];
                const score = item['종합 점수'];
                
                if (department && department !== 'N/A' && division && division !== 'N/A' && score != null) {{
                    if (!teamScores[department]) {{ teamScores[department] = {{ scores: [], division: division, unit: item['피평가Unit'] }}; }}
                    teamScores[department].scores.push(score);
                }}
            }});

            const teamRankings = Object.entries(teamScores)
                .map(([department, data]) => ({{
                    department: department,
                    division: data.division,
                    unit: data.unit,
                    avgScore: (data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length).toFixed(1),
                    count: data.scores.length
                }}))
                .sort((a, b) => parseFloat(b.avgScore) - parseFloat(a.avgScore));

            if (teamRankings.length === 0) {{
                Plotly.react(container, [], {{
                    height: 600,
                    annotations: [{{ text: '선택된 조건에 해당하는 부서 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const divisionColors = {{ '진료부문': '#1f77b4', '간호부문': '#ff7f0e', '관리부문': '#2ca02c', '의료지원부문': '#d62728', '기타': '#9467bd' }};
            const departments = teamRankings.map(item => item.department);
            const scores = teamRankings.map(item => parseFloat(item.avgScore));
            const colors = teamRankings.map(item => divisionColors[item.division] || '#17becf');
            const hoverTexts = teamRankings.map(item => `부서: ${{item.department}}<br>부문: ${{item.division}}<br>점수: ${{item.avgScore}}<br>응답수: ${{item.count}}명`);

            const allYearData = rawData.filter(item => item['설문연도'] === selectedYear);
            const yearlyOverallAverage = allYearData.length > 0 ? (allYearData.reduce((sum, item) => sum + (item['종합 점수'] || 0), 0) / allYearData.length).toFixed(1) : 0;

            const trace = {{
                x: departments, y: scores, type: 'bar', text: scores.map(score => score.toString()),
                textposition: 'outside', textfont: {{ size: 12 }}, marker: {{ color: colors }},
                hovertemplate: '%{{hovertext}}<extra></extra>', hovertext: hoverTexts
            }};

            const avgLine = {{
                x: [departments[0], departments[departments.length - 1]], y: [yearlyOverallAverage, yearlyOverallAverage],
                type: 'scatter', mode: 'lines', line: {{ color: 'red', width: 2, dash: 'dash' }},
                name: `${{selectedYear}} 전체 평균: ${{yearlyOverallAverage}}`, hoverinfo: 'skip'
            }};

            const layout = {{
                title: `<b>${{selectedYear}} 부문별 부서 점수 순위 (점수 높은 순)</b>`, height: 600,
                xaxis: {{ title: '부서', tickangle: -45, automargin: true }},
                yaxis: {{ title: '점수', range: [Math.min(...scores) - 5, Math.max(...scores) + 5] }},
                font: layoutFont, hovermode: 'closest', showlegend: false,
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                annotations: [{{
                    text: `${{selectedYear}} 전체 평균: ${{yearlyOverallAverage}}점`, xref: 'paper', yref: 'y',
                    x: 0.02, y: parseFloat(yearlyOverallAverage), showarrow: false,
                    font: {{ color: 'red', size: 12 }}, bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: 'red', borderwidth: 1
                }}]
            }};

            Plotly.react(container, [trace, avgLine], layout);
        }}

        function updateYearlyComparisonChart() {{
            const container = document.getElementById('yearly-comparison-chart-container');
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            let targetData = [...rawData];
            if (selectedDept !== '전체') {{ targetData = targetData.filter(item => item['피평가부서'] === selectedDept); }}
            if (selectedUnit !== '전체') {{ targetData = targetData.filter(item => item['피평가Unit'] === selectedUnit); }}

            if (targetData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const years = [...new Set(targetData.map(item => item['설문연도']))].sort();
            const traces = [];

            selectedScores.forEach(col => {{
                const y_values = years.map(year => {{
                    const yearData = targetData.filter(d => d['설문연도'] === year);
                    return yearData.length > 0 ? (yearData.reduce((sum, item) => sum + (item[col] || 0), 0) / yearData.length).toFixed(1) : 0;
                }});
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            
            const yearly_counts = years.map(year => targetData.filter(d => d['설문연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}명`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}명<br>연도: %{{x}}<extra></extra>' }});

            let titleText = '연도별 문항 점수 트렌드';
            if (selectedDept !== '전체' && selectedUnit !== '전체') {{ titleText = `[${{selectedDept}} > ${{selectedUnit}}] 연도별 문항 점수 트렌드`; }}
            else if (selectedDept !== '전체') {{ titleText = `[${{selectedDept}}] 연도별 문항 점수 트렌드`; }}
            else if (selectedUnit !== '전체') {{ titleText = `[${{selectedUnit}}] 연도별 문항 점수 트렌드`; }}
            
            const layout = {{
                title: `<b>${{titleText}}</b>`, barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont, hovermode: 'closest'
            }};
            
            Plotly.react(container, traces, layout);
        }}

        function setupUnitComparisonChart() {{
            const departmentSelect = document.getElementById('unit-comparison-department-filter');
            const yearSelect = document.getElementById('unit-comparison-year-filter');
            
            const allDepartments = [...new Set(rawData.map(item => item['피평가부서']))].filter(d => d && d !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            departmentSelect.innerHTML = ['부서를 선택하세요', ...allDepartments].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            yearSelect.innerHTML = ['전체', ...allYears].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1];
            
            departmentSelect.addEventListener('change', updateUnitComparisonChart);
            yearSelect.addEventListener('change', updateUnitComparisonChart);
            
            createCheckboxFilter('unit-comparison-score-filter', scoreCols, 'unit-comparison-score', updateUnitComparisonChart);
        }}

        function updateUnitComparisonChart() {{
            const container = document.getElementById('unit-comparison-chart-container');
            const selectedDepartment = document.getElementById('unit-comparison-department-filter').value;
            const selectedYear = document.getElementById('unit-comparison-year-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="unit-comparison-score"]:checked')).map(cb => cb.value);

            if (selectedDepartment === '부서를 선택하세요') {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '비교할 부서를 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            let departmentData = rawData.filter(item => item['피평가부서'] === selectedDepartment);
            if (selectedYear !== '전체') {{ departmentData = departmentData.filter(item => item['설문연도'] === selectedYear); }}

            const unitsInDepartment = [...new Set(departmentData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));

            if (unitsInDepartment.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '선택된 조건에 해당하는 Unit이 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const traces = [];
            selectedScores.forEach(col => {{
                const y_values = unitsInDepartment.map(unit => {{
                    const unitData = departmentData.filter(item => item['피평가Unit'] === unit);
                    return unitData.length > 0 ? (unitData.reduce((sum, item) => sum + (item[col] || 0), 0) / unitData.length).toFixed(1) : 0;
                }});
                traces.push({{ x: unitsInDepartment, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>Unit: %{{x}}<extra></extra>' }});
            }});

            const yearTitle = selectedYear === '전체' ? '전체 연도' : selectedYear;
            const layout = {{
                title: `<b>[${{selectedDepartment}}] Unit별 문항 점수 비교 (${{yearTitle}})</b>`, barmode: 'group', height: 500,
                xaxis: {{ title: 'Unit' }}, yaxis: {{ title: '점수', range: [0, 100] }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont, hovermode: 'closest'
            }};

            Plotly.react(container, traces, layout);
        }}

        function toggleExpander(expanderId) {{
            const content = document.getElementById(expanderId);
            const arrow = document.getElementById(expanderId.replace('-expander', '-arrow'));
            
            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                arrow.classList.remove('expanded');
            }} else {{
                content.classList.add('expanded');
                arrow.classList.add('expanded');
            }}
        }}

        function updateExpanderHeader(groupName, selectedCount, totalCount) {{
            const headerId = groupName.replace('-filter', '-header');
            const headerSpan = document.querySelector(`#${{headerId}} span:first-child`);
            if (headerSpan) {{
                if (groupName.includes('division')) {{
                    headerSpan.textContent = `부문 선택 (${{selectedCount}}개 선택됨)`;
                }} else {{
                    headerSpan.textContent = `문항 선택 (${{selectedCount}}개 선택됨)`;
                }}
            }}
        }}

        function createCheckboxFilter(containerId, items, groupName, updateFunction, startChecked = true) {{
            const container = document.getElementById(containerId);
            
            const selectAllDiv = document.createElement('div');
            selectAllDiv.className = 'checkbox-item';
            selectAllDiv.innerHTML = `<input type="checkbox" id="${{groupName}}-select-all" ${{startChecked ? 'checked' : ''}}><label for="${{groupName}}-select-all"><b>전체 선택</b></label>`;
            container.appendChild(selectAllDiv);
            
            items.forEach(item => {{
                const itemDiv = document.createElement('div');
                itemDiv.className = 'checkbox-item';
                itemDiv.innerHTML = `<input type="checkbox" id="${{groupName}}-${{item}}" name="${{groupName}}" value="${{item}}" ${{startChecked ? 'checked' : ''}}><label for="${{groupName}}-${{item}}">${{item}}</label>`;
                container.appendChild(itemDiv);
            }});

            const selectAllCheckbox = container.querySelector(`#${{groupName}}-select-all`);
            const itemCheckboxes = container.querySelectorAll(`input[name="${{groupName}}"]`);

            function updateSelectAllState() {{
                const allChecked = [...itemCheckboxes].every(cb => cb.checked);
                const someChecked = [...itemCheckboxes].some(cb => cb.checked);
                const checkedCount = [...itemCheckboxes].filter(cb => cb.checked).length;
                
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = !allChecked && someChecked;
                
                updateExpanderHeader(containerId, checkedCount, items.length);
            }}

            selectAllCheckbox.addEventListener('change', (e) => {{
                itemCheckboxes.forEach(checkbox => {{ checkbox.checked = e.target.checked; }});
                updateSelectAllState();
                updateFunction();
            }});

            itemCheckboxes.forEach(checkbox => {{
                checkbox.addEventListener('change', () => {{
                    updateSelectAllState();
                    updateFunction();
                }});
            }});

            updateSelectAllState();
        }}

        // === 협업 네트워크 분석 기능 ===
        
        // 부문-부서-Unit 매핑 생성
        const divisionDepartmentMap = rawData.reduce((acc, item) => {{
            const division = item['피평가부문'];
            const department = item['피평가부서'];
            if (division && division !== 'N/A' && department && department !== 'N/A') {{
                if (!acc[division]) {{ acc[division] = new Set(); }}
                acc[division].add(department);
            }}
            return acc;
        }}, {{}});
        for (const division in divisionDepartmentMap) {{
            divisionDepartmentMap[division] = [...divisionDepartmentMap[division]].sort((a, b) => String(a).localeCompare(String(b), 'ko'));
        }}

        function setupNetworkAnalysis() {{
            const yearSelect = document.getElementById('network-year-filter');
            const divisionSelect = document.getElementById('network-division-filter');
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const minCollabSelect = document.getElementById('min-collaboration-filter');
            const sentimentSelect = document.getElementById('network-sentiment-filter');
            
            // 연도 필터 설정
            yearSelect.innerHTML = ['전체', ...allYears].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            // 부문 필터 설정
            divisionSelect.innerHTML = ['전체', ...allDivisions].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            // 초기 부서, Unit 설정
            departmentSelect.innerHTML = '<option value="전체">전체</option>';
            unitSelect.innerHTML = '<option value="전체">전체</option>';
            
            // 이벤트 리스너 추가
            yearSelect.addEventListener('change', updateNetworkAnalysis);
            divisionSelect.addEventListener('change', updateNetworkDepartments);
            departmentSelect.addEventListener('change', updateNetworkUnits);
            unitSelect.addEventListener('change', updateNetworkAnalysis);
            minCollabSelect.addEventListener('change', updateNetworkAnalysis);
            sentimentSelect.addEventListener('change', updateNetworkReviews);
        }}

        function updateNetworkDepartments() {{
            const divisionSelect = document.getElementById('network-division-filter');
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const selectedDivision = divisionSelect.value;
            
            // 부서 드롭다운 업데이트
            const allDepartments = [...new Set(rawData.map(item => item['피평가부서']))].filter(d => d && d !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            const departments = (selectedDivision === '전체' || !divisionDepartmentMap[selectedDivision])
                ? allDepartments
                : divisionDepartmentMap[selectedDivision];
            
            departmentSelect.innerHTML = ['전체', ...departments].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            departmentSelect.value = '전체';
            
            // Unit 드롭다운 리셋
            unitSelect.innerHTML = '<option value="전체">전체</option>';
            unitSelect.value = '전체';
            
            updateNetworkAnalysis();
        }}

        function updateNetworkUnits() {{
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const selectedDept = departmentSelect.value;
            
            // Unit 드롭다운 업데이트
            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept])
                ? allUnits
                : departmentUnitMap[selectedDept];
            
            unitSelect.innerHTML = ['전체', ...units].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            unitSelect.value = '전체';
            
            updateNetworkAnalysis();
        }}

        function getNetworkFilteredData() {{
            let filteredData = [...rawData];
            
            const selectedYear = document.getElementById('network-year-filter').value;
            const selectedDivision = document.getElementById('network-division-filter').value;
            const selectedDepartment = document.getElementById('network-department-filter').value;
            const selectedUnit = document.getElementById('network-unit-filter').value;
            
            if (selectedYear !== '전체') {{ filteredData = filteredData.filter(item => item['설문연도'] === selectedYear); }}
            if (selectedDivision !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부문'] === selectedDivision); }}
            if (selectedDepartment !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부서'] === selectedDepartment); }}
            if (selectedUnit !== '전체') {{ filteredData = filteredData.filter(item => item['피평가Unit'] === selectedUnit); }}
            
            return filteredData;
        }}

        function updateNetworkAnalysis() {{
            updateCollaborationFrequencyChart();
            updateCollaborationStatusChart();
            updateCollaborationTrendChart();
            updateNetworkReviews();
        }}

        function updateCollaborationFrequencyChart() {{
            const container = document.getElementById('collaboration-frequency-chart-container');
            const filteredData = getNetworkFilteredData();
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            
            if (filteredData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            // 협업 빈도 계산
            const collaborationCounts = {{}};
            filteredData.forEach(item => {{
                const evaluator = item['평가부서'];
                const evaluated = item['피평가부서'];
                if (evaluator !== evaluated && evaluator && evaluated && evaluator !== 'N/A' && evaluated !== 'N/A') {{
                    const key = `${{evaluator}} ↔ ${{evaluated}}`;
                    collaborationCounts[key] = (collaborationCounts[key] || 0) + 1;
                }}
            }});
            
            // 최소 협업 횟수 이상인 관계만 필터링
            const filteredCollaborations = Object.entries(collaborationCounts)
                .filter(([_, count]) => count >= minCollabCount)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);
            
            if (filteredCollaborations.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: `최소 ${{minCollabCount}}회 이상 협업한 관계가 없습니다.`, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const trace = {{
                y: filteredCollaborations.map(([key, _]) => key).reverse(),
                x: filteredCollaborations.map(([_, count]) => count).reverse(),
                type: 'bar',
                orientation: 'h',
                text: filteredCollaborations.map(([_, count]) => `${{count}}회`).reverse(),
                textposition: 'outside',
                textfont: {{ size: 12 }},
                marker: {{ color: '#4a69bd' }},
                hovertemplate: '협업 횟수: %{{x}}회<extra></extra>'
            }};
            
            const layout = {{
                title: '<b>협업 빈도 TOP 10</b>',
                height: 400,
                margin: {{ l: 200 }},
                xaxis: {{ title: '협업 횟수' }},
                yaxis: {{ automargin: true }},
                font: layoutFont
            }};
            
            Plotly.react(container, [trace], layout);
        }}

        function updateCollaborationStatusChart() {{
            const container = document.getElementById('collaboration-status-chart-container');
            const filteredData = getNetworkFilteredData();
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            
            if (filteredData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            // 협업 관계별 점수 계산
            const relationshipScores = {{}};
            filteredData.forEach(item => {{
                const evaluator = item['평가부서'];
                const evaluated = item['피평가부서'];
                const score = item['종합 점수'];
                if (evaluator !== evaluated && evaluator && evaluated && evaluator !== 'N/A' && evaluated !== 'N/A' && score != null) {{
                    const key = `${{evaluator}} → ${{evaluated}}`;
                    if (!relationshipScores[key]) {{ relationshipScores[key] = {{ scores: [], count: 0 }}; }}
                    relationshipScores[key].scores.push(score);
                    relationshipScores[key].count++;
                }}
            }});
            
            // 최소 협업 횟수 이상인 관계만 필터링하고 점수별로 분류
            const statusCounts = {{ '우수 (75점 이상)': 0, '양호 (60-74점)': 0, '주의 (50-59점)': 0, '문제 (50점 미만)': 0 }};
            Object.entries(relationshipScores)
                .filter(([_, data]) => data.count >= minCollabCount)
                .forEach(([_, data]) => {{
                    const avgScore = data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length;
                    if (avgScore >= 75) statusCounts['우수 (75점 이상)']++;
                    else if (avgScore >= 60) statusCounts['양호 (60-74점)']++;
                    else if (avgScore >= 50) statusCounts['주의 (50-59점)']++;
                    else statusCounts['문제 (50점 미만)']++;
                }});
            
            const statusLabels = Object.keys(statusCounts);
            const statusValues = Object.values(statusCounts);
            const statusColors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545'];
            
            if (statusValues.every(val => val === 0)) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: `최소 ${{minCollabCount}}회 이상 협업한 관계가 없습니다.`, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const trace = {{
                x: statusLabels,
                y: statusValues,
                type: 'bar',
                text: statusValues.map(val => `${{val}}개`),
                textposition: 'outside',
                textfont: {{ size: 12 }},
                marker: {{ color: statusColors }},
                hovertemplate: '%{{x}}: %{{y}}개 관계<extra></extra>'
            }};
            
            const layout = {{
                title: '<b>협업 관계 현황</b>',
                height: 400,
                xaxis: {{ title: '관계 상태' }},
                yaxis: {{ title: '관계 수', rangemode: 'tozero' }},
                font: layoutFont
            }};
            
            Plotly.react(container, [trace], layout);
        }}

        function updateCollaborationTrendChart() {{
            const container = document.getElementById('collaboration-trend-chart-container');
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            
            // 연도별 데이터 준비 (전체 연도 사용)
            const yearlyData = {{}};
            allYears.forEach(year => {{
                let yearData = rawData.filter(item => item['설문연도'] === year);
                
                // 네트워크 필터 적용 (연도 제외)
                const selectedDivision = document.getElementById('network-division-filter').value;
                const selectedDepartment = document.getElementById('network-department-filter').value;
                const selectedUnit = document.getElementById('network-unit-filter').value;
                
                if (selectedDivision !== '전체') {{ yearData = yearData.filter(item => item['피평가부문'] === selectedDivision); }}
                if (selectedDepartment !== '전체') {{ yearData = yearData.filter(item => item['피평가부서'] === selectedDepartment); }}
                if (selectedUnit !== '전체') {{ yearData = yearData.filter(item => item['피평가Unit'] === selectedUnit); }}
                
                yearlyData[year] = yearData;
            }});
            
            // 연도별 평균 점수 계산
            const yearlyAvgScores = allYears.map(year => {{
                const data = yearlyData[year];
                if (data.length < minCollabCount) return null;
                const avgScore = data.reduce((sum, item) => sum + (item['종합 점수'] || 0), 0) / data.length;
                return avgScore.toFixed(1);
            }});
            
            if (yearlyAvgScores.every(score => score === null)) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: `최소 ${{minCollabCount}}회 이상의 데이터가 있는 연도가 없습니다.`, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const trace = {{
                x: allYears,
                y: yearlyAvgScores,
                type: 'scatter',
                mode: 'lines+markers+text',
                line: {{ color: '#4a69bd', width: 3 }},
                marker: {{ size: 8 }},
                text: yearlyAvgScores.map(score => score ? `${{score}}점` : ''),
                textposition: 'top center',
                textfont: {{ size: 12 }},
                connectgaps: false,
                hovertemplate: '연도: %{{x}}<br>평균 점수: %{{y}}점<extra></extra>'
            }};
            
            const layout = {{
                title: '<b>협업 관계 변화 트렌드</b>',
                height: 400,
                xaxis: {{ title: '연도', type: 'category' }},
                yaxis: {{ title: '평균 협업 점수', range: [0, 100] }},
                font: layoutFont
            }};
            
            Plotly.react(container, [trace], layout);
        }}

        function updateNetworkReviews() {{
            const tbody = document.querySelector('#network-reviews-table tbody');
            const filteredData = getNetworkFilteredData();
            const selectedSentiment = document.getElementById('network-sentiment-filter').value;
            
            let reviewData = filteredData;
            if (selectedSentiment !== '전체') {{
                reviewData = filteredData.filter(item => item['감정_분류'] === selectedSentiment);
            }}
            
            const reviews = reviewData
                .filter(item => item['정제된_텍스트'] && item['정제된_텍스트'] !== 'N/A')
                .map(item => ({{
                    year: item['설문연도'],
                    partner: item['평가부서'] !== item['피평가부서'] ? item['평가부서'] : '동일부서',
                    review: item['정제된_텍스트'],
                    sentiment: item['감정_분류'] || '알 수 없음'
                }}))
                .sort((a, b) => b.year - a.year)
                .slice(0, 50); // 최대 50개만 표시
            
            tbody.innerHTML = (reviews.length > 0) ?
                reviews.map(r => `<tr><td>${{r.year}}</td><td>${{r.partner}}</td><td>${{r.review}} <span style="color: #666; font-size: 0.9em;">[${{r.sentiment}}]</span></td></tr>`).join('') :
                '<tr><td colspan="3">해당 조건의 후기가 없습니다.</td></tr>';
        }}

        window.onload = () => {{ 
            populateFilters(); 
            createCheckboxFilter('hospital-score-filter', scoreCols, 'hospital-score', updateHospitalYearlyChart);
            createCheckboxFilter('drilldown-score-filter', scoreCols, 'drilldown-score', updateDashboard);
            createCheckboxFilter('review-sentiment-filter', ['긍정', '부정', '중립'], 'review-sentiment', updateReviewsTable, true);
            setupDivisionChart();
            setupComparisonChart();
            setupTeamRankingChart();
            setupUnitComparisonChart();
            setupNetworkAnalysis();
            updateDashboard(); 
            updateHospitalYearlyChart();
            updateDivisionYearlyChart();
            updateYearlyDivisionComparisonChart();
            updateTeamRankingChart();
            updateUnitComparisonChart();
            updateEmotionIntensityTrend();
            updateNetworkAnalysis();
        }};
    </script>
</body>
</html>
    """

# --- 3. 메인 실행 로직 ---
def main():
    print("🚀 개선된 대화형 대시보드 v2.0 생성을 시작합니다...")
    df = load_data()
    print("✅ 데이터 로드 완료")
    df_for_json = df[['설문연도', '평가부서', '피평가부문', '피평가부서', '피평가Unit', '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수', '정제된_텍스트', '감정_분류', '감정_강도_점수', '핵심_키워드']].copy()
    data_json = df_for_json.to_json(orient='records', force_ascii=False)
    print("✅ 데이터 JSON 변환 완료")
    dashboard_html = build_html_v2(data_json)
    print("✅ HTML 빌드 완료")
    output_filename = "서울아산병원 협업평가 대시보드 v2.0.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    print(f"🎉 '{output_filename}' 파일이 성공적으로 생성되었습니다.")
    print("\n📋 주요 개선사항:")
    print("   ✨ 자동 섹션 번호 매기기")
    print("   📈 Part별 논리적 구조 (Overview → Performance → Deep Dive)")
    print("   🔍 통합된 상세 분석 섹션")
    print("   💡 설명 텍스트로 각 섹션 목적 명시")
    print("   🎨 개선된 시각적 구분 (파트 구분선, 제목 스타일)")

if __name__ == "__main__":
    main()