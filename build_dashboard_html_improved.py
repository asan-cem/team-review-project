#!/usr/bin/env python3
"""
개선된 대시보드 HTML 생성기

기존 build_dashboard_html.py의 모든 기능을 모듈화된 구조로 개선
- 보안 강화 (XSS 방지, 데이터 검증)
- 성능 최적화 (캐싱, 모듈화)
- 코드 품질 향상 (타입 힌트, 에러 처리)
- 유지보수성 향상 (관심사 분리)
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# 프로젝트 모듈 임포트
from dashboard_builder import DashboardBuilder, build_dashboard
from dashboard_config import DashboardConfig
from security_utils import error_handler

def print_banner():
    """시작 배너 출력"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              서울아산병원 협업평가 대시보드 생성기                ║
    ║                     (개선된 버전 v2.0)                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_step(step_name: str, status: str = "진행중"):
    """단계별 진행 상황 출력"""
    status_emoji = {
        "진행중": "🔄",
        "완료": "✅", 
        "실패": "❌",
        "경고": "⚠️"
    }
    emoji = status_emoji.get(status, "📋")
    print(f"  {emoji} {step_name}...")

def print_result_summary(result: dict):
    """결과 요약 출력"""
    print("\n" + "="*60)
    print("📊 생성 결과 요약")
    print("="*60)
    
    if result['success']:
        print("✅ 대시보드 생성 성공!")
        
        # 파일 정보
        if 'steps' in result and 'file_saving' in result['steps']:
            file_info = result['steps']['file_saving']
            if file_info['success']:
                print(f"📁 출력 파일: {file_info['file_path']}")
                print(f"📦 파일 크기: {file_info['file_size']:,} bytes")
        
        # 데이터 정보
        if 'summary' in result and 'data_summary' in result['summary']:
            data_info = result['summary']['data_summary']
            print(f"📊 총 레코드 수: {data_info.get('total_records', 'N/A'):,}")
            print(f"📅 연도 범위: {', '.join(map(str, data_info.get('years', [])))}")
            print(f"🏢 부문 수: {len(data_info.get('divisions', []))}")
        
        # 기능 목록
        if 'summary' in result and 'features' in result['summary']:
            print("\n🎯 포함된 기능:")
            for feature in result['summary']['features']:
                print(f"  • {feature}")
        
        # 보안 기능
        if 'summary' in result and 'security_features' in result['summary']:
            print("\n🔒 보안 기능:")
            for feature in result['summary']['security_features']:
                print(f"  • {feature}")
    
    else:
        print("❌ 대시보드 생성 실패")
        if 'error' in result:
            print(f"오류: {result['error']}")
        
        if 'error_details' in result:
            error_details = result['error_details']
            if error_details['total_errors'] > 0:
                print(f"\n총 오류 수: {error_details['total_errors']}")
                print("최근 오류:")
                for error in error_details.get('recent_errors', []):
                    print(f"  • {error['type']}: {error['message']}")

def print_step_details(steps: dict):
    """단계별 상세 결과 출력"""
    print("\n" + "="*60)
    print("📋 단계별 실행 결과")
    print("="*60)
    
    step_names = {
        'data_loading': '데이터 로드',
        'data_validation': '데이터 검증',
        'data_processing': '데이터 전처리',
        'html_generation': 'HTML 생성',
        'file_saving': '파일 저장',
        'final_validation': '최종 검증'
    }
    
    for step_key, step_name in step_names.items():
        if step_key in steps:
            step_result = steps[step_key]
            status = "완료" if step_result.get('success', False) else "실패"
            print_step(f"{step_name}: {step_result.get('message', '')}", status)
            
            # 추가 정보 출력
            if step_key == 'data_loading' and step_result.get('success'):
                print(f"    레코드 수: {step_result.get('record_count', 'N/A'):,}")
            
            elif step_key == 'data_validation' and 'data_validation' in step_result:
                validation = step_result['data_validation']
                if validation.get('warnings'):
                    print(f"    경고: {len(validation['warnings'])}개")
                if validation.get('errors'):
                    print(f"    오류: {len(validation['errors'])}개")
            
            elif step_key == 'html_generation' and step_result.get('success'):
                print(f"    콘텐츠 크기: {step_result.get('content_size', 'N/A'):,} characters")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='서울아산병원 협업평가 대시보드 생성기 (개선된 버전)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python build_dashboard_html_improved.py
  python build_dashboard_html_improved.py --input data.xlsx --output dashboard.html
  python build_dashboard_html_improved.py --no-validation --verbose
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='입력 데이터 파일 경로 (기본: 설정 파일의 DATA_FILE)'
    )
    
    parser.add_argument(
        '--output', '-o', 
        type=str,
        help='출력 HTML 파일 경로 (기본: 설정 파일의 OUTPUT_FILE)'
    )
    
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='데이터 유효성 검증 건너뛰기'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세한 실행 정보 출력'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='사용자 정의 설정 파일 경로'
    )
    
    args = parser.parse_args()
    
    try:
        # 배너 출력
        print_banner()
        
        # 설정 로드
        config = DashboardConfig()
        if args.config and Path(args.config).exists():
            print(f"📋 사용자 정의 설정 파일 로드: {args.config}")
        
        # 입력 파일 확인
        input_file = args.input or config.DATA_FILE
        if not Path(input_file).exists():
            print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
            print(f"현재 작업 디렉토리: {Path.cwd()}")
            print("사용 가능한 Excel 파일:")
            for excel_file in Path.cwd().glob("*.xlsx"):
                print(f"  • {excel_file.name}")
            return 1
        
        # 대시보드 생성
        print("🚀 대시보드 생성을 시작합니다...\n")
        
        result = build_dashboard(
            input_file=input_file,
            output_file=args.output,
            config=config,
            validate_data=not args.no_validation
        )
        
        # 결과 출력
        if args.verbose and 'steps' in result:
            print_step_details(result['steps'])
        
        print_result_summary(result)
        
        # 종료 코드 반환
        return 0 if result['success'] else 1
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        return 1
    
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        error_handler.log_error(e, "Main execution")
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        return 1
    
    finally:
        # 에러 요약 출력 (verbose 모드에서만)
        if args.verbose:
            error_summary = error_handler.get_error_summary()
            if error_summary['total_errors'] > 0:
                print(f"\n⚠️ 총 {error_summary['total_errors']}개의 오류가 로깅되었습니다.")

def quick_build():
    """빠른 빌드 함수 (다른 스크립트에서 호출용)"""
    print_banner()
    print("🚀 빠른 대시보드 생성...")
    
    result = build_dashboard()
    
    if result['success']:
        print("✅ 대시보드 생성 완료!")
        if 'steps' in result and 'file_saving' in result['steps']:
            file_info = result['steps']['file_saving']
            if file_info['success']:
                print(f"📁 파일 위치: {file_info['file_path']}")
    else:
        print("❌ 대시보드 생성 실패")
        if 'error' in result:
            print(f"오류: {result['error']}")
    
    return result

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)