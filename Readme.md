# 📚 Smart Tutor System – Adaptive AI Teaching Framework

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red) ![AI](https://img.shields.io/badge/AI-Bayesian%20%7C%20RL%20%7C%20LLM-green)

A modular AI-driven tutoring system that adapts to student emotions and performance. This project demonstrates the coordination of five distinct AI paradigms to create a personalized learning experience.

## 🧠 System Architecture

```mermaid
graph TD;
    User-->UI[Streamlit UI];
    UI-->Bayesian[Module 1: Emotion Est];
    UI-->Search[Module 2: Topic Search];
    UI-->RL[Module 4: RL Tutor];
    RL-->Policy[Q-Table];
    UI-->LLM[Module 5: Gemini LLM];
    Planning[Module 3: Curriculum Plan]-->Search;
📂 Project StructurePlaintextsmart-tutor-system/
│
├── Module1_Bayesian.py      # 🧠 Bayesian Network (Emotion Estimation)
├── Module2_Search.py        # 🔍 Search Algos (Topic Selection)
├── Module3_Planning.py      # 🧩 Automated Planning (Curriculum Design)
├── Module4_RF.py            # 🎮 Reinforcement Learning (Q-Learning Backend)
├── Module5_llm.py           # 🤖 LLM Generation (Pedagogical Explanations)
├── module4ui.py             # 🌐 Streamlit Web Interface (Main App)
│
├── module4rf_qtable.json    # 💾 Learned RL Policy (Auto-generated/updated)
├── course_content.json      # 📖 Text content for lessons
├── questions.json           # ❓ Question bank (REQUIRED)
└── README.md
⚙️ Installation & Setup1. PrerequisitesEnsure you have Python 3.8+ installed.2. Install DependenciesBashpip install numpy networkx matplotlib imageio google-generativeai streamlit
3. API Key Setup (Required for LLM)You need a Google Gemini API Key for Module 5.Windows:Bashsetx GOOGLE_API_KEY "your_api_key_here"
Mac/Linux:Bashexport GOOGLE_API_KEY="your_api_key_here"
🚀 Running the ModulesYou can run each module individually to test specific AI behaviors, or run the full UI.🌐 Main Interface (The Full Experience)This combines the RL Tutor, LLM explanations, and Course Content.Bashstreamlit run module4ui.py
🧪 Individual Module TestingModuleCommandDescriptionEmotion Estpython Module1_Bayesian.pyCalculates probability of frustration vs. confidence.Searchpython Module2_Search.pyVisualizes BFS/A* paths for topic prerequisites.Planningpython Module3_Planning.pyGenerates a logical teaching plan from scratch.RL Trainingpython Module4_RF.pyTrains the Q-Learning agent (updates .json policy).LLM Genpython Module5_llm.pyGenerates a sample empathetic explanation.📝 Configuration Files1. questions.json (Required)The UI requires this file to load quizzes. If it is missing, create a file named questions.json in the root directory and paste this content:JSON{
  "variables": {
    "easy": {
      "problems": [
        {
          "question": "What is a variable in Python?",
          "options": ["A storage container", "A loop", "A function error"],
          "answer": "A storage container",
          "explanation": "Think of a variable as a labeled box where you can store data."
        }
      ]
    },
    "medium": {
      "problems": [
        {
          "question": "Which variable name is invalid?",
          "options": ["my_var", "2variable", "_var"],
          "answer": "2variable",
          "explanation": "Variable names cannot start with a number."
        }
      ]
    },
    "hard": {
      "problems": [
        {
          "question": "What is the output of x, y = y, x?",
          "options": ["Swap values", "Error", "Duplicate values"],
          "answer": "Swap values",
          "explanation": "Python allows tuple unpacking to swap values in one line."
        }
      ]
    }
  }
}
2. module4rf_qtable.jsonThis file stores the "brain" of the RL tutor.Missing file? Run python Module4_RF.py to train a new agent and generate this file.Reset logic? Delete this file and run the training script again.🔧 TroubleshootingModuleNotFoundError: Ensure you are running the command from inside the smart-tutor-system folder.Gemini API Error: Check your environment variable. You may need to restart your terminal/IDE after setting the key.Graphs not showing?: Search and Planning modules generate .png or .gif files in the directory. Open them manually if they don't pop up.
