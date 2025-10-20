#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 수정 적용 스크립트

데이터_수정_이력.xlsx 파일에 기록된 수정 사항을 원본 데이터에 자동 적용합니다.

작성일: 2025-01-15
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def get_latest_text_processor_file():
    """가장 최신의 text_processor_결과 파일을 찾아 반환"""
    rawdata_path = Path("rawdata")
    pattern = "2. text_processor_결과_*.xlsx"

    files = [f for f in rawdata_path.glob(pattern) if not f.name.endswith('_partial.xlsx')]

    if not files:
        print(f"⚠️  '{pattern}' 패턴의 파일을 찾을 수 없습니다.")
        return None

    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    print(f"📁 최신 데이터 파일 자동 선택: {latest_file.name}")
    return str(latest_file)


def apply_modifications():
    """데이터 수정 이력을 읽어서 원본 데이터에 적용"""

    print("=" * 80)
    print("🔧 데이터 수정 적용 스크립트")
    print("=" * 80)
    print()

    # 1. 수정 이력 파일 로드
    history_file = "데이터_수정_이력.xlsx"

    if not Path(history_file).exists():
        print(f"❌ 수정 이력 파일을 찾을 수 없습니다: {history_file}")
        print(f"   먼저 '{history_file}' 파일을 생성하고 수정 이력을 입력해주세요.")
        return

    print(f"📂 수정 이력 파일 로드: {history_file}")
    history_df = pd.read_excel(history_file, sheet_name='수정_이력')

    if len(history_df) == 0:
        print("⚠️  적용할 수정 이력이 없습니다.")
        return

    print(f"📋 총 {len(history_df)}건의 수정 이력 발견")
    print()

    # 2. 원본 데이터 로드
    input_file = get_latest_text_processor_file()
    if not input_file:
        return

    print(f"📂 원본 데이터 로드: {input_file}")
    df_original = pd.read_excel(input_file)

    # 컬럼명 정의
    EXCEL_COLUMNS = [
        'response_id', '설문시행연도', '평가_부서명', '평가_부서명_원본', '평가_Unit명', '평가_부문',
        '피평가대상 부서명', '피평가대상_부서명_원본', '피평가대상 UNIT명', '피평가대상 부문',
        '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
        '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
        '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
        '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
        '전반적으로 ○○과의 협업에 대해 만족한다.',
        '종합점수', '극단값', '결측값', '협업 유형', '협업 후기', '정제된_텍스트',
        '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]

    df_original.columns = EXCEL_COLUMNS
    print(f"✅ 원본 데이터 로드 완료: {len(df_original):,}행")
    print()

    # 3. 수정 전 백업
    df_modified = df_original.copy()

    # 4. 수정 사항 적용
    print("=" * 80)
    print("🔧 수정 사항 적용 중...")
    print("=" * 80)
    print()

    modification_log = []

    for idx, row in history_df.iterrows():
        print(f"📝 수정 {idx + 1}/{len(history_df)}: {row['수정항목']}")
        print(f"   대상 Unit: {row['수정대상_Unit']}")
        print(f"   수정 내용:")

        # 수정 대상 찾기
        if pd.notna(row.get('수정대상_Unit')):
            # 평가 Unit 기준 수정
            mask_eval = df_modified['평가_Unit명'] == row['수정대상_Unit']
            mask_target = df_modified['피평가대상 UNIT명'] == row['수정대상_Unit']

            count_eval = mask_eval.sum()
            count_target = mask_target.sum()

            # 부서명 수정
            if pd.notna(row.get('수정_부서명')) and pd.notna(row.get('원본_부서명')):
                if count_eval > 0:
                    df_modified.loc[mask_eval, '평가_부서명'] = row['수정_부서명']
                    print(f"     - 평가_부서명: {row['원본_부서명']} → {row['수정_부서명']} ({count_eval}건)")

                if count_target > 0:
                    df_modified.loc[mask_target, '피평가대상 부서명'] = row['수정_부서명']
                    print(f"     - 피평가대상 부서명: {row['원본_부서명']} → {row['수정_부서명']} ({count_target}건)")

            # 부문 수정
            if pd.notna(row.get('수정_부문')) and pd.notna(row.get('원본_부문')):
                if count_eval > 0:
                    df_modified.loc[mask_eval, '평가_부문'] = row['수정_부문']
                    print(f"     - 평가_부문: {row['원본_부문']} → {row['수정_부문']} ({count_eval}건)")

                if count_target > 0:
                    df_modified.loc[mask_target, '피평가대상 부문'] = row['수정_부문']
                    print(f"     - 피평가대상 부문: {row['원본_부문']} → {row['수정_부문']} ({count_target}건)")

            # 로그 기록
            modification_log.append({
                '수정일시': row['수정일시'],
                '수정대상_Unit': row['수정대상_Unit'],
                '수정항목': row['수정항목'],
                '평가부서_영향': count_eval,
                '피평가부서_영향': count_target,
                '총_영향': count_eval + count_target
            })

        print()

    # 5. 수정 결과 저장
    print("=" * 80)
    print("💾 수정된 데이터 저장 중...")
    print("=" * 80)
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"rawdata/2. text_processor_결과_{timestamp}_modified.xlsx"

    df_modified.to_excel(output_file, index=False)
    print(f"✅ 수정된 데이터 저장 완료: {output_file}")
    print()

    # 6. 수정 로그 저장
    log_df = pd.DataFrame(modification_log)
    log_file = f"데이터_수정_로그_{timestamp}.xlsx"

    with pd.ExcelWriter(log_file, engine='openpyxl') as writer:
        log_df.to_excel(writer, sheet_name='수정_로그', index=False)
        history_df.to_excel(writer, sheet_name='적용된_이력', index=False)

    print(f"📋 수정 로그 저장 완료: {log_file}")
    print()

    # 7. 요약
    print("=" * 80)
    print("📊 수정 요약")
    print("=" * 80)
    print()
    print(f"총 수정 건수: {len(history_df)}건")
    print(f"영향받은 데이터: {log_df['총_영향'].sum():,}건")
    print()
    print("수정 내역:")
    for idx, log in log_df.iterrows():
        print(f"  {idx + 1}. {log['수정대상_Unit']}: {log['총_영향']}건 영향")
    print()

    print("=" * 80)
    print("✅ 데이터 수정 적용 완료!")
    print("=" * 80)
    print()
    print("📂 생성된 파일:")
    print(f"  1. {output_file} - 수정이 적용된 데이터")
    print(f"  2. {log_file} - 수정 로그")
    print()


if __name__ == "__main__":
    apply_modifications()
