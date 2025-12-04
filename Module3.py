from collections import deque
import pprint
def literal(pred, ch="ch1"):
    return f"{pred}({ch})"
CH = "ch1"
ACTIONS = []
def add_action(name, pre=None, add=None, delete=None):
    ACTIONS.append({
        "name": name,
        "pre": set(pre or []),
        "add": set(add or []),
        "del": set(delete or [])
    })
# ------------------------------------------------------
# Teach → AskNeutral → 4-way emotional evaluation
# ------------------------------------------------------

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

# ---- 4 evaluation branches ----

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

# ------------------------------------------------------
# Confident/Bored → GiveHardProblem → SolvedMany
# ------------------------------------------------------

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

# ------------------------------------------------------
# Confused → GiveEasyProblem → Confident
# ------------------------------------------------------

add_action(
    "GiveEasyProblem_FromConfused",
    pre=[literal("Confused", CH)],
    add=[literal("Confident", CH)],
    delete=[literal("Confused", CH)]
)

# ------------------------------------------------------
# Frustrated → GiveHint → AskEasy → EvalEasy → Confident
# ------------------------------------------------------

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

# ------------------------------------------------------
# Final Assessment (requires ALL branches visited)
# ------------------------------------------------------

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
# ------------------------------------------------------
# Planning graph builder
# ------------------------------------------------------

def build_planning_graph(initial_literals, actions, max_levels=10):
    literal_levels = [set(initial_literals)]
    action_levels = []
    print("\n=== PLANNING GRAPH ===")
    for lvl in range(max_levels):
        print(f"\n-- Level {lvl} literals --")
        print(sorted(literal_levels[-1]))
        applicable = []
        for a in actions:
            if a["pre"].issubset(literal_levels[-1]):
                applicable.append(a)
        action_levels.append(applicable)
        print("Actions:", [a["name"] for a in applicable])
        next_literals = set(literal_levels[-1])
        for a in applicable:
            next_literals |= a["add"]
        if next_literals == literal_levels[-1]:
            break
        literal_levels.append(next_literals)
    print("\n=== END GRAPH ===")
    return literal_levels, action_levels
# ------------------------------------------------------
# GraphPlan (simple greedy extraction)
# ------------------------------------------------------

def graphplan(initial, goal, actions, max_levels=10):
    literal_levels = [set(initial)]
    action_levels = []
    for lvl in range(max_levels):
        cur = literal_levels[-1].copy()
        applicable = [a for a in actions if a["pre"].issubset(cur)]
        action_levels.append(applicable)
        nextL = set(cur)
        for a in applicable:
            nextL |= a["add"]
        literal_levels.append(nextL)
        if set(goal).issubset(nextL):
            break
    if not set(goal).issubset(literal_levels[-1]):
        return None
    needed = set(goal)
    plan = []
    for lvl in range(len(action_levels)-1, -1, -1):
        chosen = []
        for lit in list(needed):
            for a in action_levels[lvl]:
                if lit in a["add"]:
                    chosen.append(a)
                    needed |= a["pre"]
                    if lit in needed: needed.remove(lit)
                    break
        plan.extend(reversed([a["name"] for a in chosen]))
        if not needed:
            break
    return list(reversed(plan))
# ------------------------------------------------------
# POP Planner (causal link planner)
# ------------------------------------------------------

class POPPlanner:
    def __init__(self, actions):
        self.actions = actions

    def plan(self, initial_literals, goal_literals, max_iters=2000):
        Step = lambda n,p,a,d: {"name":n,"pre":set(p),"add":set(a),"del":set(d)}
        start = Step("Start",[],initial_literals,[])
        finish = Step("Finish",goal_literals,[],[])
        steps = [start,finish]
        order = {(0,1)}
        causal = []
        openconds = [(1,g) for g in goal_literals]
        def addstep(a):
            steps.append(Step(a["name"],a["pre"],a["add"],a["del"]))
            return len(steps)-1
        i=0
        while openconds and i<max_iters:
            i+=1
            consumer, lit = openconds.pop(0)
            producer = None
            for sid,s in enumerate(steps):
                if lit in s["add"]:
                    producer=sid
                    break
            if producer is None:
                chosen=None
                for a in self.actions:
                    if lit in a["add"]:
                        chosen=a; break
                if chosen is None: return None
                producer = addstep(chosen)
            causal.append((producer,lit,consumer))
            order.add((producer,consumer))
            order.add((0,producer))
            order.add((producer,1))
            for pre in steps[producer]["pre"]:
                ok=False
                for sid,s in enumerate(steps):
                    if pre in s["add"] and (sid,producer) in order:
                        ok=True; break
                if not ok:
                    openconds.append((producer,pre))
        # topo sort
        n=len(steps)
        indeg=[0]*n
        adj=[[] for _ in range(n)]
        for a,b in order:
            adj[a].append(b); indeg[b]+=1
        q=deque([i for i in range(n) if indeg[i]==0])
        topo=[]
        while q:
            u=q.popleft(); topo.append(u)
            for v in adj[u]:
                indeg[v]-=1
                if indeg[v]==0:
                    q.append(v)
        linear=[steps[i]["name"] for i in topo if steps[i]["name"] not in ("Start","Finish")]
        return {
            "steps":steps,
            "order":order,
            "causal_links":causal,
            "linearization":linear
        }
# ------------------------------------------------------
# MAIN
# ------------------------------------------------------

if __name__ == "__main__":
    initial = {literal("NoKnowledge",CH)}
    goal = {literal("FullKnowledge",CH)}

    print("\n--- PLANNING GRAPH ---")
    build_planning_graph(initial, ACTIONS)

    print("\n--- GRAPHPLAN ---")
    gp = graphplan(initial, goal, ACTIONS)
    print(gp)

    print("\n--- POP ---")
    pop = POPPlanner(ACTIONS)
    popres = pop.plan(initial, [
        literal("BranchVisited_Confident",CH),
        literal("BranchVisited_Bored",CH),
        literal("BranchVisited_Confused",CH),
        literal("BranchVisited_Frustrated",CH),
        literal("SolvedMany",CH),
        literal("FullKnowledge",CH)
    ])
    pprint.pprint(popres)
# ------------------------------------------------------
# MAIN
# ------------------------------------------------------

if __name__ == "__main__":
    initial = {literal("NoKnowledge",CH)}
    goal = {literal("FullKnowledge",CH)}

    print("\n--- PLANNING GRAPH ---")
    build_planning_graph(initial, ACTIONS)

    print("\n--- GRAPHPLAN ---")
    gp = graphplan(initial, goal, ACTIONS)
    print(gp)

    print("\n--- POP ---")
    pop = POPPlanner(ACTIONS)
    popres = pop.plan(initial, [
        literal("BranchVisited_Confident",CH),
        literal("BranchVisited_Bored",CH),
        literal("BranchVisited_Confused",CH),
        literal("BranchVisited_Frustrated",CH),
        literal("SolvedMany",CH),
        literal("FullKnowledge",CH)
    ])
    pprint.pprint(popres)