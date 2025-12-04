import random
from typing import Tuple, List, Dict, Union,Optional, Any

# 1. Define the State Space
TOPICS = ["variables", "conditionals", "loops", "functions", "oops"]
LEVELS = ["easy", "medium", "hard"]
N_TOPICS = len(TOPICS)
N_LEVELS = len(LEVELS)
TOTAL_STATES = N_TOPICS * N_LEVELS

# Create a mapping of (topic, level) -> State Index (0 to 14)
STATE_MAP: Dict[Tuple[str, str], int] = {}
# Create a reverse map: State Index -> (topic, level)
STATE_REVERSE_MAP: Dict[int, Tuple[str, str]] = {}

state_index = 0
for topic in TOPICS:
    for level in LEVELS:
        STATE_MAP[(topic, level)] = state_index
        STATE_REVERSE_MAP[state_index] = (topic, level)
        state_index += 1

# Define the Actions (Emotions)
ACTIONS = {
    'highly_confident': 0,
    'confident': 1,
    'confused': 2,
    'highly_confused': 3,
    'frustrated': 4
}


def get_next_state_index(current_index: int, direction: int) -> int:
    """
    Calculates the next state index, handling boundary conditions (start/end).
    Direction: +1 for next state, -1 for previous state.
    """
    new_index = current_index + direction
    
    # Boundary Check: If the index goes beyond the total states, stay at the boundary.
    # This assumes the learning stops at the final state, or stays in the first state.
    if new_index >= TOTAL_STATES:
        return TOTAL_STATES - 1
    if new_index < 0:
        return 0
        
    return new_index


def AdaptiveTutorEnv(current_state_tuple: Tuple[str, str], action: str) -> Tuple[Tuple[str, str], float]:
    """
    The environment function that executes an action and returns the next state and reward.

    Args:
        current_state_tuple (Tuple[str, str]): Current state (e.g., ('variables', 'easy')).
        action (str): The chosen action (emotion).

    Returns:
        Tuple[Tuple[str, str], float]: (next_state_tuple, reward).
    """
    
    # Convert state tuple to an index for easier transition logic
    if current_state_tuple not in STATE_MAP:
        raise ValueError(f"Invalid state: {current_state_tuple}")

    current_index = STATE_MAP[current_state_tuple]
    reward = 0.0
    next_index = current_index
    
    # Use random.random() to sample based on the defined probabilities
    prob_sample = random.random()

    # --- Transition Logic and Rewards based on Action (Emotion) ---

    if action == 'highly_confident':
        # 1. highly-confident: 0.9 next state, 0.1 same state
        if prob_sample < 0.9:
            # Go to next state (direction +1)
            next_index = get_next_state_index(current_index, 1)
            reward = 25
        else:
            # Stay in the same state
            reward = 10
            
    elif action == 'confident':
        # 2. confident: 0.75 next state, 0.25 same state (0.5 was given, but sum must be 1.0)
        # Assuming you meant 0.75 next state and 0.25 same state (total 1.0)
        if prob_sample < 0.75:
            # Go to next state (direction +1)
            next_index = get_next_state_index(current_index, 1)
            reward = 20
        else:
            # Stay in the same state
            reward = 10

    elif action == 'confused':
        # 3. confused: 1.0 same state
        # Stay in the same state
        reward = 15

    elif action == 'highly_confused':
        # 4. highly confused: 0.75 previous state, 0.25 same state (0.5 was given, but sum must be 1.0)
        # Assuming you meant 0.75 previous state and 0.25 same state (total 1.0)
        if prob_sample < 0.75:
            # Go to previous state (direction -1)
            next_index = get_next_state_index(current_index, -1)
            reward = -20
        else:
            # Stay in the same state
            reward = -10

    elif action == 'frustrated':
        # 5. frustrated: 0.9 previous state, 0.1 same state
        if prob_sample < 0.9:
            # Go to previous state (direction -1)
            next_index = get_next_state_index(current_index, -1)
            reward = -25
        else:
            # Stay in the same state
            reward = -10
            
    else:
        raise ValueError(f"Invalid action (emotion): {action}")

    # Convert the resulting index back to the state tuple
    next_state_tuple = STATE_REVERSE_MAP[next_index]
    print("next state that will be used: ",next_state_tuple)
    return next_state_tuple, reward




import json
import os
from typing import Dict, Any

def load_q_tables_from_json(file_path: str = 'values_for_Q-learning.json') -> Dict[str, Any]:
    """
    Loads Q-Learning tables and hyperparameters from a JSON file.

    Args:
        file_path (str): The path to the JSON file containing the Q and V tables.

    Returns:
        Dict[str, Any]: A dictionary containing the 'Q_TABLE', 'V_TABLE', and 
                        'HYPERPARAMETERS', or an error dictionary if loading fails.
    """
    
    # 1. Check if the file exists
    if not os.path.exists(file_path):
        # Create the initial JSON file if it doesn't exist
        print(f"File not found at '{file_path}'. Initializing tables...")
        
        # NOTE: You would typically write the full initial JSON structure here
        # or call a function to generate the initial structure.
        initial_tables = {
            "Q_TABLE": {},
            "V_TABLE": {},
            "HYPERPARAMETERS": {
                "learning_rate_eta": 0.7,
                "discount_factor_gamma": 0.9
            }
        }
        
        # For simplicity, we'll return a minimal structure, but you need 
        # the full structure defined previously to avoid errors later.
        return initial_tables


    try:
        # 2. Open and load the JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            tables_data = json.load(f)
            print(f"Successfully loaded Q-Learning tables from {file_path}.")
            return tables_data
            
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file at '{file_path}'. File may be corrupted.")
        return {"error": "JSON Decode Error"}
        
    except Exception as e:
        print(f"An unexpected error occurred during file loading: {e}")
        return {"error": f"File Load Error: {e}"}

# --- Utility Function to Save Tables (Recommended for Q-Learning) ---
def save_q_tables_to_json(tables: Dict[str, Any], file_path: str = 'values_for_Q-learning.json')-> None:
    """
    Saves the updated Q-Learning tables and hyperparameters back to a JSON file.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=4)
        print(f"Successfully saved Q-Learning tables to {file_path}.")
    except Exception as e:
        print(f"Error saving Q-Learning tables: {e}")



# Define the state/action string conversion utility functions
def state_tuple_to_key(state_tuple: Tuple[str, str]) -> str:
    """Converts a state tuple (topic, level) to a string key 'topic_level'."""
    return f"{state_tuple[0]}_{state_tuple[1]}"

def update_q_and_v_values(
    current_state: Tuple[str, str], 
    action: str, 
    reward: float, 
    next_state: Tuple[str, str]
) -> Dict[str, Any]:
    """
    Updates the Q-value and V-value tables based on one step of Q-Learning.

    Args:
        tables: Dictionary containing 'Q_TABLE', 'V_TABLE', and 'HYPERPARAMETERS'.
        current_state: The state before the action (s).
        action: The action taken (a).
        reward: The reward received (r).
        next_state: The state after the action (s').

    Returns:
        The updated tables dictionary.
    """
    tables=load_q_tables_from_json()
    Q = tables['Q_TABLE']
    V = tables['V_TABLE']
    eta = tables['HYPERPARAMETERS']['learning_rate_eta'] # Learning Rate (eta)
    gamma = tables['HYPERPARAMETERS']['discount_factor_gamma'] # Discount Factor (gamma)

    s_key = state_tuple_to_key(current_state)
    s_prime_key = state_tuple_to_key(next_state)

    # 1. Calculate the Optimal Value V_opt(s') for the next state
    # V_opt(s') = max_a'( Q_opt(s', a') )
    if s_prime_key in Q:
        # Get the max Q-value for all possible actions in the next state (s')
        # If the state is the terminal state, V should probably be 0, but since
        # our state space is cyclical/linear, we treat all states as non-terminal.
        V_opt_s_prime = max(Q[s_prime_key].values())
    else:
        # Should not happen if tables are initialized correctly
        V_opt_s_prime = 0.0
    
    # Update V_TABLE with the newly calculated optimal value for the next state
    V[s_prime_key] = V_opt_s_prime

    # 2. Calculate the Q-Learning Target
    # Target = r + gamma * V_opt(s')
    target = reward + (gamma * V_opt_s_prime)
    
    # 3. Get the Current Q-value (Prediction)
    # Q_opt(s, a)
    Q_s_a_prediction = Q[s_key][action]
    
    # 4. Apply the Q-Learning Update Rule
    # Q_opt(s, a) <- (1 - eta) * Q_opt(s, a) + eta * Target
    new_Q_s_a = (1 - eta) * Q_s_a_prediction + eta * target
    
    # 5. Store the new Q-value
    Q[s_key][action] = new_Q_s_a
    
    # The V_TABLE for the current state (s) might also need updating after Q[s,a] is updated,
    # if the updated Q[s,a] is now the max Q-value for state s.
    V[s_key] = max(Q[s_key].values())
    save_q_tables_to_json(tables)




# 2. Define the step (s, a, r, s') - assuming the environment function is available
s = ('variables', 'easy')
a = 'highly_confident' 

# Simulate one step using the environment function (requires the previous function)
next_s, r = AdaptiveTutorEnv(s, a) 
def evaluate_difficulty(topic_key: str,level: str, emotion_state: str):
    s=(topic_key,level)
    a=emotion_state
    next_s,r=AdaptiveTutorEnv(s,a)
    update_q_and_v_values( s, a, r, next_s)
    return next_s

