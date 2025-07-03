"""
대시보드 JavaScript 코드 관리 모듈
"""
from dashboard_config import DashboardConfig

class DashboardJavaScript:
    """대시보드 JavaScript 코드를 관리하는 클래스"""
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
    
    def get_data_cache_class(self) -> str:
        """데이터 캐시 클래스"""
        return """
        class DataCache {
            constructor(rawData) {
                this.rawData = rawData;
                this.cache = new Map();
                this.filterCache = new Map();
            }
            
            getFilteredData(filters) {
                const key = JSON.stringify(filters);
                if (!this.filterCache.has(key)) {
                    this.filterCache.set(key, this.applyFilters(filters));
                }
                return this.filterCache.get(key);
            }
            
            applyFilters(filters) {
                let filteredData = [...this.rawData];
                for (const [elementId, dataCol] of Object.entries(filters)) {
                    const selectedValue = filters[elementId];
                    if (selectedValue && selectedValue !== '전체') {
                        filteredData = filteredData.filter(item => item[dataCol] == selectedValue);
                    }
                }
                return filteredData;
            }
            
            calculateAverages(data) {
                const averages = {};
                CONFIG.SCORE_COLUMNS.forEach(col => {
                    const total = data.reduce((sum, item) => sum + (item[col] || 0), 0);
                    averages[col] = data.length > 0 ? (total / data.length) : 0;
                });
                return averages;
            }
            
            clearCache() {
                this.cache.clear();
                this.filterCache.clear();
            }
        }
        """
    
    def get_chart_manager_class(self) -> str:
        """차트 관리 클래스"""
        return """
        class ChartManager {
            constructor(dataCache) {
                this.dataCache = dataCache;
                this.charts = new Map();
                this.updateQueue = [];
                this.isUpdating = false;
            }
            
            createChart(containerId, data, layout, config = {}) {
                try {
                    const container = document.getElementById(containerId);
                    if (!container) {
                        console.warn(`Container not found: ${containerId}`);
                        return;
                    }
                    
                    const mergedLayout = {
                        ...CONFIG.DEFAULT_LAYOUT,
                        ...layout,
                        font: { size: CONFIG.CHART_CONFIG.font_size }
                    };
                    
                    Plotly.react(container, data, mergedLayout, CONFIG.PLOTLY_CONFIG);
                    this.charts.set(containerId, { data, layout: mergedLayout, config });
                } catch (error) {
                    console.error(`Chart creation failed for ${containerId}:`, error);
                    this.showChartError(containerId, 'Chart creation failed');
                }
            }
            
            updateChart(containerId, newData, newLayout = {}) {
                if (this.charts.has(containerId)) {
                    const chart = this.charts.get(containerId);
                    const mergedLayout = { ...chart.layout, ...newLayout };
                    this.createChart(containerId, newData, mergedLayout, chart.config);
                }
            }
            
            showEmptyChart(containerId, message = 'No data to display') {
                const layout = {
                    height: CONFIG.CHART_CONFIG.default_height,
                    annotations: [{
                        text: message,
                        xref: 'paper',
                        yref: 'paper',
                        x: 0.5,
                        y: 0.5,
                        showarrow: false,
                        font: { size: 16, color: '#888' }
                    }],
                    xaxis: { visible: false },
                    yaxis: { visible: false }
                };
                this.createChart(containerId, [], layout);
            }
            
            showChartError(containerId, message = 'Chart error occurred') {
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = `<div class="chart-error">${message}</div>`;
                }
            }
            
            showChartLoading(containerId) {
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = '<div class="chart-loading"><div class="loading-spinner"></div></div>';
                }
            }
            
            queueUpdate(updateFunction) {
                this.updateQueue.push(updateFunction);
                if (!this.isUpdating) {
                    this.processQueue();
                }
            }
            
            async processQueue() {
                this.isUpdating = true;
                while (this.updateQueue.length > 0) {
                    const updateFunction = this.updateQueue.shift();
                    try {
                        await updateFunction();
                        await new Promise(resolve => setTimeout(resolve, 10)); // 브라우저 리플로우 방지
                    } catch (error) {
                        console.error('Chart update error:', error);
                    }
                }
                this.isUpdating = false;
            }
        }
        """
    
    def get_filter_manager_class(self) -> str:
        """필터 관리 클래스"""
        return """
        class FilterManager {
            constructor(dataCache, chartManager) {
                this.dataCache = dataCache;
                this.chartManager = chartManager;
                this.debounceTimeouts = new Map();
                this.expanderStates = new Map();
            }
            
            setupFilters() {
                this.populateBasicFilters();
                this.setupExpanderFilters();
                this.setupEventListeners();
            }
            
            populateBasicFilters() {
                const filters = CONFIG.FILTER_MAPPING;
                for (const [elementId, dataCol] of Object.entries(filters)) {
                    const select = document.getElementById(elementId);
                    if (!select) continue;
                    
                    const values = [...new Set(this.dataCache.rawData.map(item => item[dataCol]))]
                        .sort((a, b) => String(a).localeCompare(String(b), 'ko'));
                    const options = ['전체', ...values];
                    
                    select.innerHTML = options.map(opt => 
                        `<option value="${this.escapeHtml(opt)}">${this.escapeHtml(opt)}</option>`
                    ).join('');
                }
            }
            
            setupExpanderFilters() {
                // Score filters
                this.createCheckboxFilter('hospital-score-filter', CONFIG.SCORE_COLUMNS, 'hospital-score', true);
                this.createCheckboxFilter('division-score-filter', CONFIG.SCORE_COLUMNS, 'division-score', true);
                this.createCheckboxFilter('drilldown-score-filter', CONFIG.SCORE_COLUMNS, 'drilldown-score', true);
                this.createCheckboxFilter('yearly-comparison-score-filter', CONFIG.SCORE_COLUMNS, 'yearly-comparison-score', true);
                this.createCheckboxFilter('unit-comparison-score-filter', CONFIG.SCORE_COLUMNS, 'unit-comparison-score', true);
                
                // Division filters
                const allDivisions = [...new Set(this.dataCache.rawData.map(item => item['피평가부문']))]
                    .filter(d => d && d !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
                this.createCheckboxFilter('comparison-division-filter', allDivisions, 'comparison-division', false);
                
                // Sentiment filters
                this.createCheckboxFilter('review-sentiment-filter', CONFIG.SENTIMENT_ORDER, 'review-sentiment', true);
            }
            
            createCheckboxFilter(containerId, items, groupName, startChecked = true) {
                const container = document.getElementById(containerId);
                if (!container) return;
                
                container.innerHTML = '';
                
                // Select All checkbox
                const selectAllDiv = document.createElement('div');
                selectAllDiv.className = 'checkbox-item';
                selectAllDiv.innerHTML = `
                    <input type="checkbox" id="${groupName}-select-all" ${startChecked ? 'checked' : ''}>
                    <label for="${groupName}-select-all"><b>전체 선택</b></label>
                `;
                container.appendChild(selectAllDiv);
                
                // Individual checkboxes
                items.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'checkbox-item';
                    const escapedItem = this.escapeHtml(item);
                    itemDiv.innerHTML = `
                        <input type="checkbox" id="${groupName}-${escapedItem}" name="${groupName}" 
                               value="${escapedItem}" ${startChecked ? 'checked' : ''}>
                        <label for="${groupName}-${escapedItem}">${escapedItem}</label>
                    `;
                    container.appendChild(itemDiv);
                });
                
                this.setupCheckboxLogic(container, groupName, containerId);
            }
            
            setupCheckboxLogic(container, groupName, containerId) {
                const selectAllCheckbox = container.querySelector(`#${groupName}-select-all`);
                const itemCheckboxes = container.querySelectorAll(`input[name="${groupName}"]`);
                
                const updateSelectAllState = () => {
                    const allChecked = [...itemCheckboxes].every(cb => cb.checked);
                    const someChecked = [...itemCheckboxes].some(cb => cb.checked);
                    const checkedCount = [...itemCheckboxes].filter(cb => cb.checked).length;
                    
                    selectAllCheckbox.checked = allChecked;
                    selectAllCheckbox.indeterminate = !allChecked && someChecked;
                    
                    this.updateExpanderHeader(containerId, checkedCount, itemCheckboxes.length);
                };
                
                if (selectAllCheckbox) {
                    selectAllCheckbox.addEventListener('change', (e) => {
                        itemCheckboxes.forEach(checkbox => {
                            checkbox.checked = e.target.checked;
                        });
                        updateSelectAllState();
                        this.debouncedUpdate();
                    });
                }
                
                itemCheckboxes.forEach(checkbox => {
                    checkbox.addEventListener('change', () => {
                        updateSelectAllState();
                        this.debouncedUpdate();
                    });
                });
                
                updateSelectAllState();
            }
            
            updateExpanderHeader(containerId, selectedCount, totalCount) {
                const headerId = containerId.replace('-filter', '-header');
                const headerSpan = document.querySelector(`#${headerId} span:first-child`);
                if (headerSpan) {
                    if (containerId.includes('division')) {
                        headerSpan.textContent = `부문 선택 (${selectedCount}개 선택됨)`;
                    } else {
                        headerSpan.textContent = `문항 선택 (${selectedCount}개 선택됨)`;
                    }
                }
            }
            
            setupEventListeners() {
                // Basic filter change events
                Object.keys(CONFIG.FILTER_MAPPING).forEach(elementId => {
                    const element = document.getElementById(elementId);
                    if (element) {
                        element.addEventListener('change', () => this.debouncedUpdate());
                    }
                });
                
                // Department-Unit dependency
                const deptFilter = document.getElementById('department-filter');
                if (deptFilter) {
                    deptFilter.addEventListener('change', () => {
                        this.updateUnitFilter();
                        this.debouncedUpdate();
                    });
                }
            }
            
            updateUnitFilter() {
                const deptSelect = document.getElementById('department-filter');
                const unitSelect = document.getElementById('unit-filter');
                if (!deptSelect || !unitSelect) return;
                
                const selectedDept = deptSelect.value;
                const departmentUnitMap = this.getDepartmentUnitMapping();
                
                const allUnits = [...new Set(this.dataCache.rawData.map(item => item['피평가Unit']))]
                    .filter(u => u && u !== 'N/A').sort((a, b) => a.localeCompare(b, 'ko'));
                
                const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept])
                    ? allUnits
                    : departmentUnitMap[selectedDept];
                
                unitSelect.innerHTML = ['전체', ...units].map(opt => 
                    `<option value="${this.escapeHtml(opt)}">${this.escapeHtml(opt)}</option>`
                ).join('');
                unitSelect.value = '전체';
            }
            
            getDepartmentUnitMapping() {
                const mapping = {};
                this.dataCache.rawData.forEach(item => {
                    const dept = item['피평가부서'];
                    const unit = item['피평가Unit'];
                    if (dept && dept !== 'N/A' && unit && unit !== 'N/A') {
                        if (!mapping[dept]) mapping[dept] = new Set();
                        mapping[dept].add(unit);
                    }
                });
                
                for (const dept in mapping) {
                    mapping[dept] = [...mapping[dept]].sort((a, b) => 
                        String(a).localeCompare(String(b), 'ko')
                    );
                }
                return mapping;
            }
            
            debouncedUpdate() {
                clearTimeout(this.debounceTimeouts.get('main'));
                this.debounceTimeouts.set('main', setTimeout(() => {
                    this.chartManager.queueUpdate(() => window.updateAllCharts());
                }, CONFIG.JS_CONFIG.debounce_delay));
            }
            
            toggleExpander(expanderId) {
                const content = document.getElementById(expanderId);
                const arrow = document.getElementById(expanderId.replace('-expander', '-arrow'));
                
                if (!content || !arrow) return;
                
                const isExpanded = content.classList.contains('expanded');
                
                if (isExpanded) {
                    content.classList.remove('expanded');
                    arrow.classList.remove('expanded');
                    this.expanderStates.set(expanderId, false);
                } else {
                    content.classList.add('expanded');
                    arrow.classList.add('expanded');
                    this.expanderStates.set(expanderId, true);
                }
            }
            
            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            getSelectedValues(groupName) {
                return Array.from(document.querySelectorAll(`input[name="${groupName}"]:checked`))
                    .map(cb => cb.value);
            }
        }
        """
    
    def get_config_object(self) -> str:
        """JavaScript 설정 객체"""
        return f"""
        const CONFIG = {{
            SCORE_COLUMNS: {self.config.SCORE_COLUMNS},
            FILTER_MAPPING: {dict(self.config.FILTER_MAPPING)},
            SENTIMENT_ORDER: {self.config.SENTIMENT_ORDER},
            SENTIMENT_COLORS: {dict(self.config.SENTIMENT_COLORS)},
            DIVISION_COLORS: {dict(self.config.DIVISION_COLORS)},
            CHART_CONFIG: {dict(self.config.CHART_CONFIG)},
            JS_CONFIG: {dict(self.config.JS_CONFIG)},
            DEFAULT_LAYOUT: {{
                font: {{ size: {self.config.CHART_CONFIG['font_size']} }},
                hovermode: 'closest'
            }},
            PLOTLY_CONFIG: {{
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                displaylogo: false
            }}
        }};
        """
    
    def get_chart_functions(self) -> str:
        """차트 업데이트 함수들"""
        return """
        // Global variables
        let dataCache;
        let chartManager;
        let filterManager;
        
        function initializeDashboard(rawData) {
            dataCache = new DataCache(rawData);
            chartManager = new ChartManager(dataCache);
            filterManager = new FilterManager(dataCache, chartManager);
            
            filterManager.setupFilters();
            updateAllCharts();
        }
        
        function getFilteredData() {
            const filters = {};
            Object.keys(CONFIG.FILTER_MAPPING).forEach(elementId => {
                const element = document.getElementById(elementId);
                if (element) {
                    filters[CONFIG.FILTER_MAPPING[elementId]] = element.value;
                }
            });
            return dataCache.getFilteredData(filters);
        }
        
        function updateAllCharts() {
            const filteredData = getFilteredData();
            
            // Update metrics
            updateMetrics(filteredData);
            
            // Update main charts
            updateHospitalYearlyChart();
            updateDivisionYearlyChart();
            updateYearlyDivisionComparisonChart();
            updateTeamRankingChart();
            updateDrilldownChart(filteredData);
            updateYearlyComparisonChart();
            updateUnitComparisonChart();
            
            // Update analysis charts
            updateSentimentChart(filteredData);
            updateEmotionIntensityTrend();
            updateKeywordAnalysis(filteredData);
            
            // Update tables
            updateReviewsTable(filteredData);
        }
        
        function updateMetrics(data) {
            const container = document.getElementById('metrics-container');
            if (!container) return;
            
            if (data.length === 0) {
                container.innerHTML = "<p class='text-center'>선택된 조건에 해당하는 데이터가 없습니다.</p>";
                return;
            }
            
            const averages = dataCache.calculateAverages(data);
            container.innerHTML = `
                <div class="metric">
                    <div class="metric-value">${data.length.toLocaleString()}</div>
                    <div class="metric-label">응답 수</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${averages['종합 점수'].toFixed(1)}</div>
                    <div class="metric-label">종합 점수</div>
                </div>
            `;
        }
        
        function updateHospitalYearlyChart() {
            const selectedScores = filterManager.getSelectedValues('hospital-score');
            
            if (selectedScores.length === 0) {
                chartManager.showEmptyChart('hospital-yearly-chart-container', '표시할 문항을 선택해주세요.');
                return;
            }
            
            const allYears = [...new Set(dataCache.rawData.map(item => item['설문연도']))].sort();
            const traces = [];
            
            selectedScores.forEach(col => {
                const y_values = allYears.map(year => {
                    const yearData = dataCache.rawData.filter(d => d['설문연도'] === year);
                    return dataCache.calculateAverages(yearData)[col].toFixed(1);
                });
                traces.push({
                    x: allYears,
                    y: y_values,
                    name: col,
                    type: 'bar',
                    text: y_values,
                    textposition: 'outside',
                    textfont: { size: CONFIG.CHART_CONFIG.marker_font_size },
                    hovertemplate: '%{fullData.name}: %{y}<br>연도: %{x}<extra></extra>'
                });
            });
            
            // 응답수 추가
            const yearly_counts = allYears.map(year => 
                dataCache.rawData.filter(d => d['설문연도'] === year).length
            );
            traces.push({
                x: allYears,
                y: yearly_counts,
                name: '응답수',
                type: 'scatter',
                mode: 'lines+markers+text',
                line: { shape: 'spline', smoothing: 0.3, width: 3 },
                text: yearly_counts.map(count => `${count.toLocaleString()}명`),
                textposition: 'top center',
                textfont: { size: CONFIG.CHART_CONFIG.text_font_size },
                yaxis: 'y2',
                hovertemplate: '응답수: %{y}명<br>연도: %{x}<extra></extra>'
            });
            
            const layout = {
                title: '<b>[전체] 연도별 문항 점수</b>',
                barmode: 'group',
                height: CONFIG.CHART_CONFIG.large_height,
                xaxis: { type: 'category', title: '설문 연도' },
                yaxis: { title: '점수', range: CONFIG.CHART_CONFIG.score_range },
                yaxis2: {
                    title: '응답 수',
                    overlaying: 'y',
                    side: 'right',
                    showgrid: false,
                    rangemode: 'tozero',
                    tickformat: 'd'
                },
                legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }
            };
            
            chartManager.createChart('hospital-yearly-chart-container', traces, layout);
        }
        
        // Window event handlers
        window.toggleExpander = function(expanderId) {
            filterManager.toggleExpander(expanderId);
        };
        
        window.updateAllCharts = updateAllCharts;
        window.initializeDashboard = initializeDashboard;
        """
    
    def get_all_javascript(self) -> str:
        """모든 JavaScript 코드를 결합하여 반환"""
        return f"""
        <script>
        {self.get_config_object()}
        {self.get_data_cache_class()}
        {self.get_chart_manager_class()}
        {self.get_filter_manager_class()}
        {self.get_chart_functions()}
        
        // Initialize dashboard when page loads
        window.onload = function() {{
            const rawData = {'{data_json}'};
            initializeDashboard(JSON.parse(rawData));
        }};
        </script>
        """