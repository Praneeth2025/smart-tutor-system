"""
Module3_final.py

Adaptive Teaching Strategy Planning using GraphPlan and POP
 - Planning graph builder (literal levels + action levels)
 - Mutex (inconsistent support / interference) detection
 - GraphPlan extractor that respects mutex constraints
 - POP planner (partial-order causal-link planner)
 - Simulation / validation
 - Visualizations:
     - planning_graph_layered.png (literal levels + action levels + mutex edges)
     - pop_causal_links.png (POP causal links + ordering constraints)
"""

from collections import deque
import pprint
import networkx as nx
import matplotlib.pyplot as plt
import os
from itertools import combinations

# -----------------------
# helper to create literals
# -----------------------
def literal(pred, ch="ch1"):
    return f"{pred}({ch})"

CH = "ch1"

# -----------------------
# actions container + helper
# -----------------------
ACTIONS = []
def add_action(name, pre=None, add=None, delete=None):
    ACTIONS.append({
        "name": name,
        "pre": set(pre or []),
        "add": set(add or []),
        "del": set(delete or [])
    })

# -----------------------
# Domain actions (same domain you provided)
# -----------------------
add_action(
    "TeachConcept",
    pre=[literal("NoKnowledge", CH)],
    add=[literal("BasicUnderstanding", CH), literal("Neutral", CH)],
    delete=[literal("NoKnowledge", CH)]
)

add_action(
    "AskNeutralQuestion",
    pre=[literal("Neutral", CH)],
    add=[
        literal("ReadyForNeutralEval_Confident", CH),
        literal("ReadyForNeutralEval_Bored", CH),
        literal("ReadyForNeutralEval_Confused", CH),
        literal("ReadyForNeutralEval_Frustrated", CH)
    ]
)

add_action(
    "EvalNeutral_Confident",
    pre=[literal("ReadyForNeutralEval_Confident", CH)],
    add=[literal("Confident", CH), literal("BranchVisited_Confident", CH)]
)

add_action(
    "EvalNeutral_Bored",
    pre=[literal("ReadyForNeutralEval_Bored", CH)],
    add=[literal("Bored", CH), literal("BranchVisited_Bored", CH)]
)

add_action(
    "EvalNeutral_Confused",
    pre=[literal("ReadyForNeutralEval_Confused", CH)],
    add=[literal("Confused", CH), literal("BranchVisited_Confused", CH)]
)

add_action(
    "EvalNeutral_Frustrated",
    pre=[literal("ReadyForNeutralEval_Frustrated", CH)],
    add=[literal("Frustrated", CH), literal("BranchVisited_Frustrated", CH)]
)

add_action(
    "GiveHardProblem_FromConfident",
    pre=[literal("Confident", CH)],
    add=[literal("SolvedMany", CH)]
)

add_action(
    "GiveHardProblem_FromBored",
    pre=[literal("Bored", CH)],
    add=[literal("SolvedMany", CH)]
)

add_action(
    "GiveEasyProblem_FromConfused",
    pre=[literal("Confused", CH)],
    add=[literal("Confident", CH)],
    delete=[literal("Confused", CH)]
)

add_action(
    "GiveHint_FromFrustrated",
    pre=[literal("Frustrated", CH)],
    add=[literal("ReadyForEasyQuestion", CH), literal("Confused", CH)],
    delete=[literal("Frustrated", CH)]
)

add_action(
    "AskEasyQuestion",
    pre=[literal("ReadyForEasyQuestion", CH)],
    add=[literal("ReadyForEasyEval", CH)]
)

add_action(
    "EvalEasy_Solved",
    pre=[literal("ReadyForEasyEval", CH)],
    add=[literal("Confident", CH)],
    delete=[literal("ReadyForEasyEval", CH)]
)

add_action(
    "FinalAssessment_AllBranches",
    pre=[
        literal("BranchVisited_Confident", CH),
        literal("BranchVisited_Bored", CH),
        literal("BranchVisited_Confused", CH),
        literal("BranchVisited_Frustrated", CH),
        literal("SolvedMany", CH)
    ],
    add=[literal("FullKnowledge", CH)]
)

# -----------------------
# Planning graph builder (literal levels + action levels)
# -----------------------
def build_planning_graph(initial_literals, actions, max_levels=10):
    """
    Build planning graph with:
      - literal_levels: list of sets of literals (level 0 is initial literals)
      - action_levels: list of lists of actions applicable at previous literal level
      - action_mutex: list of sets of pairs (a_name1, a_name2) mutex at that action level
      - literal_mutex: list of sets of pairs (lit1, lit2) mutex at that literal level
    """
    literal_levels = [set(initial_literals)]
    action_levels = []
    action_mutex_levels = []
    literal_mutex_levels = [set()]  # level 0 no mutex usually

    for lvl in range(max_levels):
        cur_literals = literal_levels[-1]
        # applicable actions at this level (including NO-OPs implicitly via persistence)
        applicable = []
        for a in actions:
            if a['pre'].issubset(cur_literals):
                applicable.append(a)
        action_levels.append(applicable)

        # compute action mutex (pairwise)
        mutex_actions = set()
        for a1, a2 in combinations(applicable, 2):
            if actions_mutex(a1, a2, cur_literals):
                mutex_actions.add((a1['name'], a2['name']))
                mutex_actions.add((a2['name'], a1['name']))
        action_mutex_levels.append(mutex_actions)

        # compute next literals (effects union plus persistence of current literals)
        next_literals = set(cur_literals)
        for a in applicable:
            next_literals |= a['add']

        # compute literal mutex for next level:
        mutex_literals = set()
        # Two literals l1, l2 are mutex at next level if
        # every pair of actions that can produce l1 and l2 are pairwise mutex.
        producers = {}
        # for each literal, collect actions that add it (from applicable)
        for l in next_literals:
            producers[l] = []
            for a in applicable:
                if l in a['add']:
                    producers[l].append(a['name'])
            # also include persistence (NO-OP) as producer: if l in cur_literals
            if l in cur_literals:
                producers[l].append("PERSIST_"+l)  # name for persistence

        # Build mapping for persistence producer (no-op) and treat persistence producers as never interfering
        # Mark persistence distinct: its name starts with PERSIST_
        # Now check pairs
        lits = list(next_literals)
        for l1, l2 in combinations(lits, 2):
            prods1 = producers.get(l1, [])
            prods2 = producers.get(l2, [])
            # if any producer pair is non-mutex (i.e., there exists a non-mutex producer pair),
            # then literals are not mutex. Otherwise they are mutex.
            all_pairs_mutex = True
            for p1 in prods1:
                for p2 in prods2:
                    # if both producers are persistence producers, they are non-mutex
                    if p1.startswith("PERSIST_") and p2.startswith("PERSIST_"):
                        all_pairs_mutex = False
                        break
                    # if producer pair corresponds to two action names:
                    # if pair not in action mutex set -> non-mutex
                    # treat pairs (act1, act2) where either could be persistence specially
                    name1 = p1
                    name2 = p2
                    if p1.startswith("PERSIST_") or p2.startswith("PERSIST_"):
                        # persistence isn't mutex with any action that doesn't delete the literal
                        # but we must ensure action doesn't delete the other's literal
                        # approximate: treat persistence non-mutex unless action deletes the literal it pairs with
                        # we'll check action deletes below; for simplicity, assume non-mutex here
                        all_pairs_mutex = False
                        break
                    if (name1, name2) not in mutex_actions:
                        all_pairs_mutex = False
                        break
                if not all_pairs_mutex:
                    break
            if all_pairs_mutex:
                mutex_literals.add((l1, l2))
                mutex_literals.add((l2, l1))

        literal_levels.append(next_literals)
        literal_mutex_levels.append(mutex_literals)

        # stop if fixed point
        if next_literals == cur_literals:
            break

    return literal_levels, action_levels, action_mutex_levels, literal_mutex_levels

# -----------------------
# action interference / inconsistent-effects / competing-needs checks
# -----------------------
def actions_mutex(a1, a2, current_literals):
    """
    Return True if actions a1 and a2 are mutex at the current literal level.
    We consider:
      - Inconsistent effects: one action deletes an effect of the other
      - Interference: one action deletes a precondition of the other
      - Competing needs: if any precondition of a1 is pairwise mutex with any precondition of a2
    For this simplified domain we implement:
      - inconsistent effect OR interference OR competing needs (naive)
    """
    # inconsistent effects: a1.add intersects a2.del or a2.add intersects a1.del
    if (a1['add'] & a2.get('del', set())) or (a2['add'] & a1.get('del', set())):
        return True
    # interference: a1.del intersects a2.pre OR a2.del intersects a1.pre
    if (a1.get('del', set()) & a2['pre']) or (a2.get('del', set()) & a1['pre']):
        return True
    # competing needs: if preconditions cannot be simultaneously satisfied in current_literals.
    # For an approximation: if any pre in a1.pre not in current_literals or any pre in a2.pre not in current_literals,
    # then they are not applicable; but they are known applicable before calling this, so competing needs implies
    # that some precondition of a1 is mutex with some precondition of a2. We do not track pre-level mutex yet,
    # so as a simple conservative heuristic, we consider competing needs False here.
    return False

# -----------------------
# GraphPlan extractor that respects mutexes
# -----------------------
def graphplan_extract(initial_literals, goal_literals, actions, max_levels=10):
    """
    Build planning graph and extract a plan respecting action/literal mutexes.
    Approach (simple greedy, backward selection with mutex check):
      - Build planning graph levels + mutex sets
      - Starting from top level where goal is present, mark needed=goal
      - For each level from top->0 choose actions in that action level that:
          * add at least one needed literal
          * are pairwise non-mutex
        Add their preconditions to needed and continue to previous level
      - Return final plan reversed (forward)
    This is a heuristic extractor (not guaranteed complete), but handles mutex constraints.
    """
    literal_levels, action_levels, action_mutex_levels, literal_mutex_levels = \
        build_planning_graph(initial_literals, actions, max_levels)

    # find a level where all goal_literals are present
    level_with_goal = None
    for i, lits in enumerate(literal_levels):
        if set(goal_literals).issubset(lits):
            level_with_goal = i
    if level_with_goal is None:
        return None

    needed = set(goal_literals)
    chosen_actions_by_level = [[] for _ in range(level_with_goal)]
    # iterate backwards
    for lvl in range(level_with_goal - 1, -1, -1):
        available_actions = action_levels[lvl]
        mutex_actions = action_mutex_levels[lvl]
        chosen = []
        # while there are needed literals that exist at next literal level
        # greedily pick actions that cover many needed literals and are non-mutex with already chosen
        candidate_actions = [a for a in available_actions if len(a['add'] & needed) > 0]
        # sort by coverage desc, smaller pre set better
        candidate_actions.sort(key=lambda a: (-len(a['add'] & needed), len(a['pre'])))
        for a in candidate_actions:
            # check non-mutex with chosen
            conflict = False
            for c in chosen:
                if (a['name'], c['name']) in mutex_actions:
                    conflict = True
                    break
            if conflict:
                continue
            # add action
            chosen.append(a)
            # remove covered literals from needed
            covered = a['add'] & needed
            needed -= covered
            # add its preconditions to needed for lower levels
            needed |= a['pre']
        chosen_actions_by_level[lvl] = [a['name'] for a in chosen]
    # flatten chosen actions forward-order & dedupe (first occurrence)
    flat = []
    for lvl_actions in chosen_actions_by_level:
        for name in lvl_actions:
            if name not in flat:
                flat.append(name)
    return flat

# -----------------------
# plan simulator / validator
# -----------------------
def simulate_plan(initial, plan, actions):
    """
    Simulate applying actions in plan order. Return final state, ok flag, error message if any.
    """
    state = set(initial)
    name2act = {a['name']: a for a in actions}
    for i, aname in enumerate(plan, start=1):
        if aname not in name2act:
            return state, False, f"Step {i}: action '{aname}' not found"
        a = name2act[aname]
        if not a['pre'].issubset(state):
            return state, False, f"Step {i}: preconditions {a['pre']} not satisfied (state has {state})"
        # apply
        state -= a.get('del', set())
        state |= a.get('add', set())
    return state, True, None

# -----------------------
# POP planner (partial-order causal-link planner)
# -----------------------
class POPPlanner:
    def __init__(self, actions):
        self.actions = actions

    def plan(self, initial_literals, goal_literals, max_iters=5000):
        def Step(name, pre, add, delete):
            return {"name": name, "pre": set(pre), "add": set(add), "del": set(delete)}
        start = Step("Start", [], initial_literals, [])
        finish = Step("Finish", goal_literals, [], [])
        steps = [start, finish]            # index 0 = Start, 1 = Finish
        order = set([(0,1)])               # ordering constraints (i precedes j)
        causal_links = []                  # tuples (producer_index, literal, consumer_index)
        open_conditions = [(1, lit) for lit in goal_literals]  # list of (consumer_index, literal)
        iter_count = 0

        def add_step_for_action(action):
            steps.append(Step(action["name"], action["pre"], action["add"], action["del"]))
            return len(steps)-1

        while open_conditions and iter_count < max_iters:
            iter_count += 1
            consumer_idx, lit = open_conditions.pop(0)
            # find existing producer that already adds the literal and can be ordered before consumer
            producer_idx = None
            for idx, s in enumerate(steps):
                if lit in s["add"]:
                    producer_idx = idx
                    break
            if producer_idx is None:
                # select an action that adds lit
                chosen_action = None
                for a in self.actions:
                    if lit in a["add"]:
                        chosen_action = a
                        break
                if chosen_action is None:
                    return None  # failure
                producer_idx = add_step_for_action(chosen_action)
            # add causal link and ordering constraints
            causal_links.append((producer_idx, lit, consumer_idx))
            order.add((producer_idx, consumer_idx))
            order.add((0, producer_idx))
            order.add((producer_idx, 1))
            # ensure producer's preconditions are satisfied (create open conditions)
            for pre in steps[producer_idx]["pre"]:
                satisfied = False
                for sid, s in enumerate(steps):
                    if pre in s["add"] and (sid, producer_idx) in order:
                        satisfied = True
                        break
                if not satisfied:
                    open_conditions.append((producer_idx, pre))

        # build adjacency and topologically sort using ordering constraints
        n = len(steps)
        indeg = [0]*n
        adj = [[] for _ in range(n)]
        for (u,v) in order:
            if u==v: continue
            adj[u].append(v)
            indeg[v] += 1
        q = deque([i for i in range(n) if indeg[i]==0])
        topo = []
        while q:
            u = q.popleft()
            topo.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        linear = [steps[i]["name"] for i in topo if steps[i]["name"] not in ("Start","Finish")]
        # dedupe causal_links (keeping order)
        seen_causal = []
        seen_set = set()
        for c in causal_links:
            if c not in seen_set:
                seen_causal.append(c)
                seen_set.add(c)
        return {
            "steps": steps,
            "order": order,
            "causal_links": seen_causal,
            "linearization": linear
        }

# -----------------------
# Visualization helpers
# -----------------------
def visualize_planning_graph(literal_levels, action_levels, action_mutex_levels, literal_mutex_levels, filename="planning_graph_layered.png"):
    """
    Draw a layered planning graph:
      - Literal level 0 (top), action level 0 (below), literal level 1, etc.
      - Actions shown as rectangles with their names.
      - Mutex links between actions or literals drawn as red dashed lines.
    """
    # Build a directed graph for visualization with unique node ids
    G = nx.DiGraph()
    pos = {}
    labels = {}
    node_type = {}  # 'lit' or 'act'
    y_gap = 1.8
    x_gap = 3.0

    # place literals and actions with coordinates
    max_level = len(literal_levels)-1
    for lvl in range(len(literal_levels)):
        lits = sorted(literal_levels[lvl])
        x_base = lvl * x_gap
        for i, lit in enumerate(lits):
            nid = f"L{lvl}_{i}"
            G.add_node(nid)
            pos[nid] = (x_base, -i * y_gap)
            labels[nid] = lit
            node_type[nid] = 'lit'
        if lvl < len(action_levels):
            acts = action_levels[lvl]
            for j, a in enumerate(acts):
                nid = f"A{lvl}_{j}"
                G.add_node(nid)
                pos[nid] = (x_base + 0.8, -(len(lits) + 1 + j) * (y_gap/1.8))
                labels[nid] = a['name']
                node_type[nid] = 'act'
                # connect action to its adds and pres (visual)
                for lit in a['add']:
                    # find index of lit in next literal level
                    try:
                        idx = sorted(literal_levels[lvl+1]).index(lit)
                        lit_nid = f"L{lvl+1}_{idx}"
                        G.add_edge(nid, lit_nid)
                    except Exception:
                        pass
                for lit in a['pre']:
                    try:
                        idx = sorted(literal_levels[lvl]).index(lit)
                        lit_nid = f"L{lvl}_{idx}"
                        G.add_edge(lit_nid, nid)
                    except Exception:
                        pass

    plt.figure(figsize=(14, 8))
    # draw nodes: literals as ovals, actions as rectangles
    lit_nodes = [n for n,t in node_type.items() if t=='lit']
    act_nodes = [n for n,t in node_type.items() if t=='act']
    nx.draw_networkx_nodes(G, pos, nodelist=lit_nodes, node_color='lightblue', node_size=1400)
    nx.draw_networkx_nodes(G, pos, nodelist=act_nodes, node_color='lightyellow', node_shape='s', node_size=1100)
    nx.draw_networkx_labels(G, pos, labels, font_size=8)

    # edges
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='-|>', arrowsize=10)

    # draw mutex links (literal mutex and action mutex) as red dashed lines
    # literal mutex between nodes at same literal level
    for lvl, mutex_set in enumerate(literal_mutex_levels):
        for (l1, l2) in mutex_set:
            # map l1 and l2 to node ids at level lvl (note: literal_mutex_levels index corresponds to that literal level)
            try:
                lits = sorted(literal_levels[lvl])
                i1 = lits.index(l1)
                i2 = lits.index(l2)
                n1 = f"L{lvl}_{i1}"; n2 = f"L{lvl}_{i2}"
                plt.plot([pos[n1][0], pos[n2][0]], [pos[n1][1], pos[n2][1]], 'r--', linewidth=1.0, alpha=0.7)
            except Exception:
                continue

    # action mutex within action levels
    for lvl, mutex_set in enumerate(action_mutex_levels):
        for (a1, a2) in mutex_set:
            # find node ids for a1 and a2
            acts = action_levels[lvl]
            names = [a['name'] for a in acts]
            try:
                j1 = names.index(a1); j2 = names.index(a2)
                n1 = f"A{lvl}_{j1}"; n2 = f"A{lvl}_{j2}"
                plt.plot([pos[n1][0], pos[n2][0]], [pos[n1][1], pos[n2][1]], 'r--', linewidth=1.0, alpha=0.7)
            except Exception:
                continue

    plt.axis('off')
    plt.title("Planning Graph (Literal levels + Action levels) — red dashed = mutex")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"Saved planning graph visualization → {filename}")

def visualize_pop(pop_res, filename="pop_causal_links.png"):
    """
    Draw POP causal links and ordering constraints:
    - Nodes are steps (Start, actions..., Finish)
    - Causal links: solid green arrows producer -> consumer (label = literal)
    - Ordering constraints: dashed gray arrows
    """
    steps = pop_res["steps"]
    causal = pop_res["causal_links"]
    order = pop_res["order"]

    G = nx.DiGraph()
    labels = {}
    for i, s in enumerate(steps):
        node = i
        G.add_node(node)
        labels[node] = f"{i}:{s['name']}"

    # add causal link edges (producer -> consumer)
    for (p, lit, c) in causal:
        G.add_edge(p, c, label=lit, color='green', style='solid')

    # add ordering edges (dashed) for a sample (avoid adding huge number of edges)
    for (u,v) in order:
        if u==v: continue
        if not G.has_edge(u,v):
            G.add_edge(u, v, label="", color='gray', style='dashed')

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(12, 8))

    # draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1400)
    nx.draw_networkx_labels(G, pos, labels, font_size=8)

    # draw edges with styles
    solid_edges = [(u,v) for (u,v,d) in G.edges(data=True) if d.get('style') == 'solid']
    dashed_edges = [(u,v) for (u,v,d) in G.edges(data=True) if d.get('style') == 'dashed']

    nx.draw_networkx_edges(G, pos, edgelist=solid_edges, edge_color='green', arrows=True, width=2)
    nx.draw_networkx_edges(G, pos, edgelist=dashed_edges, edge_color='gray', style='dashed', arrows=True, width=1)

    # draw causal labels
    edge_labels = {(u,v): d.get('label', '') for (u,v,d) in G.edges(data=True) if d.get('label')}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='green', font_size=8)

    plt.title("POP causal links (green) and ordering constraints (gray dashed)")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"Saved POP causal-links visualization → {filename}")

# -----------------------
# main function
# -----------------------
if __name__ == "__main__":
    initial = {literal("NoKnowledge",CH)}
    goal = {literal("FullKnowledge",CH)}

    print("\n=== ACTIONS DEFINED ===")
    print([a["name"] for a in ACTIONS])

    # Build planning graph
    literal_levels, action_levels, action_mutex_levels, literal_mutex_levels = build_planning_graph(initial, ACTIONS, max_levels=10)

    print("\n--- Literal levels (top to bottom) ---")
    for i, L in enumerate(literal_levels):
        print(f"Level {i} ({len(L)} literals):")
        for lit in sorted(L):
            print("  ", lit)

    # visualize planning levels
    visualize_planning_graph(literal_levels, action_levels, action_mutex_levels, literal_mutex_levels)

    # -------------------------
    # GraphPlan extraction
    # -------------------------
    print("\n--- GRAPHPLAN (extract respecting mutexes) ---")
    gp_plan = graphplan_extract(initial, goal, ACTIONS, max_levels=10)
    if gp_plan is None:
        print("GraphPlan: goal not reachable.")
    else:
        print("GraphPlan extracted plan (sequence):")
        pprint.pprint(gp_plan)
        final_state, ok, err = simulate_plan(initial, gp_plan, ACTIONS)
        print("GraphPlan simulation OK?", ok)
        if not ok:
            print("Simulation failed:", err)
        else:
            print("Final state contains goal?", list(goal)[0] in final_state)

    # -------------------------
    # POP planning
    # -------------------------
    print("\n--- POP Planner ---")
    pop = POPPlanner(ACTIONS)
    pop_res = pop.plan(initial, list(goal))
    if pop_res is None:
        print("POP failed to produce a plan.")
    else:
        print("\nPOP linearization (one legal total order):")
        pprint.pprint(pop_res["linearization"])
        print("\nPOP causal links (producer_idx, literal, consumer_idx):")
        pprint.pprint(pop_res["causal_links"])
        # Pretty-print causal links (names)
        print("\nPOP causal links (names):")
        for (p, lit, c) in pop_res["causal_links"]:
            pname = pop_res["steps"][p]["name"]
            cname = pop_res["steps"][c]["name"]
            print(f"  {pname} --[{lit}]--> {cname}")

        # Save pop causal-links visualization
        visualize_pop(pop_res)

        # Validate the linearization by simulation
        lin = pop_res["linearization"]
        final_state2, ok2, err2 = simulate_plan(initial, lin, ACTIONS)
        print("\nPOP linearization simulation OK?", ok2)
        if not ok2:
            print("POP linearization failed:", err2)
        else:
            print("Final state contains goal?", list(goal)[0] in final_state2)

    print("\n--- EXPLANATION ---")
    print("GraphPlan builds leveled literals and actions and identifies mutex relationships.")
    print("The extractor then picks non-mutex actions backward from a level containing the goal.")
    print("POP constructs partial-order plans with causal links and ordering constraints; it")
    print("is more flexible at runtime because new steps can be inserted and multiple valid")
    print("linearizations can be derived from the partial order — useful for adaptive tutoring.")

