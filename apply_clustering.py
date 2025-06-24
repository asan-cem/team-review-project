import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

def apply_clustering_to_analysis():
    """실제로 클러스터링을 적용하는 함수"""
    
    print("🔧 협업 후기 클러스터링 적용 시작")
    print("=" * 50)
    
    try:
        # 1. 분석된 파일 읽기
        print("📁 분석 파일 로드 중...")
        df = pd.read_excel('협업후기_분석결과_상위200건.xlsx', engine='openpyxl')
        print(f"✅ {len(df)}건 로드 완료")
        
        # 2. 유효한 텍스트만 추출 (의료용어 제외)
        print("\n📊 클러스터링 대상 텍스트 준비...")
        valid_mask = df['협업후기_정제텍스트'].notna() & (df['협업후기_정제텍스트'].str.len() > 3)
        valid_df = df[valid_mask].copy()
        
        texts = valid_df['협업후기_정제텍스트'].tolist()
        print(f"✅ 유효한 텍스트: {len(texts)}건")
        
        if len(texts) < 5:
            print("❌ 클러스터링을 위한 텍스트가 부족합니다.")
            return
        
        # 3. TF-IDF 벡터화 (의료용어 제외 처리)
        print("\n🔤 TF-IDF 벡터화 중...")
        
        # 한국어 불용어 및 의미없는 단어들
        stop_words = [
            '없습니다', '감사합니다', '만족', '항상', '매우', '정말', '너무', '아주',
            '없음', '해당없음', '무', '...', '....', '.', 'x000d'
        ]
        
        vectorizer = TfidfVectorizer(
            max_features=80,           # 특성 수 조정
            min_df=2,                  # 최소 2번 이상 등장
            max_df=0.8,                # 80% 이상 문서에 등장하는 단어 제외
            ngram_range=(1, 2),        # 1-2 단어 조합
            stop_words=stop_words      # 불용어 제외
        )
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        print(f"✅ 벡터 크기: {tfidf_matrix.shape}")
        
        # 4. 최적 클러스터 수 결정
        n_clusters = min(8, max(3, len(texts) // 20))  # 3~8개 클러스터
        print(f"\n🎯 {n_clusters}개 클러스터로 K-means 실행...")
        
        # 5. K-means 클러스터링
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        # 6. 클러스터 분포 확인
        cluster_counts = Counter(clusters)
        print(f"📊 클러스터 분포: {dict(cluster_counts)}")
        
        # 7. 원본 DataFrame에 클러스터 결과 추가
        print("\n📋 클러스터 결과를 원본 데이터에 추가...")
        df['협업후기_클러스터'] = np.nan
        df.loc[valid_mask, '협업후기_클러스터'] = clusters
        
        # 클러스터 번호를 의미있는 이름으로 변경
        cluster_names = {}
        for i in range(n_clusters):
            cluster_names[i] = f"그룹{i+1}"
        
        df['협업후기_클러스터그룹'] = df['협업후기_클러스터'].map(cluster_names)
        
        # 8. 클러스터별 상세 분석
        print("\n📝 클러스터별 특성 분석...")
        cluster_summary = []
        feature_names = vectorizer.get_feature_names_out()
        
        for i in range(n_clusters):
            cluster_mask = (df['협업후기_클러스터'] == i)
            cluster_data = df[cluster_mask]
            
            # 클러스터 대표 키워드 (상위 5개)
            cluster_center = kmeans.cluster_centers_[i]
            top_indices = cluster_center.argsort()[-5:][::-1]
            keywords = [feature_names[idx] for idx in top_indices]
            
            # 감정 분포
            sentiments = cluster_data['협업후기_주감정'].value_counts()
            main_sentiment = sentiments.index[0] if len(sentiments) > 0 else "중립"
            sentiment_dist = dict(sentiments)
            
            # 세부감정 분포
            detailed_sentiments = cluster_data['협업후기_세부감정'].value_counts()
            main_detailed = detailed_sentiments.index[0] if len(detailed_sentiments) > 0 else "기타"
            
            # 평균 감정 강도
            avg_intensity = cluster_data['협업후기_감정강도'].mean() if len(cluster_data) > 0 else 5.0
            
            # 대표 예시 (가장 센터에 가까운 텍스트)
            if len(cluster_data) > 0:
                cluster_texts = cluster_data['협업후기_정제텍스트'].tolist()
                # 클러스터 중심에 가장 가까운 텍스트 찾기
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
                '클러스터그룹': f"그룹{i+1}",
                '피드백수': len(cluster_data),
                '비율': f"{len(cluster_data)/len(df)*100:.1f}%",
                '주요키워드': ' | '.join(keywords[:3]),  # 상위 3개만
                '전체키워드': ' | '.join(keywords),
                '주감정': main_sentiment,
                '세부감정': main_detailed,
                '평균감정강도': f"{avg_intensity:.1f}",
                '감정분포': str(sentiment_dist),
                '대표예시': representative_text[:80] + "..." if len(representative_text) > 80 else representative_text
            })
            
            print(f"  그룹{i+1}: {len(cluster_data)}건 ({len(cluster_data)/len(df)*100:.1f}%) - {' | '.join(keywords[:2])}")
        
        # 9. 유사도가 높은 피드백 쌍 찾기
        print("\n📏 유사도 높은 피드백 쌍 분석...")
        similarity_pairs = []
        
        # 샘플로 상위 50건만 계산 (계산 시간 단축)
        sample_size = min(50, len(texts))
        sample_matrix = tfidf_matrix[:sample_size]
        similarity_matrix = cosine_similarity(sample_matrix)
        
        for i in range(sample_size):
            for j in range(i+1, sample_size):
                similarity = similarity_matrix[i][j]
                if similarity > 0.3:  # 30% 이상 유사한 경우
                    similarity_pairs.append({
                        '텍스트1_번호': i+1,
                        '텍스트2_번호': j+1,
                        '유사도': f"{similarity:.3f}",
                        '텍스트1': texts[i][:50] + "...",
                        '텍스트2': texts[j][:50] + "...",
                        '클러스터1': f"그룹{clusters[i]+1}",
                        '클러스터2': f"그룹{clusters[j]+1}"
                    })
        
        print(f"✅ 유사도 30% 이상인 피드백 쌍: {len(similarity_pairs)}개 발견")
        
        # 10. 결과를 Excel 파일로 저장
        print("\n💾 클러스터링 결과 저장...")
        output_file = '협업후기_분석결과_클러스터링포함_상위200건.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 메인 시트: 기존 분석 + 클러스터 결과
            df.to_excel(writer, sheet_name='분석결과_클러스터포함', index=False)
            
            # 클러스터 요약 시트
            pd.DataFrame(cluster_summary).to_excel(writer, sheet_name='클러스터별요약', index=False)
            
            # 유사 피드백 쌍 시트
            if similarity_pairs:
                pd.DataFrame(similarity_pairs).to_excel(writer, sheet_name='유사피드백쌍', index=False)
        
        print(f"✅ 저장 완료: {output_file}")
        
        # 11. 최종 요약 출력
        print(f"\n🎉 클러스터링 적용 완료!")
        print(f"📊 총 {n_clusters}개 그룹으로 분류")
        print(f"📋 추가된 컬럼: '협업후기_클러스터', '협업후기_클러스터그룹'")
        print(f"📑 생성된 시트: '클러스터별요약', '유사피드백쌍'")
        
        print(f"\n📈 그룹별 분포:")
        for summary in cluster_summary:
            print(f"  {summary['클러스터그룹']}: {summary['피드백수']}건 ({summary['비율']}) - {summary['주요키워드']}")
        
        return output_file, cluster_summary
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    result_file, summary = apply_clustering_to_analysis()
    
    if result_file:
        print(f"\n{'='*60}")
        print("🎯 클러스터링 결과 활용 가이드:")
        print("1. Excel 파일을 열어 '클러스터별요약' 시트 확인")
        print("2. '유사피드백쌍' 시트에서 중복 이슈 확인")
        print("3. 메인 시트에서 그룹별 필터링하여 패턴 분석")
        print("4. 각 그룹의 대표 이슈를 바탕으로 개선 계획 수립")