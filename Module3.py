#!/usr/bin/env python3
"""
Module 3 — Adaptive Teaching Strategy Planning (GraphPlan + POP)

Run: python module3_planning.py
"""

from collections import deque
import pprint

# -----------------------
# Helper to create literals
# -----------------------
def literal(pred, ch="ch1"):
    return f"{pred}({ch})"

CH = "ch1"

# -----------------------
# Actions container + helper
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
# Domain actions
# -----------------------
# Teach -> neutral state + basic understanding
add_action(
    "TeachConcept",
    pre=[literal("NoKnowledge", CH)],
    add=[literal("BasicUnderstanding", CH), literal("Neutral", CH)],
    delete=[literal("NoKnowledge", CH)]
)

# Ask a neutral question to branch into emotion evaluation readiness
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

# Four evaluation actions (one per branch)
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

# Confident/Bored -> GiveHardProblem -> SolvedMany
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

# Confused -> GiveEasyProblem -> Confident
add_action(
    "GiveEasyProblem_FromConfused",
    pre=[literal("Confused", CH)],
    add=[literal("Confident", CH)],
    delete=[literal("Confused", CH)]
)

# Frustrated -> GiveHint -> AskEasy -> EvalEasy -> Confident
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

# Final assessment requires all branches visited and SolvedMany
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
    literal_levels = [set(initial_literals)]
    action_levels = []
    print("\n=== BUILDING PLANNING GRAPH ===")
    for lvl in range(max_levels):
        cur = literal_levels[-1]
        print(f"\n-- Level {lvl} Literals ({len(cur)} items) --")
        for lit in sorted(cur):
            print("   ", lit)
        # actions applicable at this level (preconditions subset of cur)
        applicable = [a for a in actions if a["pre"].issubset(cur)]
        action_levels.append(applicable)
        print("  Applicable actions:", [a["name"] for a in applicable])
        next_literals = set(cur)
        for a in applicable:
            next_literals |= a["add"]
        # if no new literals, fixed point reached
        if next_literals == cur:
            print("\nReached fixed point at level", lvl)
            break
        literal_levels.append(next_literals)
    print("\n=== PLANNING GRAPH BUILT ===")
    return literal_levels, action_levels

# -----------------------
# GraphPlan greedy extractor (backward)
# -----------------------
def graphplan(initial, goal, actions, max_levels=10):
    literal_levels, action_levels = build_planning_graph(initial, actions, max_levels)
    # check reachability
    if not set(goal).issubset(literal_levels[-1]):
        print("\nGraphPlan: Goal not reachable in planning graph.")
        return None
    # Backward selection: select actions that achieve goals at highest possible level
    needed = set(goal)
    plan_actions = []
    # iterate levels backward
    for lvl in range(len(action_levels)-1, -1, -1):
        chosen_this_level = []
        for a in action_levels[lvl]:
            # if action adds any needed literal, pick it
            if len(a["add"] & needed) > 0:
                chosen_this_level.append(a)
                # add its preconditions to needed set
                needed |= (a["pre"])
                # remove added literals from needed
                needed -= a["add"]
        # append chosen actions (in some order) to plan
        # we append names (earliest-first ordering will be reversed at end)
        plan_actions.extend(reversed([a["name"] for a in chosen_this_level]))
        if not needed:
            break
    # reverse to forward order
    plan = list(reversed(plan_actions))
    return plan

# -----------------------
# POP planner (simple partial-order causal-link planner)
# -----------------------
class POPPlanner:
    def __init__(self, actions):
        self.actions = actions

    def plan(self, initial_literals, goal_literals, max_iters=5000):
        # Steps are dicts with name, pre, add, del
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
            # find existing producer
            producer_idx = None
            for idx, s in enumerate(steps):
                if lit in s["add"]:
                    # also ensure producer can be ordered before consumer
                    producer_idx = idx
                    break
            if producer_idx is None:
                # create a new step from actions that add lit
                chosen_action = None
                for a in self.actions:
                    if lit in a["add"]:
                        chosen_action = a
                        break
                if chosen_action is None:
                    # failed to find producer
                    print(f"POP: cannot find producer for literal {lit}")
                    return None
                producer_idx = add_step_for_action(chosen_action)
            # add causal link and ordering
            causal_links.append((producer_idx, lit, consumer_idx))
            order.add((producer_idx, consumer_idx))
            order.add((0, producer_idx))  # ensure Start before producer
            order.add((producer_idx, 1))  # producer before Finish
            # ensure preconditions of producer are open (unless already provided)
            for pre in steps[producer_idx]["pre"]:
                satisfied = False
                for idx, s in enumerate(steps):
                    if pre in s["add"] and (idx, producer_idx) in order:
                        satisfied = True
                        break
                if not satisfied:
                    open_conditions.append((producer_idx, pre))

        # Build adjacency and topologically sort using ordering constraints
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
        # linearization: names excluding Start and Finish
        linear = [steps[i]["name"] for i in topo if steps[i]["name"] not in ("Start","Finish")]
        return {
            "steps": steps,
            "order": order,
            "causal_links": causal_links,
            "linearization": linear
        }

# -----------------------
# MAIN (demo)
# -----------------------
if __name__ == "__main__":
    initial = {literal("NoKnowledge", CH)}
    goal = {literal("FullKnowledge", CH)}

    print("\n=== ACTIONS DEFINED ===")
    print([a["name"] for a in ACTIONS])

    # Build planning graph and show levels
    literal_levels, action_levels = build_planning_graph(initial, ACTIONS, max_levels=8)

    print("\n=== GRAPHPLAN (extract) ===")
    gp_plan = graphplan(initial, goal, ACTIONS, max_levels=8)
    if gp_plan:
        print("GraphPlan extracted plan (sequence of action names):")
        pprint.pprint(gp_plan)
    else:
        print("GraphPlan did not find a plan.")

    print("\n=== POP Planner ===")
    pop = POPPlanner(ACTIONS)
    pop_result = pop.plan(initial, list(goal))
    if pop_result is None:
        print("POP failed to produce a plan.")
    else:
        print("\nPOP Linearization (one valid total order):")
        pprint.pprint(pop_result["linearization"])
        print("\nPOP Causal Links (producer_index, literal, consumer_index):")
        pprint.pprint(pop_result["causal_links"])
        print("\nPOP Ordering Constraints (sample pairs):")
        # show some ordering constraints
        sorted_order = sorted(pop_result["order"])
        pprint.pprint(sorted_order[:40])

    # -----------------------------
    # Extra: Short textual justification
    # -----------------------------
    print("\n=== EXPLANATION / JUSTIFICATION ===\n")
    print("GraphPlan builds leveled literals and actions and extracts a solution by selecting")
    print("actions that achieve the goals from the highest levels backward. GraphPlan is")
    print("efficient for finding parallelizable plans when the planning graph captures")
    print("the reachable literals. However GraphPlan's extracted plan is usually a linear")
    print("sequence (or simple parallel set) and can be brittle to unexpected changes in")
    print("the student's state at runtime.\n")
    print("POP (Partial Order Planner) constructs steps, causal links and ordering constraints.")
    print("POP keeps partial order (not a single total order) and preserves causal links.")
    print("This lets POP adapt: actions can be interleaved, new steps inserted to satisfy")
    print("open conditions, and different linearizations derived from the partial order.")
    print("Therefore POP offers more runtime flexibility and easier local repair (important")
    print("for an adaptive tutor that must react to the student's evolving cognitive/emotional state).")
