import numpy as np

EMOTION_STATES = ['highly_confident', 'confident', 'confused', 'highly_confused', 'frustrated']

EVIDENCE_CARDINALITIES = [2, 3, 3] 


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

assert np.allclose(CPD_EMOTION_VALUES.sum(axis=0), 1.0), "CPD columns must sum to 1.0"
assert CPD_EMOTION_VALUES.shape == (5, 18), "CPD array size is incorrect"


def evaluate_emotional_status(correct: bool, time: float, feedback: str) -> str:
    """
    Calculates the Maximum A Posteriori (MAP) emotional status P(EmotionalStatus | Evidence) 
    by directly indexing the Conditional Probability Table and returning the 
    single most probable state label.
    """
    
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
    print("Emotion found using bayesian network:",EMOTION_STATES[max_index])
    return EMOTION_STATES[max_index]

