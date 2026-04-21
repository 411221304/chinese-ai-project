import os
import sys
import json
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# =========================
# 基本設定
# =========================
st.set_page_config(page_title="國文 AI 學習系統", page_icon="📘", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_SRC = os.path.join(BASE_DIR, "src")
MODULE_DIR = os.path.join(PROJECT_SRC, "my_project")
EXCEL_FILE = os.path.join(MODULE_DIR, "ExamSystem_GoogleSheet_Template.xlsx")

if PROJECT_SRC not in sys.path:
    sys.path.append(PROJECT_SRC)

# =========================
# 匯入核心模組
# =========================
IMPORT_OK = True
IMPORT_ERROR = ""

try:
    from my_project.crew import MyProject
    from my_project.auto_crew import run_proportional_ai_exam
    from my_project.report_crew import run_diagnostic_report
except Exception as e:
    IMPORT_OK = False
    IMPORT_ERROR = str(e)

# =========================
# Session State 初始化
# =========================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "generated_exam" not in st.session_state:
    st.session_state.generated_exam = None

if "flat_questions" not in st.session_state:
    st.session_state.flat_questions = []

if "exam_submitted" not in st.session_state:
    st.session_state.exam_submitted = False

if "exam_result" not in st.session_state:
    st.session_state.exam_result = None

if "diagnostic_report" not in st.session_state:
    st.session_state.diagnostic_report = ""

if "generation_message" not in st.session_state:
    st.session_state.generation_message = ""


# =========================
# 作文功能
# =========================
def get_rubric_from_excel(file_path: str) -> str:
    try:
        df = pd.read_excel(file_path, sheet_name="會考作文批改標準")
        rubric_text = ""
        for _, row in df.iterrows():
            rubric_text += f"【{row['grade']} 級分：{row['comment']}】\n"
            rubric_text += f"- 立意取材：{row['Ideas & Substance']}\n"
            rubric_text += f"- 結構組織：{row['Structure & Organization']}\n"
            rubric_text += f"- 遣詞造句：{row['Vocabulary & Phrasing']}\n"
            rubric_text += f"- 標點與格式：{row['Punctuation, Spelling & Format']}\n\n"
        return rubric_text
    except Exception as e:
        return f"讀取評分規準失敗：{e}"


def get_examples_from_excel(file_path: str) -> str:
    try:
        df = pd.read_excel(file_path, sheet_name="歷屆作文範文")
        df = df.dropna(subset=["content", "review"])

        sampled_indices = []
        target_grades = [1, 2, 3, 4, 5, 6]

        for grade in target_grades:
            grade_df = df[df["grade(0-6)"] == grade]
            if not grade_df.empty:
                chosen_index = grade_df.sample(n=1, random_state=42).index[0]
                sampled_indices.append(chosen_index)

        final_df = df.loc[sampled_indices]

        examples_text = ""
        for _, row in final_df.iterrows():
            examples_text += "【歷屆範文參考】\n"
            examples_text += f"獲得級分：{row['grade(0-6)']} 級分\n"
            examples_text += f"作文內容：\n{row['content']}\n\n"
            examples_text += f"官方評語：\n{row['review']}\n"
            examples_text += "-" * 40 + "\n\n"

        return examples_text
    except Exception as e:
        return f"讀取範文失敗：{e}"


def analyze_essay_text(text: str) -> dict:
    clean_text = text.strip()
    char_count = len(clean_text)
    paragraph_count = len([p for p in clean_text.split("\n") if p.strip()])

    sentence_count = 0
    for mark in ["。", "！", "？", ".", "!", "?"]:
        sentence_count += clean_text.count(mark)

    return {
        "字數": char_count,
        "段落數": paragraph_count,
        "句子數": sentence_count
    }


def grade_essay(topic: str, essay: str) -> str:
    if not IMPORT_OK:
        return f"目前無法匯入 my_project，錯誤：{IMPORT_ERROR}"

    rubric_text = get_rubric_from_excel(EXCEL_FILE)
    examples_text = get_examples_from_excel(EXCEL_FILE)
    stats = analyze_essay_text(essay)

    inputs = {
        "essay_topic": topic if topic.strip() else "未提供題目",
        "essay_content": essay,
        "grading_rubric": rubric_text,
        "example_essays": examples_text,
        "essay_stats": stats,
    }

    result = MyProject().crew().kickoff(inputs=inputs)

    if hasattr(result, "raw"):
        return result.raw
    return str(result)


def display_essay_result(result_text: str):
    st.subheader("作文回饋")

    try:
        result_json = json.loads(result_text)

        st.metric("最終級分", f"{result_json['final_grade']} 級分")

        st.markdown("### 整體評語")
        st.write(result_json.get("summary_comment", ""))

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 語文表達")
            st.write(result_json.get("grammar_review", ""))

        with col2:
            st.markdown("### 結構組織")
            st.write(result_json.get("structure_review", ""))

        st.markdown("### 改進建議")
        suggestions = result_json.get("improvement_suggestions", [])
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                st.write(f"{i}. {suggestion}")
        else:
            st.write("目前沒有提供改進建議。")

    except Exception:
        st.warning("結果不是標準 JSON，以下顯示原始輸出：")
        st.write(result_text)


# =========================
# 題目功能：驗證、展平、統計
# =========================
def validate_single_question(item, idx):
    required = ["題型", "題幹", "A", "B", "C", "D", "答案", "詳解"]
    missing = [k for k in required if not str(item.get(k, "")).strip()]
    if missing:
        return f"單題第 {idx} 題缺少欄位：{', '.join(missing)}"
    if item.get("答案") not in ["A", "B", "C", "D"]:
        return f"單題第 {idx} 題答案欄位異常：{item.get('答案')}"
    return None


def validate_group_question(sub_q, group_idx, sub_idx):
    required = ["題型", "題幹", "A", "B", "C", "D", "答案", "詳解"]
    missing = [k for k in required if not str(sub_q.get(k, "")).strip()]
    if missing:
        return f"題組第 {group_idx} 組第 {sub_idx} 題缺少欄位：{', '.join(missing)}"
    if sub_q.get("答案") not in ["A", "B", "C", "D"]:
        return f"題組第 {group_idx} 組第 {sub_idx} 題答案欄位異常：{sub_q.get('答案')}"
    return None


def validate_exam_data(exam_data, expected_total=42):
    if not isinstance(exam_data, dict):
        return False, "AI 回傳不是字典格式。"

    if "單題部分" not in exam_data or "題組部分" not in exam_data:
        return False, "AI 回傳缺少『單題部分』或『題組部分』。"

    single_part = exam_data.get("單題部分")
    group_part = exam_data.get("題組部分")

    if not isinstance(single_part, list):
        return False, "『單題部分』不是陣列。"
    if not isinstance(group_part, list):
        return False, "『題組部分』不是陣列。"

    total_count = 0

    for i, item in enumerate(single_part, start=1):
        if not isinstance(item, dict):
            return False, f"單題第 {i} 題不是物件格式。"
        err = validate_single_question(item, i)
        if err:
            return False, err
        total_count += 1

    for group_idx, group in enumerate(group_part, start=1):
        if not isinstance(group, dict):
            return False, f"題組第 {group_idx} 組不是物件格式。"

        article = str(group.get("文章內容", "")).strip()
        if not article:
            return False, f"題組第 {group_idx} 組缺少『文章內容』。"

        question_list = group.get("題目列表")
        if not isinstance(question_list, list) or len(question_list) == 0:
            return False, f"題組第 {group_idx} 組缺少『題目列表』或為空。"

        for sub_idx, sub_q in enumerate(question_list, start=1):
            if not isinstance(sub_q, dict):
                return False, f"題組第 {group_idx} 組第 {sub_idx} 題不是物件格式。"
            err = validate_group_question(sub_q, group_idx, sub_idx)
            if err:
                return False, err
            total_count += 1

    if total_count != expected_total:
        return False, f"本次總題數為 {total_count} 題，不是預期的 {expected_total} 題。"

    return True, "考卷格式正確"


def generate_ai_exam():
    if not IMPORT_OK:
        return None, f"模組匯入失敗：{IMPORT_ERROR}"

    retry_delays = [5, 8, 12]

    for attempt, delay in enumerate(retry_delays, start=1):
        try:
            exam_data = run_proportional_ai_exam(total_questions=42)

            if isinstance(exam_data, dict) and exam_data.get("error"):
                return None, exam_data["error"]

            is_valid, msg = validate_exam_data(exam_data, expected_total=42)
            if not is_valid:
                return None, f"AI 生題失敗：{msg}"

            return exam_data, ""

        except Exception as e:
            error_text = str(e)

            if "503" in error_text or "UNAVAILABLE" in error_text:
                if attempt < len(retry_delays):
                    st.warning(f"第 {attempt} 次命題遇到模型忙碌，{delay} 秒後自動重試...")
                    time.sleep(delay)
                    continue
                return None, f"命題過程發生錯誤：模型目前忙碌，已重試 {attempt} 次仍失敗。\n\n原始錯誤：{e}"

            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                return None, f"命題過程發生錯誤：目前 API 額度不足。\n\n原始錯誤：{e}"

            return None, f"命題過程發生錯誤：{e}"

    return None, "命題失敗：未知錯誤"


def flatten_exam_data(exam_data: dict):
    flat_questions = []
    q_number = 1

    single_part = exam_data.get("單題部分", [])
    for item in single_part:
        flat_questions.append({
            "id": f"Q{q_number}",
            "number": q_number,
            "group_type": "單題",
            "question_type": item.get("題型", ""),
            "article": item.get("文章內容", ""),
            "question": item.get("題幹", ""),
            "A": item.get("A", ""),
            "B": item.get("B", ""),
            "C": item.get("C", ""),
            "D": item.get("D", ""),
            "answer": item.get("答案", ""),
            "explanation": item.get("詳解", "")
        })
        q_number += 1

    group_part = exam_data.get("題組部分", [])
    for group in group_part:
        article = group.get("文章內容", "")
        question_list = group.get("題目列表", [])

        for sub_q in question_list:
            flat_questions.append({
                "id": f"Q{q_number}",
                "number": q_number,
                "group_type": "題組",
                "question_type": sub_q.get("題型", ""),
                "article": article,
                "question": sub_q.get("題幹", ""),
                "A": sub_q.get("A", ""),
                "B": sub_q.get("B", ""),
                "C": sub_q.get("C", ""),
                "D": sub_q.get("D", ""),
                "answer": sub_q.get("答案", ""),
                "explanation": sub_q.get("詳解", "")
            })
            q_number += 1

    return flat_questions


def build_student_stats(result):
    details = result["details"]
    total = result["total"]
    correct = result["correct"]
    accuracy = result["accuracy"]

    type_stats = {}
    group_type_stats = {
        "單題": {"total": 0, "correct": 0},
        "題組": {"total": 0, "correct": 0}
    }

    for item in details:
        qtype = item["question_type"] if item["question_type"] else "未分類"
        gtype = item["group_type"]

        if qtype not in type_stats:
            type_stats[qtype] = {"total": 0, "correct": 0, "wrong": 0}

        type_stats[qtype]["total"] += 1
        group_type_stats[gtype]["total"] += 1

        if item["is_correct"]:
            type_stats[qtype]["correct"] += 1
            group_type_stats[gtype]["correct"] += 1
        else:
            type_stats[qtype]["wrong"] += 1

    for qtype, stat in type_stats.items():
        stat["accuracy"] = round((stat["correct"] / stat["total"]) * 100, 2) if stat["total"] > 0 else 0

    for gtype, stat in group_type_stats.items():
        stat["wrong"] = stat["total"] - stat["correct"]
        stat["accuracy"] = round((stat["correct"] / stat["total"]) * 100, 2) if stat["total"] > 0 else 0

    weakest_types = sorted(type_stats.items(), key=lambda x: x[1]["accuracy"])[:3]
    strongest_types = sorted(type_stats.items(), key=lambda x: x[1]["accuracy"], reverse=True)[:3]

    student_stats = {
        "總題數": total,
        "答對題數": correct,
        "答錯題數": total - correct,
        "整體正確率": accuracy,
        "單題與題組統計": group_type_stats,
        "各題型統計": type_stats,
        "最弱題型前三": [{"題型": k, **v} for k, v in weakest_types],
        "最強題型前三": [{"題型": k, **v} for k, v in strongest_types]
    }

    return student_stats


def grade_exam_answers(questions):
    total = len(questions)
    correct = 0
    results = []

    for q in questions:
        user_key = f"answer_{q['id']}"
        user_answer = st.session_state.get(user_key, "")
        correct_answer = q.get("answer", "")
        is_correct = (user_answer == correct_answer)

        if is_correct:
            correct += 1

        results.append({
            "number": q["number"],
            "group_type": q["group_type"],
            "question_type": q["question_type"],
            "article": q["article"],
            "question": q["question"],
            "A": q["A"],
            "B": q["B"],
            "C": q["C"],
            "D": q["D"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": q["explanation"]
        })

    accuracy = round(correct / total * 100, 2) if total > 0 else 0

    result = {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "details": results
    }

    result["student_stats"] = build_student_stats(result)
    return result


def display_type_stats(student_stats):
    st.markdown("### 各題型作答統計")

    type_stats = student_stats.get("各題型統計", {})
    if not type_stats:
        st.write("目前沒有題型統計資料。")
        return

    rows = []
    for qtype, stat in type_stats.items():
        rows.append({
            "題型": qtype,
            "題數": stat["total"],
            "答對": stat["correct"],
            "答錯": stat["wrong"],
            "正確率(%)": stat["accuracy"]
        })

    df = pd.DataFrame(rows).sort_values(by="正確率(%)")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### 單題 / 題組統計")
    group_stats = student_stats.get("單題與題組統計", {})
    rows2 = []
    for gtype, stat in group_stats.items():
        rows2.append({
            "類別": gtype,
            "題數": stat["total"],
            "答對": stat["correct"],
            "答錯": stat["wrong"],
            "正確率(%)": stat["accuracy"]
        })
    df2 = pd.DataFrame(rows2)
    st.dataframe(df2, use_container_width=True, hide_index=True)


def display_exam_result(result):
    st.subheader("作答結果")
    c1, c2, c3 = st.columns(3)
    c1.metric("總題數", result["total"])
    c2.metric("答對題數", result["correct"])
    c3.metric("正確率", f"{result['accuracy']}%")

    display_type_stats(result["student_stats"])

    st.markdown("### 每題詳解")
    for item in result["details"]:
        icon = "✅" if item["is_correct"] else "❌"
        title = f"{icon} 第{item['number']}題｜{item['group_type']}｜{item['question_type'] or '未分類'}"
        with st.expander(title):
            if item["group_type"] == "題組" and item["article"]:
                st.markdown("**題組文章：**")
                st.write(item["article"])

            st.markdown("**題目：**")
            st.write(item["question"])

            st.markdown("**選項：**")
            st.write(f"(A) {item['A']}")
            st.write(f"(B) {item['B']}")
            st.write(f"(C) {item['C']}")
            st.write(f"(D) {item['D']}")

            st.write(f"你的答案：{item['user_answer'] or '未作答'}")
            st.write(f"正確答案：{item['correct_answer'] or '未提供'}")
            st.write(f"詳解：{item['explanation'] or '目前沒有詳解'}")


# =========================
# 畫面：首頁
# =========================
def render_home():
    st.title("📘 國文 AI 學習系統")
    st.write("請選擇要使用的功能。")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("## 題目作答")
        st.write("進入 42 題作答頁面，提交後可查看答案、詳解與學習回饋。")
        if st.button("進入題目作答", use_container_width=True):
            st.session_state.page = "exam"
            st.rerun()

    with col2:
        st.markdown("## 作文批改")
        st.write("輸入作文後，由系統提供級分、評語與改進建議。")
        if st.button("進入作文批改", use_container_width=True):
            st.session_state.page = "essay"
            st.rerun()


# =========================
# 畫面：題目頁
# =========================
def render_exam_page():
    st.title("📝 題目作答")

    top1, top2, top3 = st.columns(3)

    with top1:
        if st.button("回首頁", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    with top2:
        if st.button("清空目前考卷", use_container_width=True):
            st.session_state.generated_exam = None
            st.session_state.flat_questions = []
            st.session_state.exam_submitted = False
            st.session_state.exam_result = None
            st.session_state.diagnostic_report = ""
            st.session_state.generation_message = ""
            st.rerun()

    with top3:
        if st.button("AI 生成新考卷", use_container_width=True):
            with st.spinner("AI 正在生成 42 題考卷，請稍候..."):
                exam_data, error_msg = generate_ai_exam()

            if error_msg:
                st.session_state.generated_exam = None
                st.session_state.flat_questions = []
                st.session_state.exam_submitted = False
                st.session_state.exam_result = None
                st.session_state.diagnostic_report = ""
                st.session_state.generation_message = ""
                st.error(error_msg)
            else:
                st.session_state.generated_exam = exam_data
                st.session_state.flat_questions = flatten_exam_data(exam_data)
                st.session_state.exam_submitted = False
                st.session_state.exam_result = None
                st.session_state.diagnostic_report = ""
                st.session_state.generation_message = "本次為即時 AI 新生成考卷。"
                st.rerun()

    if st.session_state.generated_exam:
        exam_name = st.session_state.generated_exam.get("試卷名稱", "AI 原創模擬考")
        st.subheader(exam_name)

    if st.session_state.generation_message:
        st.success(st.session_state.generation_message)

    questions = st.session_state.flat_questions
    if not questions:
        st.info("請先按上方「AI 生成新考卷」。")
        return

    st.write(f"目前共有 {len(questions)} 題。")

    for q in questions:
        st.markdown(f"### 第 {q['number']} 題｜{q['group_type']}｜{q['question_type'] or '未分類'}")

        if q["group_type"] == "題組" and q["article"]:
            st.markdown("**題組文章：**")
            st.write(q["article"])

        st.write(q["question"])

        option_map = {
            "A": q["A"],
            "B": q["B"],
            "C": q["C"],
            "D": q["D"]
        }

        st.radio(
            "請選擇答案：",
            options=["A", "B", "C", "D"],
            format_func=lambda x, option_map=option_map: f"({x}) {option_map[x]}",
            key=f"answer_{q['id']}",
            index=None
        )

        st.divider()

    if st.button("提交答案", use_container_width=True):
        result = grade_exam_answers(questions)
        st.session_state.exam_result = result
        st.session_state.exam_submitted = True
        st.session_state.diagnostic_report = ""
        st.rerun()

    if st.session_state.exam_submitted and st.session_state.exam_result:
        display_exam_result(st.session_state.exam_result)

        st.markdown("### 後端學習分析")
        if st.button("產生 AI 學習診斷報告", use_container_width=True):
            with st.spinner("AI 正在分析作答統計，請稍候..."):
                try:
                    student_stats = st.session_state.exam_result["student_stats"]
                    report = run_diagnostic_report(student_stats)
                    st.session_state.diagnostic_report = report
                    st.rerun()
                except Exception as e:
                    st.error(f"學習診斷報告生成失敗：{e}")

        if st.session_state.diagnostic_report:
            st.markdown(st.session_state.diagnostic_report)


# =========================
# 畫面：作文頁
# =========================
def render_essay_page():
    st.title("📝 作文批改")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("回首頁", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    with col2:
        with st.expander("目前系統狀態", expanded=False):
            st.write(f"my_project 匯入狀態：{'成功' if IMPORT_OK else '失敗'}")
            st.write(f"Excel 路徑：{EXCEL_FILE}")
            st.write(f"Excel 是否存在：{'是' if os.path.exists(EXCEL_FILE) else '否'}")
            if not IMPORT_OK:
                st.error(IMPORT_ERROR)

    essay_topic = st.text_input("作文題目（選填）", placeholder="例如：我最難忘的一天")
    essay_content = st.text_area("作文內容", height=300, placeholder="請把作文貼在這裡…")

    c1, c2 = st.columns(2)
    with c1:
        submit = st.button("開始批改", use_container_width=True)
    with c2:
        clear = st.button("清空內容", use_container_width=True)

    if clear:
        st.rerun()

    if submit:
        if not essay_content.strip():
            st.warning("請先貼上作文內容。")
        else:
            with st.spinner("批改中，請稍候..."):
                try:
                    stats = analyze_essay_text(essay_content)

                    st.subheader("作文基本資訊")
                    s1, s2, s3 = st.columns(3)
                    s1.metric("字數", stats["字數"])
                    s2.metric("段落數", stats["段落數"])
                    s3.metric("句子數", stats["句子數"])

                    result_text = grade_essay(essay_topic, essay_content)
                    display_essay_result(result_text)

                except Exception as e:
                    st.error(f"執行失敗：{e}")


# =========================
# 主程式
# =========================
if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "exam":
    render_exam_page()
elif st.session_state.page == "essay":
    render_essay_page()