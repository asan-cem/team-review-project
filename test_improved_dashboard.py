#!/usr/bin/env python3
"""
개선된 대시보드 시스템 테스트 스크립트
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 테스트 대상 모듈들
from dashboard_config import DashboardConfig
from data_processor import DataProcessor
from dashboard_templates import DashboardTemplates
from dashboard_javascript import DashboardJavaScript
from dashboard_styles import DashboardStyles
from security_utils import SecurityUtils, DataValidator
from dashboard_builder import DashboardBuilder

class TestDashboardConfig(unittest.TestCase):
    """DashboardConfig 테스트"""
    
    def test_default_values(self):
        """기본값 테스트"""
        config = DashboardConfig()
        
        self.assertEqual(config.DATA_FILE, "설문조사_전처리데이터_20250620_0731_processed.xlsx")
        self.assertEqual(config.OUTPUT_FILE, "서울아산병원 협업평가 대시보드.html")
        self.assertEqual(len(config.SCORE_COLUMNS), 6)
        self.assertIn('존중배려', config.SCORE_COLUMNS)
    
    def test_export_columns(self):
        """내보내기 컬럼 테스트"""
        config = DashboardConfig()
        export_cols = config.get_export_columns()
        
        self.assertIn('설문연도', export_cols)
        self.assertIn('종합 점수', export_cols)
        self.assertGreater(len(export_cols), 5)

class TestDataProcessor(unittest.TestCase):
    """DataProcessor 테스트"""
    
    def setUp(self):
        self.config = DashboardConfig()
        self.processor = DataProcessor(self.config)
    
    def test_safe_literal_eval(self):
        """안전한 리터럴 평가 테스트"""
        # 정상 케이스
        result = self.processor.safe_literal_eval("['test', 'data']")
        self.assertEqual(result, ['test', 'data'])
        
        # 잘못된 형식
        result = self.processor.safe_literal_eval("invalid")
        self.assertEqual(result, [])
        
        # 비문자열
        result = self.processor.safe_literal_eval(123)
        self.assertEqual(result, [])
    
    def test_cache_functionality(self):
        """캐시 기능 테스트"""
        self.processor._cache['test'] = 'value'
        self.assertEqual(self.processor._cache['test'], 'value')
        
        self.processor.clear_cache()
        self.assertEqual(len(self.processor._cache), 0)

class TestSecurityUtils(unittest.TestCase):
    """SecurityUtils 테스트"""
    
    def test_sanitize_html(self):
        """HTML 새니타이징 테스트"""
        # 기본 이스케이프
        result = SecurityUtils.sanitize_html("<script>alert('xss')</script>")
        self.assertNotIn('<script>', result)
        
        # 일반 텍스트
        result = SecurityUtils.sanitize_html("안전한 텍스트")
        self.assertEqual(result, "안전한 텍스트")
        
        # HTML 엔티티
        result = SecurityUtils.sanitize_html("A&B<C>D")
        self.assertIn('&lt;', result)
        self.assertIn('&gt;', result)
    
    def test_validate_file_path(self):
        """파일 경로 검증 테스트"""
        # 안전한 경로
        self.assertTrue(SecurityUtils.validate_file_path("data.xlsx"))
        self.assertTrue(SecurityUtils.validate_file_path("./report.html"))
        
        # 위험한 경로
        self.assertFalse(SecurityUtils.validate_file_path("../../../etc/passwd"))
        self.assertFalse(SecurityUtils.validate_file_path("C:\\Windows\\system32\\config"))
        
        # 잘못된 확장자
        self.assertFalse(SecurityUtils.validate_file_path("malicious.exe"))
    
    def test_sanitize_json_data(self):
        """JSON 데이터 새니타이징 테스트"""
        data = {
            'text': '<script>alert("xss")</script>',
            'number': 123,
            'list': ['<b>bold</b>', 'normal'],
            'nested': {'html': '<div>content</div>'}
        }
        
        sanitized = SecurityUtils.sanitize_json_data(data)
        
        self.assertNotIn('<script>', sanitized['text'])
        self.assertEqual(sanitized['number'], 123)
        self.assertNotIn('<b>', sanitized['list'][0])
        self.assertNotIn('<div>', sanitized['nested']['html'])

class TestDataValidator(unittest.TestCase):
    """DataValidator 테스트"""
    
    def test_validate_score_range(self):
        """점수 범위 검증 테스트"""
        self.assertTrue(DataValidator.validate_score_range(50))
        self.assertTrue(DataValidator.validate_score_range(0))
        self.assertTrue(DataValidator.validate_score_range(100))
        
        self.assertFalse(DataValidator.validate_score_range(-1))
        self.assertFalse(DataValidator.validate_score_range(101))
        self.assertFalse(DataValidator.validate_score_range("invalid"))
    
    def test_validate_year(self):
        """연도 검증 테스트"""
        self.assertTrue(DataValidator.validate_year(2023))
        self.assertTrue(DataValidator.validate_year("2024"))
        
        self.assertFalse(DataValidator.validate_year(1999))
        self.assertFalse(DataValidator.validate_year(2031))
        self.assertFalse(DataValidator.validate_year("invalid"))
    
    def test_validate_required_fields(self):
        """필수 필드 검증 테스트"""
        data = {'field1': 'value1', 'field2': None, 'field3': ''}
        required = ['field1', 'field2', 'field3', 'field4']
        
        missing = DataValidator.validate_required_fields(data, required)
        
        self.assertIn('field2', missing)  # None
        self.assertIn('field3', missing)  # 빈 문자열
        self.assertIn('field4', missing)  # 존재하지 않음
        self.assertNotIn('field1', missing)  # 정상

class TestDashboardTemplates(unittest.TestCase):
    """DashboardTemplates 테스트"""
    
    def setUp(self):
        self.templates = DashboardTemplates()
    
    def test_escape_html(self):
        """HTML 이스케이프 테스트"""
        result = self.templates.escape_html("<div>test</div>")
        self.assertEqual(result, "&lt;div&gt;test&lt;/div&gt;")
    
    def test_html_head_generation(self):
        """HTML head 생성 테스트"""
        head = self.templates.get_html_head()
        
        self.assertIn('<head>', head)
        self.assertIn('charset="utf-8"', head)
        self.assertIn('plotly', head.lower())
        self.assertIn('<style>', head)
    
    def test_render_dashboard(self):
        """대시보드 렌더링 테스트"""
        test_data = json.dumps([{'test': 'data'}])
        html = self.templates.render_dashboard(test_data)
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('<html lang="ko">', html)
        self.assertIn('서울아산병원', html)
        self.assertIn('</html>', html)

class TestDashboardBuilder(unittest.TestCase):
    """DashboardBuilder 테스트"""
    
    def setUp(self):
        self.config = DashboardConfig()
        self.builder = DashboardBuilder(self.config)
    
    def test_initialization(self):
        """초기화 테스트"""
        self.assertIsNotNone(self.builder.config)
        self.assertIsNotNone(self.builder.data_processor)
        self.assertIsNotNone(self.builder.templates)
    
    def test_get_system_info(self):
        """시스템 정보 조회 테스트"""
        info = self.builder.get_system_info()
        
        self.assertIn('config', info)
        self.assertIn('components', info)
        self.assertIn('error_summary', info)
        
        self.assertIn('data_file', info['config'])
        self.assertIn('output_file', info['config'])
    
    def test_clear_cache(self):
        """캐시 정리 테스트"""
        # 예외 없이 실행되어야 함
        self.builder.clear_cache()

class IntegrationTest(unittest.TestCase):
    """통합 테스트"""
    
    def test_full_pipeline_with_mock_data(self):
        """모의 데이터를 사용한 전체 파이프라인 테스트"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_input = temp_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_output = temp_file.name
        
        try:
            # DataProcessor.load_data를 모킹
            with patch.object(DataProcessor, 'load_data') as mock_load:
                # 모의 데이터프레임 생성
                import pandas as pd
                mock_df = pd.DataFrame({
                    '설문연도': ['2023', '2024'],
                    '피평가부문': ['진료부문', '간호부문'],
                    '피평가부서': ['내과', '외과'],
                    '피평가Unit': ['Unit1', 'Unit2'],
                    '존중배려': [85.0, 90.0],
                    '정보공유': [80.0, 88.0],
                    '명확처리': [82.0, 87.0],
                    '태도개선': [79.0, 85.0],
                    '전반만족': [83.0, 89.0],
                    '종합 점수': [81.8, 87.8],
                    '정제된_텍스트': ['좋은 협업이었습니다', '매우 만족스러웠습니다'],
                    '감정_분류': ['긍정', '긍정'],
                    '감정_강도_점수': [8.0, 9.0],
                    '핵심_키워드': [['협업', '만족'], ['우수', '추천']]
                })
                
                # DataProcessor 인스턴스에 모의 데이터 설정
                def mock_load_side_effect(*args, **kwargs):
                    processor = args[0]  # self
                    processor.data = mock_df
                    return mock_df
                
                mock_load.side_effect = mock_load_side_effect
                
                # 대시보드 빌더 생성 및 실행
                builder = DashboardBuilder()
                result = builder.build_dashboard(
                    input_file=temp_input,
                    output_file=temp_output,
                    validate_data=False  # 검증 건너뛰기 (모의 데이터이므로)
                )
                
                # 결과 검증
                self.assertTrue(result['success'], f"Build failed: {result.get('error', 'Unknown error')}")
                self.assertIn('steps', result)
                self.assertTrue(Path(temp_output).exists())
                
                # HTML 파일 내용 검증
                with open(temp_output, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                self.assertIn('<!DOCTYPE html>', html_content)
                self.assertIn('서울아산병원', html_content)
                self.assertIn('협업평가', html_content)
        
        finally:
            # 임시 파일 정리
            for temp_file in [temp_input, temp_output]:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()

def run_tests():
    """테스트 실행 함수"""
    print("="*60)
    print("🧪 개선된 대시보드 시스템 테스트 시작")
    print("="*60)
    
    # 테스트 스위트 생성
    test_classes = [
        TestDashboardConfig,
        TestDataProcessor,
        TestSecurityUtils,
        TestDataValidator,
        TestDashboardTemplates,
        TestDashboardBuilder,
        IntegrationTest
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    print(f"총 테스트 수: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"에러: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  • {test}")
    
    if result.errors:
        print("\n💥 에러가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  • {test}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n성공률: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 모든 테스트가 통과했습니다!")
    elif success_rate >= 80:
        print("✅ 대부분의 테스트가 통과했습니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인하세요.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)