"""
대시보드 CSS 스타일 관리 모듈
"""
from dashboard_config import DashboardConfig

class DashboardStyles:
    """대시보드 CSS 스타일을 관리하는 클래스"""
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
    
    def get_base_styles(self) -> str:
        """기본 스타일 반환"""
        return """
        body { 
            font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 0; 
            background-color: #f8f9fa; 
            color: #343a40; 
            font-size: 16px;
            line-height: 1.6;
        }
        
        * {
            box-sizing: border-box;
        }
        
        .container { 
            max-width: 1400px; 
            margin: auto; 
            padding: 20px; 
        }
        
        .header { 
            background: linear-gradient(90deg, #4a69bd, #6a89cc); 
            color: white; 
            padding: 25px; 
            text-align: center; 
            border-radius: 0 0 10px 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1, h2, h3 { 
            margin: 0; 
            padding: 0; 
        }
        
        h1 {
            font-size: 2.5em;
            font-weight: 300;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        
        h2 { 
            color: #4a69bd; 
            border-bottom: 3px solid #6a89cc; 
            padding-bottom: 10px; 
            margin-top: 40px; 
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 600;
        }
        
        h3 { 
            color: #555; 
            margin-top: 30px; 
            margin-bottom: 15px;
            font-size: 1.4em;
            font-weight: 500;
        }
        """
    
    def get_section_styles(self) -> str:
        """섹션 관련 스타일"""
        return """
        .section { 
            background: white; 
            padding: 25px; 
            border-radius: 8px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.05); 
            margin-bottom: 30px;
            transition: box-shadow 0.3s ease;
        }
        
        .section:hover {
            box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .section-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background-color: #4a69bd;
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #3d5aa0;
        }
        
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background-color: #5a6268;
        }
        """
    
    def get_filter_styles(self) -> str:
        """필터 관련 스타일"""
        return """
        .filters, .trend-filters { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 20px; 
            align-items: flex-end; 
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .filter-group { 
            display: flex; 
            flex-direction: column;
            min-width: 200px;
        }
        
        .filter-group label { 
            margin-bottom: 5px; 
            font-weight: 600; 
            font-size: 0.9em;
            color: #495057;
        }
        
        .filter-group select, .filter-group input { 
            padding: 10px 12px; 
            border-radius: 6px; 
            border: 1px solid #ced4da;
            font-size: 14px;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        .filter-group select:focus, .filter-group input:focus {
            outline: none;
            border-color: #4a69bd;
            box-shadow: 0 0 0 2px rgba(74, 105, 189, 0.2);
        }
        
        .filter-group select:hover, .filter-group input:hover {
            border-color: #adb5bd;
        }
        """
    
    def get_expander_styles(self) -> str:
        """확장 가능한 필터 스타일"""
        return """
        .expander-container { 
            border: 1px solid #ced4da; 
            border-radius: 6px; 
            background-color: white; 
            min-width: 200px; 
            max-width: 300px; 
            position: relative;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .expander-header { 
            padding: 10px 12px; 
            background-color: #f8f9fa; 
            cursor: pointer; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-radius: 6px; 
            user-select: none; 
            font-size: 14px;
            font-weight: 500;
            transition: background-color 0.2s ease;
        }
        
        .expander-header:hover { 
            background-color: #e9ecef; 
        }
        
        .expander-arrow { 
            transition: transform 0.3s ease; 
            font-size: 12px;
            color: #6c757d;
        }
        
        .expander-arrow.expanded { 
            transform: rotate(180deg); 
        }
        
        .expander-content { 
            padding: 8px; 
            display: none; 
            max-height: 250px; 
            overflow-y: auto; 
            position: absolute; 
            top: 100%; 
            left: 0; 
            width: 100%; 
            background-color: white; 
            border: 1px solid #ced4da; 
            border-top: none; 
            border-radius: 0 0 6px 6px; 
            z-index: 1000; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .expander-content.expanded { 
            display: block; 
        }
        
        .checkbox-item { 
            display: flex; 
            align-items: center; 
            padding: 6px 4px; 
            border-radius: 4px;
            transition: background-color 0.2s ease;
        }
        
        .checkbox-item:hover { 
            background-color: #f8f9fa; 
        }
        
        .checkbox-item input[type="checkbox"] { 
            width: 16px; 
            height: 16px; 
            margin-right: 8px;
            cursor: pointer;
        }
        
        .checkbox-item label { 
            cursor: pointer; 
            font-weight: normal; 
            font-size: 13px; 
            line-height: 1.3; 
            margin: 0;
            flex: 1;
        }
        
        /* 스크롤바 스타일링 */
        .expander-content::-webkit-scrollbar {
            width: 6px;
        }
        
        .expander-content::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }
        
        .expander-content::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        
        .expander-content::-webkit-scrollbar-thumb:hover {
            background: #a1a1a1;
        }
        """
    
    def get_metrics_styles(self) -> str:
        """메트릭 관련 스타일"""
        return """
        #metrics-container { 
            display: flex; 
            gap: 30px; 
            margin-top: 20px; 
            text-align: center; 
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .metric { 
            background: linear-gradient(135deg, #e9ecef, #f8f9fa);
            padding: 20px; 
            border-radius: 12px; 
            flex: 1;
            min-width: 150px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .metric-value { 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #4a69bd;
            margin-bottom: 5px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .metric-label { 
            font-size: 0.95em; 
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        """
    
    def get_table_styles(self) -> str:
        """테이블 관련 스타일"""
        return """
        #reviews-table-container, #keyword-reviews-table-container { 
            max-height: 450px; 
            overflow-y: auto; 
            margin-top: 20px; 
            border: 1px solid #dee2e6; 
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        #reviews-table, #keyword-reviews-table { 
            width: 100%; 
            border-collapse: collapse;
            font-size: 14px;
        }
        
        #reviews-table th, #reviews-table td, 
        #keyword-reviews-table th, #keyword-reviews-table td { 
            padding: 12px 15px; 
            border-bottom: 1px solid #dee2e6; 
            text-align: left;
            vertical-align: top;
        }
        
        #reviews-table th, #keyword-reviews-table th { 
            background-color: #f8f9fa; 
            position: sticky; 
            top: 0;
            font-weight: 600;
            color: #495057;
            z-index: 10;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        #reviews-table tr:last-child td, 
        #keyword-reviews-table tr:last-child td { 
            border-bottom: none; 
        }
        
        #reviews-table tbody tr:hover,
        #keyword-reviews-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        /* 테이블 스크롤바 스타일링 */
        #reviews-table-container::-webkit-scrollbar,
        #keyword-reviews-table-container::-webkit-scrollbar {
            width: 8px;
        }
        
        #reviews-table-container::-webkit-scrollbar-track,
        #keyword-reviews-table-container::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        #reviews-table-container::-webkit-scrollbar-thumb,
        #keyword-reviews-table-container::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 4px;
        }
        """
    
    def get_chart_styles(self) -> str:
        """차트 관련 스타일"""
        return """
        .keyword-charts-container { 
            display: flex; 
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .keyword-chart { 
            flex: 1;
            min-width: 300px;
        }
        
        .chart-container {
            margin: 20px 0;
            padding: 15px;
            background-color: #fafafa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .chart-loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
            font-size: 16px;
            color: #6c757d;
        }
        
        .chart-error {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
            font-size: 16px;
            color: #dc3545;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
        }
        """
    
    def get_responsive_styles(self) -> str:
        """반응형 스타일"""
        return """
        /* 태블릿 */
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .filters {
                flex-direction: column;
                gap: 15px;
            }
            
            .filter-group {
                min-width: auto;
                width: 100%;
            }
            
            #metrics-container {
                flex-direction: column;
                gap: 15px;
            }
            
            .keyword-charts-container {
                flex-direction: column;
            }
            
            .keyword-chart {
                min-width: auto;
            }
            
            h1 {
                font-size: 2em;
            }
            
            h2 {
                font-size: 1.5em;
            }
        }
        
        /* 모바일 */
        @media (max-width: 480px) {
            .container {
                padding: 10px;
            }
            
            .section {
                padding: 15px;
            }
            
            .header {
                padding: 20px 15px;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            h2 {
                font-size: 1.3em;
            }
            
            .metric {
                padding: 15px;
            }
            
            .metric-value {
                font-size: 2em;
            }
            
            #reviews-table th, #reviews-table td,
            #keyword-reviews-table th, #keyword-reviews-table td {
                padding: 8px 10px;
                font-size: 13px;
            }
        }
        """
    
    def get_utility_styles(self) -> str:
        """유틸리티 스타일"""
        return """
        .text-center { text-align: center; }
        .text-left { text-align: left; }
        .text-right { text-align: right; }
        
        .mb-0 { margin-bottom: 0; }
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-3 { margin-bottom: 1rem; }
        .mb-4 { margin-bottom: 1.5rem; }
        .mb-5 { margin-bottom: 3rem; }
        
        .mt-0 { margin-top: 0; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .mt-3 { margin-top: 1rem; }
        .mt-4 { margin-top: 1.5rem; }
        .mt-5 { margin-top: 3rem; }
        
        .p-0 { padding: 0; }
        .p-1 { padding: 0.25rem; }
        .p-2 { padding: 0.5rem; }
        .p-3 { padding: 1rem; }
        .p-4 { padding: 1.5rem; }
        .p-5 { padding: 3rem; }
        
        .d-none { display: none; }
        .d-block { display: block; }
        .d-flex { display: flex; }
        .d-inline { display: inline; }
        .d-inline-block { display: inline-block; }
        
        .fade-in {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .loading-spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #4a69bd;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        """
    
    def get_all_styles(self) -> str:
        """모든 스타일을 결합하여 반환"""
        return f"""
        <style>
        {self.get_base_styles()}
        {self.get_section_styles()}
        {self.get_filter_styles()}
        {self.get_expander_styles()}
        {self.get_metrics_styles()}
        {self.get_table_styles()}
        {self.get_chart_styles()}
        {self.get_responsive_styles()}
        {self.get_utility_styles()}
        </style>
        """