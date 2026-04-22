# 作文批改專用模組

# src/my_project/essay_crew.py
import json
from my_project.crew import MyProject 
from my_project.utils import analyze_essay_stats, get_rubric_from_excel, get_examples_from_excel

EXCEL_FILE = "src/my_project/ExamSystem_GoogleSheet_Template.xlsx"

def run_essay_grading(topic, content):
    """專門負責執行作文批改的流程"""
    rubric_text = get_rubric_from_excel(EXCEL_FILE)
    examples_text = get_examples_from_excel(EXCEL_FILE)
    essay_stats_text = analyze_essay_stats(content)
    
    inputs = {
        'essay_topic': topic,
        'essay_content': content,
        'grading_rubric': rubric_text,
        'example_essays': examples_text,
        'essay_stats': essay_stats_text
    }
    
    try:
        result = MyProject().crew().kickoff(inputs=inputs)
        
        raw_output = result.raw.strip()
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
            
        return json.loads(raw_output.strip())
        
    except Exception as e:
        print(f"\n批改發生錯誤: {e}")
        return {"error": str(e)}