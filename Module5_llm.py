"""
Module5_llm.py
LLM-Based Friendly Tutor Response Generation

This script:
- Builds a clean prompt tailored to the student's emotional state.
- Sends the prompt to a Gemini LLM.
- Produces a friendly explanation + motivation.
- Prints the LLM response + justification of prompt design.
"""

import os
from google import genai

# ---------------------------
# STUDENT INPUT SIMULATION
# ---------------------------

student_emotion = "confused"
topic = "Data Structures"

question_data = {
    "question": "Which data structure uses FIFO ordering?",
    "options": ["Stack", "Queue", "Tree", "Graph"],
    "correct_answer": "Queue"
}

# ---------------------------
# BUILD CLEAN, CONTROLLED PROMPT
# ---------------------------

def build_tutor_prompt(emotion, topic, q):
    correct = q["correct_answer"].strip()

    prompt = f"""
You are a friendly AI tutor. Your goal is to help the student learn with clarity and emotional safety.

STUDENT EMOTIONAL STATE: {emotion}
TOPIC: {topic}

The student attempted an MCQ. Generate:
1. A gentle emotional acknowledgement based on the student's state.
2. A clear explanation of the underlying concept.
3. Why the correct answer is correct.
4. A short explanation of why each incorrect option is wrong.
5. A motivational closing line.

QUESTION:
{q['question']}

OPTIONS:
{chr(10).join(f"- {opt}" for opt in q['options'])}

CORRECT ANSWER:
{correct}

Your tone MUST be:
- supportive
- simple
- encouraging
- non-judgmental
- confidence-building
"""
    return prompt


# ---------------------------
# SEND TO GEMINI
# ---------------------------

def call_gemini(prompt):
    client = genai.Client(api_key="YOUR_API_KEY_HERE")
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return resp.text


# ---------------------------
# MAIN EXECUTION
# ---------------------------

if __name__ == "__main__":

    prompt = build_tutor_prompt(student_emotion, topic, question_data)

    print("\n========== PROMPT SENT TO GEMINI ==========\n")
    print(prompt)
    print("===========================================\n")

    print("Gemini Response:\n")

    try:
        llm_output = call_gemini(prompt)
        print(llm_output)
    except Exception as e:
        print("Error contacting Gemini:", e)

    # ---------------------------
    # Prompt Justification
    # ---------------------------
    print("\n\n========== JUSTIFICATION ==========\n")
    print("""
1. Emotional Safety Guarantee:
   - The prompt explicitly instructs the LLM to acknowledge the student’s emotional state
     (confused, frustrated, bored, confident…).
   - This ensures responses are validating and supportive.

2. Pedagogical Clarity:
   - The stepwise structure (concept → correct answer → wrong answers → motivation)
     ensures the explanation is clear and structured.
   - The LLM cannot wander because the format is strictly defined.

3. Encouraging Tone:
   - The prompt constrains tone to be simple, non-judgmental, and motivational.
   - This avoids harsh or overly complex feedback.

4. Context Awareness:
   - Topic, question, emotional state, and options are all embedded,
     allowing the LLM to generate contextually accurate guidance.

5. No hallucination risk:
   - The correct answer is explicitly provided.
   - The LLM is prevented from guessing alternative answers.
""")
