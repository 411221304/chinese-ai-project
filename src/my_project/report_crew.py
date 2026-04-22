# 處理生成學習診斷報告的 Crew 定義和執行函式

# src/my_project/report_crew.py
import json
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class ReportProject():
    """學習診斷報告團隊"""
    
    agents_config = 'config/report_agents.yaml'
    tasks_config = 'config/report_tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def diagnostic_tutor_agent(self) -> Agent:
        return Agent(config=self.agents_config['diagnostic_tutor_agent'], verbose=True) # type: ignore

    @task
    def generate_diagnostic_report_task(self) -> Task:
        return Task(config=self.tasks_config['generate_diagnostic_report_task']) # type: ignore

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )

def run_diagnostic_report(student_stats_dict):
    """執行生成報告：接收一個包含統計數據的字典，轉成字串餵給 AI"""
    
    print("\n👩‍🏫 王牌導師正在分析您的作答數據...")
    
    # 將字典轉換為漂亮的 JSON 字串，方便 AI 閱讀
    stats_str = json.dumps(student_stats_dict, indent=2, ensure_ascii=False)
    
    inputs = {
        'student_stats': stats_str
    }
    
    try:
        result = ReportProject().crew().kickoff(inputs=inputs)
        
        # 報告是純文字 (Markdown)，直接回傳字串即可
        report_content = result.raw if hasattr(result, 'raw') else str(result)
        return report_content.strip()
        
    except Exception as e:
        return f"報告生成發生錯誤: {str(e)}"