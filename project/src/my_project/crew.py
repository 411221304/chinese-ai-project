# 定義 Crew 團隊與 Agent 的核心模組，這裡是整個系統的「大腦」，負責協調不同部門的工作流程

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

# 🌟 關鍵修改 1：在這裡引入我們剛剛寫好的萌典 API 工具
from my_project.tools.tool import TaiwanIdiomTool

# ==========================================
# 📝 第一組團隊：作文批改部門
# ==========================================
@CrewBase
class MyProject():
    """Essay Grader crew"""

    # 🌟 明確指定作文部門的 YAML 路徑
    agents_config = 'config/essay_agents.yaml'
    tasks_config = 'config/essay_tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    # --- 註冊作文 Agents ---
    @agent
    def grammar_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['grammar_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def structure_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['structure_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def chief_evaluator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['chief_evaluator_agent'], # type: ignore[index]
            verbose=True
        )

    # --- 註冊作文 Tasks ---
    @task
    def grammar_task(self) -> Task:
        return Task(
            config=self.tasks_config['grammar_task'], # type: ignore[index]
        )

    @task
    def structure_task(self) -> Task:
        return Task(
            config=self.tasks_config['structure_task'], # type: ignore[index]
        )

    @task
    def scoring_task(self) -> Task:
        return Task(
            config=self.tasks_config['scoring_task'], # type: ignore[index]
            output_file='essay_feedback.md' 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Essay Grader crew"""
        return Crew(
            agents=self.agents, 
            tasks=self.tasks,  
            process=Process.sequential, 
            verbose=True,
        )


# ==========================================
# 📖 第二組團隊：閱讀測驗命題部門
# ==========================================
@CrewBase
class ReadingProject():
    """Reading Question Generator crew"""
    
    # 🌟 明確指定閱讀部門的 YAML 路徑
    agents_config = 'config/reading_agents.yaml'
    tasks_config = 'config/reading_tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    # --- 註冊閱讀 Agents (對應 reading_agents.yaml) ---
    @agent
    def detail_extraction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['detail_extraction_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def theme_inference_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['theme_inference_agent'], # type: ignore[index]
            verbose=True
        )

    # --- 註冊閱讀 Tasks (對應 reading_tasks.yaml) ---
    @task
    def generate_detail_question_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_detail_question_task'], # type: ignore[index]
        )

    @task
    def generate_theme_question_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_theme_question_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Reading Question Generator crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential, # 依序執行，先出細節題，再出推論題
            verbose=True,
        )


# ==========================================
# ✨ 第三組團隊：原創命題部門 (無中生有)
# ==========================================
@CrewBase
class AutoGenerationProject():
    """負責憑空生成國學常識與原創文章題組的團隊"""
    
    # 🌟 這裡已經修正！指向專屬於「原創部門」的設定檔
    agents_config = 'config/auto_agents.yaml'
    tasks_config = 'config/auto_tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def knowledge_expert_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['knowledge_expert_agent'], 
            tools=[TaiwanIdiomTool()], # 🌟 關鍵修改 2：把成語辭典工具配發給這位國學大師
            verbose=True
        ) # type: ignore

    @agent
    def creative_author_agent(self) -> Agent:
        return Agent(config=self.agents_config['creative_author_agent'], verbose=True) # type: ignore

    @task
    def generate_knowledge_task(self) -> Task:
        return Task(config=self.tasks_config['generate_knowledge_task']) # type: ignore

    @task
    def generate_creative_reading_task(self) -> Task:
        return Task(config=self.tasks_config['generate_creative_reading_task']) # type: ignore

    @crew
    def knowledge_crew(self) -> Crew:
        """專門出國學常識的團隊"""
        return Crew(
            agents=[self.knowledge_expert_agent()],
            tasks=[self.generate_knowledge_task()],
            process=Process.sequential, verbose=True
        )
        
    @crew
    def creative_reading_crew(self) -> Crew:
        """專門寫文章兼出題的團隊"""
        return Crew(
            agents=[self.creative_author_agent()],
            tasks=[self.generate_creative_reading_task()],
            process=Process.sequential, verbose=True
        )