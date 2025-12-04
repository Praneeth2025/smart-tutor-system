"""
Module4_RF.py
Reinforcement Learning for Long-Term Learning Optimization (Q-learning tutor + student simulator).
Adaptive Teaching Strategy RL with Streamlit-friendly helper API.
"""

from __future__ import annotations
import random
import json
from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import os

# -----------------------------
# Student simulator (stochastic)
# -----------------------------
class StudentSimulator:
    """
    Simple stochastic student model with internal continuous state:
      - mastery_level (0..1)
      - frustration   (0..1)
      - engagement    (0..1)
    The `respond(action, difficulty)` method mutates the internal state and returns a response label.
    """
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        self.mastery_level: float = 0.30
        self.frustration: float = 0.20
        self.engagement: float = 0.70

    def respond(self, action: str, difficulty: float) -> str:
        """
        Simulate the student's immediate reaction to a tutor action.
        Returns one of: 'success', 'frustrated', 'bored', 'engaged', 'improved', 'neutral'
        """
        noise = lambda: float(np.random.normal(scale=0.01))

        if action == 'increase_difficulty':
            if difficulty > self.mastery_level + 0.2:
                self.frustration = min(1.0, self.frustration + 0.12 + noise())
                self.engagement = max(0.0, self.engagement - 0.08 + noise())
                return 'frustrated'
            else:
                self.mastery_level = min(1.0, self.mastery_level + 0.05 + noise())
                self.engagement = min(1.0, self.engagement + 0.02 + noise())
                return 'success'

        elif action == 'decrease_difficulty':
            if difficulty < self.mastery_level - 0.2:
                self.engagement = max(0.0, self.engagement - 0.06 + noise())
                return 'bored'
            else:
                self.mastery_level = min(1.0, self.mastery_level + 0.03 + noise())
                self.frustration = max(0.0, self.frustration - 0.05 + noise())
                return 'success'

        elif action == 'switch_style':
            self.engagement = min(1.0, self.engagement + 0.10 + noise())
            self.frustration = max(0.0, self.frustration - 0.05 + noise())
            return 'engaged'

        elif action == 'offer_revision':
            self.mastery_level = min(1.0, self.mastery_level + 0.02 + noise())
            self.frustration = max(0.0, self.frustration - 0.10 + noise())
            return 'improved'

        return 'neutral'

# -----------------------------
# Q-learning Tutor
# -----------------------------
class QLearningTutor:
    """
    Q-learning agent that stores a Q-table over discretized student states:
      state = (mastery_bucket, frustration_bucket, engagement_bucket)  each 0..(n_buckets-1)
    Actions: increase_difficulty, decrease_difficulty, switch_style, offer_revision
    """
    def __init__(self, learning_rate: float = 0.1, discount: float = 0.95, epsilon: float = 0.12,
                 n_buckets: int = 5, seed: Optional[int] = None):
        self.lr = float(learning_rate)
        self.gamma = float(discount)
        self.epsilon = float(epsilon)
        self.n_buckets = int(n_buckets)
        self.actions = ['increase_difficulty', 'decrease_difficulty', 'switch_style', 'offer_revision']
        self.q_table: Dict[Tuple[int,int,int], Dict[str, float]] = {}
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    # ----- discretization helpers -----
    def discretize_state(self, mastery: float, frustration: float, engagement: float) -> Tuple[int,int,int]:
        """Map continuous state to integer buckets."""
        b = self.n_buckets
        m = int(np.clip(mastery, 0.0, 0.9999) * b)
        f = int(np.clip(frustration, 0.0, 0.9999) * b)
        e = int(np.clip(engagement, 0.0, 0.9999) * b)
        return (m, f, e)

    def ensure_state(self, state: Tuple[int,int,int]):
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}

    # ----- policy -----
    def choose_action(self, state: Tuple[int,int,int]) -> str:
        self.ensure_state(state)
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        qvals = self.q_table[state]
        max_val = max(qvals.values())
        best = [a for a,v in qvals.items() if v == max_val]
        return random.choice(best)

    # ----- learning update -----
    def update(self, state: Tuple[int,int,int], action: str, reward: float, next_state: Tuple[int,int,int]):
        self.ensure_state(state)
        self.ensure_state(next_state)
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values()) if self.q_table[next_state] else 0.0
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q

    # ----- reward function -----
    def reward_function(self, student: StudentSimulator, response: str) -> float:
        """
        Reward that encourages mastery and engagement; penalizes frustration / dropout.
        Tunable; returns a float reward.
        """
        reward = 0.0
        if response in ('success', 'improved', 'engaged'):
            reward += 10.0
        if response == 'frustrated':
            reward -= 12.0
        if response == 'bored':
            reward -= 6.0

        reward += student.engagement * 3.0
        reward += student.mastery_level * 5.0

        if student.frustration > 0.9 or student.engagement < 0.15:
            reward -= 50.0
        return float(reward)

    # ----- persistence -----
    def save_q_table(self, path: str):
        serializable = {str(k): v for k, v in self.q_table.items()}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2)

    def load_q_table(self, path: str):
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # Deserialize keys back to tuples
        new_q = {}
        for k_str, v in raw.items():
            # key was str(state_tuple)
            # try to eval it safely: format is "(m, f, e)"
            try:
                key = tuple(int(x.strip()) for x in k_str.strip("() ").split(","))
                if len(key) == 3:
                    new_q[key] = v
            except Exception:
                continue
        self.q_table = new_q

# -----------------------------
# Utility: mapping between difficulty value <-> level
# -----------------------------
def difficulty_to_level(diff: float) -> str:
    """Map continuous difficulty in [0,1] to 'easy'/'medium'/'hard'."""
    if diff < 0.33:
        return 'easy'
    if diff < 0.66:
        return 'medium'
    return 'hard'

def apply_action_to_difficulty(action: str, cur_diff: float) -> float:
    """Deterministic mapping of action to how it changes difficulty (UI-friendly)."""
    if action == 'increase_difficulty':
        return min(1.0, cur_diff + 0.08)
    if action == 'decrease_difficulty':
        return max(0.0, cur_diff - 0.08)
    # switch_style and offer_revision change difficulty only slightly
    if action == 'switch_style':
        return min(1.0, cur_diff + 0.02)
    if action == 'offer_revision':
        return max(0.0, cur_diff - 0.04)
    return cur_diff

# -----------------------------
# High-level API for UI integration
# -----------------------------
def infer_response_from_user_feedback(user_correct: Optional[bool], time_spent: Optional[float], feedback: Optional[str]) -> str:
    """
    Heuristic mapping from user-provided signals to a response label.
    If user_correct is provided, it takes precedence. Otherwise fallback to feedback/time heuristics.
    """
    if user_correct is True:
        # fast correct -> success; slow correct -> success (still success)
        return 'success'
    if user_correct is False:
        # incorrect: classify as frustrated or confused based on feedback/time
        if feedback and 'hard' in feedback.lower():
            return 'frustrated'
        if time_spent is not None and time_spent > 45.0:
            return 'frustrated'
        return 'bored'  # generic incorrect label
    # if correctness unknown, map feedback
    if feedback:
        fb = feedback.lower()
        if 'too hard' in fb or 'hard' in fb:
            return 'frustrated'
        if 'too easy' in fb or 'easy' in fb:
            return 'bored'
        if 'unclear' in fb:
            return 'confused'
        return 'improved'
    return 'neutral'

def update_from_feedback(
    tutor: QLearningTutor,
    student: StudentSimulator,
    last_action: Optional[str],
    last_state: Optional[Tuple[int,int,int]],
    current_diff: float,
    user_correct: Optional[bool],
    time_spent: Optional[float],
    feedback: Optional[str]
) -> Dict[str, Any]:
    """
    Apply the effect of the previous action (last_action) to the student, update the tutor's Q-table,
    and return the chosen next action and difficulty level for the UI.

    Args:
      - tutor: QLearningTutor instance
      - student: StudentSimulator instance
      - last_action: the action that was applied during the last question (or None)
      - last_state: the discretized state corresponding to before-last-action (or None)
      - current_diff: numeric difficulty at which the last question was presented (0..1)
      - user_correct: bool if known
      - time_spent: seconds spent on last question (optional)
      - feedback: textual feedback (optional)

    Returns dict:
      {
        "updated": True/False,
        "response_label": str,
        "reward": float,
        "next_action": str,
        "next_difficulty": float,
        "next_level": 'easy'/'medium'/'hard',
        "current_state": (m,f,e),
        "next_state": (m',f',e')
      }
    """
    # 1) Apply student.respond if last_action provided (mutates student state)
    if last_action is not None:
        # simulate student's reaction to last action at the previous difficulty
        simulated_response = student.respond(last_action, current_diff)
    else:
        simulated_response = infer_response_from_user_feedback(user_correct, time_spent, feedback)

    # 2) Create reward (use tutor.reward_function) and optionally adjust with direct correctness signal
    reward = tutor.reward_function(student, simulated_response)
    if user_correct is True:
        reward += 5.0
    elif user_correct is False:
        reward -= 2.0
    # small penalty for very slow answers
    if time_spent is not None and time_spent > 120.0:
        reward -= 3.0

    # 3) Update Q-table if we have previous state & action
    if last_state is not None and last_action is not None:
        # CORRECT: discretize using numeric student fields
        next_state = tutor.discretize_state(
            student.mastery_level,
            student.frustration,
            student.engagement
        )
        tutor.update(last_state, last_action, reward, next_state)
    else:
        next_state = tutor.discretize_state(
            student.mastery_level,
            student.frustration,
            student.engagement
        )

    # 4) Choose next action according to tutor (epsilon-greedy)
    cur_state = tutor.discretize_state(
        student.mastery_level,
        student.frustration,
        student.engagement
    )
    next_action = tutor.choose_action(cur_state)

    # 5) Compute next difficulty numeric value
    next_diff = apply_action_to_difficulty(next_action, current_diff)

    # 6) Map to level for question selection
    next_level = difficulty_to_level(next_diff)

    return {
        "updated": True,
        "response_label": simulated_response,
        "reward": float(reward),
        "next_action": next_action,
        "next_difficulty": float(next_diff),
        "next_level": next_level,
        "current_state": cur_state,
        "next_state": next_state
    }

# -----------------------------
# Training / evaluation utilities (kept from earlier)
# -----------------------------
def train_tutor(episodes: int = 2000, steps_per_episode: int = 50, seed: Optional[int] = None) -> Tuple[QLearningTutor, List[Dict[str, Any]]]:
    tutor = QLearningTutor(learning_rate=0.1, discount=0.95, epsilon=0.12, seed=seed)
    episode_stats: List[Dict[str,Any]] = []

    for ep in range(episodes):
        student = StudentSimulator(seed=(None if seed is None else seed + ep))
        current_difficulty = 0.3
        total_reward = 0.0

        for step in range(steps_per_episode):
            state = tutor.discretize_state(student.mastery_level, student.frustration, student.engagement)
            action = tutor.choose_action(state)
            response = student.respond(action, current_difficulty)

            if action == 'increase_difficulty':
                current_difficulty = min(1.0, current_difficulty + 0.08)
            elif action == 'decrease_difficulty':
                current_difficulty = max(0.0, current_difficulty - 0.08)

            reward = tutor.reward_function(student, response)
            next_state = tutor.discretize_state(student.mastery_level, student.frustration, student.engagement)
            tutor.update(state, action, reward, next_state)
            total_reward += reward

            if student.frustration > 0.98 or student.mastery_level > 0.995:
                break

        episode_stats.append({
            'episode': ep,
            'final_mastery': student.mastery_level,
            'final_frustration': student.frustration,
            'total_reward': total_reward
        })

        if tutor.epsilon > 0.01:
            tutor.epsilon *= 0.9995

        if (ep+1) % max(1, episodes//10) == 0:
            recent_slice = episode_stats[-max(1, episodes//50):]
            avg_recent = float(np.mean([s['total_reward'] for s in recent_slice]))
            print(f"Ep {ep+1}/{episodes}  recent_avg_reward={avg_recent:.2f}  eps={tutor.epsilon:.3f}")

    return tutor, episode_stats

def evaluate_policy(tutor: QLearningTutor, episodes: int = 50, steps: int = 50, seed: Optional[int] = None) -> List[Tuple[float,float]]:
    results = []
    for ep in range(episodes):
        student = StudentSimulator(seed=(None if seed is None else seed + 1000 + ep))
        cur_diff = 0.3
        for step in range(steps):
            state = tutor.discretize_state(student.mastery_level, student.frustration, student.engagement)
            tutor.ensure_state(state)
            qvals = tutor.q_table[state]
            if all(v == 0.0 for v in qvals.values()):
                action = random.choice(tutor.actions)
            else:
                action = max(qvals.items(), key=lambda kv: kv[1])[0]
            response = student.respond(action, cur_diff)
            if action == 'increase_difficulty':
                cur_diff = min(1.0, cur_diff + 0.08)
            elif action == 'decrease_difficulty':
                cur_diff = max(0.0, cur_diff - 0.08)
            if student.frustration > 0.98:
                break
        results.append((student.mastery_level, student.frustration))
    return results

# -----------------------------
# Optional: plotting helper (kept minimal)
# -----------------------------
def plot_training_stats(stats: List[Dict[str,Any]]):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipping plotting.")
        return
    rewards = [s['total_reward'] for s in stats]
    mastery = [s['final_mastery'] for s in stats]
    frustration = [s['final_frustration'] for s in stats]

    fig, ax = plt.subplots(3,1, figsize=(9,10))
    ax[0].plot(rewards); ax[0].set_title("Episode total reward")
    ax[1].plot(mastery); ax[1].set_title("Final mastery per episode")
    ax[2].plot(frustration); ax[2].set_title("Final frustration per episode")
    plt.tight_layout()
    plt.show()

# -----------------------------
# CLI Main for quick testing
# -----------------------------
if __name__ == "__main__":
    print("Module4_RF quick test: training short policy (demo)...")
    tutor, stats = train_tutor(episodes=600, steps_per_episode=40, seed=42)
    plot_training_stats(stats)
    print("Training done. Evaluating...")
    eval_results = evaluate_policy(tutor, episodes=50, steps=40, seed=500)
    avg_mastery = float(np.mean([r[0] for r in eval_results]))
    avg_frustr = float(np.mean([r[1] for r in eval_results]))
    print(f"Eval avg mastery={avg_mastery:.3f}, avg frustration={avg_frustr:.3f}")
    try:
        tutor.save_q_table("module4rf_qtable.json")
        print("Q-table saved to module4rf_qtable.json")
    except Exception:
        pass
