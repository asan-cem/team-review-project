#!/usr/bin/env python3
"""
전체 부서 보고서를 단독 실행 가능한 HTML로 변환하는 스크립트
plotly.min.js를 각 HTML 파일에 임베드합니다.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re


def create_standalone_html(html_path, plotly_js_path, output_path):
    """
    HTML 파일에 plotly.js를 임베드하여 단독 실행 가능한 파일 생성
    
    Args:
        html_path: 원본 HTML 파일 경로
        plotly_js_path: plotly.min.js 파일 경로
        output_path: 출력 HTML 파일 경로
    """
    # HTML 파일 읽기
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # plotly.min.js 읽기
    with open(plotly_js_path, 'r', encoding='utf-8') as f:
        plotly_content = f.read()
    
    # 외부 스크립트 참조를 인라인으로 변경
    html_content = html_content.replace(
        '<script src="../shared/plotly.min.js"></script>',
        f'<script>{plotly_content}</script>'
    )
    
    # 출력 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 새 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def main():
    """메인 실행 함수"""
    # 기본 경로 설정
    base_dir = Path.cwd()
    
    # 특정 디렉토리 지정 (가장 최근 생성된 것으로 보이는 디렉토리)
    # 먼저 오늘 생성한 디렉토리들을 찾아보고, 없으면 기존 것 사용
    import sys
    
    if len(sys.argv) > 1:
        # 명령줄 인자로 디렉토리 지정
        source_dir = Path(sys.argv[1])
        if not source_dir.exists():
            print(f"❌ 지정된 디렉토리를 찾을 수 없습니다: {source_dir}")
            return
        reports_dirs = [source_dir]
    else:
        # 가장 최근의 reports 디렉토리 찾기
        reports_dirs = sorted(
            [d for d in base_dir.glob("generated_reports/reports_*") if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
    
    if not reports_dirs:
        print("❌ 생성된 보고서를 찾을 수 없습니다.")
        return
    
    source_dir = reports_dirs[0]
    print(f"📂 소스 디렉토리: {source_dir}")
    
    # plotly.min.js 경로
    plotly_js_path = base_dir / "generated_reports" / "never delete" / "plotly.min.js"
    if not plotly_js_path.exists():
        print(f"❌ plotly.min.js 파일을 찾을 수 없습니다: {plotly_js_path}")
        return
    
    # 출력 디렉토리 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base_dir = base_dir / "generated_reports" / f"standalone_reports_{timestamp}"
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 출력 디렉토리: {output_base_dir}")
    
    # 모든 HTML 파일 찾기
    html_files = list(source_dir.glob("**/*.html"))
    
    if not html_files:
        print("❌ HTML 파일을 찾을 수 없습니다.")
        return
    
    print(f"📊 총 {len(html_files)}개의 보고서를 변환합니다.")
    
    # 각 HTML 파일 처리
    success_count = 0
    for i, html_path in enumerate(html_files, 1):
        try:
            # 상대 경로 계산
            relative_path = html_path.relative_to(source_dir)
            
            # 출력 경로 설정
            output_path = output_base_dir / relative_path
            
            # 단독 실행 가능한 HTML 생성
            create_standalone_html(html_path, plotly_js_path, output_path)
            
            # 진행 상황 표시
            progress = (i / len(html_files)) * 100
            print(f"✅ [{i}/{len(html_files)}] {progress:.1f}% - {relative_path}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ 오류 발생 ({html_path}): {str(e)}")
    
    # 완료 메시지
    print(f"\n✨ 변환 완료!")
    print(f"📊 성공: {success_count}/{len(html_files)}개")
    print(f"📁 단독 실행 파일 위치: {output_base_dir}")
    
    # 파일 크기 정보
    total_size = sum(f.stat().st_size for f in output_base_dir.glob("**/*.html"))
    print(f"💾 총 용량: {total_size / (1024*1024):.1f}MB")


if __name__ == "__main__":
    main()