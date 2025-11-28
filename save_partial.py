import sys
import pandas as pd
from pathlib import Path
import pickle
import time
import json

class CheckpointManager:
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

def save_partial():
    print("Saving partial results from checkpoints...")
    checkpoint_manager = CheckpointManager()
    
    # Find all checkpoints
    checkpoints = list(checkpoint_manager.checkpoint_dir.glob("checkpoint_*.pkl"))
    if not checkpoints:
        print("No checkpoints found.")
        return

    # Find the latest one
    latest_checkpoint = max(checkpoints, key=lambda x: x.stat().st_mtime)
    print(f"Latest checkpoint: {latest_checkpoint.name}")
    
    # Load it
    try:
        with open(latest_checkpoint, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return
    
    input_file = data['input_file']
    results = data['results']
    
    print(f"Loading original data from {input_file}...")
    # Load original data
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"Error loading input file: {e}")
        return
    
    # Create result dataframe
    cleaned_results = []
    for r in results:
        if r is None:
            cleaned_results.append({
                "정제된_텍스트": "",
                "비식별_처리": False,
                "감정_분류": "",
                "감정_강도_점수": "",
                "핵심_키워드": [],
                "의료_맥락": [],
                "신뢰도_점수": ""
            })
        else:
            # Remove original_text if present
            if "original_text" in r:
                del r["original_text"]
            # Map keys if needed (English to Korean)
            if "refined_text" in r: r["정제된_텍스트"] = r.pop("refined_text")
            if "is_anonymized" in r: r["비식별_처리"] = r.pop("is_anonymized")
            if "sentiment" in r: r["감정_분류"] = r.pop("sentiment")
            if "sentiment_intensity" in r: r["감정_강도_점수"] = r.pop("sentiment_intensity")
            if "key_terms" in r: r["핵심_키워드"] = r.pop("key_terms")
            if "medical_context" in r: r["의료_맥락"] = r.pop("medical_context")
            if "confidence_score" in r: r["신뢰도_점수"] = r.pop("confidence_score")
            
            cleaned_results.append(r)
            
    result_df = pd.DataFrame(cleaned_results)
    
    # Select columns
    analysis_columns = [
        '정제된_텍스트', '비식별_처리', '감정_분류', '감정_강도_점수',
        '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]
    
    # Merge
    final_df = pd.concat([
        df,
        result_df[[col for col in analysis_columns if col in result_df.columns]]
    ], axis=1)
    
    # Save
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"rawdata/2. text_processor_결과_partial_{timestamp}.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        final_df.to_excel(writer, sheet_name='분석 시트', index=False)
        
    print(f"Saved partial results to {output_file}")
    print(f"Processed count: {data.get('processed_count', 0)}")

if __name__ == "__main__":
    save_partial()
