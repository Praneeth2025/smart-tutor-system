# 4_reinforcement_learning.py
import numpy as np
import random

class StudentSimulator:
    def _init_(self):
        self.mastery_level = 0.3  # 0-1
        self.frustration = 0.2    # 0-1
        self.engagement = 0.7     # 0-1
    
    def respond(self, action, difficulty):
        """Simulate student response to teaching action"""
        if action == 'increase_difficulty':
            if difficulty > self.mastery_level + 0.2:
                self.frustration += 0.1
                self.engagement -= 0.1
                return 'frustrated'
            else:
                self.mastery_level += 0.05
                return 'success'
        
        elif action == 'decrease_difficulty':
            if difficulty < self.mastery_level - 0.2:
                self.engagement -= 0.05
                return 'bored'
            else:
                self.mastery_level += 0.03
                self.frustration -= 0.05
                return 'success'
        
        elif action == 'switch_style':
            self.engagement += 0.1
            return 'engaged'
        
        elif action == 'offer_revision':
            self.mastery_level += 0.02
            self.frustration -= 0.1
            return 'improved'
        
        return 'neutral'

class QLearningTutor:
    def _init_(self, learning_rate=0.1, discount=0.9, epsilon=0.1):
        self.lr = learning_rate
        self.gamma = discount
        self.epsilon = epsilon
        
        # State: (mastery_level_bucket, frustration_bucket, engagement_bucket)
        # Actions: increase_difficulty, decrease_difficulty, switch_style, offer_revision
        self.actions = ['increase_difficulty', 'decrease_difficulty', 
                       'switch_style', 'offer_revision']
        
        # Discretize state space
        self.q_table = {}
    
    def get_state(self, student):
        """Discretize continuous state"""
        mastery_bucket = int(student.mastery_level * 5)  # 0-4
        frustration_bucket = int(student.frustration * 5)  # 0-4
        engagement_bucket = int(student.engagement * 5)  # 0-4
        return (mastery_bucket, frustration_bucket, engagement_bucket)
    
    def get_q_value(self, state, action):
        if (state, action) not in self.q_table:
            self.q_table[(state, action)] = 0.0
        return self.q_table[(state, action)]
    
    def choose_action(self, state):
        """Epsilon-greedy action selection"""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        
        q_values = [self.get_q_value(state, action) for action in self.actions]
        max_q = max(q_values)
        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return self.actions[random.choice(best_actions)]
    
    def update_q(self, state, action, reward, next_state):
        """Q-learning update"""
        current_q = self.get_q_value(state, action)
        max_next_q = max([self.get_q_value(next_state, a) for a in self.actions])
        
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[(state, action)] = new_q
    
    def reward_function(self, student, action, response):
        """Reward function: encourage learning, minimize frustration"""
        reward = 0
        
        # Learning gain
        if response == 'success' or response == 'improved':
            reward += 10
        
        # Frustration penalty
        if student.frustration > 0.7:
            reward -= 20
        
        # Engagement bonus
        if student.engagement > 0.8:
            reward += 5
        
        # Dropout prevention
        if student.frustration > 0.9 or student.engagement < 0.2:
            reward -= 50
        
        # Mastery progress
        reward += student.mastery_level * 5
        
        return reward

def train_tutor(episodes=1000):
    """Train RL tutor"""
    tutor = QLearningTutor()
    results = []
    
    for episode in range(episodes):
        student = StudentSimulator()
        current_difficulty = 0.3
        total_reward = 0
        
        for step in range(50):  # Max steps per episode
            state = tutor.get_state(student)
            action = tutor.choose_action(state)
            
            response = student.respond(action, current_difficulty)
            
            # Update difficulty based on action
            if action == 'increase_difficulty':
                current_difficulty += 0.1
            elif action == 'decrease_difficulty':
                current_difficulty -= 0.1
            
            reward = tutor.reward_function(student, action, response)
            next_state = tutor.get_state(student)
            
            tutor.update_q(state, action, reward, next_state)
            total_reward += reward
            
            # Early termination
            if student.frustration > 0.9 or student.mastery_level > 0.95:
                break
        
        results.append({
            'episode': episode,
            'final_mastery': student.mastery_level,
            'final_frustration': student.frustration,
            'total_reward': total_reward
        })
    
    return tutor, results

def naive_tutor(student, difficulty=0.5):
    """Fixed difficulty tutor for comparison"""
    responses = []
    for _ in range(50):
        response = student.respond('increase_difficulty', difficulty)
        responses.append(response)
        if student.frustration > 0.9:
            break
    return student.mastery_level, student.frustration

if __name__ == "_main_":
    print("=" * 60)
    print("REINFORCEMENT LEARNING FOR TUTOR OPTIMIZATION")
    print("=" * 60)
    
    # Train RL tutor
    print("\nTraining RL Tutor...")
    rl_tutor, training_results = train_tutor(episodes=50000)
    
    # Test RL tutor
    print("\nTesting RL Tutor:")
    test_student = StudentSimulator()
    test_difficulty = 0.3
    
    for step in range(20):
        state = rl_tutor.get_state(test_student)
        action = rl_tutor.choose_action(state)
        print(f"Step {step+1}: Action={action}, Mastery={test_student.mastery_level:.2f}, "
              f"Frustration={test_student.frustration:.2f}")
        
        test_student.respond(action, test_difficulty)
        if action == 'increase_difficulty':
            test_difficulty += 0.1
        elif action == 'decrease_difficulty':
            test_difficulty -= 0.1
    
    # Compare with naive tutor
    print("\nComparing with Naive Fixed-Difficulty Tutor:")
    naive_student = StudentSimulator()
    naive_mastery, naive_frustration = naive_tutor(naive_student)
    
    print(f"\nRL Tutor Results:")
    print(f"  Final Mastery: {test_student.mastery_level:.3f}")
    print(f"  Final Frustration: {test_student.frustration:.3f}")
    
    print(f"\nNaive Tutor Results:")
    print(f"  Final Mastery: {naive_mastery:.3f}")
    print(f"  Final Frustration: {naive_frustration:.3f}")
    
    print(f"\nImprovement:")
    print(f"  Mastery gain: {test_student.mastery_level - naive_mastery:.3f}")
    print(f"  Frustration reduction: {naive_frustration - test_student.frustration:.3f}")