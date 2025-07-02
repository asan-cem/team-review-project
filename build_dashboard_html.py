import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# --- 1. 데이터 로드 및 전처리 ---
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
    df.dropna(subset=['종합 점수'], inplace=True)
    
    for col in ['피평가부문', '피평가부서', '피평가Unit', '정제된_텍스트']:
        df[col] = df[col].fillna('N/A')
        
    return df

# --- 2. 시각화 및 HTML 생성 ---
def build_html(data_json):
    """Plotly 차트와 JS 필터링 로직을 포함한 대화형 HTML 생성 (개선)"""
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>서울아산병원 협업 평가 대시보드</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; color: #343a40; font-size: 16px;}}
        .container {{ max-width: 1400px; margin: auto; padding: 20px; }}
        .header {{ background: linear-gradient(90deg, #4a69bd, #6a89cc); color: white; padding: 25px; text-align: center; border-radius: 0 0 10px 10px; }}
        h1, h2, h3 {{ margin: 0; padding: 0; }}
        h2 {{ color: #4a69bd; border-bottom: 3px solid #6a89cc; padding-bottom: 10px; margin-top: 40px; margin-bottom: 20px; }}
        h3 {{ color: #555; margin-top: 30px; margin-bottom: 15px;}}
        .section {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 30px;}}
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
        #reviews-table-container {{ max-height: 400px; overflow-y: auto; margin-top: 20px; border: 1px solid #dee2e6; border-radius: 5px; }}
        #reviews-table {{ width: 100%; border-collapse: collapse; }}
        #reviews-table th, #reviews-table td {{ padding: 12px; border-bottom: 1px solid #dee2e6; text-align: left; }}
        #reviews-table th {{ background-color: #f8f9fa; position: sticky; top: 0; }}
        #reviews-table tr:last-child td {{ border-bottom: none; }}
    </style>
</head>
<body>
    <div class="header"><h1>📊 서울아산병원 협업 평가 대시보드</h1></div>
    <div class="container">
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
        <div class="section">
            <h2>상세 분석 (부서/Unit별)</h2>
            <div class="filters">
                <div class="filter-group"><label for="year-filter">연도 (전체)</label><select id="year-filter"></select></div>
                <div class="filter-group"><label for="department-filter">피평가부서</label><select id="department-filter"></select></div>
                <div class="filter-group"><label for="unit-filter">피평가Unit</label><select id="unit-filter"></select></div>
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
            <div id="drilldown-chart-container" style="margin-top: 20px;"></div>
            
            <h3>협업 주관식 피드백 감정 분석</h3>
            <div id="sentiment-chart-container" style="margin-top: 20px;"></div>
            
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
            
            <h3>감정 강도 분석</h3>
            <div id="emotion-intensity-trend-container"></div>
        </div>
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
            
            const titlePrefix = titleParts.length > 0 ? titleParts.join(' > ') : '피평가부서, 피평가Unit';
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

            const sentiments = Object.keys(sentimentCounts);
            const counts = Object.values(sentimentCounts);
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
            
            // 디버깅: 전체 데이터와 감정 강도 데이터 확인
            console.log('전체 데이터 수:', rawData.length);
            const intensityDataCount = rawData.filter(item => {{
                const intensity = item['감정_강도_점수'];
                return intensity !== null && intensity !== undefined && intensity !== '' && !isNaN(parseFloat(intensity));
            }}).length;
            console.log('감정 강도 데이터가 있는 항목 수:', intensityDataCount);
            
            // 감정 강도 데이터가 있는 항목만 필터링 (0도 유효한 값으로 처리)
            let targetData = rawData.filter(item => {{
                const intensity = item['감정_강도_점수'];
                return intensity !== null && intensity !== undefined && intensity !== '' && !isNaN(parseFloat(intensity));
            }});
            
            console.log('필터링 전 감정 강도 데이터 수:', targetData.length);
            
            // 부서 필터 적용
            if (selectedDept !== '전체') {{
                targetData = targetData.filter(item => item['피평가부서'] === selectedDept);
                console.log(`${{selectedDept}} 부서 필터링 후 데이터 수:`, targetData.length);
            }}
            
            // Unit 필터 적용
            if (selectedUnit !== '전체') {{
                targetData = targetData.filter(item => item['피평가Unit'] === selectedUnit);
                console.log(`${{selectedUnit}} Unit 필터링 후 데이터 수:`, targetData.length);
            }}
            
            if (targetData.length === 0) {{
                // 더 구체적인 메시지 제공
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
            
            // 연도별 감정 강도 및 감정 분류별 집계
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
            
            // 연도 정렬
            const years = Object.keys(yearlyData).sort();
            
            if (years.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '표시할 연도별 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            // 트레이스 생성
            const traces = [];
            
            // 전체 평균 감정 강도 라인
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
            
            // 감정 분류별 평균 강도 라인
            const sentimentColors = {{
                '긍정': '#28a745',
                '부정': '#dc3545',
                '중립': '#6c757d'
            }};
            
            Object.entries(sentimentColors).forEach(([sentiment, color]) => {{
                const sentimentAvg = years.map(year => {{
                    const sentimentIntensities = yearlyData[year].sentiments[sentiment];
                    if (sentimentIntensities.length === 0) return null;
                    return (sentimentIntensities.reduce((sum, val) => sum + val, 0) / sentimentIntensities.length).toFixed(2);
                }});
                
                // null이 아닌 값이 있는 경우에만 트레이스 추가
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
            
            // 제목 생성
            let titleParts = [];
            if (selectedDept !== '전체') {{ titleParts.push(selectedDept); }}
            if (selectedUnit !== '전체') {{ titleParts.push(selectedUnit); }}
            
            const titlePrefix = titleParts.length > 0 ? titleParts.join(' > ') : '전체';
            const title = `<b>${{titlePrefix}} 연도별 감정 강도 트렌드</b>`;
            
            const layout = {{
                title: title,
                height: 400,
                xaxis: {{ 
                    title: '연도',
                    type: 'category'
                }},
                yaxis: {{ 
                    title: '평균 감정 강도',
                    range: [1, 10]
                }},
                font: layoutFont,
                hovermode: 'x unified',
                showlegend: true,
                legend: {{
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: 1.02,
                    xanchor: 'right',
                    x: 1
                }}
            }};
            
            Plotly.react(container, traces, layout);
        }}

        function updateReviewsTable(data = null) {{
            const tbody = document.querySelector("#reviews-table tbody");
            
            // data가 null인 경우 getFilteredData() 사용 (필터에서 호출될 때)
            if (data === null) {{
                data = getFilteredData();
            }}
            
            // 감정 분류 필터 적용
            const selectedSentiments = Array.from(document.querySelectorAll('input[name="review-sentiment"]:checked')).map(cb => cb.value);
            
            let filteredData = data;
            if (selectedSentiments.length > 0 && !selectedSentiments.includes('전체')) {{
                filteredData = data.filter(item => {{
                    const sentiment = item['감정_분류'];
                    return selectedSentiments.includes(sentiment);
                }});
            }}
            
            const reviews = filteredData.map(item => ({{ 
                year: item['설문연도'], 
                review: item['정제된_텍스트'],
                sentiment: item['감정_분류'] || '알 수 없음'
            }})).filter(r => r.review && r.review !== 'N/A')
            .sort((a, b) => b.year - a.year); // 연도 내림차순 정렬 (2025, 2024, 2023, 2022)
            
            tbody.innerHTML = (reviews.length > 0) ? 
                reviews.map(r => `<tr><td>${{r.year}}</td><td>${{r.review}} <span style="color: #666; font-size: 0.9em;">[${{r.sentiment}}]</span></td></tr>`).join('') : 
                '<tr><td colspan="2">해당 조건의 후기가 없습니다.</td></tr>';
        }}

        function setupTeamRankingChart() {{
            const yearSelect = document.getElementById('team-ranking-year-filter');
            const divisionSelect = document.getElementById('team-ranking-division-filter');
            
            // 연도 선택지 설정
            yearSelect.innerHTML = allYears.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1]; // 최신 연도로 기본 설정
            
            // 부문 선택지 설정
            divisionSelect.innerHTML = ['부문을 선택하세요', ...allDivisions].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            yearSelect.addEventListener('change', updateTeamRankingChart);
            divisionSelect.addEventListener('change', updateTeamRankingChart);
        }}

        function updateTeamRankingChart() {{
            const container = document.getElementById('team-ranking-chart-container');
            const selectedYear = document.getElementById('team-ranking-year-filter').value;
            const selectedDivision = document.getElementById('team-ranking-division-filter').value;

            // 선택된 연도의 데이터 필터링
            let yearData = rawData.filter(item => item['설문연도'] === selectedYear);

            // 부문별 필터링
            if (selectedDivision !== '부문을 선택하세요') {{
                yearData = yearData.filter(item => item['피평가부문'] === selectedDivision);
            }}

            // 부서별 평균 점수 계산
            const teamScores = {{}};
            yearData.forEach(item => {{
                const department = item['피평가부서'];
                const division = item['피평가부문'];
                const score = item['종합 점수'];
                
                if (department && department !== 'N/A' && division && division !== 'N/A' && score != null) {{
                    if (!teamScores[department]) {{
                        teamScores[department] = {{ 
                            scores: [], 
                            division: division,
                            unit: item['피평가Unit']
                        }};
                    }}
                    teamScores[department].scores.push(score);
                }}
            }});

            // 평균 계산 및 정렬
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

            // 부문별 색상 매핑
            const divisionColors = {{
                '진료부문': '#1f77b4',
                '간호부문': '#ff7f0e', 
                '관리부문': '#2ca02c',
                '의료지원부문': '#d62728',
                '기타': '#9467bd'
            }};

            // 차트 데이터 생성
            const departments = teamRankings.map(item => item.department);
            const scores = teamRankings.map(item => parseFloat(item.avgScore));
            const colors = teamRankings.map(item => divisionColors[item.division] || '#17becf');
            const hoverTexts = teamRankings.map(item => 
                `부서: ${{item.department}}<br>부문: ${{item.division}}<br>점수: ${{item.avgScore}}<br>응답수: ${{item.count}}명`
            );

            // 연도별 전체 평균 계산 (선택된 연도의 모든 데이터)
            const allYearData = rawData.filter(item => item['설문연도'] === selectedYear);
            const yearlyOverallAverage = allYearData.length > 0 ? 
                (allYearData.reduce((sum, item) => sum + (item['종합 점수'] || 0), 0) / allYearData.length).toFixed(1) : 0;

            const trace = {{
                x: departments,
                y: scores,
                type: 'bar',
                text: scores.map(score => score.toString()),
                textposition: 'outside',
                textfont: {{ size: 12 }},
                marker: {{ color: colors }},
                hovertemplate: '%{{hovertext}}<extra></extra>',
                hovertext: hoverTexts
            }};

            // 평균선 추가
            const avgLine = {{
                x: [departments[0], departments[departments.length - 1]],
                y: [yearlyOverallAverage, yearlyOverallAverage],
                type: 'scatter',
                mode: 'lines',
                line: {{ color: 'red', width: 2, dash: 'dash' }},
                name: `${{selectedYear}} 전체 평균: ${{yearlyOverallAverage}}`,
                hoverinfo: 'skip'
            }};

            const layout = {{
                title: `<b>${{selectedYear}} 부문별 부서 점수 순위 (점수 높은 순)</b>`,
                height: 600,
                xaxis: {{ 
                    title: '부서',
                    tickangle: -45,
                    automargin: true
                }},
                yaxis: {{ 
                    title: '점수',
                    range: [Math.min(...scores) - 5, Math.max(...scores) + 5]
                }},
                font: layoutFont,
                hovermode: 'closest',
                showlegend: false,
                legend: {{ 
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: 1.02,
                    xanchor: 'right',
                    x: 1
                }},
                annotations: [{{
                    text: `${{selectedYear}} 전체 평균: ${{yearlyOverallAverage}}점`,
                    xref: 'paper',
                    yref: 'y',
                    x: 0.02,
                    y: parseFloat(yearlyOverallAverage),
                    showarrow: false,
                    font: {{ color: 'red', size: 12 }},
                    bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: 'red',
                    borderwidth: 1
                }}]
            }};

            Plotly.react(container, [trace, avgLine], layout);
        }}

        function setupYearlyComparisonChart() {{
            const departmentSelect = document.getElementById('yearly-comparison-department-filter');
            const unitSelect = document.getElementById('yearly-comparison-unit-filter');
            
            // 부서 선택지 설정
            const allDepartments = [...new Set(rawData.map(item => item['피평가부서']))].filter(d => d && d !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            departmentSelect.innerHTML = ['전체', ...allDepartments].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            // Unit 선택지 설정
            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            unitSelect.innerHTML = ['전체', ...allUnits].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            departmentSelect.addEventListener('change', () => {{
                updateYearlyComparisonUnitFilter();
                updateYearlyComparisonChart();
            }});
            unitSelect.addEventListener('change', updateYearlyComparisonChart);
            
            createCheckboxFilter('yearly-comparison-score-filter', scoreCols, 'yearly-comparison-score', updateYearlyComparisonChart);
        }}

        function updateYearlyComparisonUnitFilter() {{
            const deptSelect = document.getElementById('yearly-comparison-department-filter');
            const unitSelect = document.getElementById('yearly-comparison-unit-filter');
            const selectedDept = deptSelect.value;

            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept])
                ? allUnits
                : departmentUnitMap[selectedDept];

            unitSelect.innerHTML = ['전체', ...units].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            unitSelect.value = '전체';
        }}

        function updateYearlyComparisonChart() {{
            const container = document.getElementById('yearly-comparison-chart-container');
            const selectedDept = document.getElementById('yearly-comparison-department-filter').value;
            const selectedUnit = document.getElementById('yearly-comparison-unit-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="yearly-comparison-score"]:checked')).map(cb => cb.value);

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 데이터 필터링
            let targetData = [...rawData];
            
            if (selectedDept !== '전체') {{
                targetData = targetData.filter(item => item['피평가부서'] === selectedDept);
            }}
            
            if (selectedUnit !== '전체') {{
                targetData = targetData.filter(item => item['피평가Unit'] === selectedUnit);
            }}

            if (targetData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 연도별 데이터 추출
            const years = [...new Set(targetData.map(item => item['설문연도']))].sort();
            const traces = [];

            selectedScores.forEach(col => {{
                const y_values = years.map(year => {{
                    const yearData = targetData.filter(d => d['설문연도'] === year);
                    const average = yearData.length > 0 ? 
                        (yearData.reduce((sum, item) => sum + (item[col] || 0), 0) / yearData.length).toFixed(1) : 0;
                    return average;
                }});
                traces.push({{ 
                    x: years, 
                    y: y_values, 
                    name: col, 
                    type: 'bar', 
                    text: y_values, 
                    textposition: 'outside', 
                    textfont: {{ size: 14 }}, 
                    hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' 
                }});
            }});
            
            // 응답수 추가
            const yearly_counts = years.map(year => targetData.filter(d => d['설문연도'] === year).length);
            traces.push({{ 
                x: years, 
                y: yearly_counts, 
                name: '응답수', 
                type: 'scatter', 
                mode: 'lines+markers+text', 
                line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, 
                text: yearly_counts.map(count => `${{count.toLocaleString()}}명`), 
                textposition: 'top center', 
                textfont: {{ size: 12 }}, 
                yaxis: 'y2', 
                hovertemplate: '응답수: %{{y}}명<br>연도: %{{x}}<extra></extra>' 
            }});

            // 제목 생성
            let titleText = '연도별 문항 점수';
            if (selectedDept !== '전체' && selectedUnit !== '전체') {{
                titleText = `[${{selectedDept}} > ${{selectedUnit}}] 연도별 문항 점수`;
            }} else if (selectedDept !== '전체') {{
                titleText = `[${{selectedDept}}] 연도별 문항 점수`;
            }} else if (selectedUnit !== '전체') {{
                titleText = `[${{selectedUnit}}] 연도별 문항 점수`;
            }}
            
            const layout = {{
                title: `<b>${{titleText}}</b>`,
                barmode: 'group', 
                height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont,
                hovermode: 'closest'
            }};
            
            Plotly.react(container, traces, layout);
        }}

        function setupUnitComparisonChart() {{
            const departmentSelect = document.getElementById('unit-comparison-department-filter');
            const yearSelect = document.getElementById('unit-comparison-year-filter');
            
            // 부서 선택지 설정
            const allDepartments = [...new Set(rawData.map(item => item['피평가부서']))].filter(d => d && d !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            departmentSelect.innerHTML = ['부서를 선택하세요', ...allDepartments].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            // 연도 선택지 설정
            yearSelect.innerHTML = ['전체', ...allYears].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1]; // 최신 연도로 기본 설정
            
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

            // 선택된 부서의 데이터 필터링
            let departmentData = rawData.filter(item => item['피평가부서'] === selectedDepartment);
            
            if (selectedYear !== '전체') {{
                departmentData = departmentData.filter(item => item['설문연도'] === selectedYear);
            }}

            // 부서 내 유닛 목록 추출
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
                const y_values = [];
                unitsInDepartment.forEach(unit => {{
                    const unitData = departmentData.filter(item => item['피평가Unit'] === unit);
                    const average = unitData.length > 0 ? 
                        (unitData.reduce((sum, item) => sum + (item[col] || 0), 0) / unitData.length).toFixed(1) : 0;
                    y_values.push(average);
                }});
                
                traces.push({{
                    x: unitsInDepartment,
                    y: y_values,
                    name: col,
                    type: 'bar',
                    text: y_values,
                    textposition: 'outside',
                    textfont: {{ size: 14 }},
                    hovertemplate: '%{{fullData.name}}: %{{y}}<br>Unit: %{{x}}<extra></extra>'
                }});
            }});

            const yearTitle = selectedYear === '전체' ? '전체 연도' : selectedYear;
            const layout = {{
                title: `<b>[${{selectedDepartment}}] Unit별 문항 점수 비교 (${{yearTitle}})</b>`,
                barmode: 'group',
                height: 500,
                xaxis: {{ title: 'Unit' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont,
                hovermode: 'closest'
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
            
            // 전체 선택 체크박스 생성
            const selectAllDiv = document.createElement('div');
            selectAllDiv.className = 'checkbox-item';
            selectAllDiv.innerHTML = `
                <input type="checkbox" id="${{groupName}}-select-all" ${{startChecked ? 'checked' : ''}}>
                <label for="${{groupName}}-select-all"><b>전체 선택</b></label>
            `;
            container.appendChild(selectAllDiv);
            
            // 개별 체크박스 생성
            items.forEach(item => {{
                const itemDiv = document.createElement('div');
                itemDiv.className = 'checkbox-item';
                itemDiv.innerHTML = `
                    <input type="checkbox" id="${{groupName}}-${{item}}" name="${{groupName}}" value="${{item}}" ${{startChecked ? 'checked' : ''}}>
                    <label for="${{groupName}}-${{item}}">${{item}}</label>
                `;
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
                
                // 헤더 업데이트
                updateExpanderHeader(containerId, checkedCount, items.length);
            }}

            selectAllCheckbox.addEventListener('change', (e) => {{
                itemCheckboxes.forEach(checkbox => {{
                    checkbox.checked = e.target.checked;
                }});
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

        window.onload = () => {{ 
            populateFilters(); 
            createCheckboxFilter('hospital-score-filter', scoreCols, 'hospital-score', updateHospitalYearlyChart);
            createCheckboxFilter('drilldown-score-filter', scoreCols, 'drilldown-score', updateDashboard);
            createCheckboxFilter('review-sentiment-filter', ['긍정', '부정', '중립'], 'review-sentiment', updateReviewsTable, true);
            setupDivisionChart();
            setupComparisonChart();
            setupTeamRankingChart();
            setupYearlyComparisonChart();
            setupUnitComparisonChart();
            updateDashboard(); 
            updateHospitalYearlyChart();
            updateDivisionYearlyChart();
            updateYearlyDivisionComparisonChart();
            updateTeamRankingChart();
            updateYearlyComparisonChart();
            updateUnitComparisonChart();
            updateEmotionIntensityTrend();
        }};
    </script>
</body>
</html>
    """

# --- 3. 메인 실행 로직 ---
def main():
    print("🚀 대화형 대시보드 생성을 시작합니다...")
    df = load_data()
    print("✅ 데이터 로드 완료")
    df_for_json = df[['설문연도', '피평가부문', '피평가부서', '피평가Unit', '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수', '정제된_텍스트', '감정_분류', '감정_강도_점수']].copy()
    data_json = df_for_json.to_json(orient='records', force_ascii=False)
    print("✅ 데이터 JSON 변환 완료")
    dashboard_html = build_html(data_json)
    print("✅ HTML 빌드 완료")
    output_filename = "dashboard_interactive_v7.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    print(f"🎉 '{output_filename}' 파일이 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    main() 