import json
import random
from pathlib import Path

import streamlit as st

DATA_FILE = Path("data/questions.json")


def load_questions() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    return data


def weeks_available(questions: list[dict]) -> list[int]:
    weeks = sorted(
        {
            int(q["week"])
            for q in questions
            if isinstance(q.get("week"), int) or str(q.get("week", "")).isdigit()
        }
    )
    return weeks


def prepare_questions(base_questions: list[dict], shuffle_options: bool = True) -> list[dict]:
    prepared = []
    for q in base_questions:
        options = list(q["options"])
        correct_index = int(q["answer_index"])
        order = list(range(len(options)))
        if shuffle_options:
            random.shuffle(order)
        shuffled_options = [options[i] for i in order]
        new_correct_index = order.index(correct_index)

        prepared.append(
            {
                **q,
                "display_options": shuffled_options,
                "display_correct_index": new_correct_index,
            }
        )
    return prepared


def reset_test_state() -> None:
    st.session_state["active_questions"] = []
    st.session_state["submitted"] = False
    st.session_state["user_answers"] = {}
    st.session_state["test_title"] = ""


def start_test(title: str, questions: list[dict], shuffle_options: bool = True) -> None:
    prepared = prepare_questions(questions, shuffle_options=shuffle_options)
    random.shuffle(prepared)
    st.session_state["active_questions"] = prepared
    st.session_state["submitted"] = False
    st.session_state["user_answers"] = {}
    st.session_state["test_title"] = title


def score_test(questions: list[dict], user_answers: dict[int, int]) -> tuple[int, int]:
    total = len(questions)
    score = 0
    for idx, q in enumerate(questions):
        if user_answers.get(idx, -1) == q["display_correct_index"]:
            score += 1
    return score, total


def show_results(questions: list[dict], user_answers: dict[int, int]) -> None:
    score, total = score_test(questions, user_answers)
    st.success(f"Marks: {score}/{total} (1 mark per correct answer, 0 for wrong)")
    st.write("Answers are shown below after submission.")
    for idx, q in enumerate(questions, start=1):
        selected = user_answers.get(idx - 1, None)
        correct = q["display_correct_index"]
        question_mark = 1 if selected == correct else 0
        st.markdown(f"### Q{idx}. {q['question']}")
        for opt_idx, opt in enumerate(q["display_options"]):
            if opt_idx == correct:
                st.markdown(f"- :green[✅ {opt} (Correct answer)]")
            elif selected == opt_idx and selected != correct:
                st.markdown(f"- :red[❌ {opt} (Your selected answer)]")
            else:
                st.write(f"- {opt}")
        st.caption(f"Marks for this question: {question_mark}/1")
        if q.get("explanation"):
            st.caption(f"Explanation: {q['explanation']}")
        st.divider()


st.set_page_config(page_title="NPTEL Industrial Engineering Quiz", layout="wide")
st.title("Principles of Industrial Engineering - Practice Tests")
st.caption("Week-wise tests + random test series with shuffled options")

if "active_questions" not in st.session_state:
    reset_test_state()

all_questions = load_questions()
if not all_questions:
    st.warning(
        "No questions found in data/questions.json. "
        "Add your 120 questions (12 weeks x 10 each) and rerun."
    )
    st.stop()

for q in all_questions:
    required = ["id", "week", "question", "options", "answer_index"]
    if any(k not in q for k in required):
        st.error("Question format invalid. Please check data/questions.json.")
        st.stop()

tab_weekly, tab_random = st.tabs(["Week-wise Tests", "Random Test Series"])

with tab_weekly:
    weeks = weeks_available(all_questions)
    if not weeks:
        st.info("No week info found.")
    else:
        selected_week = st.selectbox("Select week", weeks)
        week_questions = [q for q in all_questions if int(q["week"]) == int(selected_week)]
        st.write(f"Questions in Week {selected_week}: {len(week_questions)}")
        weekly_shuffle = st.checkbox("Shuffle options", value=True, key="weekly_shuffle")
        if st.button(f"Start Week {selected_week} Test", type="primary"):
            start_test(
                title=f"Week {selected_week} Test",
                questions=week_questions,
                shuffle_options=weekly_shuffle,
            )

with tab_random:
    st.write("Random tests include all questions from all 12 assignments.")
    question_count = len(all_questions)
    st.info(f"Random test is fixed to full set: {question_count} questions (out of {question_count} marks).")
    random_shuffle = st.checkbox(
        "Shuffle options every attempt",
        value=True,
        key="random_shuffle",
    )
    if st.button("Start Random Test", type="primary"):
        sample = random.sample(all_questions, int(question_count))
        start_test(
            title=f"Random Test ({int(question_count)} Questions)",
            questions=sample,
            shuffle_options=random_shuffle,
        )

active_questions = st.session_state.get("active_questions", [])
if active_questions:
    st.header(st.session_state.get("test_title", "Test"))
    st.write("No negative marking. Answers are revealed only after submit. Marking: 1 for correct, 0 for wrong.")
    user_answers = {}
    for idx, q in enumerate(active_questions):
        answer = st.radio(
            f"Q{idx + 1}. {q['question']}",
            options=list(range(len(q["display_options"]))),
            format_func=lambda x, opts=q["display_options"]: opts[x],
            index=None,
            key=f"q_{idx}",
        )
        user_answers[idx] = answer if answer is not None else -1

    if st.button("Submit Test", type="primary"):
        st.session_state["submitted"] = True
        st.session_state["user_answers"] = user_answers

    if st.session_state.get("submitted", False):
        show_results(active_questions, st.session_state["user_answers"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retake (New Shuffle)"):
                current_title = st.session_state["test_title"]
                shuffle_choice = (
                    st.session_state.get("random_shuffle", True)
                    if "Random" in current_title
                    else st.session_state.get("weekly_shuffle", True)
                )
                raw_questions = [
                    {
                        "id": q["id"],
                        "week": q["week"],
                        "question": q["question"],
                        "options": q["options"],
                        "answer_index": q["answer_index"],
                        "explanation": q.get("explanation", ""),
                    }
                    for q in active_questions
                ]
                start_test(current_title, raw_questions, shuffle_options=shuffle_choice)
                st.rerun()
        with col2:
            if st.button("Reset / Choose New Test"):
                reset_test_state()
                st.rerun()
