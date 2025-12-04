# 📚 Smart Tutor System – Adaptive AI Teaching Framework

A modular AI-driven tutoring system combining Bayesian Knowledge Tracing, Search Algorithms, Automated Planning, Reinforcement Learning, and LLM-based Pedagogy. This project demonstrates how different AI paradigms can coordinate to create an adaptive learning experience.

## 📂 Project Structure

Ensure your directory looks like this before running:

```text
smart-tutor-system/
│
├── Module1_Bayesian.py      # Bayesian Network for Emotion Estimation
├── Module2_Search.py        # BFS/UCS/A* for Topic Selection
├── Module3_Planning.py      # GraphPlan & POP for Curriculum Planning
├── Module4_RF.py            # Reinforcement Learning (Q-Learning Backend)
├── Module5_llm.py           # LLM Response Generation (Gemini)
├── module4ui.py             # Streamlit Web Interface (Frontend)
│
├── module4rf_qtable.json    # Pre-trained Q-Table (for RL)
├── course_content.json      # Course text content (for UI)
├── questions.json           # (Required) Question bank for the UI
└── README.md
⚙️ Prerequisites & Installation
Python 3.8+ is required.

Install the necessary dependencies:

Bash

pip install numpy networkx matplotlib imageio google-generativeai streamlit
API Key Setup (For Module 5): You need a Google Gemini API key.

Option A (Environment Variable - Recommended):

Bash

# Windows
setx GOOGLE_API_KEY "your_api_key_here"

# Mac/Linux
export GOOGLE_API_KEY="your_api_key_here"
Option B (Direct Edit): Open Module5_llm.py and replace YOUR_API_KEY_HERE with your actual key.

🚀 How to Run Each Module
🧠 Module 1: Bayesian Emotion Estimation
Calculates the probability of student emotions based on correctness, time taken, and feedback.

Bash

python Module1_Bayesian.py
Output: Prints the posterior probabilities and the most likely emotional state in the console.

🔍 Module 2: Search-Based Topic Recommendation
Uses BFS, UCS, and A* to traverse a concept dependency graph and recommend the next topic.

Bash

python Module2_Search.py
Input: You will be prompted to enter a Student Readiness (1-5) and Target Difficulty (1-5).

Output: Prints the recommended path in the console and generates GIF visualizations (bfs_visualization.gif, etc.) in the folder.

🧩 Module 3: Automated Planning (GraphPlan & POP)
Generates a multi-step teaching plan using partial-order planning to move a student from "NoKnowledge" to "FullKnowledge".

Bash

python Module3_Planning.py
Output: Prints the linearization of the plan and saves visualization images:

planning_graph_layered.png

pop_causal_links.png

🎮 Module 4: Reinforcement Learning (Backend)
Trains the Q-Learning agent to optimize teaching strategies (difficulty adjustment, hints, etc.).

Bash

python Module4_RF.py
Action: Runs a training simulation (default 600 episodes).

Output: Prints training stats and saves the learned policy to module4rf_qtable.json.

🤖 Module 5: LLM Response Generation
Uses Google Gemini to generate an empathetic, pedagogically structured explanation for a quiz question.

Bash

python Module5_llm.py
Output: Prints the prompt sent to the LLM and the generated response text.

🌐 Running the Web Interface (UI)
The Streamlit interface brings Module 4 (RL), Module 5 (LLM), and the course content together into an interactive web app.

Requirement: Ensure module4rf_qtable.json, course_content.json, and a valid questions.json are in the same folder.

Bash

streamlit run module4ui.py
Features in UI:

Sidebar: Select topics and view live student state (Frustration/Engagement).

Learning Area: Read course material (from course_content.json).

Quiz Area:

Takes quizzes.

Receives immediate feedback.

RL Agent adjusts difficulty automatically based on your performance.

LLM provides detailed explanations.

📝 Note on Data Files
module4rf_qtable.json: This file stores the "brain" of the RL agent. If you delete it, run Module4_RF.py to regenerate it.

questions.json: The UI requires a question bank file. If you do not have one, create a file named questions.json with the following structure:

JSON

{
  "variables": {
    "easy": {
      "problems": [
        {
          "question": "What is a variable?",
          "options": ["A container", "A loop", "A function"],
          "answer": "A container",
          "explanation": "Variables store data values."
        }
      ]
    }
  }
}