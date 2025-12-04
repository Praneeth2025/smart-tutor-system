import numpy as np

# -----------------------------
# 1. Define Network Structure and States
# -----------------------------
# EmotionalStatus (5 states):
# 0: Highly Confident, 1: Confident, 2: Confused, 3: Highly Confused, 4: Frustrated
EMOTION_STATES = ['highly_confident', 'confident', 'confused', 'highly_confused', 'frustrated']

# Evidence Nodes (Parent Order):
# 1. Correct (2 states): 0: True, 1: False
# 2. TimeTaken (3 states): 0: Short (<10s), 1: Medium (10-30s), 2: Long (>30s)
# 3. Feedback (3 states): 0: Too Easy, 1: Just Right (Default), 2: Too Hard
EVIDENCE_CARDINALITIES = [2, 3, 3] # [Card_C, Card_T, Card_F]

# -----------------------------
# 2. Define Conditional Probability Distribution (CPD) for EmotionalStatus
# -----------------------------
# P(EmotionalStatus | Correct, TimeTaken, Feedback)
# This 5x18 matrix defines the probability of each Emotional State (rows) 
# for every combination of parent states (columns). 
# Indexing Order (based on pgmpy convention for evidence_card=[C, T, F]):
# Index I = C_state + (Card_C * T_state) + (Card_C * Card_T * F_state)
# I = C_state + (2 * T_state) + (6 * F_state)

# The values below are illustrative but logically structured:
# Example Logic: Correct(0), Short(0), Too Easy(0) -> Index 0 -> High Confident (High Prob)
# Example Logic: Incorrect(1), Long(2), Too Hard(2) -> Index 17 -> Frustrated (High Prob)

CPD_EMOTION_VALUES = np.array([
    # F=TooEasy(0) -> T=Short(0), T=Medium(1), T=Long(2)
    # C=True(0), C=False(1) | C=True(0), C=False(1) | C=True(0), C=False(1)
    # I: 0, 1 | 2, 3 | 4, 5
    [0.95, 0.40, 0.85, 0.30, 0.70, 0.20,
    # F=JustRight(1) -> T=Short(0), T=Medium(1), T=Long(2)
    # C=True(0), C=False(1) | C=True(0), C=False(1) | C=True(0), C=False(1)
    # I: 6, 7 | 8, 9 | 10, 11
     0.80, 0.30, 0.75, 0.25, 0.60, 0.15,
    # F=TooHard(2) -> T=Short(0), T=Medium(1), T=Long(2)
    # C=True(0), C=False(1) | C=True(0), C=False(1) | C=True(0), C=False(1)
    # I: 12, 13 | 14, 15 | 16, 17
     0.60, 0.10, 0.40, 0.05, 0.10, 0.01], # Highly Confident (Row 0)

    [0.05, 0.30, 0.10, 0.35, 0.15, 0.30,
     0.15, 0.40, 0.20, 0.40, 0.25, 0.30,
     0.25, 0.30, 0.40, 0.25, 0.40, 0.05], # Confident (Row 1)

    [0.00, 0.20, 0.05, 0.25, 0.10, 0.30,
     0.05, 0.20, 0.05, 0.25, 0.10, 0.30,
     0.10, 0.40, 0.15, 0.50, 0.30, 0.15], # Confused (Row 2)

    [0.00, 0.10, 0.00, 0.08, 0.05, 0.10,
     0.00, 0.05, 0.00, 0.08, 0.05, 0.15,
     0.05, 0.15, 0.05, 0.15, 0.15, 0.35], # Highly Confused (Row 3)

    [0.00, 0.00, 0.00, 0.02, 0.00, 0.10,
     0.00, 0.05, 0.00, 0.02, 0.00, 0.10,
     0.00, 0.05, 0.00, 0.05, 0.05, 0.44]  # Frustrated (Row 4)
])

# Ensure all columns sum to 1 (within floating point tolerance)
assert np.allclose(CPD_EMOTION_VALUES.sum(axis=0), 1.0), "CPD columns must sum to 1.0"
assert CPD_EMOTION_VALUES.shape == (5, 18), "CPD array size is incorrect"


# Define the function for evaluation
def evaluate_emotional_status(correct: bool, time: float, feedback: str) -> str:
    """
    Calculates the Maximum A Posteriori (MAP) emotional status P(EmotionalStatus | Evidence) 
    by directly indexing the Conditional Probability Table and returning the 
    single most probable state label.
    """
    
    # -----------------------------
    # 3. Convert inputs to categorical states (Indices)
    # -----------------------------
    
    # Correctness State (C_state): 0 (True), 1 (False)
    C_state = 0 if correct else 1
    
    # TimeTaken State (T_state): 0 (Short), 1 (Medium), 2 (Long)
    if time < 10:
        T_state = 0  # Short
    elif time < 30:
        T_state = 1  # Medium
    else:
        T_state = 2  # Long
    
    # Feedback State (F_state): 0 (Too Easy), 1 (Just Right), 2 (Too Hard)
    # Note: "Unclear Question" is mapped to "Just Right" (1) to fit the CPD size.
    feedback_map = {"Too Easy": 0, "Just Right": 1, "Too Hard": 2, "Unclear Question": 1}
    F_state = feedback_map.get(feedback, 1) 
    
    # -----------------------------
    # 4. Calculate the Joint Index I
    # -----------------------------
    # I = C_state + (Card_C * T_state) + (Card_C * Card_T * F_state)
    # I = C_state + (2 * T_state) + (6 * F_state)
    
    index_I = C_state
    index_I += EVIDENCE_CARDINALITIES[0] * T_state # 2 * T_state
    index_I += (EVIDENCE_CARDINALITIES[0] * EVIDENCE_CARDINALITIES[1]) * F_state # 6 * F_state

    # -----------------------------
    # 5. Extract the Posterior Distribution and find the MAP state
    # -----------------------------
    # The posterior is the column vector at index_I
    posterior_values = CPD_EMOTION_VALUES[:, index_I]

    # Find the index of the maximum probability
    max_index = np.argmax(posterior_values)

    # Return the corresponding emotional state label
    return EMOTION_STATES[max_index]


# -----------------------------
# Example Usage (Updated to reflect string return)
# -----------------------------
if __name__ == "__main__":
    print("--- Example 1: Correct, Medium Time, Just Right Feedback ---")
    # Expected Index: 8. Most probable state (Index 0: 0.75, Index 1: 0.20) -> highly_confident
    result1 = evaluate_emotional_status(correct=True, time=15, feedback="Just Right")
    print(f"Input: Correct, Time=15, Feedback=Just Right. Most likely status: {result1}")
        
    print("\n--- Example 2: Incorrect, Long Time, Too Hard Feedback ---")
    # Expected Index: 17. Most probable state (Index 4: 0.44) -> frustrated
    result2 = evaluate_emotional_status(correct=False, time=45, feedback="Too Hard")
    print(f"Input: Incorrect, Time=45, Feedback=Too Hard. Most likely status: {result2}")
        
    print("\n--- Example 3: Correct, Short Time, Too Easy Feedback ---")
    # Expected Index: 0. Most probable state (Index 0: 0.95) -> highly_confident
    result3 = evaluate_emotional_status(correct=True, time=5, feedback="Too Easy")
    print(f"Input: Correct, Time=5, Feedback=Too Easy. Most likely status: {result3}")