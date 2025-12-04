import streamlit as st
import time
import os
import re

from bayes_model import infer_emotion, EMOTION_STATES
from google import genai


# =====================================================
#  GEMINI MCQ GENERATION
# =====================================================
def generate_question(difficulty):

    client = genai.Client(api_key="YOUR_API_KEY_HERE")

    prompt = f"""
    Generate ONE {difficulty} difficulty Python MCQ.
    USE THIS EXACT FORMAT ONLY:

    Q: <question>

    <python code here but DO NOT use backticks>

    A: <option1>
    B: <option2>
    C: <option3>

    Correct: <A/B/C>

    RULES:
    - No explanations.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text
    print("Gemini Response:", raw)

    lines = [l.strip() for l in raw.split("\n") if l.strip()]

    # ---- Extract Question ----
    q_line = next((l for l in lines if l.startswith("Q:")), "")
    question_text = q_line.replace("Q:", "").strip()

    # ---- Extract code lines ----
    code_lines = []
    for l in lines:
        if l.startswith(("Q:", "A:", "B:", "C:", "Correct:")):
            continue
        if "=" in l or "print" in l or "(" in l:
            code_lines.append(l)

    # Code block
    if code_lines:
        question = question_text + "\n\n```python\n" + "\n".join(code_lines) + "\n```"
    else:
        question = question_text

    # Extract Options
    def extract(prefix):
        line = next((l for l in lines if l.startswith(prefix)), "")
        return line.replace(prefix, "").strip()

    optA = extract("A:")
    optB = extract("B:")
    optC = extract("C:")

    # Extract Correct Answer
    correct_line = next((l for l in lines if l.startswith("Correct:")), "")
    match = re.search(r"Correct:\s*([ABC])", correct_line)
    correct_letter = match.group(1) if match else "A"

    answer_index = {"A": 0, "B": 1, "C": 2}[correct_letter]

    return {
        "question": question,
        "options": [optA, optB, optC],
        "answer": answer_index
    }


# =====================================================
# STREAMLIT UI
# =====================================================
st.set_page_config(page_title="Smart Tutor (Gemini + Bayesian AI)")

st.title("🎓 Smart AI Tutor (Gemini + Bayesian Emotional Intelligence)")


# -------- SESSION STATE --------
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "easy"

if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# NEW FIX FLAG
if "next_flag" not in st.session_state:
    st.session_state.next_flag = False


# =====================================================
# LOAD QUESTION 
# =====================================================
if st.session_state.current_question is None or st.session_state.next_flag:
    st.session_state.current_question = generate_question(st.session_state.difficulty)
    st.session_state.start_time = time.time()
    st.session_state.next_flag = False  


q = st.session_state.current_question


# =====================================================
#  DISPLAY QUESTION
# =====================================================
st.subheader(f"Difficulty: {st.session_state.difficulty.upper()}")
st.markdown(q["question"])

choice = st.radio("Choose answer:", q["options"], index=None)

submit = st.button("Submit")


# =====================================================
#  ON SUBMIT
# =====================================================
if submit and choice is not None:

    time_taken = round(time.time() - st.session_state.start_time, 3)
    st.success(f"⏱ Time Taken: {time_taken} seconds")

    correct = (q["options"].index(choice) == q["answer"])
    st.write("✅ Correct!" if correct else "❌ Incorrect.")

    feedback = st.selectbox("How was this question?",
                            ["Too Easy", "Just Right", "Too Hard"])

    # Bayesian inference
    emotion, posterior = infer_emotion(correct, time_taken, feedback)

    st.markdown("### 🤖 Bayesian Emotional State")
    st.info(f"Predicted Emotion: **{emotion.upper()}**")

    st.markdown("### Posterior Distribution")
    for s, p in zip(EMOTION_STATES, posterior):
        st.write(f"- {s} : {p:.4f}")

    st.markdown("### 📘 Full Calculation Details")
    st.code(f"""
Correct       = {correct}
Time Taken    = {time_taken} sec
Feedback      = {feedback}

Posterior Probabilities:
{EMOTION_STATES[0]} = {posterior[0]:.4f}
{EMOTION_STATES[1]} = {posterior[1]:.4f}
{EMOTION_STATES[2]} = {posterior[2]:.4f}
{EMOTION_STATES[3]} = {posterior[3]:.4f}
{EMOTION_STATES[4]} = {posterior[4]:.4f}

Final Emotion = {emotion.upper()}
""")

    # Adaptive difficulty
    if emotion in ["highly_confident", "confident"]:
        st.session_state.difficulty = "medium"
    else:
        st.session_state.difficulty = "easy"

    st.markdown("---")
    if st.button("Next Question →"):
        st.session_state.next_flag = True
        st.rerun()
