import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

def fix_clustering_results():
    """클러스터링 결과 수정 및 개선"""
    
    print("🔧 클러스터링 결과 수정 및 개선")
    print("=" * 50)
    
    try:
        # 1. 원본 분석 결과 읽기
        print("📁 원본 분석 파일 로드...")
        df = pd.read_excel('협업후기_분석결과_상위200건.xlsx', engine='openpyxl')
        
        # 2. 유효한 텍스트만 추출
        print("📊 클러스터링 대상 텍스트 준비...")
        valid_mask = df['협업후기_정제텍스트'].notna() & (df['협업후기_정제텍스트'].str.len() > 3)
        valid_df = df[valid_mask].copy()
        texts = valid_df['협업후기_정제텍스트'].tolist()
        
        # 3. TF-IDF 벡터화 (의료용어 제외)
        stop_words = ['없습니다', '감사합니다', '만족', '항상', '매우', '정말', '너무', '아주', 
                     '없음', '해당없음', '무', '...', '....', '.', 'x000d',
                     # 의료용어 제외 추가
                     '간호사', '의사', '약사', '검사실', '병동', '외래', '수술실', '응급실']
        
        vectorizer = TfidfVectorizer(
            max_features=80, min_df=2, max_df=0.8, 
            ngram_range=(1, 2), stop_words=stop_words
        )
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # 4. K-means 클러스터링
        n_clusters = 7
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        # 5. 원본 DataFrame에 클러스터 결과 추가
        df['협업후기_클러스터'] = np.nan
        df.loc[valid_mask, '협업후기_클러스터'] = clusters
        
        # 6. 의미있는 그룹 이름 매핑
        meaningful_names = {
            0: '업무협조감사그룹',
            1: '업무지원요청그룹', 
            2: '일반감사표현그룹',
            3: '검사환자케어그룹',
            4: '종합만족평가그룹',
            5: '환자중심업무그룹',
            6: '처방만족그룹'
        }
        
        df['협업후기_클러스터그룹'] = df['협업후기_클러스터'].map(meaningful_names)
        
        # 7. 클러스터별 상세 분석 (감정분포 수정)
        print("📝 클러스터별 특성 분석 (수정된 감정분포)...")
        cluster_summary = []
        feature_names = vectorizer.get_feature_names_out()
        
        for i in range(n_clusters):
            cluster_mask = (df['협업후기_클러스터'] == i)
            cluster_data = df[cluster_mask]
            
            # 클러스터 대표 키워드
            cluster_center = kmeans.cluster_centers_[i]
            top_indices = cluster_center.argsort()[-5:][::-1]
            keywords = [feature_names[idx] for idx in top_indices]
            
            # 감정 분포 (수정된 형식)
            sentiments = cluster_data['협업후기_주감정'].value_counts()
            main_sentiment = sentiments.index[0] if len(sentiments) > 0 else "중립"
            
            # 감정분포를 깔끔한 문자열로 변환
            sentiment_dict = {}
            for sentiment, count in sentiments.items():
                sentiment_dict[sentiment] = int(count)  # numpy int를 python int로 변환
            
            # 문자열 형태로 정리
            sentiment_str = ', '.join([f"{k}:{v}건" for k, v in sentiment_dict.items()])
            
            # 세부감정 분포
            detailed_sentiments = cluster_data['협업후기_세부감정'].value_counts()
            main_detailed = detailed_sentiments.index[0] if len(detailed_sentiments) > 0 else "기타"
            
            # 평균 감정 강도
            avg_intensity = cluster_data['협업후기_감정강도'].mean() if len(cluster_data) > 0 else 5.0
            
            # 대표 예시
            if len(cluster_data) > 0:
                cluster_texts = cluster_data['협업후기_정제텍스트'].tolist()
                cluster_indices = cluster_data.index[cluster_data.index.isin(valid_df.index)]
                if len(cluster_indices) > 0:
                    cluster_tfidf = tfidf_matrix[[valid_df.index.get_loc(idx) for idx in cluster_indices]]
                    similarities = cosine_similarity(cluster_tfidf, [cluster_center])
                    best_idx = similarities.flatten().argmax()
                    representative_text = cluster_texts[best_idx]
                else:
                    representative_text = cluster_texts[0]
            else:
                representative_text = ""
            
            cluster_summary.append({
                '클러스터그룹': meaningful_names[i],
                '피드백수': len(cluster_data),
                '비율': f"{len(cluster_data)/len(df)*100:.1f}%",
                '주요키워드': ' | '.join(keywords[:3]),
                '전체키워드': ' | '.join(keywords),
                '주감정': main_sentiment,
                '세부감정': main_detailed,
                '평균감정강도': f"{avg_intensity:.1f}",
                '감정분포': sentiment_str,  # 수정된 형식
                '대표예시': representative_text[:80] + "..." if len(representative_text) > 80 else representative_text
            })
        
        # 8. 유사도 분석
        print("📏 유사도 높은 피드백 쌍 분석...")
        similarity_pairs = []
        sample_size = min(50, len(texts))
        sample_matrix = tfidf_matrix[:sample_size]
        similarity_matrix = cosine_similarity(sample_matrix)
        
        for i in range(sample_size):
            for j in range(i+1, sample_size):
                similarity = similarity_matrix[i][j]
                if similarity > 0.3:
                    similarity_pairs.append({
                        '텍스트1_번호': i+1,
                        '텍스트2_번호': j+1,
                        '유사도': f"{similarity:.3f}",
                        '텍스트1': texts[i][:60] + "...",
                        '텍스트2': texts[j][:60] + "...",
                        '클러스터1': meaningful_names[clusters[i]],
                        '클러스터2': meaningful_names[clusters[j]],
                        '같은그룹여부': '예' if clusters[i] == clusters[j] else '아니오'
                    })
        
        # 9. 수정된 결과를 Excel 파일로 저장
        print("💾 수정된 클러스터링 결과 저장...")
        output_file = '협업후기_분석결과_클러스터링_최종_상위200건.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 메인 시트
            df.to_excel(writer, sheet_name='분석결과_클러스터포함', index=False)
            
            # 클러스터 요약 시트 (수정된 감정분포)
            pd.DataFrame(cluster_summary).to_excel(writer, sheet_name='클러스터별요약', index=False)
            
            # 유사 피드백 쌍 시트 (개선된 형식)
            if similarity_pairs:
                pd.DataFrame(similarity_pairs).to_excel(writer, sheet_name='유사피드백쌍', index=False)
            
            # 부문별 분석 시트 추가
            부문별_분석 = []
            for 부문 in df['평가_부문'].unique():
                if pd.notna(부문):
                    부문_data = df[df['평가_부문'] == 부문]
                    감정_분포 = 부문_data['협업후기_주감정'].value_counts()
                    감정_분포_str = ', '.join([f"{k}:{v}건" for k, v in 감정_분포.items()])
                    
                    부문별_분석.append({
                        '부문': 부문,
                        '총피드백수': len(부문_data),
                        '감정분포': 감정_분포_str,
                        '주요감정': 감정_분포.index[0] if len(감정_분포) > 0 else "중립",
                        '평균감정강도': f"{부문_data['협업후기_감정강도'].mean():.1f}" if len(부문_data) > 0 else "N/A"
                    })
            
            pd.DataFrame(부문별_분석).to_excel(writer, sheet_name='부문별분석', index=False)
            
            # 부서별 분석 시트 추가
            부서별_분석 = []
            for 부서 in df['피평가대상 부서명'].value_counts().head(10).index:
                부서_data = df[df['피평가대상 부서명'] == 부서]
                감정_분포 = 부서_data['협업후기_주감정'].value_counts()
                감정_분포_str = ', '.join([f"{k}:{v}건" for k, v in 감정_분포.items()])
                
                부서별_분석.append({
                    '피평가부서': 부서,
                    '총피드백수': len(부서_data),
                    '감정분포': 감정_분포_str,
                    '주요감정': 감정_분포.index[0] if len(감정_분포) > 0 else "중립",
                    '평균감정강도': f"{부서_data['협업후기_감정강도'].mean():.1f}" if len(부서_data) > 0 else "N/A"
                })
            
            pd.DataFrame(부서별_분석).to_excel(writer, sheet_name='주요부서별분석', index=False)
        
        print(f"✅ 수정 완료: {output_file}")
        
        # 10. 수정사항 요약
        print(f"\n🎉 수정 및 개선 사항:")
        print(f"1. ✅ 감정분포 형식 수정: 'np.int64' 제거, '긍정:25건, 부정:10건' 형식으로 변경")
        print(f"2. ✅ 의미있는 그룹명 적용: '업무협조감사그룹', '일반감사표현그룹' 등")
        print(f"3. ✅ 부문별/부서별 분석 시트 추가")
        print(f"4. ✅ 유사피드백쌍에 '같은그룹여부' 컬럼 추가")
        print(f"5. ✅ 대시보드 구현을 위한 기초 데이터 완비")
        
        return output_file, cluster_summary
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    result_file, summary = fix_clustering_results()
    
    if result_file:
        print(f"\n{'='*60}")
        print("📋 최종 파일 구성:")
        print("• 분석결과_클러스터포함: 모든 분석 결과 + 클러스터")
        print("• 클러스터별요약: 7개 그룹 특성 분석 (수정된 감정분포)")
        print("• 유사피드백쌍: 중복 이슈 후보들")
        print("• 부문별분석: 6개 부문별 감정 분포")
        print("• 주요부서별분석: 상위 10개 부서별 분석")