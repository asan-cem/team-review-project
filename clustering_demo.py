import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

def demo_clustering_process():
    """클러스터링 과정 데모"""
    
    print("🔍 텍스트 유사도 및 클러스터링 구현 방식 설명")
    print("=" * 60)
    
    # 1. 현재 분석된 파일 읽기
    try:
        df = pd.read_excel('협업후기_분석결과_상위200건.xlsx', engine='openpyxl')
        print(f"✅ 분석 파일 로드: {len(df)}건")
    except:
        print("❌ 분석 파일이 없습니다. 먼저 텍스트 분석을 완료하세요.")
        return
    
    # 2. 텍스트 데이터 준비
    texts = df['협업후기_정제텍스트'].fillna('').tolist()
    valid_texts = [t for t in texts if len(str(t).strip()) > 0]
    
    print(f"📊 클러스터링 대상: {len(valid_texts)}건")
    
    # 3. TF-IDF 벡터화
    print("\n🔤 1단계: TF-IDF 벡터화")
    vectorizer = TfidfVectorizer(
        max_features=100,  # 상위 100개 단어만 사용
        stop_words=None,   # 한국어 불용어는 별도 처리
        ngram_range=(1, 2) # 1-2 단어 조합
    )
    
    if len(valid_texts) > 5:  # 최소 5개 이상의 텍스트가 있을 때만
        tfidf_matrix = vectorizer.fit_transform(valid_texts)
        print(f"   벡터 크기: {tfidf_matrix.shape}")
        
        # 4. K-means 클러스터링
        print("\n🎯 2단계: K-means 클러스터링")
        n_clusters = min(5, len(valid_texts) // 10)  # 클러스터 수 자동 결정
        if n_clusters < 2:
            n_clusters = 2
            
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        print(f"   클러스터 수: {n_clusters}")
        
        # 5. 클러스터별 분포
        cluster_counts = Counter(clusters)
        print(f"   클러스터 분포: {dict(cluster_counts)}")
        
        # 6. 각 클러스터의 대표 키워드
        print("\n📝 3단계: 클러스터별 대표 키워드")
        feature_names = vectorizer.get_feature_names_out()
        
        for i in range(n_clusters):
            cluster_center = kmeans.cluster_centers_[i]
            top_indices = cluster_center.argsort()[-5:][::-1]  # 상위 5개
            top_words = [feature_names[idx] for idx in top_indices]
            
            cluster_texts = [valid_texts[j] for j in range(len(valid_texts)) if clusters[j] == i]
            print(f"   클러스터 {i}: {', '.join(top_words)} ({len(cluster_texts)}건)")
            if cluster_texts:
                print(f"     예시: {cluster_texts[0][:50]}...")
        
        # 7. 유사도 계산 (샘플)
        print("\n📏 4단계: 텍스트 유사도 계산 (상위 5건)")
        similarity_matrix = cosine_similarity(tfidf_matrix[:5])
        
        for i in range(min(5, len(valid_texts))):
            for j in range(i+1, min(5, len(valid_texts))):
                similarity = similarity_matrix[i][j]
                if similarity > 0.1:  # 유사도가 0.1 이상인 경우만
                    print(f"   텍스트 {i+1} ↔ 텍스트 {j+1}: {similarity:.3f}")
                    print(f"     1: {valid_texts[i][:30]}...")
                    print(f"     2: {valid_texts[j][:30]}...")
                    print()
    
    print("\n" + "=" * 60)
    print("💡 클러스터링 결과 활용 방안:")
    print("1. 엑셀 컬럼 추가: 각 피드백의 클러스터 번호")
    print("2. 별도 시트: 클러스터별 요약 및 대표 피드백")
    print("3. 시각화: 클러스터 분포도 및 워드클라우드")
    print("4. 유사 피드백 그룹핑: 중복 이슈 식별")

def add_clustering_to_excel():
    """실제로 클러스터링 결과를 엑셀에 추가하는 함수"""
    
    print("\n🔧 실제 클러스터링 적용")
    print("=" * 40)
    
    try:
        # 분석된 파일 읽기
        df = pd.read_excel('협업후기_분석결과_상위200건.xlsx', engine='openpyxl')
        
        # 유효한 텍스트만 추출
        valid_indices = df['협업후기_정제텍스트'].notna() & (df['협업후기_정제텍스트'].str.len() > 0)
        valid_df = df[valid_indices].copy()
        
        if len(valid_df) < 5:
            print("❌ 클러스터링을 위한 텍스트가 부족합니다.")
            return
        
        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer(max_features=50, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(valid_df['협업후기_정제텍스트'])
        
        # K-means 클러스터링
        n_clusters = min(8, len(valid_df) // 15)  # 적절한 클러스터 수
        if n_clusters < 2:
            n_clusters = 2
            
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        # 원본 DataFrame에 클러스터 결과 추가
        df['협업후기_클러스터'] = np.nan
        df.loc[valid_indices, '협업후기_클러스터'] = clusters
        
        # 클러스터별 요약 생성
        cluster_summary = []
        feature_names = vectorizer.get_feature_names_out()
        
        for i in range(n_clusters):
            cluster_mask = (df['협업후기_클러스터'] == i)
            cluster_data = df[cluster_mask]
            
            # 클러스터 대표 키워드
            cluster_center = kmeans.cluster_centers_[i]
            top_indices = cluster_center.argsort()[-3:][::-1]
            keywords = [feature_names[idx] for idx in top_indices]
            
            # 감정 분포
            sentiments = cluster_data['협업후기_주감정'].value_counts()
            main_sentiment = sentiments.index[0] if len(sentiments) > 0 else "중립"
            
            cluster_summary.append({
                '클러스터': f"그룹 {i+1}",
                '건수': len(cluster_data),
                '주요키워드': ', '.join(keywords),
                '주감정': main_sentiment,
                '대표예시': cluster_data['협업후기_정제텍스트'].iloc[0][:50] + "..." if len(cluster_data) > 0 else ""
            })
        
        # 결과 저장
        output_file = '협업후기_분석결과_클러스터링포함_상위200건.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 메인 시트 (기존 분석 + 클러스터)
            df.to_excel(writer, sheet_name='분석결과', index=False)
            
            # 클러스터 요약 시트
            pd.DataFrame(cluster_summary).to_excel(writer, sheet_name='클러스터요약', index=False)
        
        print(f"✅ 클러스터링 결과 저장: {output_file}")
        print(f"📊 {n_clusters}개 클러스터로 분류")
        
        # 클러스터별 분포 출력
        print(f"\n📈 클러스터별 분포:")
        cluster_counts = df['협업후기_클러스터'].value_counts().sort_index()
        for cluster_id, count in cluster_counts.items():
            if pd.notna(cluster_id):
                print(f"  그룹 {int(cluster_id)+1}: {count}건")
        
        return output_file
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 1. 클러스터링 과정 설명
    demo_clustering_process()
    
    # 2. 실제 적용 여부 확인
    print(f"\n{'='*60}")
    print("🤔 실제로 클러스터링을 적용하시겠습니까?")
    print("- 현재 분석 파일에 '협업후기_클러스터' 컬럼이 추가됩니다")
    print("- 별도 '클러스터요약' 시트가 생성됩니다")
    print("- 유사한 피드백들이 그룹별로 분류됩니다")