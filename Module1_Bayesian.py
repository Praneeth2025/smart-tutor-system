import numpy as np

# -----------------------------------------------------------
# MODULE 1 — BAYESIAN NETWORK FOR EMOTION ESTIMATION
# -----------------------------------------------------------

EMOTION_STATES = [
    'highly_confident',
    'confident',
    'confused',
    'highly_confused',
    'frustrated'
]

# Conditional Probability Table (5 emotion states × 18 parent combinations)
CPD = np.array([
    [0.95,0.40,0.85,0.30,0.70,0.20, 0.80,0.30,0.75,0.25,0.60,0.15, 0.60,0.10,0.40,0.05,0.10,0.01],
    [0.05,0.30,0.10,0.35,0.15,0.30, 0.15,0.40,0.20,0.40,0.25,0.30, 0.25,0.30,0.40,0.25,0.40,0.05],
    [0.00,0.20,0.05,0.25,0.10,0.30, 0.05,0.20,0.05,0.25,0.10,0.30, 0.10,0.40,0.15,0.50,0.30,0.15],
    [0.00,0.10,0.00,0.08,0.05,0.10, 0.00,0.05,0.00,0.08,0.05,0.15, 0.05,0.15,0.05,0.15,0.15,0.35],
    [0.00,0.00,0.00,0.02,0.00,0.10, 0.00,0.05,0.00,0.02,0.00,0.10, 0.00,0.05,0.00,0.05,0.05,0.44]
])

# -----------------------------------------------------------
# FINAL Step-wise evaluation
# -----------------------------------------------------------

def evaluate_emotional_status_stepwise(correct, time_taken, feedback):
    print("\n=== STEP 1: INPUT EVIDENCE ===")
    print(f"Correctness       : {correct}")
    print(f"Time Taken (sec)  : {time_taken}")
    print(f"Feedback          : {feedback}\n")

    # Convert evidence → categorical states
    C = 0 if correct else 1
    T = 0 if time_taken < 10 else (1 if time_taken < 30 else 2)
    F = {"Too Easy":0, "Just Right":1, "Too Hard":2}.get(feedback, 1)

    print(f"Mapped Evidence:")
    print(f"  C_state = {C} ({'Correct' if C==0 else 'Incorrect'})")
    print(f"  T_state = {T} ({['Short','Medium','Long'][T]})")
    print(f"  F_state = {F} ({['Too Easy','Just Right','Too Hard'][F]})\n")

    print("=== STEP 2: COMPUTE INTERMEDIATE INDEX ===")
    part1 = C
    part2 = 2*T
    part3 = 6*F

    print(f"Contribution from Correctness       : {part1}")
    print(f"Contribution from Time Category     : {part2}")
    print(f"Contribution from Feedback Category : {part3}")

    index = part1 + part2 + part3
    print(f"\nComputed Index (C + 2T + 6F) = {index}\n")

    print("=== STEP 3: RETRIEVE POSTERIOR FROM CPT ===")
    posterior = CPD[:, index]

    for state, prob in zip(EMOTION_STATES, posterior):
        print(f"P({state}) : {prob:.4f}")
    print()

    print("=== STEP 4: FINAL RESULT (MAP ESTIMATION) ===")
    most_idx = np.argmax(posterior)
    most_state = EMOTION_STATES[most_idx]
    confidence = posterior[most_idx]

    print(f"Most Probable Emotional State : {most_state.upper()}")
    print(f"Confidence                    : {confidence:.4f}\n")

    print("============================================================\n")
    return most_state


# -----------------------------------------------------------
# Examples
# -----------------------------------------------------------
if __name__ == "__main__":
    evaluate_emotional_status_stepwise(True, 15, "Just Right")
    evaluate_emotional_status_stepwise(False, 45, "Too Hard")
    evaluate_emotional_status_stepwise(True, 5, "Too Easy")
