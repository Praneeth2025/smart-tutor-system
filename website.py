import streamlit as st
import json
import os
from gemini_api import generate_mcq_explanation
def load_content():
    """Loads the course content from the JSON file."""
    # Construct path to the file
    file_path = os.path.join(".", "course_content.json")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Content file not found! Check assets/course_content.json")
        return None

def display_topic(topic_key):
    """
    Displays the formatted content for a specific topic.
    topic_key options: 'variables', 'loops', 'functions', 'recursion', 'debugging'
    """
    content_db = load_content()
    
    if content_db and topic_key in content_db:
        topic_data = content_db[topic_key]
        
        # Display the Title nicely
        st.header(topic_data["title"])
        st.divider()
        
        # Display the Main Body with Markdown support
        # This will render the Bold, Italic, and Code Blocks automatically
        st.markdown(topic_data["body"])
        
    else:
        st.warning("Topic not found.")


# Assuming other functions like load_content and display_topic are here

QUIZ_QUESTIONS = {
    "variables": {
        "question": "What is the result of the following code? `x = 5; x = x + 1; print(x)`",
        "options": ["5", "6", "Error", "1"],
        "answer": "6",
        "explanation": "The variable `x` is reassigned. It starts at 5, then is incremented by 1, making its final value 6."
    },
    "loops": {
        "question": "Which loop type is generally preferred when you know the exact number of iterations?",
        "options": ["While Loop", "Do-While Loop", "For Loop", "Infinite Loop"],
        "answer": "For Loop",
        "explanation": "The `for` loop is ideal for definite iteration, such as iterating over a range or a list."
    }
}

def take_quiz(topic_key):
    """Displays a quiz question for the given topic key."""
    
    quiz_data = QUIZ_QUESTIONS.get(topic_key)
    
    if not quiz_data:
        st.warning(f"Quiz questions for '{topic_key.capitalize()}' are not yet available.")
        return

    st.header(f"Quiz: {topic_key.capitalize()} Mastery Check")
    st.markdown("---")

    question = quiz_data["question"]
    options = quiz_data["options"]
    answer = quiz_data["answer"]
    explanation = quiz_data["explanation"]

    st.subheader(question)
    
    # Create radio buttons for options
    user_choice = st.radio("Select your answer:", options, key=f"quiz_{topic_key}")

    if st.button("Submit Answer"):
        if user_choice == answer:
            st.success("✅ Correct! Excellent work.")
        else:
            st.error(f"❌ Incorrect. The correct answer was **{answer}**.")
        
        st.info(f"**Explanation:** {explanation}")



import random

import json
import os
from typing import Dict, Any

def import_quiz_data(file_path: str = 'questions.json') -> Dict[str, Any]:
    """
    Imports all quiz data from a specified JSON file.

    Args:
        file_path (str): The path to the questions.json file.

    Returns:
        Dict[str, Any]: A dictionary containing the entire quiz structure
                        or an empty dictionary if the file is not found/readable.
    """
    try:
        # Check if the file exists before attempting to open it
        if not os.path.exists(file_path):
            print(f"Error: File not found at '{file_path}'")
            return {}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            # Use json.load() to parse the JSON content into a Python dictionary
            data = json.load(f)
            print(f"Successfully loaded quiz data from {file_path}.")
            return data
            
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file at '{file_path}'.")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}

from evaluate import evaluate_emotional_status, evaluate_difficulty

def get_adaptive_quiz_data(topic_key: str) -> dict:
    """
    Generates an adaptive quiz question by selecting a question randomly
    from the difficulty level determined adaptively.

    Args:
        topic_key (str): The programming concept (e.g., 'variables', 'Loops').

    Returns:
        dict: A dictionary containing only 'question', 'answer', and 'explanation' (from hint + answer),
              or an error message if generation fails.
    """
    # 1. Evaluate student's current state (emotion and difficulty)
    current_emotion = evaluate_emotional_status(topic_key)
    current_difficulty = evaluate_difficulty(current_emotion)
    QUESTIONS_DATA = import_quiz_data()
    # 2. Validate Topic and Difficulty
    if topic_key not in QUESTIONS_DATA:
        return {"error": f"Topic '{topic_key}' not found in quiz data."}
    
    topic_data = QUESTIONS_DATA[topic_key]
    
    if current_difficulty not in topic_data:
        # Fallback if the chosen difficulty is missing for this topic
        return {"error": f"Difficulty '{current_difficulty}' not available for topic '{topic_key}'."}

    # 3. Select a random problem from the determined difficulty pool
    problem_pool = topic_data[current_difficulty]["problems"]
    if not problem_pool:
        return {"error": f"No problems available for '{topic_key}' at difficulty '{current_difficulty}'."}
        
    selected_problem = random.choice(problem_pool)
    expalnation= generate_mcq_explanation(selected_problem["question"],selected_problem["options"],selected_problem["answer"],current_emotion,topic_key)
    
    return {
        "question": selected_problem["question"],
        "options": selected_problem["options"],
        "answer": selected_problem["answer"],
        "answer_index": selected_problem["answer_index"],
        "hint": selected_problem["hint"],
        "explanation": expalnation,
        "difficulty_chosen": current_difficulty, # Added for debugging/tracking
        "emotion_evaluated": current_emotion     # Added for debugging/tracking
    }

