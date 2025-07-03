"""
메인 대시보드 빌더 클래스
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from dashboard_config import DashboardConfig
from data_processor import DataProcessor
from dashboard_templates import DashboardTemplates
from security_utils import SecurityUtils, ErrorHandler, error_handler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardBuilder:
    """대시보드 생성을 담당하는 메인 클래스"""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        DashboardBuilder 초기화
        
        Args:
            config: 대시보드 설정 객체. None이면 기본값 사용
        """
        self.config = config or DashboardConfig()
        self.data_processor = DataProcessor(self.config)
        self.templates = DashboardTemplates(self.config)
        self.error_handler = error_handler
        
        logger.info("DashboardBuilder 초기화 완료")
    
    def build_dashboard(
        self, 
        input_file: Optional[str] = None, 
        output_file: Optional[str] = None,
        validate_data: bool = True
    ) -> Dict[str, Any]:
        """
        대시보드 생성
        
        Args:
            input_file: 입력 데이터 파일 경로
            output_file: 출력 HTML 파일 경로
            validate_data: 데이터 유효성 검증 여부
            
        Returns:
            생성 결과 정보
        """
        try:
            logger.info("🚀 대시보드 생성 시작")
            
            # 파일 경로 설정 및 검증
            input_file = input_file or self.config.DATA_FILE
            output_file = output_file or self.config.OUTPUT_FILE
            
            if not SecurityUtils.validate_file_path(input_file):
                raise ValueError(f"Invalid input file path: {input_file}")
            
            if not SecurityUtils.validate_file_path(output_file):
                raise ValueError(f"Invalid output file path: {output_file}")
            
            # 단계별 실행
            result = {
                'success': False,
                'input_file': input_file,
                'output_file': output_file,
                'steps': {}
            }
            
            # 1. 데이터 로드
            result['steps']['data_loading'] = self._load_data_step(input_file)
            
            # 2. 데이터 검증
            if validate_data:
                result['steps']['data_validation'] = self._validate_data_step()
            
            # 3. 데이터 전처리
            result['steps']['data_processing'] = self._process_data_step()
            
            # 4. HTML 생성
            result['steps']['html_generation'] = self._generate_html_step()
            
            # 5. 파일 저장
            result['steps']['file_saving'] = self._save_file_step(output_file)
            
            # 6. 최종 검증
            result['steps']['final_validation'] = self._final_validation_step(output_file)
            
            result['success'] = True
            result['summary'] = self._generate_summary()
            
            logger.info("✅ 대시보드 생성 완료")
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, "Dashboard build process")
            result['success'] = False
            result['error'] = str(e)
            result['error_details'] = self.error_handler.get_error_summary()
            
            logger.error(f"❌ 대시보드 생성 실패: {e}")
            return result
    
    def _load_data_step(self, input_file: str) -> Dict[str, Any]:
        """데이터 로드 단계"""
        try:
            logger.info(f"📊 데이터 로드: {input_file}")
            
            if not Path(input_file).exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
            
            self.data_processor.load_data(input_file)
            
            return {
                'success': True,
                'message': 'Data loaded successfully',
                'record_count': len(self.data_processor.data)
            }
        except Exception as e:
            self.error_handler.log_error(e, "Data loading step")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_data_step(self) -> Dict[str, Any]:
        """데이터 검증 단계"""
        try:
            logger.info("🔍 데이터 유효성 검증")
            
            validation_result = self.data_processor.validate_data()
            
            if not validation_result['valid']:
                logger.warning(f"Data validation issues: {validation_result['errors']}")
            
            # 보안 검증
            data_records = self.data_processor.data.to_dict('records')
            security_validation = SecurityUtils.validate_data_integrity(data_records)
            
            return {
                'success': validation_result['valid'],
                'data_validation': validation_result,
                'security_validation': security_validation
            }
        except Exception as e:
            self.error_handler.log_error(e, "Data validation step")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_data_step(self) -> Dict[str, Any]:
        """데이터 전처리 단계"""
        try:
            logger.info("⚙️ 데이터 전처리")
            
            # JSON 데이터 생성
            json_data = self.data_processor.get_export_data()
            
            # 보안 처리
            import json
            data_dict = json.loads(json_data)
            sanitized_data = [SecurityUtils.sanitize_json_data(record) for record in data_dict]
            self.processed_json = json.dumps(sanitized_data, ensure_ascii=False)
            
            return {
                'success': True,
                'message': 'Data processed successfully',
                'export_record_count': len(sanitized_data)
            }
        except Exception as e:
            self.error_handler.log_error(e, "Data processing step")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_html_step(self) -> Dict[str, Any]:
        """HTML 생성 단계"""
        try:
            logger.info("🏗️ HTML 생성")
            
            self.html_content = self.templates.render_dashboard(self.processed_json)
            
            # HTML 콘텐츠 해시 생성 (무결성 검증용)
            content_hash = SecurityUtils.generate_content_hash(self.html_content)
            
            return {
                'success': True,
                'message': 'HTML generated successfully',
                'content_size': len(self.html_content),
                'content_hash': content_hash
            }
        except Exception as e:
            self.error_handler.log_error(e, "HTML generation step")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_file_step(self, output_file: str) -> Dict[str, Any]:
        """파일 저장 단계"""
        try:
            logger.info(f"💾 파일 저장: {output_file}")
            
            # 출력 디렉토리 생성
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # HTML 파일 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self.html_content)
            
            # 파일 크기 확인
            file_size = output_path.stat().st_size
            
            return {
                'success': True,
                'message': f'File saved successfully to {output_file}',
                'file_size': file_size,
                'file_path': str(output_path.absolute())
            }
        except Exception as e:
            self.error_handler.log_error(e, "File saving step")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _final_validation_step(self, output_file: str) -> Dict[str, Any]:
        """최종 검증 단계"""
        try:
            logger.info("✅ 최종 검증")
            
            output_path = Path(output_file)
            
            # 파일 존재 확인
            if not output_path.exists():
                raise FileNotFoundError(f"Output file was not created: {output_file}")
            
            # 파일 내용 검증
            with open(output_file, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            
            # 기본 HTML 구조 확인
            required_elements = ['<!DOCTYPE html>', '<html', '<head>', '<body>', '</html>']
            missing_elements = [elem for elem in required_elements if elem not in saved_content]
            
            if missing_elements:
                raise ValueError(f"Invalid HTML structure. Missing: {missing_elements}")
            
            return {
                'success': True,
                'message': 'Final validation passed',
                'file_exists': True,
                'html_structure_valid': len(missing_elements) == 0,
                'content_length': len(saved_content)
            }
        except Exception as e:
            self.error_handler.log_error(e, "Final validation step")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """생성 결과 요약"""
        try:
            stats = self.data_processor.get_summary_stats()
            
            return {
                'data_summary': stats,
                'generation_time': 'Generated successfully',
                'features': [
                    '연도별 문항 점수 분석',
                    '부문별 비교 분석',
                    '팀 순위 분석',
                    '감정 분석',
                    '키워드 분석',
                    '상세 드릴다운 분석'
                ],
                'security_features': [
                    'XSS 방지 처리',
                    '데이터 유효성 검증',
                    '파일 경로 검증',
                    '콘텐츠 무결성 확인'
                ]
            }
        except Exception as e:
            self.error_handler.log_error(e, "Summary generation")
            return {
                'error': f'Summary generation failed: {str(e)}'
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """시스템 정보 반환"""
        return {
            'config': {
                'data_file': self.config.DATA_FILE,
                'output_file': self.config.OUTPUT_FILE,
                'score_columns': self.config.SCORE_COLUMNS,
                'chart_config': self.config.CHART_CONFIG
            },
            'components': {
                'data_processor': type(self.data_processor).__name__,
                'templates': type(self.templates).__name__,
                'error_handler': type(self.error_handler).__name__
            },
            'error_summary': self.error_handler.get_error_summary()
        }
    
    def clear_cache(self):
        """캐시 정리"""
        if hasattr(self.data_processor, 'clear_cache'):
            self.data_processor.clear_cache()
        self.error_handler.clear_errors()
        logger.info("Cache cleared")

# 편의 함수
def build_dashboard(
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
    config: Optional[DashboardConfig] = None,
    validate_data: bool = True
) -> Dict[str, Any]:
    """
    대시보드 생성 편의 함수
    
    Args:
        input_file: 입력 파일 경로
        output_file: 출력 파일 경로
        config: 설정 객체
        validate_data: 데이터 검증 여부
        
    Returns:
        생성 결과
    """
    builder = DashboardBuilder(config)
    return builder.build_dashboard(input_file, output_file, validate_data)