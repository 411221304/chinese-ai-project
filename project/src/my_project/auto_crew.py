# 自動命題crew模組

# src/my_project/auto_crew.py
import json
import math
import re  # 🌟 必須引入這個套件來進行強制擷取

from my_project.crew import AutoGenerationProject
from my_project.utils import get_exam_proportions

def clean_json_string(raw_str):
    """終極清理器：利用正則表達式硬生生把 JSON 陣列挖出來"""
    cleaned = str(raw_str).strip()
    
    # 🌟 尋找從第一個 '[' 到最後一個 ']' 之間的所有內容 (包含換行)
    match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    
    if match:
        return match.group(0) # 只回傳乾淨的 JSON 陣列部分
    
    # 如果真的找不到陣列括號，才退回原本的去頭去尾法當作保底
    if cleaned.startswith("```json"): 
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"): 
        cleaned = cleaned[3:]
    if cleaned.endswith("```"): 
        cleaned = cleaned[:-3]
    return cleaned.strip()

def run_proportional_ai_exam(total_questions=42):
    """終極功能：根據歷屆比例，AI 全原創生成完整模擬考卷"""
    
    print(f"\n📊 正在分析歷屆題庫，計算最佳出題比例...")
    
    # 1. 取得歷屆比例
    single_count, group_count = get_exam_proportions(total_q=total_questions)
    
    # 核心邏輯：計算題組需要幾篇文章 (假設每篇平均配 2.5 題)
    if group_count > 0:
        article_count = max(1, round(group_count / 2.5))
    else:
        article_count = 0
        
    print(f"🎯 計算完成！本次將生成：")
    print(f"  👉 【單題部分】：{single_count} 題 (含語文常識與短文單題)")
    print(f"  👉 【題組部分】：{group_count} 題 (分配於 {article_count} 篇長篇文章中)")
    
    # 準備傳給 YAML 任務的變數
    inputs = {
        'single_count': single_count,
        'group_count': group_count,
        'article_count': article_count 
    }
    
    try:
        print("\n🚀 AI 原創命題團隊雙主將出動中！(需生成完整考卷，約需 1~3 分鐘，請耐心等候...)")
        
        # 啟動兩個團隊
        knowledge_crew = AutoGenerationProject().knowledge_crew()
        reading_crew = AutoGenerationProject().creative_reading_crew()
        
        # 讓國學大師出單題
        knowledge_result = knowledge_crew.kickoff(inputs=inputs)
        print("✅ 單題部分生成完畢！正在請暢銷作家生成長篇題組...")
        
        # 讓暢銷作家出題組
        reading_result = reading_crew.kickoff(inputs=inputs)
        print("✅ 題組部分生成完畢！正在為您組合考卷...")
        
        # 兼容輸出格式
        know_raw = knowledge_result.raw if hasattr(knowledge_result, 'raw') else str(knowledge_result)
        read_raw = reading_result.raw if hasattr(reading_result, 'raw') else str(reading_result)
        
        # 轉為 JSON (此時會呼叫我們上面寫好的超強 Regex 清理器)
        try: know_json = json.loads(clean_json_string(know_raw))
        except: know_json = [{"錯誤": "單題 JSON 解析失敗", "內容": know_raw}]
            
        try: read_json = json.loads(clean_json_string(read_raw))
        except: read_json = [{"錯誤": "題組 JSON 解析失敗", "內容": read_raw}]
            
        # 確保格式為陣列 (List)
        if isinstance(know_json, dict): know_json = [know_json]
        if isinstance(read_json, dict): read_json = [read_json]
            
        # 合併成終極大考卷
        ultimate_exam = {
            "試卷名稱": f"AI 原創超擬真模擬考 (共 {total_questions} 題)",
            "單題部分": know_json,
            "題組部分": read_json
        }
        
        return ultimate_exam
        
    except Exception as e:
        print(f"\n❌ 命題發生致命錯誤: {e}")
        return {"error": f"命題過程發生錯誤: {str(e)}"}

# ==========================================
# 保留單獨測試用的函式 (選項中雖然沒用到，但開發時備用)
# ==========================================
def run_auto_knowledge():
    try:
        result = AutoGenerationProject().knowledge_crew().kickoff(inputs={'single_count': 1})
        raw = result.raw if hasattr(result, 'raw') else str(result)
        return json.loads(clean_json_string(raw))
    except Exception as e:
        return {"error": str(e)}

def run_auto_reading():
    try:
        result = AutoGenerationProject().creative_reading_crew().kickoff(inputs={'group_count': 2, 'article_count': 1})
        raw = result.raw if hasattr(result, 'raw') else str(result)
        return json.loads(clean_json_string(raw))
    except Exception as e:
        return {"error": str(e)}