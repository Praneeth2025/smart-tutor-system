
import random
def evaluate_emotional_status(topic_key: str) -> str:
    states = ["Confident", "Mildly Confused", "Frustrated", "Engaged"]
    return random.choice(states) 

def evaluate_difficulty(topic_key: str) -> str:
    levels = ["Easy", "Medium", "Hard"]
    return random.choice(levels)
