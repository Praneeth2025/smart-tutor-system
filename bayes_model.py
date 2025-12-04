import numpy as np
import math

# -----------------------------------------------------------
# EMOTIONAL STATES (ordered)
# -----------------------------------------------------------
EMOTION_STATES = [
    "highly_confident",
    "confident",
    "confused",
    "highly_confused",
    "frustrated"
]

# -----------------------------------------------------------
# PRIOR PROBABILITIES (P(Emotion))
# -----------------------------------------------------------
PRIORS = np.array([
    0.25,  # highly confident
    0.30,  # confident
    0.20,  # confused
    0.15,  # highly confused
    0.10   # frustrated
])

# -----------------------------------------------------------
# LIKELIHOOD 1 — CORRECTNESS: P(Correct | Emotion)
# Format: [emotion_index][0 = correct, 1 = incorrect]
# -----------------------------------------------------------
P_correct = np.array([
    [0.90, 0.10],  # highly confident
    [0.80, 0.20],  # confident
    [0.60, 0.40],  # confused
    [0.40, 0.60],  # highly confused
    [0.30, 0.70],  # frustrated
])

# -----------------------------------------------------------
# LIKELIHOOD 2 — FEEDBACK: P(Feedback | Emotion)
# Column mapping: 0=Too Easy, 1=Just Right, 2=Too Hard
# -----------------------------------------------------------
P_feedback = np.array([
    [0.70, 0.25, 0.05],  # highly confident
    [0.50, 0.40, 0.10],  # confident
    [0.20, 0.50, 0.30],  # confused
    [0.10, 0.40, 0.50],  # highly confused
    [0.05, 0.30, 0.65],  # frustrated
])

# -----------------------------------------------------------
# LIKELIHOOD 3 — CONTINUOUS TIME DISTRIBUTION
# Gaussian parameters for each emotion
# -----------------------------------------------------------
TIME_PARAMS = {
    "highly_confident":  (5.0, 3.0),   # mean=5s, stdev=3
    "confident":         (10.0, 5.0),
    "confused":          (18.0, 6.0),
    "highly_confused":   (30.0, 8.0),
    "frustrated":        (40.0,10.0),
}

# -----------------------------------------------------------
# Gaussian likelihood P(time | emotion)
# -----------------------------------------------------------
def gaussian(x, mu, sigma):
    coeff = 1 / (sigma * np.sqrt(2*np.pi))
    exponent = -((x - mu) ** 2) / (2 * sigma * sigma)
    return coeff * np.exp(exponent)

# -----------------------------------------------------------
# MAIN FUNCTION: Bayesian Inference
# -----------------------------------------------------------
def infer_emotion(correct_bool, time_sec, feedback):
    """
    Performs Bayesian inference using:
        - correctness (bool)
        - time taken (float seconds)
        - subjective feedback ("Too Easy", "Just Right", "Too Hard")
    Returns:
        predicted_emotion (string),
        posterior_array (numpy array of size 5)
    """

    # Map correctness to index
    c_idx = 0 if correct_bool else 1

    # Map feedback
    f_idx = {"Too Easy":0, "Just Right":1, "Too Hard":2}.get(feedback, 1)

    # Prepare unnormalized posterior
    unnorm = np.zeros(5)

    for i, emotion in enumerate(EMOTION_STATES):
        # Likelihood from time
        mu, sigma = TIME_PARAMS[emotion]
        p_time = gaussian(time_sec, mu, sigma)

        unnorm[i] = (
            PRIORS[i] *
            P_correct[i][c_idx] *
            P_feedback[i][f_idx] *
            p_time
        )

    # Normalize
    posterior = unnorm / unnorm.sum()

    # Best prediction
    best_state = EMOTION_STATES[np.argmax(posterior)]

    return best_state, posterior


# -----------------------------------------------------------
# MAIN
# -----------------------------------------------------------
if __name__ == "__main__":
    e, p = infer_emotion(
        correct_bool=False,
        time_sec=33.5,
        feedback="Too Hard"
    )
    print("Prediction:", e)
    print("Posterior:", p)
