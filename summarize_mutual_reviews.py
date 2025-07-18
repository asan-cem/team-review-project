import pandas as pd

def summarize_mutual_reviews_by_year():
    """
    Finds mutually reviewing department pairs for all years without sample size constraints
    and creates a summary Excel file with separate sheets for each year.
    Also includes Unit-level mutual reviews.
    """
    print("🚀 연도별 상호평가 요약 분석을 시작합니다...")

    # 1. 데이터 로드
    try:
        df = pd.read_excel("rawdata/2. text_processor_결과_20250715_160846.xlsx")
        print("✅ 엑셀 파일 로드 완료")
    except FileNotFoundError:
        print("❌ 'rawdata/2. text_processor_결과_20250715_160846.xlsx' 파일을 찾을 수 없습니다.")
        return

    original_cols = [
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
    df.columns = original_cols

    # 2. 데이터 전처리
    df['설문시행연도'] = df['설문시행연도'].astype(str)
    df.dropna(subset=['평가_부서명', '피평가대상 부서명', '종합점수'], inplace=True)
    
    # Unit 컬럼의 결측값을 'N/A'로 처리
    df['평가_Unit명'] = df['평가_Unit명'].fillna('N/A')
    df['피평가대상 UNIT명'] = df['피평가대상 UNIT명'].fillna('N/A')

    # 3. 연도별 데이터 분석
    years = sorted(df['설문시행연도'].unique())
    print(f"🔍 분석할 연도: {', '.join(years)}")

    # 4. 연도별 결과를 저장할 딕셔너리
    year_results = {}
    year_unit_results = {}

    for year in years:
        print(f"\n📅 {year}년 데이터 분석 중...")
        
        # 연도별 데이터 필터링
        df_year = df[df['설문시행연도'] == year].copy()
        print(f"   - {year}년 데이터: {len(df_year)}건")

        if df_year.empty:
            print(f"   - {year}년 데이터가 없어 건너뜁니다.")
            continue

        # === 부서별 상호평가 분석 ===
        # 부서별 종합점수 및 응답 수 집계
        agg_data = df_year.groupby(['평가_부서명', '피평가대상 부서명']).agg(
            종합점수=('종합점수', 'mean'),
            응답수=('종합점수', 'size')
        ).reset_index()

        # 상호평가 쌍 찾기 (표본수 제약 없음)
        summary_list = []
        processed_pairs = set()

        for _, row in agg_data.iterrows():
            team_a = row['평가_부서명']
            team_b = row['피평가대상 부서명']

            # 중복 처리를 피하기 위해 정렬된 튜플 사용
            pair_key = tuple(sorted((team_a, team_b)))
            if pair_key in processed_pairs:
                continue

            # B -> A 평가 데이터 찾기
            mutual_row = agg_data[
                (agg_data['평가_부서명'] == team_b) & (agg_data['피평가대상 부서명'] == team_a)
            ]

            if not mutual_row.empty:
                # A -> B 평가 데이터 (현재 row)
                stats_b_by_a = row
                # B -> A 평가 데이터
                stats_a_by_b = mutual_row.iloc[0]

                # 표본수 제약 없이 모든 상호평가 쌍 포함
                summary_list.append({
                    '부서 A': team_a,
                    '부서 B': team_b,
                    'A팀 종합점수 (B팀 평가)': round(stats_a_by_b['종합점수'], 2),
                    'B팀 종합점수 (A팀 평가)': round(stats_b_by_a['종합점수'], 2),
                    'A팀 응답수 (B팀 평가)': stats_a_by_b['응답수'],
                    'B팀 응답수 (A팀 평가)': stats_b_by_a['응답수'],
                    '총 응답수': stats_a_by_b['응답수'] + stats_b_by_a['응답수']
                })
                
                processed_pairs.add(pair_key)

        print(f"   - {year}년 상호평가 부서 쌍: {len(summary_list)}개")
        
        if summary_list:
            year_results[year] = pd.DataFrame(summary_list)

        # === Unit별 상호평가 분석 ===
        # Unit별 종합점수 및 응답 수 집계
        agg_unit_data = df_year.groupby(['평가_Unit명', '피평가대상 UNIT명']).agg(
            종합점수=('종합점수', 'mean'),
            응답수=('종합점수', 'size')
        ).reset_index()

        # Unit별 상호평가 쌍 찾기
        unit_summary_list = []
        processed_unit_pairs = set()

        for _, row in agg_unit_data.iterrows():
            unit_a = row['평가_Unit명']
            unit_b = row['피평가대상 UNIT명']

            # 자기 자신 평가는 제외
            if unit_a == unit_b:
                continue

            # 중복 처리를 피하기 위해 정렬된 튜플 사용
            pair_key = tuple(sorted((unit_a, unit_b)))
            if pair_key in processed_unit_pairs:
                continue

            # B -> A 평가 데이터 찾기
            mutual_row = agg_unit_data[
                (agg_unit_data['평가_Unit명'] == unit_b) & (agg_unit_data['피평가대상 UNIT명'] == unit_a)
            ]

            if not mutual_row.empty:
                # A -> B 평가 데이터 (현재 row)
                stats_b_by_a = row
                # B -> A 평가 데이터
                stats_a_by_b = mutual_row.iloc[0]

                unit_summary_list.append({
                    'Unit A': unit_a,
                    'Unit B': unit_b,
                    'A Unit 종합점수 (B Unit 평가)': round(stats_a_by_b['종합점수'], 2),
                    'B Unit 종합점수 (A Unit 평가)': round(stats_b_by_a['종합점수'], 2),
                    'A Unit 응답수 (B Unit 평가)': stats_a_by_b['응답수'],
                    'B Unit 응답수 (A Unit 평가)': stats_b_by_a['응답수'],
                    '총 응답수': stats_a_by_b['응답수'] + stats_b_by_a['응답수']
                })
                
                processed_unit_pairs.add(pair_key)

        print(f"   - {year}년 상호평가 Unit 쌍: {len(unit_summary_list)}개")
        
        if unit_summary_list:
            year_unit_results[year] = pd.DataFrame(unit_summary_list)

    # 5. 엑셀 파일에 연도별 시트로 저장
    if year_results or year_unit_results:
        output_filename = "상호평가_요약_연도별.xlsx"
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            # 부서별 결과 저장
            for year, df_result in year_results.items():
                # 총 응답수 기준으로 정렬
                df_result = df_result.sort_values('총 응답수', ascending=False)
                df_result.to_excel(writer, sheet_name=f'{year}년_부서별', index=False)
                print(f"   - {year}년 부서별 결과를 '{year}년_부서별' 시트에 저장")
            
            # Unit별 결과 저장
            for year, df_result in year_unit_results.items():
                # 총 응답수 기준으로 정렬
                df_result = df_result.sort_values('총 응답수', ascending=False)
                df_result.to_excel(writer, sheet_name=f'{year}년_Unit별', index=False)
                print(f"   - {year}년 Unit별 결과를 '{year}년_Unit별' 시트에 저장")
        
        print(f"\n🎉 분석 완료! 결과가 '{output_filename}' 파일로 저장되었습니다.")
    else:
        print("\n⚠️ 상호평가 데이터가 없습니다.")

def classify_departments_by_relationships():
    """
    상호평가 관계를 분석하여 부서를 우수/저조로 분류합니다.
    양방향 평가 패턴과 관계 품질을 기반으로 분류합니다.
    """
    print("\n🔍 상호평가 관계 기반 부서 분류를 시작합니다...")
    
    # 1. 데이터 로드
    try:
        df = pd.read_excel("rawdata/2. text_processor_결과_20250715_160846.xlsx")
        print("✅ 엑셀 파일 로드 완료")
    except FileNotFoundError:
        print("❌ 'rawdata/2. text_processor_결과_20250715_160846.xlsx' 파일을 찾을 수 없습니다.")
        return

    original_cols = [
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
    df.columns = original_cols

    # 2. 데이터 전처리
    df['설문시행연도'] = df['설문시행연도'].astype(str)
    df.dropna(subset=['평가_부서명', '피평가대상 부서명', '종합점수'], inplace=True)
    
    # 3. 전체 데이터로 관계 분석 (최근 3년 데이터)
    recent_years = ['2023', '2024', '2025']
    df_recent = df[df['설문시행연도'].isin(recent_years)].copy()
    print(f"📊 분석 대상 데이터: {len(df_recent)}건 (2023-2025)")
    
    # 4. 부서별 종합점수 및 응답 수 집계
    agg_data = df_recent.groupby(['평가_부서명', '피평가대상 부서명']).agg(
        종합점수=('종합점수', 'mean'),
        응답수=('종합점수', 'size')
    ).reset_index()
    
    # 5. 부서별 관계 품질 지표 계산
    dept_metrics = {}
    
    for dept in df_recent['피평가대상 부서명'].unique():
        # 해당 부서를 평가한 모든 데이터
        received_evals = agg_data[agg_data['피평가대상 부서명'] == dept]
        
        # 해당 부서가 평가한 모든 데이터  
        given_evals = agg_data[agg_data['평가_부서명'] == dept]
        
        if len(received_evals) == 0:
            continue
            
        # 기본 지표
        avg_received_score = received_evals['종합점수'].mean()
        total_received_responses = received_evals['응답수'].sum()
        num_evaluator_depts = len(received_evals)
        
        # 상호평가 관계 분석
        mutual_relationships = []
        mutual_scores = []
        
        for _, row in received_evals.iterrows():
            evaluator = row['평가_부서명']
            score_received = row['종합점수']
            
            # 역방향 평가 찾기 (dept가 evaluator를 평가한 경우)
            reverse_eval = given_evals[given_evals['피평가대상 부서명'] == evaluator]
            
            if not reverse_eval.empty:
                score_given = reverse_eval['종합점수'].iloc[0]
                mutual_relationships.append({
                    'partner': evaluator,
                    'received_score': score_received,
                    'given_score': score_given,
                    'score_difference': abs(score_received - score_given),
                    'avg_mutual_score': (score_received + score_given) / 2
                })
                mutual_scores.append((score_received + score_given) / 2)
        
        # 상호평가 품질 지표
        num_mutual_relationships = len(mutual_relationships)
        mutual_score_avg = sum(mutual_scores) / len(mutual_scores) if mutual_scores else 0
        
        # 점수 일관성 (상호평가에서 점수 차이의 평균)
        score_consistency = sum([rel['score_difference'] for rel in mutual_relationships]) / num_mutual_relationships if num_mutual_relationships > 0 else 0
        
        # 관계 균형도 (받은 점수와 준 점수의 균형)
        if mutual_relationships:
            balance_scores = [abs(rel['received_score'] - rel['given_score']) for rel in mutual_relationships]
            relationship_balance = sum(balance_scores) / len(balance_scores)
        else:
            relationship_balance = 0
            
        dept_metrics[dept] = {
            '부서명': dept,
            '평균_받은_점수': round(avg_received_score, 2),
            '총_응답수': total_received_responses,
            '평가_부서수': num_evaluator_depts,
            '상호평가_관계수': num_mutual_relationships,
            '상호평가_평균점수': round(mutual_score_avg, 2),
            '점수_일관성': round(score_consistency, 2),  # 낮을수록 일관됨
            '관계_균형도': round(relationship_balance, 2),  # 낮을수록 균형됨
            '상호평가_비율': round(num_mutual_relationships / num_evaluator_depts * 100, 1) if num_evaluator_depts > 0 else 0
        }
    
    # 6. 분류 기준 개발
    metrics_df = pd.DataFrame(list(dept_metrics.values()))
    
    # 통계적 기준점 계산
    score_threshold_high = metrics_df['평균_받은_점수'].quantile(0.75)  # 상위 25%
    score_threshold_low = metrics_df['평균_받은_점수'].quantile(0.25)   # 하위 25%
    
    mutual_score_threshold_high = metrics_df['상호평가_평균점수'].quantile(0.75)
    mutual_score_threshold_low = metrics_df['상호평가_평균점수'].quantile(0.25)
    
    consistency_threshold = metrics_df['점수_일관성'].quantile(0.5)  # 중간값 이하가 일관성 좋음
    balance_threshold = metrics_df['관계_균형도'].quantile(0.5)      # 중간값 이하가 균형 좋음
    
    min_responses = 10  # 최소 응답수
    min_mutual_relationships = 3  # 최소 상호평가 관계수
    
    # 7. 부서 분류
    classifications = []
    
    for dept, metrics in dept_metrics.items():
        # 기본 조건 확인
        has_sufficient_data = (metrics['총_응답수'] >= min_responses and 
                              metrics['상호평가_관계수'] >= min_mutual_relationships)
        
        if not has_sufficient_data:
            classification = '데이터_부족'
            reason = f"응답수 {metrics['총_응답수']}건, 상호평가 관계 {metrics['상호평가_관계수']}개"
        else:
            # 우수 부서 기준
            excellent_criteria = (
                metrics['평균_받은_점수'] >= score_threshold_high and
                metrics['상호평가_평균점수'] >= mutual_score_threshold_high and
                metrics['점수_일관성'] <= consistency_threshold and
                metrics['관계_균형도'] <= balance_threshold
            )
            
            # 저조 부서 기준  
            poor_criteria = (
                metrics['평균_받은_점수'] <= score_threshold_low and
                metrics['상호평가_평균점수'] <= mutual_score_threshold_low
            )
            
            if excellent_criteria:
                classification = '우수_부서'
                reason = f"높은 평가점수({metrics['평균_받은_점수']}), 좋은 상호관계({metrics['상호평가_평균점수']}), 일관성 우수"
            elif poor_criteria:
                classification = '저조_부서'
                reason = f"낮은 평가점수({metrics['평균_받은_점수']}), 상호관계 점수 저조({metrics['상호평가_평균점수']})"
            else:
                classification = '보통_부서'
                reason = "중간 수준의 평가 지표"
        
        classifications.append({
            **metrics,
            '분류': classification,
            '분류_사유': reason
        })
    
    # 8. 결과 정리
    classification_df = pd.DataFrame(classifications)
    classification_df = classification_df.sort_values(['분류', '평균_받은_점수'], ascending=[True, False])
    
    # 9. 통계 요약
    print(f"\n📈 분류 결과 요약:")
    print(f"   - 분석 대상 부서: {len(classification_df)}개")
    
    for category in ['우수_부서', '보통_부서', '저조_부서', '데이터_부족']:
        count = len(classification_df[classification_df['분류'] == category])
        print(f"   - {category}: {count}개 부서")
    
    print(f"\n📊 분류 기준:")
    print(f"   - 우수 부서 점수 기준: {score_threshold_high:.1f}점 이상")
    print(f"   - 저조 부서 점수 기준: {score_threshold_low:.1f}점 이하")
    print(f"   - 최소 응답수: {min_responses}건")
    print(f"   - 최소 상호평가 관계: {min_mutual_relationships}개")
    
    # 10. 엑셀로 저장
    with pd.ExcelWriter("상호평가_부서분류_결과.xlsx", engine='openpyxl') as writer:
        classification_df.to_excel(writer, sheet_name='부서_분류_결과', index=False)
        
        # 분류별 상세 결과
        for category in ['우수_부서', '저조_부서', '보통_부서', '데이터_부족']:
            category_data = classification_df[classification_df['분류'] == category]
            if not category_data.empty:
                category_data.to_excel(writer, sheet_name=category, index=False)
    
    print(f"\n🎉 분류 결과가 '상호평가_부서분류_결과.xlsx' 파일로 저장되었습니다!")
    
    return classification_df

if __name__ == "__main__":
    summarize_mutual_reviews_by_year()
    print("\n" + "="*60)
    classify_departments_by_relationships()