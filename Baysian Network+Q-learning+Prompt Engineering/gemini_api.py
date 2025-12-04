import os
import json
from google import genai
from google.genai import types
from typing import List


API_KEY = "AIzaSyCL7V3y0xEwj-MyNodSuSBRAvmAqMyonME"

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print("Gemini initialization error:", e)
    client = None



def generate_mcq_explanation(
    question: str,
    options: List[str],
    correct_answer_text: str,
    student_emotion: str,
    topic: str
) -> str:
    return f"As a {student_emotion} student learning about {topic}, here's an explanation for why the correct answer is '{correct_answer_text}' for the question: '{question}' with options {options}."
