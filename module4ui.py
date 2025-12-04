# website.py
"""
Streamlit front-end for the adaptive tutoring system.
Uses Module4_RF (adaptive RL tutor + student simulator),
Module5_llm for explanation generation, and evaluate.py for optional emotion eval.
"""

import streamlit as st
import json
import os
import random
import time
from typing import Dict, Any, Optional

# Your modules (must be available in PYTHONPATH)
from Module5_llm import generate_mcq_explanation
from evaluate import evaluate_emotional_status  # optional, used for logging/inspection
from Module4_RF import (
    QLearningTutor,
    StudentSimulator,
    update_from_feedback,
    difficulty_to_level
)

# -------------------------
# Utility: load course content
# -------------------------
def load_content(file_path: str = "course_content.json") -> Optional[Dict[str, Any]]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("⚠️ course_content.json not found. Put it in project root.")
        return None
    except Exception as e:
        st.error(f"Error loading content: {e}")
        return None

# -------------------------
# Utility: load question bank
# -------------------------
def import_quiz_data(file_path: str = "questions.json") -> Dict[str, Any]:
    if not os.path.exists(file_path):
        st.error(f"questions.json not found at {file_path}")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error reading questions.json: {e}")
        return {}

# -------------------------
# Question fetcher (uses question DB)
# -------------------------
def fetch_data(topic_key: str, difficulty: str, emotion: str) -> Dict[str, Any]:
    db = import_quiz_data()
    if not db:
        return {"error": "questions.json missing or invalid."}
    if topic_key not in db:
        return {"error": f"Topic {topic_key} not found."}
    if difficulty not in db[topic_key]:
        return {"error": f"Difficulty {difficulty} not available for topic {topic_key}."}

    problems = db[topic_key][difficulty].get("problems", [])
    if not problems:
        return {"error": "No problems found for selected topic/difficulty."}

    problem = random.choice(problems)

    # optional: generate explanation via LLM module
    try:
        explanation = generate_mcq_explanation(
            problem.get("question", ""),
            problem.get("options", []),
            problem.get("answer", ""),
            emotion,
            topic_key
        )
    except Exception:
        # fallback: simple explanation
        explanation = problem.get("explanation", "") or f"Answer: {problem.get('answer', '')}"

    return {
        "question": problem.get("question", ""),
        "options": problem.get("options", []),
        "answer": problem.get("answer", ""),
        "answer_index": problem.get("answer_index", None),
        "hint": problem.get("hint", ""),
        "explanation": explanation,
        "image": problem.get("image", None),  # allow image field (path or base64 URL)
        "difficulty_chosen": difficulty,
        "topic_key": topic_key,
        "raw_problem": problem
    }


# -------------------------
# Streamlit session initialization
# -------------------------
def init_session_state():
    if "tutor" not in st.session_state:
        st.session_state.tutor = QLearningTutor()
    if "student" not in st.session_state:
        st.session_state.student = StudentSimulator()
    if "difficulty_value" not in st.session_state:
        st.session_state.difficulty_value = 0.30
    if "last_action" not in st.session_state:
        st.session_state.last_action = None
    if "last_state" not in st.session_state:
        st.session_state.last_state = None
    if "current_topic" not in st.session_state:
        # default topic; change as per course_content.json
        st.session_state.current_topic = "variables"
    if "current_difficulty_level" not in st.session_state:
        st.session_state.current_difficulty_level = difficulty_to_level(st.session_state.difficulty_value)
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "question_start_time" not in st.session_state:
        st.session_state.question_start_time = None
    if "last_answer_correct" not in st.session_state:
        st.session_state.last_answer_correct = None
    if "last_feedback" not in st.session_state:
        st.session_state.last_feedback = None
    if "show_explanation" not in st.session_state:
        st.session_state.show_explanation = False
    if "next_rl_out" not in st.session_state:
        st.session_state.next_rl_out = None
    if "qtable_save_path" not in st.session_state:
        st.session_state.qtable_save_path = "module4rf_qtable.json"


# -------------------------
# UI: Sidebar controls
# -------------------------
def sidebar_controls():
    st.sidebar.title("Adaptive Tutor Controls")
    content = load_content()
    topics = list(content.keys()) if content else ["variables", "conditionals", "loops", "functions", "oops"]
    sel = st.sidebar.selectbox("Choose topic", topics, index=topics.index(st.session_state.current_topic) if st.session_state.current_topic in topics else 0)
    st.session_state.current_topic = sel

    # show current numeric difficulty
    diff_val = st.sidebar.slider("Difficulty (numeric)", 0.0, 1.0, float(st.session_state.difficulty_value), 0.01)
    st.session_state.difficulty_value = float(diff_val)
    st.session_state.current_difficulty_level = difficulty_to_level(st.session_state.difficulty_value)

    st.sidebar.markdown("---")
    if st.sidebar.button("Save Q-table"):
        try:
            st.session_state.tutor.save_q_table(st.session_state.qtable_save_path)
            st.sidebar.success(f"Saved Q-table to {st.session_state.qtable_save_path}")
        except Exception as e:
            st.sidebar.error(f"Save failed: {e}")

    st.sidebar.markdown("**Session student state**")
    st.sidebar.write(f"Mastery: {st.session_state.student.mastery_level:.3f}")
    st.sidebar.write(f"Frustration: {st.session_state.student.frustration:.3f}")
    st.sidebar.write(f"Engagement: {st.session_state.student.engagement:.3f}")
    st.sidebar.write(f"Last action: {st.session_state.last_action}")
    st.sidebar.write(f"Difficulty level: {st.session_state.current_difficulty_level}")

# -------------------------
# UI: Show topic content
# -------------------------
def show_topic_content():
    content = load_content()
    if content and st.session_state.current_topic in content:
        data = content[st.session_state.current_topic]
        st.header(data.get("title", st.session_state.current_topic))
        st.divider()
        st.markdown(data.get("body", ""))
    else:
        st.warning("Topic content not found.")

# -------------------------
# Present question + collect answer
# -------------------------
def present_question():
    # Ensure we have a current question; if not, fetch one (initial)
    if not st.session_state.current_question:
        # fetch initial question according to current difficulty level
        q = fetch_data(st.session_state.current_topic, st.session_state.current_difficulty_level, "neutral")
        st.session_state.current_question = q
        st.session_state.question_start_time = time.time()
        st.session_state.show_explanation = False
        st.session_state.next_rl_out = None

    q = st.session_state.current_question
    if "error" in q:
        st.error(q["error"])
        return

    st.subheader(f"Question ({st.session_state.current_difficulty_level})")
    if q.get("image"):
        try:
            # if image is a path
            if os.path.exists(q["image"]):
                st.image(q["image"])
            else:
                # treat image as URL or base64 (Streamlit can display URL)
                st.image(q["image"])
        except Exception:
            # ignore image display errors
            pass

    st.write(q["question"])

    # options as radio buttons
    options = q.get("options", [])
    if not options:
        st.error("No options available for this question.")
        return

    # radio returns the selected option text
    selected = st.radio("Select an answer", options, key="answer_radio")

    # Submit button
    col1, col2 = st.columns([1,1])
    with col1:
        submit = st.button("Submit Answer")
    with col2:
        show_hint = st.button("Show Hint")

    if show_hint:
        st.info(q.get("hint", "No hint available."))

    if submit:
        # compute time spent
        end_t = time.time()
        start_t = st.session_state.question_start_time or end_t
        time_spent = end_t - start_t

        correct_answer = q.get("answer")
        is_correct = (selected == correct_answer)
        st.session_state.last_answer_correct = is_correct
        st.session_state.last_feedback = None  # could collect free-text feedback here
        st.success("Correct!" if is_correct else f"Incorrect. Correct answer: {correct_answer}")

        # Optional: call external evaluate_emotional_status for logging
        try:
            emo = evaluate_emotional_status(is_correct, time_spent, "")
        except Exception:
            emo = None

        # Update RL and student state via update_from_feedback
        rl_out = update_from_feedback(
            tutor=st.session_state.tutor,
            student=st.session_state.student,
            last_action=st.session_state.last_action,
            last_state=st.session_state.last_state,
            current_diff=st.session_state.difficulty_value,
            user_correct=is_correct,
            time_spent=time_spent,
            feedback=None
        )

        # Store for next step (but do NOT immediately drop the question so explanation is visible)
        st.session_state.last_state = rl_out["current_state"]
        st.session_state.last_action = rl_out["next_action"]
        st.session_state.difficulty_value = rl_out["next_difficulty"]
        st.session_state.current_difficulty_level = rl_out["next_level"]
        st.session_state.show_explanation = True
        st.session_state.next_rl_out = rl_out  # store the rl output for the Next button

        # attach RL debug info to UI
        st.write("### RL info (debug)")
        st.json({
            "response_label": rl_out["response_label"],
            "reward": rl_out["reward"],
            "next_action": rl_out["next_action"],
            "next_difficulty": rl_out["next_difficulty"],
            "next_level": rl_out["next_level"],
            "current_state": rl_out["current_state"],
            "next_state": rl_out["next_state"]
        })

        # show explanation
        st.markdown("**Explanation:**")
        st.write(q.get("explanation", ""))

        # Show Next Question button so user controls when to move on
        if st.button("Next Question →"):
            next_rl = st.session_state.next_rl_out or rl_out
            # Fetch the next question using RL-chosen difficulty and emotion label
            next_q = fetch_data(
                st.session_state.current_topic,
                next_rl["next_level"],
                next_rl["response_label"]
            )
            # Set the new question into session state (will be shown on next render)
            st.session_state.current_question = next_q
            st.session_state.question_start_time = time.time()
            st.session_state.show_explanation = False
            st.session_state.next_rl_out = None

# -------------------------
# App entry point
# -------------------------
def main():
    st.set_page_config(page_title="Adaptive Tutor", layout="wide")
    init_session_state()
    sidebar_controls()

    st.title("Adaptive Tutoring — RL-powered")

    # show topic content left column, quiz on right
    left, right = st.columns([2, 3])
    with left:
        show_topic_content()

    with right:
        present_question()

    # footer: controls for debugging / evaluation
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Quick train small (demo)"):
            # Train a small tutor in-memory and load qtable
            t, stats = train_short_demo()
            st.session_state.tutor = t
            st.success("Trained demo tutor (in-memory).")
    with c2:
        if st.button("Save session Q-table"):
            try:
                st.session_state.tutor.save_q_table(st.session_state.qtable_save_path)
                st.success(f"Saved Q-table to {st.session_state.qtable_save_path}")
            except Exception as e:
                st.error(f"Save failed: {e}")
    with c3:
        if st.button("Load Q-table (if exists)"):
            try:
                st.session_state.tutor.load_q_table(st.session_state.qtable_save_path)
                st.success("Loaded Q-table (if file exists).")
            except Exception as e:
                st.error(f"Load failed: {e}")

# -------------------------
# Small helper demo trainer
# -------------------------
def train_short_demo():
    """
    Train a short policy quickly (small episodes) and return tutor + stats.
    Useful to demo changes quickly.
    """
    from Module4_RF import train_tutor  # import local trainer
    tutor, stats = train_tutor(episodes=300, steps_per_episode=30, seed=42)
    return tutor, stats


# -------------------------
# Expose training/eval for interactive debugging (optional)
# -------------------------
def evaluate_current_policy(samples: int = 50):
    tutor = st.session_state.tutor
    from Module4_RF import evaluate_policy
    results = evaluate_policy(tutor, episodes=samples, steps=50, seed=123)
    mastery = float(sum([r[0] for r in results]) / len(results))
    frustr = float(sum([r[1] for r in results]) / len(results))
    st.write(f"Eval avg mastery: {mastery:.3f}, avg frustration: {frustr:.3f}")
    return results

# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    main()
