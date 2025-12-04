"""
Module 2 – Search-Based Selection of Next Teaching Topic
"""

from collections import deque
import heapq
import networkx as nx
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import os


# ============================================================
#  CONCEPT GRAPH
# ============================================================
class ConceptGraph:
    def __init__(self):
        self.graph = {
            "Variables": ["Conditionals", "Loops"],
            "Conditionals": ["Loops", "Functions"],
            "Loops": ["Functions", "Recursion"],
            "Functions": ["Recursion"],
            "Recursion": []
        }

        self.difficulty = {
            "Variables": 1,
            "Conditionals": 2,
            "Loops": 3,
            "Functions": 4,
            "Recursion": 5
        }

    def neighbors(self, node):
        return self.graph.get(node, [])

    def diff(self, node):
        return self.difficulty[node]


# ============================================================
#  STUDENT PROFILE
# ============================================================
class StudentProfile:
    def __init__(self, readiness, target):
        self.readiness = readiness
        self.target = target

    def mismatch(self, concept, graph):
        d = graph.diff(concept)
        return abs(d - self.readiness) + 0.5 * abs(d - self.target)


# ============================================================
#  DRAW FUNCTION FOR GIFs
# ============================================================
def draw_graph(G, pos, highlight, explored, path, title, frames, final=False):
    plt.figure(figsize=(7, 5))
    plt.clf()

    node_colors = []
    for n in G.nodes:
        if final and n in path:
            node_colors.append("lightgreen")
        elif n == highlight:
            node_colors.append("orange")
        elif n in explored:
            node_colors.append("lightblue")
        else:
            node_colors.append("white")

    edge_colors = []
    widths = []
    for u, v in G.edges:
        if final and u in path and v in path and path.index(v) == path.index(u) + 1:
            edge_colors.append("green")
            widths.append(3)
        else:
            edge_colors.append("black")
            widths.append(1)

    nx.draw(
        G, pos, node_color=node_colors,
        edge_color=edge_colors, width=widths,
        node_size=2400, arrows=True, with_labels=True
    )

    if final:
        plt.title("Final Path: " + " → ".join(path))
    else:
        plt.title(f"{title} — Exploring: {highlight}")

    fname = f"frame_{len(frames)}.png"
    plt.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.05)
    plt.savefig(fname, dpi=120)
    plt.close()
    frames.append(fname)


# ============================================================
#  BFS (uninformed)
# ============================================================
def bfs_search(graph, start, student):
    print("\n\n=== BFS EXPLORATION ===")

    G = nx.DiGraph(graph.graph)
    pos = nx.spring_layout(G, seed=42)

    frames = []
    explored = []
    queue = deque([start])

    while queue:
        node = queue.popleft()
        explored.append(node)

        print(f"Visited {node} (difficulty={graph.diff(node)})")

        draw_graph(G, pos, node, explored, [], "BFS Traversal", frames)

        for nb in graph.neighbors(node):
            if nb not in explored and nb not in queue:
                queue.append(nb)

    remaining = explored[1:]
    best = min(remaining, key=lambda n: student.mismatch(n, graph))

    final_path = [start, best]
    draw_graph(G, pos, None, explored, final_path, "BFS Final", frames, final=True)

    gif = "bfs_visualization.gif"
    imageio.mimsave(gif, [imageio.imread(f) for f in frames], fps=2)
    for f in frames:
        os.remove(f)

    return explored, best, final_path, gif


# ============================================================
#  UCS (uniform cost)
# ============================================================
def ucs_search(graph, start, student):
    print("\n\n=== UCS EXPLORATION ===")
    print("Edge cost = 1, Node cost = mismatch(node)\n")

    G = nx.DiGraph(graph.graph)
    pos = nx.spring_layout(G, seed=42)

    frames = []
    explored = []
    pq = [(0, start, [start])]
    visited_cost = {start: 0}

    best_goal = None
    best_path = None
    best_total = float("inf")

    while pq:
        g_cost, node, path = heapq.heappop(pq)
        explored.append(node)

        mismatch = student.mismatch(node, graph)
        total_cost = g_cost + mismatch

        print(f"Visiting {node} | g={g_cost}, mismatch={mismatch}, total={total_cost}")

        draw_graph(G, pos, node, explored, [], "UCS Traversal", frames)

        if node != start and total_cost < best_total:
            best_total = total_cost
            best_goal = node
            best_path = path

        for nb in graph.neighbors(node):
            new_g = g_cost + 1
            if new_g < visited_cost.get(nb, float("inf")):
                visited_cost[nb] = new_g
                heapq.heappush(pq, (new_g, nb, path + [nb]))

    draw_graph(G, pos, None, explored, best_path, "UCS Final", frames, final=True)

    gif = "ucs_visualization.gif"
    imageio.mimsave(gif, [imageio.imread(f) for f in frames], fps=2)
    for f in frames:
        os.remove(f)

    return explored, best_goal, best_path, best_total, gif


# ============================================================
#  A* Search (informed)
# ============================================================
def astar_search(graph, start, student):
    print("\n\n=== A* EXPLORATION ===")
    print("Heuristic h(n) = mismatch(node)\n")

    G = nx.DiGraph(graph.graph)
    pos = nx.spring_layout(G, seed=42)

    frames = []
    explored = []

    pq = []
    heapq.heappush(pq, (student.mismatch(start, graph), 0, start, [start]))
    best_g = {start: 0}

    best_goal = None
    best_path = None
    best_total = float("inf")

    while pq:
        f, g, node, path = heapq.heappop(pq)
        explored.append(node)

        h = student.mismatch(node, graph)
        total = g + h

        print(f"Visiting {node} | g={g}, h={h}, f={f}, total={total}")

        draw_graph(G, pos, node, explored, [], "A* Traversal", frames)

        if node != start and total < best_total:
            best_total = total
            best_goal = node
            best_path = path

        for nb in graph.neighbors(node):
            new_g = g + 1
            h_nb = student.mismatch(nb, graph)
            new_f = new_g + h_nb

            if new_g < best_g.get(nb, float("inf")):
                best_g[nb] = new_g
                heapq.heappush(pq, (new_f, new_g, nb, path + [nb]))

    draw_graph(G, pos, None, explored, best_path, "A* Final", frames, final=True)

    gif = "astar_visualization.gif"
    imageio.mimsave(gif, [imageio.imread(f) for f in frames], fps=2)
    for f in frames:
        os.remove(f)

    return explored, best_goal, best_path, best_total, gif


# ============================================================
#  MAIN
# ============================================================
if __name__ == "__main__":
    graph = ConceptGraph()

    readiness = int(input("\nEnter student readiness (1–5):\n> "))
    target = int(input("\nEnter target difficulty (1–5):\n> "))

    student = StudentProfile(readiness, target)

    start = "Variables"

    bfs_order, bfs_goal, bfs_path, bfs_gif = bfs_search(graph, start, student)
    print("\nBFS recommends:", bfs_goal)

    ucs_order, ucs_goal, ucs_path, ucs_cost, ucs_gif = ucs_search(graph, start, student)
    print("\nUCS recommends:", ucs_goal, "| Cost:", ucs_cost)

    a_order, a_goal, a_path, a_cost, a_gif = astar_search(graph, start, student)
    print("\nA* recommends:", a_goal, "| Cost:", a_cost)
