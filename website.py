import streamlit as st
import json
import os
from Module5_llm import generate_mcq_explanation
from evaluate import evaluate_emotional_status
from Module4_other import evaluate_difficulty


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



def fetch_data(topic_key:str,current_difficulty:str,current_emotion:str) -> dict:
    QUESTIONS_DATA = import_quiz_data()
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
        "emotion_evaluated": current_emotion,
        "topic_key":topic_key     # Added for debugging/tracking
    }



def get_adaptive_quiz_data(topic_key: str,current_level: str,feedback: str, correct: bool, time: float) -> dict:
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
    current_emotion = evaluate_emotional_status(correct,time,feedback)
    (current_topic,current_difficulty) = evaluate_difficulty(topic_key=topic_key,level=current_level,emotion_state=current_emotion)
    return fetch_data(current_topic,current_difficulty,current_emotion)