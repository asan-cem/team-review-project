"""
보안 및 안전성 유틸리티 모듈
"""
import html
import re
import logging
from typing import Any, Dict, List, Optional, Union
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SecurityUtils:
    """보안 관련 유틸리티 클래스"""
    
    # XSS 방지를 위한 위험한 태그 패턴
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'on\w+\s*=',  # onclick, onload 등
    ]
    
    @classmethod
    def sanitize_html(cls, text: Union[str, Any]) -> str:
        """HTML 문자열을 안전하게 이스케이프 처리"""
        if not isinstance(text, str):
            text = str(text)
        
        # HTML 이스케이프
        sanitized = html.escape(text, quote=True)
        
        # 위험한 패턴 제거
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized
    
    @classmethod
    def sanitize_json_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 데이터의 문자열 필드를 안전하게 처리"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_html(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_html(item) if isinstance(item, str) else item for item in value]
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_json_data(value)
            else:
                sanitized[key] = value
                
        return sanitized
    
    @classmethod
    def validate_file_path(cls, file_path: str) -> bool:
        """파일 경로의 안전성 검증"""
        if not isinstance(file_path, str):
            return False
        
        # 경로 탐색 공격 방지
        dangerous_patterns = ['../', '..\\', '/etc/', '/proc/', '/sys/', 'C:\\Windows\\']
        
        for pattern in dangerous_patterns:
            if pattern in file_path:
                logger.warning(f"Dangerous path pattern detected: {pattern} in {file_path}")
                return False
        
        # 허용된 확장자 검증
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.html', '.json']
        if not any(file_path.lower().endswith(ext) for ext in allowed_extensions):
            logger.warning(f"Invalid file extension: {file_path}")
            return False
        
        return True
    
    @classmethod
    def generate_content_hash(cls, content: str) -> str:
        """콘텐츠의 해시값 생성 (무결성 검증용)"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @classmethod
    def validate_data_integrity(cls, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """데이터 무결성 검증"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {
                'total_records': len(data),
                'valid_records': 0,
                'invalid_records': 0,
                'suspicious_records': []
            }
        }
        
        for i, record in enumerate(data):
            record_issues = []
            
            # 필수 필드 검증
            required_fields = ['설문연도', '피평가부문', '종합 점수']
            for field in required_fields:
                if field not in record or record[field] is None:
                    record_issues.append(f"Missing required field: {field}")
            
            # 점수 범위 검증
            score_fields = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수']
            for field in score_fields:
                if field in record and record[field] is not None:
                    try:
                        score = float(record[field])
                        if not (0 <= score <= 100):
                            record_issues.append(f"Score out of range: {field} = {score}")
                    except (ValueError, TypeError):
                        record_issues.append(f"Invalid score format: {field} = {record[field]}")
            
            # 의심스러운 텍스트 패턴 검증
            text_fields = ['정제된_텍스트', '협업후기']
            for field in text_fields:
                if field in record and isinstance(record[field], str):
                    text = record[field]
                    if cls._contains_suspicious_content(text):
                        record_issues.append(f"Suspicious content in {field}")
                        validation_result['stats']['suspicious_records'].append({
                            'index': i,
                            'field': field,
                            'content_preview': text[:100] + '...' if len(text) > 100 else text
                        })
            
            if record_issues:
                validation_result['stats']['invalid_records'] += 1
                validation_result['errors'].extend([f"Record {i}: {issue}" for issue in record_issues])
            else:
                validation_result['stats']['valid_records'] += 1
        
        # 전체 유효성 판단
        if validation_result['stats']['invalid_records'] > 0:
            validation_result['is_valid'] = False
        
        # 의심스러운 레코드가 전체의 10% 이상이면 경고
        if len(validation_result['stats']['suspicious_records']) > len(data) * 0.1:
            validation_result['warnings'].append("High number of suspicious records detected")
        
        return validation_result
    
    @classmethod
    def _contains_suspicious_content(cls, text: str) -> bool:
        """텍스트에 의심스러운 내용이 포함되어 있는지 검사"""
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'eval\s*\(',
            r'document\.',
            r'window\.',
            r'alert\s*\(',
            r'confirm\s*\(',
            r'prompt\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def create_csp_header(cls) -> str:
        """Content Security Policy 헤더 생성"""
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.plot.ly",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
        ]
        
        return "; ".join(csp_directives)

class ErrorHandler:
    """에러 처리 클래스"""
    
    def __init__(self):
        self.error_log = []
    
    def log_error(self, error: Exception, context: str = "", severity: str = "ERROR"):
        """에러 로깅"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'severity': severity
        }
        
        self.error_log.append(error_info)
        logger.error(f"{severity}: {context} - {error}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """에러 요약 정보 반환"""
        if not self.error_log:
            return {'total_errors': 0, 'error_types': {}, 'recent_errors': []}
        
        error_types = {}
        for error in self.error_log:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_log),
            'error_types': error_types,
            'recent_errors': self.error_log[-5:],  # 최근 5개 에러
            'last_error_time': self.error_log[-1]['timestamp'] if self.error_log else None
        }
    
    def clear_errors(self):
        """에러 로그 초기화"""
        self.error_log.clear()

class DataValidator:
    """데이터 유효성 검증 클래스"""
    
    @staticmethod
    def validate_score_range(value: Any, min_val: float = 0, max_val: float = 100) -> bool:
        """점수 범위 검증"""
        try:
            num_val = float(value)
            return min_val <= num_val <= max_val
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_year(value: Any) -> bool:
        """연도 유효성 검증"""
        try:
            year = int(value)
            return 2000 <= year <= 2030  # 합리적인 연도 범위
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_text_length(value: Any, max_length: int = 10000) -> bool:
        """텍스트 길이 검증"""
        if not isinstance(value, str):
            return False
        return len(value) <= max_length
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """필수 필드 검증"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        return missing_fields

# 전역 에러 핸들러 인스턴스
error_handler = ErrorHandler()