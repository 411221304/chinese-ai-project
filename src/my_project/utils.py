# 分析數據、處理文本、讀取 Excel、組卷等工具函式都放在這裡

#  src/my_project/utils.py
import pandas as pd
import jieba
import re
import sys
import random
import math
import glob
import os

# ==========================================
# ✍️ 作文批改專用工具
# ==========================================
def analyze_essay_stats(content):
    clean_content = content.replace(" ", "").replace("\n", "").replace("\r", "")
    total_chars = len(clean_content)
    if total_chars == 0: return "無法分析：文章為空"
    sentences = re.split(r'[。！？]', clean_content)
    sentences = [s for s in sentences if len(s) > 0] 
    total_sentences = len(sentences)
    avg_sentence_length = total_chars / total_sentences if total_sentences > 0 else total_chars
    words = list(jieba.cut(clean_content))
    words = [w for w in words if re.match(r'^[\u4e00-\u9fa5]+$', w)]
    total_words = len(words)
    unique_words = len(set(words))
    ttr = (unique_words / total_words * 100) if total_words > 0 else 0
    stats_report = (
        f"📊【客觀數據分析報告】\n"
        f"- 總字數 (不含空白)：{total_chars} 字\n"
        f"- 總句數：{total_sentences} 句\n"
        f"- 平均句長：約 {avg_sentence_length:.1f} 字/句\n"
        f"- 總詞彙數：{total_words} 個\n"
        f"- 不重複詞彙數：{unique_words} 個\n"
        f"- 詞彙豐富度 (TTR)：{ttr:.1f}%\n"
    )
    return stats_report

def get_rubric_from_excel(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name='會考作文批改標準')
        rubric_str = ""
        for index, row in df.iterrows():
            rubric_str += f"【{row['grade']} 級分：{row['comment']}】\n"
            rubric_str += f"- 立意取材：{row['Ideas & Substance']}\n"
            rubric_str += f"- 結構組織：{row['Structure & Organization']}\n"
            rubric_str += f"- 遣詞造句：{row['Vocabulary & Phrasing']}\n"
            rubric_str += f"- 標點與格式：{row['Punctuation, Spelling & Format']}\n\n"
        return rubric_str
    except Exception as e:
        print(f"讀取評分標準失敗：{e}")
        sys.exit(1)

def get_examples_from_excel(file_path, total_sample_size=10):
    try:
        df = pd.read_excel(file_path, sheet_name='歷屆作文範文')
        df = df.dropna(subset=['content', 'review'])
        sampled_indices = []
        target_grades = [1, 2, 3, 4, 5, 6]
        for grade in target_grades:
            grade_df = df[df['grade(0-6)'] == grade]
            if not grade_df.empty:
                chosen_index = grade_df.sample(n=1).index[0]
                sampled_indices.append(chosen_index)
        remaining_count = total_sample_size - len(sampled_indices)
        if remaining_count > 0:
            remaining_df = df.drop(index=sampled_indices)
            draw_count = min(remaining_count, len(remaining_df))
            extra_indices = remaining_df.sample(n=draw_count).index.tolist()
            sampled_indices.extend(extra_indices)
        final_sampled_df = df.loc[sampled_indices].sample(frac=1)
        examples_str = ""
        for index, row in final_sampled_df.iterrows():
            examples_str += f"【歷屆範文參考】\n獲得級分：{row['grade(0-6)']} 級分\n"
            examples_str += f"作文內容：\n{row['content']}\n\n官方評語：\n{row['review']}\n"
            examples_str += "-" * 40 + "\n\n"
        return examples_str
    except Exception as e:
        print(f"讀取歷屆範文失敗：{e}")
        sys.exit(1)


# ==========================================
# 📖 閱讀命題與組卷專用工具
# ==========================================
def load_all_past_exams(data_dir):
    """內部輔助函式：載入 109~114 的所有題庫並合併"""
    all_merged_data = []
    years = ['109', '110', '111', '112', '113', '114']
    
    for year in years:
        try:
            q_files = glob.glob(os.path.join(data_dir, f"*{year}歷屆.csv"))
            opt_files = glob.glob(os.path.join(data_dir, f"*{year}歷屆選項.csv"))
            ans_files = glob.glob(os.path.join(data_dir, f"*{year}歷屆詳解.csv"))
            
            if q_files and opt_files and ans_files:
                df_q = pd.read_csv(q_files[0])
                df_opt = pd.read_csv(opt_files[0])
                df_ans = pd.read_csv(ans_files[0])
                
                if 'id' in df_opt.columns: df_opt = df_opt.drop(columns=['id'])
                if 'id' in df_ans.columns: df_ans = df_ans.drop(columns=['id'])
                    
                merged_df = pd.merge(df_q, df_opt, left_on='id', right_on='question_id', how='left')
                merged_df = pd.merge(merged_df, df_ans, left_on='id', right_on='question_id', how='left')
                all_merged_data.append(merged_df)
        except Exception as e:
            pass
            
    if not all_merged_data:
        return None
    return pd.concat(all_merged_data, ignore_index=True)


def get_reading_examples(data_dir="src/my_project", sample_count=3):
    """給 AI 看的歷屆範本"""
    final_db = load_all_past_exams(data_dir)
    if final_db is None:
        return "無學習範本可參考。"
        
    draw_count = min(sample_count, len(final_db))
    if draw_count == 0:
         return "無學習範本可參考。"
         
    sampled_df = final_db.sample(n=draw_count)
    examples_str = ""
    for index, row in sampled_df.iterrows():
        examples_str += f"【年份】：{row.get('year', '')}年\n"
        examples_str += f"【文章內容】：\n{row.get('description', '無文章')}\n"
        examples_str += f"【題幹】：{row.get('title', '')}\n"
        examples_str += f"【選項】：\n(A) {row.get('選項A', '')}\n(B) {row.get('選項B', '')}\n(C) {row.get('選項C', '')}\n(D) {row.get('選項D', '')}\n"
        examples_str += f"【正確答案】：{row.get('answer', '')}\n"
        examples_str += f"【詳解】：{row.get('content', '無提供詳解')}\n"
        examples_str += "=" * 40 + "\n\n"
    return examples_str


def generate_full_mock_exam(data_dir="src/my_project", single_q_count=15, group_q_count=5):
    """智能組卷系統：自動從題庫撈取單題與題組"""
    df = load_all_past_exams(data_dir)
    if df is None:
        return {"error": "找不到題庫資料，無法組卷"}
        
    # 填補空值，避免字串過濾報錯
    df['type'] = df['type'].fillna('')
    
    df_single = df[df['type'].str.contains('單題', na=False)]
    df_group = df[df['type'].str.contains('題組', na=False)]
    
    sampled_single = df_single.sample(n=min(single_q_count, len(df_single)))
    sampled_group = df_group.sample(n=min(group_q_count, len(df_group)))
    
    exam_paper = {
        "試卷名稱": "AI 歷屆精選國文模擬考",
        "單題部分": [],
        "題組部分": []
    }
    
    for idx, row in sampled_single.iterrows():
        exam_paper["單題部分"].append({
            "年份": str(row.get('year', '')),
            "題型": str(row.get('type', '單題')),
            "題幹": str(row.get('title', '')),
            "選項": {
                "A": str(row.get('選項A', '')),
                "B": str(row.get('選項B', '')),
                "C": str(row.get('選項C', '')),
                "D": str(row.get('選項D', ''))
            },
            "答案": str(row.get('answer', '')),
            "詳解": str(row.get('content', ''))
        })
        
    for idx, row in sampled_group.iterrows():
        exam_paper["題組部分"].append({
            "年份": str(row.get('year', '')),
            "題型": str(row.get('type', '題組')),
            "文章內容": str(row.get('description', '')),
            "題幹": str(row.get('title', '')),
            "選項": {
                "A": str(row.get('選項A', '')),
                "B": str(row.get('選項B', '')),
                "C": str(row.get('選項C', '')),
                "D": str(row.get('選項D', ''))
            },
            "答案": str(row.get('answer', '')),
            "詳解": str(row.get('content', ''))
        })
        
    return exam_paper
# 請貼在 utils.py 的最下方
def get_exam_proportions(data_dir="src/my_project", total_q=42):
    """分析歷屆題庫，計算單題與題組的最佳比例"""
    df = load_all_past_exams(data_dir)
    
    # 防呆：如果找不到題庫，就給定會考預設比例 (約 65% 單題, 35% 題組)
    if df is None:
        single_count = round(total_q * 0.65)
        return single_count, total_q - single_count

    df['type'] = df['type'].fillna('')
    single_total = len(df[df['type'].str.contains('單題', na=False)])
    group_total = len(df[df['type'].str.contains('題組', na=False)])
    history_total = single_total + group_total

    if history_total == 0:
        single_count = round(total_q * 0.65)
    else:
        single_count = round((single_total / history_total) * total_q)

    group_count = total_q - single_count
    return single_count, group_count