import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD


class StudentStateEstimator:
    def __init__(self):

        # Create empty model
        self.model = DiscreteBayesianNetwork()

        # Add only nodes (no edges inside pgmpy)
        self.model.add_nodes_from([
            'ResponseCorrectness',
            'HesitationTime',
            'EmotionalKeywords',
            'RepeatedMistakes',
            'StudentState'
        ])

        # Valid CPDs (independent)
        cpd_correctness = TabularCPD(
            'ResponseCorrectness', 2,
            [[0.6], [0.4]]
        )

        cpd_hesitation = TabularCPD(
            'HesitationTime', 3,
            [[0.5], [0.3], [0.2]]
        )

        cpd_emotions = TabularCPD(
            'EmotionalKeywords', 2,
            [[0.7], [0.3]]
        )

        cpd_mistakes = TabularCPD(
            'RepeatedMistakes', 3,
            [[0.6], [0.25], [0.15]]
        )

        cpd_state = TabularCPD(
            'StudentState', 4,
            [[0.25], [0.25], [0.25], [0.25]]
        )

        # Now pgmpy will accept the CPDs
        self.model.add_cpds(
            cpd_correctness, cpd_hesitation,
            cpd_emotions, cpd_mistakes, cpd_state
        )

        self.model.check_model()

        # Manual causal edges (for drawing only)
        self.graph_edges = [
            ('ResponseCorrectness', 'StudentState'),
            ('HesitationTime', 'StudentState'),
            ('EmotionalKeywords', 'StudentState'),
            ('RepeatedMistakes', 'StudentState'),
        ]


    # --------- CUSTOM SOFTMAX INFERENCE ----------
    def estimate_state(self, correctness, hesitation, emotions, mistakes):
        score = 0

        if correctness == 'Incorrect': score += 2
        if hesitation == 'Medium': score += 1
        if hesitation == 'High': score += 2
        if emotions == 'Present': score += 2
        if mistakes == 'Medium': score += 1
        if mistakes == 'High': score += 2

        probs = self.softmax([
            max(0, 5 - score),   # Confident
            score * 0.5,         # Mild confusion
            score * 0.8,         # High confusion
            score * 1.2          # Frustrated
        ])

        return {
            "Confident": probs[0],
            "MildlyConfused": probs[1],
            "HighlyConfused": probs[2],
            "Frustrated": probs[3]
        }

    def softmax(self, x):
        ex = np.exp(x - np.max(x))
        return ex / ex.sum()

    # --------- DRAW GRAPH ----------
    def draw_network(self):
        G = nx.DiGraph()
        G.add_edges_from(self.graph_edges)

        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G, seed=42)

        nx.draw(
            G, pos, with_labels=True,
            node_size=3000, node_color="lightgreen",
            arrowsize=20, font_weight="bold"
        )

        plt.title("Causal Graph: Observed Symptoms → StudentState")
        plt.tight_layout()
        plt.show()


# -------------------------
# Test
# -------------------------
if __name__ == "__main__":
    estimator = StudentStateEstimator()
    estimator.draw_network()

    result = estimator.estimate_state(
        correctness='Incorrect',
        hesitation='High',
        emotions='Present',
        mistakes='High'
    )

    print("\nPredicted Student State Probabilities:")
    for k, v in result.items():
        print(f"{k:15s}: {v:.4f}")

    print("\nMost likely state:", max(result, key=result.get))
