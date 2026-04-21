# src/my_project/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import json
import sys
import re

# 載入原本的核心與工具 (作文批改用)
from my_project.crew import MyProject
from my_project.main import get_rubric_from_excel, get_examples_from_excel, analyze_essay_stats, EXCEL_FILE

# 🌟 新增：載入學習診斷報告的核心
from my_project.report_crew import run_diagnostic_report

# ==========================================
# 定義 FastAPI 應用程式
# ==========================================
app = FastAPI(
    title="會考 AI 語文學習系統 API",
    description="提供作文批改與學習診斷報告的後端服務。",
    version="2.0.0"
)

# 🌟 必加！CORS 設定：允許前端網頁呼叫這台伺服器
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# ==========================================
# [資料模型] 作文批改 Request
# ==========================================
class EssayRequest(BaseModel):
    topic: str = Field(..., title="作文題目", examples=["靜夜思情"])
    content: str = Field(..., title="作文內容", examples=["晚上的時候黑黑的..."])

# ==========================================
# 🌟 [資料模型] 學習診斷報告 Request
# ==========================================
class StudentStats(BaseModel):
    總題數: int = Field(..., examples=[42])
    答對題數: int = Field(..., examples=[32])
    答錯題數: int = Field(..., examples=[10])
    表現優異項目: List[str] = Field(..., examples=[["白話文閱讀理解", "字音字形"]])
    待加強項目: List[str] = Field(..., examples=[["文言文文意推論", "成語運用"]])
    學習特徵: str = Field(..., examples=["作答速度快，但在文言文細節題容易粗心。"])

# ==========================================
# [工具函式] 強化版 JSON 清理器
# ==========================================
def clean_json_output(raw_str):
    """確保從 AI 輸出的 Markdown 文字中精準擷取 JSON"""
    cleaned = str(raw_str).strip()
    
    # 🌟 第一道防線：用正則表達式尋找最外層的 { } 括號
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        return match.group(0)
        
    # 🌟 保底清理：如果正則沒抓到，退回字串去頭去尾法
    if cleaned.startswith("```json"): 
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"): 
        cleaned = cleaned[3:]
    if cleaned.endswith("```"): 
        cleaned = cleaned[:-3]
        
    return cleaned.strip()