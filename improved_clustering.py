import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

def improved_clustering_analysis():
    """개선된 클러스터링 분석 (감정-그룹명 일치성 개선)"""
    
    print("🔧 개선된 클러스터링 분석 시작")
    print("=" * 50)
    
    try:
        # 1. 원본 분석 결과 읽기
        print("📁 원본 분석 파일 로드...")
        df = pd.read_excel('협업후기_분석결과_상위200건.xlsx', engine='openpyxl')
        
        # 2. 감정별로 먼저 분리하여 클러스터링
        print("📊 감정별 분리 클러스터링 준비...")
        valid_mask = df['협업후기_정제텍스트'].notna() & (df['협업후기_정제텍스트'].str.len() > 3)
        valid_df = df[valid_mask].copy()
        
        # 3. 감정별 데이터 분리
        positive_df = valid_df[valid_df['협업후기_주감정'] == '긍정'].copy()
        negative_df = valid_df[valid_df['협업후기_주감정'] == '부정'].copy()
        neutral_df = valid_df[valid_df['협업후기_주감정'] == '중립'].copy()
        
        print(f"  긍정: {len(positive_df)}건")
        print(f"  부정: {len(negative_df)}건") 
        print(f"  중립: {len(neutral_df)}건")
        
        # 4. 개선된 클러스터 할당 (감정 기반)
        df['협업후기_클러스터'] = np.nan
        df['협업후기_클러스터그룹'] = np.nan
        
        cluster_counter = 0
        cluster_details = []
        
        # 긍정 감정 클러스터링
        if len(positive_df) > 5:
            pos_texts = positive_df['협업후기_정제텍스트'].tolist()
            pos_clusters, pos_details = cluster_by_content(pos_texts, "긍정", cluster_counter)
            
            for i, idx in enumerate(positive_df.index):
                df.loc[idx, '협업후기_클러스터'] = pos_clusters[i] + cluster_counter
            
            cluster_details.extend(pos_details)
            cluster_counter += len(pos_details)
        
        # 부정 감정 클러스터링
        if len(negative_df) > 5:
            neg_texts = negative_df['협업후기_정제텍스트'].tolist()
            neg_clusters, neg_details = cluster_by_content(neg_texts, "부정", cluster_counter)
            
            for i, idx in enumerate(negative_df.index):
                df.loc[idx, '협업후기_클러스터'] = neg_clusters[i] + cluster_counter
                
            cluster_details.extend(neg_details)
            cluster_counter += len(neg_details)
        
        # 중립 감정 클러스터링
        if len(neutral_df) > 3:
            neu_texts = neutral_df['협업후기_정제텍스트'].tolist() 
            neu_clusters, neu_details = cluster_by_content(neu_texts, "중립", cluster_counter)
            
            for i, idx in enumerate(neutral_df.index):
                df.loc[idx, '협업후기_클러스터'] = neu_clusters[i] + cluster_counter
                
            cluster_details.extend(neu_details)
        
        # 5. 그룹명 매핑 (감정 기반)
        cluster_name_mapping = {}
        for detail in cluster_details:
            cluster_name_mapping[detail['cluster_id']] = detail['group_name']
        
        df['협업후기_클러스터그룹'] = df['협업후기_클러스터'].map(cluster_name_mapping)
        
        # 6. 클러스터별 상세 분석
        print("📝 클러스터별 특성 분석...")
        cluster_summary = []
        
        for detail in cluster_details:
            cluster_mask = (df['협업후기_클러스터'] == detail['cluster_id'])
            cluster_data = df[cluster_mask]
            
            if len(cluster_data) == 0:
                continue
                
            # 감정 분포
            sentiments = cluster_data['협업후기_주감정'].value_counts()
            sentiment_dict = {sentiment: int(count) for sentiment, count in sentiments.items()}
            sentiment_str = ', '.join([f"{k}:{v}건" for k, v in sentiment_dict.items()])
            
            # 세부감정 분포
            detailed_sentiments = cluster_data['협업후기_세부감정'].value_counts()
            main_detailed = detailed_sentiments.index[0] if len(detailed_sentiments) > 0 else "기타"
            
            # 평균 감정 강도
            avg_intensity = cluster_data['협업후기_감정강도'].mean() if len(cluster_data) > 0 else 5.0
            
            # 대표 예시
            representative_text = ""
            if len(cluster_data) > 0:
                cluster_texts = cluster_data['협업후기_정제텍스트'].tolist()
                representative_text = cluster_texts[0]
            
            cluster_summary.append({
                '클러스터그룹': detail['group_name'],
                '피드백수': len(cluster_data),
                '비율': f"{len(cluster_data)/len(df)*100:.1f}%",
                '주요키워드': detail['keywords'],
                '전체키워드': detail['keywords'],
                '주감정': detail['sentiment_type'],
                '세부감정': main_detailed,
                '평균감정강도': f"{avg_intensity:.1f}",
                '감정분포': sentiment_str,
                '대표예시': representative_text[:80] + "..." if len(representative_text) > 80 else representative_text
            })
        
        # 7. 부문/부서/Unit별 이슈 분석 추가
        print("🏢 부문/부서/Unit별 이슈 분석...")
        department_analysis = analyze_department_issues(df)
        
        # 8. 유사도 분석 (기존 로직 유지)
        print("📏 유사도 높은 피드백 쌍 분석...")
        similarity_pairs = analyze_similarity_pairs(valid_df)
        
        # 9. 개선된 결과를 Excel 파일로 저장
        print("💾 개선된 클러스터링 결과 저장...")
        output_file = '협업후기_분석결과_개선된클러스터링_상위200건.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 메인 시트
            df.to_excel(writer, sheet_name='분석결과_개선된클러스터', index=False)
            
            # 클러스터 요약 시트
            pd.DataFrame(cluster_summary).to_excel(writer, sheet_name='개선된클러스터별요약', index=False)
            
            # 유사 피드백 쌍 시트
            if similarity_pairs:
                pd.DataFrame(similarity_pairs).to_excel(writer, sheet_name='유사피드백쌍', index=False)
            
            # 부문별 이슈 분석
            pd.DataFrame(department_analysis['부문별']).to_excel(writer, sheet_name='부문별이슈분석', index=False)
            pd.DataFrame(department_analysis['부서별']).to_excel(writer, sheet_name='부서별이슈분석', index=False)
            pd.DataFrame(department_analysis['Unit별']).to_excel(writer, sheet_name='Unit별이슈분석', index=False)
        
        print(f"✅ 개선 완료: {output_file}")
        
        # 10. 개선사항 요약
        print(f"\n🎉 개선 사항:")
        print(f"1. ✅ 감정별 분리 클러스터링으로 논리적 일관성 확보")
        print(f"2. ✅ 그룹명과 감정의 일치성 개선")
        print(f"3. ✅ 부문/부서/Unit별 주요 이슈 및 개선사항 분석 추가")
        print(f"4. ✅ 시급성별 우선순위 도출")
        
        return output_file, cluster_summary, department_analysis
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def cluster_by_content(texts, sentiment_type, start_cluster_id):
    """텍스트 내용 기반 클러스터링"""
    
    if len(texts) < 3:
        # 데이터가 적으면 하나의 클러스터로
        return [0], [{
            'cluster_id': start_cluster_id,
            'group_name': f"{sentiment_type}_기타그룹",
            'sentiment_type': sentiment_type,
            'keywords': "일반 키워드"
        }]
    
    # TF-IDF 벡터화
    stop_words = ['없습니다', '감사합니다', '만족', '항상', '매우', '정말', '너무', '아주', 
                 '없음', '해당없음', '무', '...', '....', '.', 'x000d',
                 # 의료용어 제외
                 '간호사', '의사', '약사', '검사실', '병동', '외래', '수술실', '응급실']
    
    vectorizer = TfidfVectorizer(
        max_features=50, min_df=1, max_df=0.8, 
        ngram_range=(1, 2), stop_words=stop_words
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # 클러스터 수 결정 (데이터 양에 따라)
        n_clusters = min(3, max(1, len(texts) // 10))
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        # 클러스터별 특성 분석
        cluster_details = []
        for i in range(n_clusters):
            # 대표 키워드 추출
            cluster_center = kmeans.cluster_centers_[i]
            top_indices = cluster_center.argsort()[-3:][::-1]
            keywords = ' | '.join([feature_names[idx] for idx in top_indices])
            
            # 감정별 그룹명 생성
            group_name = generate_group_name(sentiment_type, keywords, i)
            
            cluster_details.append({
                'cluster_id': start_cluster_id + i,
                'group_name': group_name,
                'sentiment_type': sentiment_type,
                'keywords': keywords
            })
        
        return clusters, cluster_details
        
    except Exception as e:
        print(f"클러스터링 오류: {e}")
        # 실패 시 단일 클러스터
        return [0] * len(texts), [{
            'cluster_id': start_cluster_id,
            'group_name': f"{sentiment_type}_일반그룹",
            'sentiment_type': sentiment_type,
            'keywords': "일반 키워드"
        }]

def generate_group_name(sentiment_type, keywords, cluster_idx):
    """감정과 키워드 기반 그룹명 생성"""
    
    # 키워드 기반 카테고리 판단
    keywords_lower = keywords.lower()
    
    if sentiment_type == "긍정":
        if any(word in keywords_lower for word in ['감사', '고마', '친절']):
            return "긍정_감사표현그룹"
        elif any(word in keywords_lower for word in ['만족', '좋', '훌륭']):
            return "긍정_만족평가그룹"
        elif any(word in keywords_lower for word in ['도움', '지원', '협조']):
            return "긍정_협업지원그룹"
        else:
            return f"긍정_일반칭찬그룹_{cluster_idx+1}"
    
    elif sentiment_type == "부정":
        if any(word in keywords_lower for word in ['불만', '실망', '화']):
            return "부정_불만표출그룹"
        elif any(word in keywords_lower for word in ['개선', '문제', '부족']):
            return "부정_개선요구그룹"
        elif any(word in keywords_lower for word in ['소통', '태도', '응대']):
            return "부정_소통문제그룹"
        else:
            return f"부정_일반불만그룹_{cluster_idx+1}"
    
    else:  # 중립
        if any(word in keywords_lower for word in ['제안', '의견']):
            return "중립_개선제안그룹"
        elif any(word in keywords_lower for word in ['정보', '확인']):
            return "중립_정보문의그룹"
        else:
            return f"중립_일반의견그룹_{cluster_idx+1}"

def analyze_department_issues(df):
    """부문/부서/Unit별 이슈 분석"""
    
    department_analysis = {
        '부문별': [],
        '부서별': [],
        'Unit별': []
    }
    
    # 부문별 분석
    for 부문 in df['평가_부문'].unique():
        if pd.notna(부문):
            부문_data = df[df['평가_부문'] == 부문]
            
            # 주요 이슈 추출 (부정적 피드백 위주)
            부정_data = 부문_data[부문_data['협업후기_주감정'] == '부정']
            주요이슈 = extract_main_issues(부정_data)
            
            # 감정 분포
            감정_분포 = 부문_data['협업후기_주감정'].value_counts()
            감정_분포_str = ', '.join([f"{k}:{v}건" for k, v in 감정_분포.items()])
            
            # 우선순위 판단
            우선순위 = determine_priority(부문_data)
            
            department_analysis['부문별'].append({
                '부문': 부문,
                '총피드백수': len(부문_data),
                '감정분포': 감정_분포_str,
                '부정비율': f"{len(부정_data)/len(부문_data)*100:.1f}%",
                '주요이슈': 주요이슈,
                '개선우선순위': 우선순위,
                '권장조치': get_recommended_actions(주요이슈, 우선순위)
            })
    
    # 부서별 분석 (상위 10개)
    for 부서 in df['피평가대상 부서명'].value_counts().head(10).index:
        부서_data = df[df['피평가대상 부서명'] == 부서]
        부정_data = 부서_data[부서_data['협업후기_주감정'] == '부정']
        주요이슈 = extract_main_issues(부정_data)
        
        감정_분포 = 부서_data['협업후기_주감정'].value_counts()
        감정_분포_str = ', '.join([f"{k}:{v}건" for k, v in 감정_분포.items()])
        
        우선순위 = determine_priority(부서_data)
        
        department_analysis['부서별'].append({
            '피평가부서': 부서,
            '총피드백수': len(부서_data),
            '감정분포': 감정_분포_str,
            '부정비율': f"{len(부정_data)/len(부서_data)*100:.1f}%",
            '주요이슈': 주요이슈,
            '개선우선순위': 우선순위,
            '권장조치': get_recommended_actions(주요이슈, 우선순위)
        })
    
    # Unit별 분석
    if 'Unit' in df.columns:
        for unit in df['Unit'].value_counts().head(5).index:
            if pd.notna(unit):
                unit_data = df[df['Unit'] == unit]
                부정_data = unit_data[unit_data['협업후기_주감정'] == '부정']
                주요이슈 = extract_main_issues(부정_data)
                
                감정_분포 = unit_data['협업후기_주감정'].value_counts()
                감정_분포_str = ', '.join([f"{k}:{v}건" for k, v in 감정_분포.items()])
                
                우선순위 = determine_priority(unit_data)
                
                department_analysis['Unit별'].append({
                    'Unit': unit,
                    '총피드백수': len(unit_data),
                    '감정분포': 감정_분포_str,
                    '부정비율': f"{len(부정_data)/len(unit_data)*100:.1f}%",
                    '주요이슈': 주요이슈,
                    '개선우선순위': 우선순위,
                    '권장조치': get_recommended_actions(주요이슈, 우선순위)
                })
    
    return department_analysis

def extract_main_issues(negative_data):
    """부정적 피드백에서 주요 이슈 추출"""
    if len(negative_data) == 0:
        return "특별한 이슈 없음"
    
    # 키워드 빈도 분석
    all_keywords = []
    for keywords in negative_data['협업후기_키워드']:
        if pd.notna(keywords):
            all_keywords.extend([k.strip() for k in str(keywords).split(',')])
    
    if not all_keywords:
        return "키워드 부족으로 이슈 분석 어려움"
    
    from collections import Counter
    keyword_freq = Counter(all_keywords)
    top_issues = [f"{keyword}({count}회)" for keyword, count in keyword_freq.most_common(3)]
    
    return ", ".join(top_issues)

def determine_priority(dept_data):
    """개선 우선순위 판단"""
    부정_비율 = len(dept_data[dept_data['협업후기_주감정'] == '부정']) / len(dept_data)
    피드백_수 = len(dept_data)
    평균강도 = dept_data['협업후기_감정강도'].mean()
    
    if 부정_비율 > 0.6 and 피드백_수 > 10:
        return "시급"
    elif 부정_비율 > 0.4 or 피드백_수 > 15:
        return "중요"
    elif 부정_비율 > 0.2:
        return "보통"
    else:
        return "낮음"

def get_recommended_actions(issues, priority):
    """권장 조치사항 제안"""
    if priority == "시급":
        return "즉시 개선팀 구성, 1개월 내 개선계획 수립"
    elif priority == "중요":
        return "3개월 내 개선계획 수립, 정기 모니터링"
    elif priority == "보통":
        return "6개월 내 점진적 개선, 분기별 점검"
    else:
        return "현 상태 유지, 반기별 모니터링"

def analyze_similarity_pairs(valid_df):
    """유사도 분석 (기존 로직)"""
    similarity_pairs = []
    
    try:
        texts = valid_df['협업후기_정제텍스트'].tolist()
        
        stop_words = ['없습니다', '감사합니다', '만족', '항상', '매우', '정말', '너무', '아주']
        vectorizer = TfidfVectorizer(max_features=50, stop_words=stop_words)
        
        sample_size = min(50, len(texts))
        sample_texts = texts[:sample_size]
        sample_matrix = vectorizer.fit_transform(sample_texts)
        similarity_matrix = cosine_similarity(sample_matrix)
        
        for i in range(sample_size):
            for j in range(i+1, sample_size):
                similarity = similarity_matrix[i][j]
                if similarity > 0.3:
                    similarity_pairs.append({
                        '텍스트1_번호': i+1,
                        '텍스트2_번호': j+1,
                        '유사도': f"{similarity:.3f}",
                        '텍스트1': sample_texts[i][:60] + "...",
                        '텍스트2': sample_texts[j][:60] + "...",
                        '같은감정여부': '예' if valid_df.iloc[i]['협업후기_주감정'] == valid_df.iloc[j]['협업후기_주감정'] else '아니오'
                    })
    
    except Exception as e:
        print(f"유사도 분석 오류: {e}")
    
    return similarity_pairs

if __name__ == "__main__":
    result_file, summary, dept_analysis = improved_clustering_analysis()
    
    if result_file:
        print(f"\n{'='*60}")
        print("📋 개선된 최종 파일 구성:")
        print("• 분석결과_개선된클러스터: 모든 분석 결과 + 개선된 클러스터")
        print("• 개선된클러스터별요약: 감정-그룹명 일치성 개선된 분석")
        print("• 유사피드백쌍: 중복 이슈 후보들")
        print("• 부문별이슈분석: 부문별 주요 이슈 및 개선사항")
        print("• 부서별이슈분석: 부서별 상세 이슈 분석")
        print("• Unit별이슈분석: Unit별 세부 분석")