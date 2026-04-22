# 閱讀測驗命題專用模組，負責整合 AI 產出、清理格式、合併題目等

# src/my_project/reading_crew.py
import json
from my_project.crew import ReadingProject 
from my_project.utils import get_reading_examples

DATA_DIR = "src/my_project"

def clean_json_string(raw_str):
    """清理 AI 輸出的 Markdown 標記，確保能轉成 JSON"""
    cleaned = str(raw_str).strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def run_reading_generation(article_content, detail_count=2, theme_count=1):
    """專門負責執行閱讀測驗命題的流程 (支援多老師聯合命題)"""
    
    print(f"正在為您規劃題型：細節題 {detail_count} 題、推論題 {theme_count} 題...")
    
    # 1. 準備 AI 學習範本 (自動從資料夾搜尋歷屆題庫)
    examples_text = get_reading_examples(DATA_DIR, sample_count=3)
    
    if not examples_text or examples_text == "無學習範本可參考。":
        print("⚠️ 警告：無法讀取題庫範本，AI 將在沒有參考的情況下出題。")
        examples_text = "請依照一般國中會考難度出題。"

    # 2. 準備塞給 YAML 的變數 (加入題數分配)
    inputs = {
        'article_content': article_content,
        'examples_str': examples_text,
        'detail_count': detail_count,
        'theme_count': theme_count
    }
    
    try:
        print("啟動【細節擷取專家】與【文意推論專家】雙主將命題中...")
        
        # 3. 取得 Crew 團隊實例並啟動
        crew_instance = ReadingProject().crew()
        crew_instance.kickoff(inputs=inputs)
        
        # 4. 【關鍵技術】分別抓取兩位老師的獨立產出
        # 兼容不同 CrewAI 版本的屬性讀取方式
        detail_raw = crew_instance.tasks[0].output.raw if hasattr(crew_instance.tasks[0].output, 'raw') else str(crew_instance.tasks[0].output)
        theme_raw = crew_instance.tasks[1].output.raw if hasattr(crew_instance.tasks[1].output, 'raw') else str(crew_instance.tasks[1].output)
        
        # 5. 清理並轉換為 JSON 格式 (預期是 Python List)
        try:
            detail_questions = json.loads(clean_json_string(detail_raw))
        except json.JSONDecodeError:
            detail_questions = [{"錯誤": "細節題 JSON 解析失敗", "原始輸出": detail_raw}]
            
        try:
            theme_questions = json.loads(clean_json_string(theme_raw))
        except json.JSONDecodeError:
            theme_questions = [{"錯誤": "推論題 JSON 解析失敗", "原始輸出": theme_raw}]
            
        # 確保兩者都是 List (陣列)，避免 AI 偶爾只回傳單一字典
        if isinstance(detail_questions, dict): detail_questions = [detail_questions]
        if isinstance(theme_questions, dict): theme_questions = [theme_questions]
            
        # 6. 把兩位老師的題目合併成一份完整的考卷
        final_exam_paper = {
            "試卷標題": "AI 閱讀測驗專題",
            "文章內容": article_content,
            "總題數": len(detail_questions) + len(theme_questions),
            "題目列表": detail_questions + theme_questions
        }
        
        return final_exam_paper
        
    except Exception as e:
        print(f"\n命題發生錯誤: {e}")
        return {"error": str(e)}