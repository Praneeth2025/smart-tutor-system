# 📚 Smart Tutor System – Adaptive AI Teaching Framework

A modular AI-driven tutoring system combining Bayesian Knowledge Tracing, Search Algorithms, Automated Planning, Reinforcement Learning, and LLM-based Pedagogy.

## 📂 Project Structure

```
smart-tutor-system/
├── Module1_Bayesian.py
├── Module2_Search.py
├── Module3_Planning.py
├── Module4_RF.py
├── Module5_llm.py
├── module4ui.py
├── module4rf_qtable.json
├── course_content.json
├── questions.json
└── README.md
```

## ⚙️ Installation

```
pip install numpy networkx matplotlib imageio google-generativeai streamlit
```

## 🔧 API Key Setup

### Windows
```
setx GOOGLE_API_KEY "your_key"
```

### Linux/macOS
```
export GOOGLE_API_KEY="your_key"
```

---

## 🚀 Running Modules

### **Module 1 – Bayesian Estimator**
```
python Module1_Bayesian.py
```

### **Module 2 – Search System**
```
python Module2_Search.py
```

### **Module 3 – Planning (GraphPlan + POP)**
```
python Module3_Planning.py
```

Generates:
- `planning_graph_levels.png`
- `pop_causal_links.png`

### **Module 4 – Reinforcement Learning**
```
python Module4_RF.py
```

Saves:
- `module4rf_qtable.json`

### **Module 5 – LLM Tutor**
```
python Module5_llm.py
```

---

## 🌐 Web UI (Streamlit)

```
streamlit run module4ui.py
```

Requires:
- module4rf_qtable.json  
- course_content.json  
- questions.json  

---

## 📝 questions.json Template

```
{
  "variables": {
    "easy": {
      "problems": [
        {
          "question": "What is a variable?",
          "options": ["A container", "A loop", "A function"],
          "answer": "A container",
          "explanation": "Variables store data."
        }
      ]
    }
  }
}
```

---

## ✅ Summary
This system integrates:
- Bayesian emotion modeling  
- Search-based topic selection  
- Curriculum planning via GraphPlan/POP  
- RL-based adaptive instruction  
- LLM-generated pedagogical explanations  

