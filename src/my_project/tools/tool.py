#　放置各種工具類型的定義，這些工具會被 Agent 呼叫來執行特定任務，例如查詢 API、處理數據等

# src/my_project/tools/tool.py
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class IdiomSearchInput(BaseModel):
    idiom: str = Field(..., description="要查詢的成語，例如：'破釜沉舟'")

class TaiwanIdiomTool(BaseTool):
    name: str = "台灣教育部成語辭典API"
    description: str = (
        "當你需要為成語出題，或者撰寫成語的「詳解」時，"
        "必須先使用此工具查詢該成語的精確定義，以確保解釋 100% 正確，絕不能憑空捏造。"
    )
    args_schema: type[BaseModel] = IdiomSearchInput

    def _run(self, idiom: str) -> str:
        """真實串接 API 的執行邏輯"""
        print(f"\n[🌐 網路連線] Agent 正在呼叫萌典 API 查詢：{idiom}...")
        
        try:
            # 🌟 修正點 1：改用 a/ 目錄，且必須加上 .json 結尾
            url = f"https://www.moedict.tw/a/{idiom}.json"
            
            # 發送請求
            response = requests.get(url, timeout=5)
            
            # 如果 HTTP 狀態碼是 200，代表有查到資料
            if response.status_code == 200:
                # 🌟 修正點 2：加上 JSON 解析的 Try-Catch 防禦
                try:
                    data = response.json()
                except ValueError:
                    return f"API 回傳了無法解析的格式，請改用您的內建國學知識進行推斷。"
                
                # 解析萌典的 JSON 結構
                definitions = []
                for hetero in data.get('heteronyms', []):
                    for idx, def_item in enumerate(hetero.get('definitions', [])):
                        # 清理萌典 API 偶爾會帶有的特殊符號 (如 `~`)
                        clean_def = str(def_item.get('def')).replace('`', '').replace('~', '')
                        definitions.append(f"{idx+1}. {clean_def}")
                
                result_text = " ".join(definitions)
                return f"【{idiom}】的標準解釋為：{result_text}"
                
            elif response.status_code == 404:
                return f"辭典 API 中查無【{idiom}】的資料，這可能不是標準成語，請考慮換一個詞彙出題。"
            else:
                return f"API 連線異常 (狀態碼: {response.status_code})，請改用內建知識。"
                
        # 🌟 修正點 3：捕捉所有可能的錯誤，確保 Agent 永遠能收到回覆字串，而不是當機
        except Exception as e:
            return f"網路工具發生錯誤：{str(e)}，請改用內建知識。"