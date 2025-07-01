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
    
    for col in ['피평가부문', '피평가부서', '피평가Unit', '협업후기']:
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
        .checkbox-group {{ display: flex; flex-direction: column; gap: 5px; align-items: stretch; padding: 10px; border-radius: 5px; background-color: #f1f3f5; border: 1px solid #dee2e6; }}
        .checkbox-group label {{ font-weight: normal; display: flex; width: 100%; justify-content: space-between; align-items: center; cursor: pointer; padding: 2px 5px; }}
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
                    <div id="hospital-score-filter" class="checkbox-group"></div>
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
                    <div id="division-score-filter" class="checkbox-group"></div>
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
                    <div id="comparison-division-filter" class="checkbox-group"></div>
                </div>
            </div>
            <div id="comparison-chart-container"></div>
        </div>
        <div class="section">
            <h2>상세 분석 (부서/Unit별)</h2>
            <div class="filters">
                <div class="filter-group"><label for="year-filter">연도 (전체)</label><select id="year-filter"></select></div>
                <div class="filter-group"><label for="department-filter">피평가부서</label><select id="department-filter"></select></div>
                <div class="filter-group"><label for="unit-filter">피평가Unit</label><select id="unit-filter"></select></div>
            </div>
            <div id="metrics-container"></div>
            <div id="drilldown-chart-container" style="margin-top: 20px;"></div>
            <div class="filters" style="margin-top: 20px;">
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div id="drilldown-score-filter" class="checkbox-group"></div>
                </div>
            </div>
            
            <h3>협업 후기</h3>
            <div id="reviews-table-container"><table id="reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody></tbody></table></div>
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
            createCheckboxFilter('comparison-division-filter', allDivisions, 'comparison-division', updateYearlyDivisionComparisonChart, false);
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
            updateReviewsTable(filteredData);
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
            const chartData = [{{ x: selectedScores, y: selectedScores.map(col => averages[col].toFixed(1)), type: 'bar', text: selectedScores.map(col => averages[col].toFixed(1)), textposition: 'outside', marker: {{ color: '#6a89cc' }} }}];
            const selectedYear = document.getElementById('year-filter').value;
            const title = selectedYear === '전체' ? '<b>선택 조건별 문항 점수 (전체 연도)</b>' : `<b>선택 조건별 문항 점수 (${{selectedYear}})</b>`;
            const layout = {{ title: title, yaxis: {{ title: '종합 점수', range: [0, 100] }}, font: layoutFont }};
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
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 10 }} }});
            }});
            
            const yearly_counts = years.map(year => rawData.filter(d => d['설문연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers', yaxis: 'y2' }});

            const layout = {{
                title: '<b>[전체] 연도별 문항 점수</b>',
                barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '종합 점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont
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
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 10 }} }});
            }});
            
            const yearly_counts = years.map(year => divisionData.filter(d => d['설문연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers', yaxis: 'y2' }});

            const layout = {{
                title: `<b>[${{selectedDivision}}] 연도별 문항 점수</b>`,
                barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '종합 점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                font: layoutFont
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

            const trace = [{{ x: divisions, y: avgScores, type: 'bar', text: avgScores, textposition: 'outside' }}];
            const layout = {{
                title: `<b>${{selectedYear}} 부문별 종합 점수 비교</b>`,
                yaxis: {{ title: '종합 점수', range: [0, 100] }},
                font: layoutFont,
                height: 500,
                barmode: 'group'
            }};
            Plotly.react(container, trace, layout);
        }}

        function updateReviewsTable(data) {{
            const tbody = document.querySelector("#reviews-table tbody");
            const reviews = data.map(item => ({{ year: item['설문연도'], review: item['협업후기'] }})).filter(r => r.review && r.review !== 'N/A');
            tbody.innerHTML = (reviews.length > 0) ? reviews.map(r => `<tr><td>${{r.year}}</td><td>${{r.review}}</td></tr>`).join('') : '<tr><td colspan="2">해당 조건의 후기가 없습니다.</td></tr>';
        }}

        function createCheckboxFilter(containerId, items, groupName, updateFunction, startChecked = true) {{
            const container = document.getElementById(containerId);
            const content = `
                <label>
                    <b>전체 선택</b> <input type="checkbox" name="${{groupName}}-select-all" ${{startChecked ? 'checked' : ''}}>
                </label>
                ${{items.map(item => `
                    <label>
                        <span>${{item}}</span> <input type="checkbox" name="${{groupName}}" value="${{item}}" ${{startChecked ? 'checked' : ''}}>
                    </label>
                `).join('')}}
            `;
            container.innerHTML = content;

            const selectAllCheckbox = container.querySelector(`input[name="${{groupName}}-select-all"]`);
            const itemCheckboxes = container.querySelectorAll(`input[name="${{groupName}}"]`);

            function updateSelectAllState() {{
                const allChecked = [...itemCheckboxes].every(cb => cb.checked);
                const someChecked = [...itemCheckboxes].some(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = !allChecked && someChecked;
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
            setupDivisionChart();
            setupComparisonChart();
            updateDashboard(); 
            updateHospitalYearlyChart();
            updateDivisionYearlyChart();
            updateYearlyDivisionComparisonChart();
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
    df_for_json = df[['설문연도', '피평가부문', '피평가부서', '피평가Unit', '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수', '협업후기']].copy()
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