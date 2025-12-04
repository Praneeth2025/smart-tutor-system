# 2_search_methods.py
from collections import deque
import heapq
import networkx as nx
import matplotlib.pyplot as plt

# -----------------------------
# CONCEPT GRAPH + DIFFICULTY
# -----------------------------
class ConceptGraph:
    def __init__(self):
        self.graph = {
            'Variables': ['Conditionals', 'Loops'],
            'Conditionals': ['Loops', 'Functions'],
            'Loops': ['Functions', 'Recursion'],
            'Functions': ['Recursion'],
            'Recursion': []
        }

        self.difficulty = {
            'Variables': 1,
            'Conditionals': 2,
            'Loops': 3,
            'Functions': 4,
            'Recursion': 5
        }
    
    def get_neighbors(self, node):
        return self.graph.get(node, [])
    
    def get_difficulty(self, node):
        return self.difficulty.get(node, 0)


# -----------------------------
# STUDENT READINESS + TARGET DIFFICULTY
# -----------------------------
class StudentProfile:
    def __init__(self, readiness, target_difficulty):
        self.readiness = readiness
        self.target_difficulty = target_difficulty

    def score(self, concept, graph):
        """Combined metric"""
        diff = graph.get_difficulty(concept)
        return abs(diff - self.readiness) + abs(diff - self.target_difficulty)


# -----------------------------
# DIFFICULTY + READINESS BASED TRANSITION
# -----------------------------
def next_topic(graph, current_topic, student):
    neighbors = graph.get_neighbors(current_topic)
    if not neighbors:
        return None, None   # end

    best = None
    best_score = float("inf")

    print("\nEvaluating neighbors:")
    for n in neighbors:
        score = student.score(n, graph)
        print(f"  {n}: difficulty={graph.get_difficulty(n)}, score={score}")
        
        if score < best_score:
            best_score = score
            best = n

    return best, best_score


# -----------------------------
# VISUALIZATION
# -----------------------------
def visualize_graph(graph):
    G = nx.DiGraph()

    for node, neighbors in graph.graph.items():
        G.add_node(node, difficulty=graph.get_difficulty(node))
        for n in neighbors:
            G.add_edge(node, n)

    pos = nx.spring_layout(G, seed=42)
    labels = {n: f"{n}\n(d={graph.get_difficulty(n)})" for n in G.nodes}

    plt.figure(figsize=(10, 6))
    nx.draw(
        G, pos,
        with_labels=True,
        labels=labels,
        node_color="lightblue",
        node_size=2500,
        arrows=True,
        arrowstyle='-|>',
        arrowsize=20,
        font_size=9
    )
    plt.title("Concept Graph with Difficulty Levels")
    plt.show()


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    graph = ConceptGraph()

    print("\nEnter your readiness level (1–5): ")
    readiness = int(input("> "))

    print("\nEnter target difficulty level (1–5): ")
    target = int(input("> "))

    student = StudentProfile(readiness, target)
    current = "Variables"

    print("\nStarting at:", current)

    while True:
        nxt, score = next_topic(graph, current, student)
        if nxt is None:
            print("\nReached end of graph.")
            break

        print(f"\nNext topic → {nxt} (score={score})")
        current = nxt

    print("\nFinal learning sequence complete.")
