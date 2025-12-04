import os
import json
from google import genai
from google.genai import types
from typing import Dict, Any
from typing import List, Dict, Optional


# Initialize Gemini client using API key (keeping your setup)
# NOTE: Ensure you replace the placeholder with a valid key or load it from environment variables
try:
    # Use environment variable for security, or keep the placeholder for testing
    API_KEY = "AIzaSyD-A3uBFC2jzddc0oKLdOWYHZ9-nIpebK4" 
    client = genai.Client(api_key=API_KEY) 
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None
# Return empty if topic not found

def generate_mcq_explanation(
    question: str, 
    options: List[str], 
    correct_answer_text: str, 
    student_emotion: str, 
    topic: str
) -> str:
    """
    Generates an empathetic and step-by-step explanation for an MCQ.

    Args:
        question (str): The quiz question.
        options (List[str]): The available options.
        correct_answer_text (str): The text of the correct option.
        student_emotion (str): The emotional state of the student.
        topic (str): The topic of the question (e.g., 'Variables').

    Returns:
        str: The emotionally supportive and accurate explanation text.
    """
    if not client:
        return "Error: Gemini client not initialized."

    # Format options for the prompt
    formatted_options = "\n".join([f"- {opt}" for opt in options])

    # --- System Instruction ---
    # Defines the role and tone.
    system_instruction = (
        "You are an empathetic, encouraging, and supportive AI programming tutor. "
        "Your goal is to provide a clear, step-by-step explanation for an attempted multiple-choice question. "
        "Your response MUST be conversational and emotionally supportive. "
        "Do not use markdown headers or formatting besides bolding key terms. "
        "Acknowledge the student's effort and struggle without judgment. "
    )

    # --- User Prompt ---
    # Provides all context for the explanation.
    user_prompt = f"""
    The student attempted a quiz on the topic of **{topic}**. 
    Their emotional status is currently: **{student_emotion}**.

    Here is the question and the options:
    **Question:** {question}
    **Options:**
    {formatted_options}

    The **CORRECT ANSWER** is: {correct_answer_text}

    Your job:
    1. Explain the correct answer in a simple, conversational way.
    2. Do NOT overwhelm the student—keep it step-by-step.
    3. Include the reasoning behind the answer, not just the final output.
    4. End by inviting the student to ask a follow-up question.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        
        # The return must be in str format as requested
        return response.text

    except Exception as e:
        return f"API call failed during explanation generation: {e}"

