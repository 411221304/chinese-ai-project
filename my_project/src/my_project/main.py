# src/my_project/main.py

import sys
import json
from my_project.essay_crew import run_essay_grading
from my_project.utils import generate_full_mock_exam
from my_project.auto_crew import run_proportional_ai_exam 

# 🌟 新增：引入學習診斷報告核心
from my_project.report_crew import run_diagnostic_report

def run():
    print("="*50)
    print("👑 歡迎使用 AI 語文學習系統 (開發者測試主控台)")
    print("="*50)
    print("1. ✍️ 作文檢測模式 (需提供學生作文)")
    print("2. 📚 智能歷屆組卷 (自動從 Excel 題庫抽題組卷)")
    print("3. 🌟 AI 原創模擬考 (依歷屆比例，AI 憑空生成完整 42 題)")
    print("4. 📊 AI 學習診斷報告 (帶入模擬測驗數據測試)") # 🌟 新增的選項 4
    print("0. 離開系統")
    print("="*50)
    
    choice = input("請輸入數字代號 (0~4): ")
    
    if choice == '1':
        print("\n--- 進入作文檢測模式 ---")
        topic = input("請輸入作文題目: ")
        content = input("請貼上學生作文內容: ")
        print("\n正在進行深度批改，請稍候...")
        result_json = run_essay_grading(topic, content)
        print("\n" + "="*40)
        print("AI 綜合評閱成績單 (JSON 格式)：")
        print("="*40)
        print(json.dumps(result_json, indent=2, ensure_ascii=False))
        
    elif choice == '2':
        print("\n--- 進入智能歷屆題庫組卷 ---")
        print("系統正在從歷屆題庫中為您隨機抽題，組合完整試卷...")
        exam_json = generate_full_mock_exam(data_dir="src/my_project", single_q_count=28, group_q_count=14)
        print("\n" + "="*40)
        print("💯 完整模擬試卷產生完畢 (JSON 格式)：")
        print("="*40)
        print(json.dumps(exam_json, indent=2, ensure_ascii=False))

    elif choice == '3':
        print("\n--- 進入 AI 原創模擬考系統 ---")
        print("系統正在準備為您生成整份模擬考卷...")
        result_json = run_proportional_ai_exam(total_questions=42) 
        
        output_filename = "AI_Mock_Exam_42Q.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)
            
        print("\n" + "="*40)
        print("🎉 恭喜！42 題大考卷已成功生成！")
        print(f"📁 檔案已自動儲存至：{output_filename}")
        print("="*40)
        
    elif choice == '4':  # 🌟 新增：診斷報告測試區
        print("\n--- 進入 AI 學習診斷報告測試 ---")
        print("將使用預設的虛擬學生成績數據進行測試...")
        
        mock_student_data = {
            "總題數": 42,
            "答對題數": 28,
            "答錯題數": 14,
            "表現優異項目": ["白話文閱讀理解", "修辭判別"],
            "待加強項目": ["文言文文意推論 (錯 6 題)", "成語運用 (錯 4 題)"],
            "學習特徵": "長篇文章耐心足夠，但古文語感與單字量明顯不足。"
        }
        
        report = run_diagnostic_report(mock_student_data)
        
        print("\n" + "="*50)
        print("📝 專屬學習診斷報告 (Markdown)")
        print("="*50)
        print(report)

    elif choice == '0':
        print("系統已關閉。")
        sys.exit(0)
    else:
        print("輸入錯誤，請重新執行程式。")

if __name__ == "__main__":
    run()