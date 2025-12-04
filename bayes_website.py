import streamlit as st
import time
import re
from google import genai
from bayes_model import infer_emotion, EMOTION_STATES


# =====================================================
# PAGE SETTINGS
# =====================================================
st.set_page_config(page_title="Smart Tutor (Gemini + Bayesian AI)")
st.title("🎓 Smart AI Tutor (Gemini + Bayesian Emotional Intelligence)")


# =====================================================
# MAIN-SCREEN API KEY INPUT (NOT SIDEBAR)
# =====================================================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if st.session_state.api_key == "":
    st.subheader("🔐 Enter Your Gemini API Key to Begin")

    st.session_state.api_key = st.text_input(
        "Gemini API Key:",
        placeholder="AIzaSy.................",
        type="password"
    )

    if st.button("Continue ➜"):
        if st.session_state.api_key.strip() == "":
            st.error("API key cannot be empty.")
        else:
            st.rerun()

    st.stop()   # STOP app until key is given


# =====================================================
# GEMINI MCQ GENERATION
# =====================================================
def generate_question(difficulty):

    client = genai.Client(api_key=st.session_state.api_key)

    prompt = f"""
    Generate ONE {difficulty}-difficulty Python MCQ.

    FORMAT STRICTLY:

    Q: <question text>

    <python code here but DO NOT use backticks>

    A: <option1>
    B: <option2>
    C: <option3>

    Correct: <A/B/C>
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text
    lines = [l.strip() for l in raw.split("\n") if l.strip()]

    # Extract question
    q_line = next((l for l in lines if l.startswith("Q:")), "")
    question_text = q_line.replace("Q:", "").strip()

    # Detect code
    code_lines = []
    for l in lines:
        if l.startswith(("Q:", "A:", "B:", "C:", "Correct:")):
            continue
        if "=" in l or "print" in l or "(" in l:
            code_lines.append(l)

    if code_lines:
        question = question_text + "\n\n```python\n" + "\n".join(code_lines) + "\n```"
    else:
        question = question_text

    # Extract options
    def get_opt(p):
        line = next((l for l in lines if l.startswith(p)), "")
        return line.replace(p, "").strip()

    optA = get_opt("A:")
    optB = get_opt("B:")
    optC = get_opt("C:")

    # Extract correct
    correct_line = next((l for l in lines if l.startswith("Correct:")), "")
    match = re.search(r"Correct:\s*([ABC])", correct_line)
    correct_letter = match.group(1) if match else "A"
    answer_idx = {"A": 0, "B": 1, "C": 2}[correct_letter]

    return {
        "question": question,
        "options": [optA, optB, optC],
        "answer": answer_idx
    }


# =====================================================
# SESSION STATE VARIABLES
# =====================================================
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "easy"

if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None


# =====================================================
# LOAD NEXT QUESTION
# =====================================================
def load_new_question():
    st.session_state.current_question = generate_question(st.session_state.difficulty)
    st.session_state.submitted = False
    st.session_state.start_time = time.time()


# INITIAL LOAD
if st.session_state.current_question is None:
    load_new_question()

q = st.session_state.current_question


# =====================================================
# DISPLAY QUESTION
# =====================================================
st.subheader(f"Difficulty: {st.session_state.difficulty.upper()}")
st.markdown(q["question"])

choice = st.radio(
    "Choose answer:",
    q["options"],
    index=None,
    disabled=st.session_state.submitted
)

submit_button = st.button("Submit")


# =====================================================
# SUBMIT HANDLING
# =====================================================
if submit_button and not st.session_state.submitted:

    if choice is None:
        st.warning("Please select an answer.")
        st.stop()

    st.session_state.submitted = True
    st.rerun()


# =====================================================
# RESULTS
# =====================================================
if st.session_state.submitted:

    time_taken = round(time.time() - st.session_state.start_time, 3)
    correct = (q["options"].index(choice) == q["answer"])

    if correct:
        st.success(f"✅ Correct! (Time: {time_taken}s)")
    else:
        st.error(f"❌ Incorrect. Correct answer: {q['options'][q['answer']]}")
        st.info(f"Time Taken: {time_taken}s")

    feedback = st.selectbox("How was the difficulty?", ["Too Easy", "Just Right", "Too Hard"])

    # Bayesian inference
    emotion, posterior = infer_emotion(correct, time_taken, feedback)

    st.markdown("### 🤖 Bayesian Emotional State")
    st.info(f"Predicted Emotion: **{emotion.upper()}**")

    with st.expander("📘 Full Bayesian Calculations"):
        for e, p in zip(EMOTION_STATES, posterior):
            st.write(f"{e}: {p:.4f}")

    # Difficulty adaptation
    if emotion in ["highly_confident", "confident"]:
        st.session_state.difficulty = "medium"
    else:
        st.session_state.difficulty = "easy"

    st.markdown("---")

    if st.button("Next Question →"):
        load_new_question()
        st.rerun()
