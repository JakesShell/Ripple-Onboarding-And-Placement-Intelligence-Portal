from collections import Counter
import re

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

ARCHETYPE_ORDER = ["Architect", "Current", "Signal", "Spark", "Anchor"]

QUESTIONS = [
    {
        "id": 1,
        "division": "Identity",
        "insight": "Every company has a pattern. Before we place you inside ours, we need to understand yours.",
        "question": "When you enter a new work environment, what do you focus on first: people, rules, tasks, problems, or possibilities? Explain why.",
        "chips": ["Rules", "Tasks", "People", "Possibilities", "Stability"],
    },
    {
        "id": 2,
        "division": "Communication",
        "insight": "Communication shapes how fast a team moves and how safely it handles pressure.",
        "question": "When something is unclear at work, do you usually ask, observe, act, explain, or wait? Explain your instinct.",
        "chips": ["Explain", "Act", "Ask", "Possibilities", "Observe"],
    },
    {
        "id": 3,
        "division": "Pressure",
        "insight": "Pressure reveals operating style. Some people accelerate. Some stabilize. Some scan for risk.",
        "question": "When a deadline becomes urgent, do you speed up, slow down, organize, ask for help, or prioritize one key task? Explain what happens.",
        "chips": ["Organize", "Speed up", "Ask for help", "Prioritize", "Slow down"],
    },
    {
        "id": 4,
        "division": "Innovation",
        "insight": "Improvement begins when someone notices what others have accepted as normal.",
        "question": "When you see a system that could work better, do you suggest, adjust, test, follow, or wait? Explain your approach.",
        "chips": ["Adjust", "Act", "Suggest", "Test", "Wait"],
    },
    {
        "id": 5,
        "division": "Leadership",
        "insight": "Leadership is not always loud. Sometimes it appears as ownership, direction, or calm responsibility.",
        "question": "When a group feels uncertain, do you direct, question, support, organize, or observe first? Explain your role.",
        "chips": ["Organize", "Direct", "Support", "Question", "Observe"],
    },
    {
        "id": 6,
        "division": "Precision",
        "insight": "Quality lives in the details people choose not to ignore.",
        "question": "When work requires accuracy or repetition, do you feel focused, calm, responsible, frustrated, or bored? Explain how you handle it.",
        "chips": ["Focused", "Responsible", "Support", "Improve", "Calm"],
    },
    {
        "id": 7,
        "division": "Client",
        "insight": "Every client interaction leaves a signal. Trust is built through consistency, clarity, and attention.",
        "question": "When someone is frustrated or difficult to satisfy, do you listen, clarify, calm, explain, or solve first? Explain your response.",
        "chips": ["Clarify", "Solve", "Listen", "Explain", "Calm"],
    },
    {
        "id": 8,
        "division": "Team Dynamics",
        "insight": "Strong teams are not made of identical people. They are made of patterns that balance each other.",
        "question": "In a team, are you usually the organizer, encourager, challenger, problem-solver, peacekeeper, or driver? Explain why.",
        "chips": ["Organizer", "Driver", "Encourager", "Problem-solver", "Peacekeeper"],
    },
    {
        "id": 9,
        "division": "Growth",
        "insight": "Growth begins when feedback becomes information instead of threat.",
        "question": "When someone corrects your work, do you feel curious, defensive, motivated, embarrassed, calm, or eager to improve? Explain what you do next.",
        "chips": ["Curious", "Motivated", "Support", "Improve", "Calm"],
    },
    {
        "id": 10,
        "division": "Autonomy",
        "insight": "Some roles need direction. Some need independence. The right fit depends on how you move without being watched.",
        "question": "When trusted to work independently, do you plan, start, check in, set targets, wait for clarity, or work toward a deadline? Explain how you keep moving.",
        "chips": ["Plan", "Start", "Check in", "Set targets", "Routine"],
    },
]

ARCHETYPES = {
    "Architect": {
        "accent": "#7f8da3",
        "model": "models/architect.glb",
        "operating_pattern": "Architects create clarity through structure. They tend to look for standards, systems, and decision logic before moving quickly.",
        "primary_strengths": [
            "Builds dependable process and quality standards",
            "Translates ambiguity into organized next steps",
            "Protects accuracy, documentation, and operational trust",
        ],
        "friction_points": [
            "Can hesitate when expectations are vague",
            "May resist rushed decisions that bypass standards",
            "Needs room to understand the system before optimizing it",
        ],
        "recommended_placement": "Operations design, compliance support, quality assurance, project coordination, systems implementation",
        "manager_guidance": "Give clear outcomes, decision rules, documentation, and enough context to understand why the work matters.",
        "work_best": "They work best with defined expectations, visible standards, and a calm route from analysis to execution.",
        "onboarding_path": "Structured orientation, tool walkthroughs, process maps, and early ownership of a contained operational improvement.",
        "growth_note": "Practice moving before every variable is resolved when the risk is low and the learning value is high.",
    },
    "Current": {
        "accent": "#8db5c7",
        "model": "models/current.glb",
        "operating_pattern": "Currents learn through motion. They create momentum, act on urgency, and convert unclear situations into visible progress.",
        "primary_strengths": [
            "Moves work forward quickly",
            "Adapts well when priorities shift",
            "Creates urgency and visible execution energy",
        ],
        "friction_points": [
            "Can move faster than the team can absorb",
            "May become frustrated by slow approvals",
            "Needs guardrails so speed does not reduce quality",
        ],
        "recommended_placement": "Operations execution, launch support, field coordination, implementation, rapid response workflows",
        "manager_guidance": "Set short milestones, clarify decision rights, and give practical feedback while the work is active.",
        "work_best": "They work best with live goals, fast feedback, and enough authority to make practical progress.",
        "onboarding_path": "Early hands-on tasks, quick wins, direct manager checkpoints, and a visible 30-day execution lane.",
        "growth_note": "Pause long enough to share context so the team can follow the pace without losing alignment.",
    },
    "Signal": {
        "accent": "#9fb8ad",
        "model": "models/signal.glb",
        "operating_pattern": "Signals interpret people and context. They notice tone, support needs, communication gaps, and the trust conditions behind performance.",
        "primary_strengths": [
            "Builds psychological safety and team connection",
            "Listens for nuance before responding",
            "Improves collaboration through empathy and clarity",
        ],
        "friction_points": [
            "Can carry too much emotional context",
            "May need clearer boundaries around ownership",
            "Can slow down if the team climate feels unstable",
        ],
        "recommended_placement": "Client success, employee support, onboarding coordination, account care, people operations",
        "manager_guidance": "Invite perspective, define boundaries, and pair relational trust with practical outcomes.",
        "work_best": "They work best where communication, care, and shared understanding are treated as business assets.",
        "onboarding_path": "Relationship-led introductions, mentor pairing, client or team context briefings, and frequent early check-ins.",
        "growth_note": "Keep empathy connected to action so support becomes a clear next step, not an invisible load.",
    },
    "Spark": {
        "accent": "#d9b66f",
        "model": "models/spark.glb",
        "operating_pattern": "Sparks create possibility. They look for new angles, better experiences, creative improvements, and experiments that reveal what could work.",
        "primary_strengths": [
            "Generates ideas and reframes stale problems",
            "Brings creative energy to change",
            "Tests new approaches when the current path is not enough",
        ],
        "friction_points": [
            "Can lose energy in repetitive work without context",
            "May need help narrowing ideas into sequence",
            "Can overextend when too many possibilities are open",
        ],
        "recommended_placement": "Creative strategy, product improvement, innovation projects, campaign support, experience design",
        "manager_guidance": "Give a clear problem, a real constraint, and a place to test ideas without derailing core operations.",
        "work_best": "They work best with purpose, creative latitude, and a practical bridge from idea to prototype.",
        "onboarding_path": "Mission context, cross-functional exposure, guided experiments, and a first project with room to improve the experience.",
        "growth_note": "Turn the strongest idea into one measurable next action before opening the next possibility.",
    },
    "Anchor": {
        "accent": "#aeb7c2",
        "model": "models/anchor.glb",
        "operating_pattern": "Anchors create steadiness. They observe carefully, protect continuity, and help teams stay reliable when conditions change.",
        "primary_strengths": [
            "Provides calm, consistent execution",
            "Maintains reliability across repeated workflows",
            "Notices risk through patient observation",
        ],
        "friction_points": [
            "Can be overlooked in loud or high-speed environments",
            "May need explicit invitation before surfacing concerns",
            "Can resist abrupt change when the purpose is unclear",
        ],
        "recommended_placement": "Support operations, service quality, internal coordination, documentation, continuity roles",
        "manager_guidance": "Create a stable cadence, explain change early, and ask directly for observations before issues surface.",
        "work_best": "They work best with trust, consistency, and a team rhythm that values durable follow-through.",
        "onboarding_path": "Steady ramp, repeatable practice, clear routines, and a dependable point of contact during the first weeks.",
        "growth_note": "Share observations sooner, especially when quiet concerns could prevent team rework.",
    },
}

KEYWORDS = {
    "Architect": ["structure", "rules", "accuracy", "planning", "plan", "systems", "standards", "precise", "framework", "audit", "quality", "documentation", "organize", "organizer", "mastery"],
    "Current": ["action", "speed", "movement", "adapt", "urgency", "execution", "direct", "act", "progress", "driver", "challenge", "pace", "decisive", "fast", "move"],
    "Signal": ["people", "communication", "listen", "support", "empathy", "team", "supportive", "heard", "connector", "mentorship", "conversation", "coordinate", "client", "trust"],
    "Spark": ["ideas", "possibilities", "improve", "innovation", "creativity", "test", "expressive", "experiment", "inspired", "catalyst", "discovery", "vision", "creative"],
    "Anchor": ["calm", "steady", "reliable", "observe", "consistency", "support", "stable", "repeat", "routine", "safe", "stabilizer", "practice", "continuity"],
}

CHIP_SCORES = {
    chip.lower(): archetype
    for question in QUESTIONS
    for chip, archetype in zip(question["chips"], ARCHETYPE_ORDER)
}

PATHS = [
    {"name": "Operations", "archetypes": ["Architect", "Current", "Anchor"]},
    {"name": "Strategy", "archetypes": ["Architect", "Spark", "Current"]},
    {"name": "Client Success", "archetypes": ["Signal", "Anchor", "Current"]},
    {"name": "Creative", "archetypes": ["Spark", "Signal", "Architect"]},
    {"name": "Support", "archetypes": ["Anchor", "Signal", "Architect"]},
    {"name": "Project Coordination", "archetypes": ["Architect", "Signal", "Current"]},
]

DEMO_CANDIDATES = [
    {"id": "mara-chen", "name": "Mara Chen", "role": "New hire", "status": "Completed", "archetype": "Architect"},
    {"id": "eli-ramos", "name": "Eli Ramos", "role": "Candidate", "status": "Completed", "archetype": "Signal"},
    {"id": "nina-patel", "name": "Nina Patel", "role": "New hire", "status": "Pending", "archetype": "Current"},
    {"id": "jon-brooks", "name": "Jon Brooks", "role": "Candidate", "status": "Completed", "archetype": "Spark"},
    {"id": "sora-lee", "name": "Sora Lee", "role": "Internal move", "status": "Completed", "archetype": "Anchor"},
]


class RippleSignalError(ValueError):
    pass


def alpha_words(text):
    return re.findall(r"[a-zA-Z]{2,}", (text or "").lower())


def is_mostly_repeated_letters(letters):
    if not letters:
        return True

    counts = Counter(letters)
    most_common = counts.most_common(1)[0][1]
    return most_common / len(letters) > 0.62


def looks_like_keyboard_noise(text):
    joined = "".join(alpha_words(text))
    keyboard_patterns = [
        "asdf", "qwer", "qwerty", "zxcv", "dfgdfg", "sdfg", "hjkl",
        "aaaa", "zzzz", "blah", "idk", "lolol"
    ]

    if joined in keyboard_patterns:
        return True

    if any(pattern in joined for pattern in keyboard_patterns):
        return True

    if len(joined) >= 6 and len(set(joined)) <= 3:
        return True

    return False


def is_meaningful_response(text, chips):
    chips = chips or []
    text = (text or "").strip()

    # If the user typed anything, the typed response must be meaningful.
    # Signal chips may support the answer, but they cannot rescue gibberish.
    if text:
        letters = re.sub(r"[^A-Za-z]", "", text).lower()
        words = alpha_words(text)

        if len(text) < 12:
            return False

        if len(words) < 3:
            return False

        if len(set(words)) < 2:
            return False

        if not letters:
            return False

        if not any(vowel in letters for vowel in "aeiou"):
            return False

        if is_mostly_repeated_letters(letters):
            return False

        if looks_like_keyboard_noise(text):
            return False

        meaningful_words = [
            word for word in words
            if len(word) >= 3 and any(vowel in word for vowel in "aeiou")
        ]

        if len(meaningful_words) < 2:
            return False

        # Reject repeated fake-word answers like "banana banana banana" or "hello hello hello"
        if len(set(meaningful_words)) < 2:
            return False

        return True

    # If the text box is blank, require at least two selected signal chips.
    # One chip alone is too weak for an open-response assessment.
    return len(chips) >= 2


def build_path_matches(scores):
    total = sum(scores.values()) or 1
    path_matches = []

    for path in PATHS:
        weight = sum(scores[name] for name in path["archetypes"])
        percent = max(42, min(96, round((weight / total) * 100)))
        path_matches.append({"name": path["name"], "percent": percent, "basis": ", ".join(path["archetypes"])})

    path_matches.sort(key=lambda item: item["percent"], reverse=True)
    return path_matches


def build_confidence(scores, chip_count):
    total = sum(scores.values())
    top_score = max(scores.values()) if scores else 0

    if total <= 0:
        return 0, "No signal"

    confidence = round((top_score / total) * 100)

    if chip_count >= 7 or confidence >= 62:
        return confidence, "High signal"

    if chip_count >= 4 or confidence >= 45:
        return confidence, "Moderate signal"

    return confidence, "Low signal"


def score_responses(responses, enforce_quality=True):
    scores = {name: 0 for name in ARCHETYPE_ORDER}
    normalized_responses = []
    meaningful_count = 0
    chip_count = 0

    for response in responses:
        text = response.get("text", "") or ""
        chips = response.get("chips", []) or []
        chip_count += len(chips)

        normalized_responses.append({
            "division": response.get("division", ""),
            "text": text,
            "chips": chips
        })

        if is_meaningful_response(text, chips):
            meaningful_count += 1

        lower_text = text.lower()

        for archetype, words in KEYWORDS.items():
            for word in words:
                if word in lower_text:
                    scores[archetype] += 2

        for chip in [chip.lower() for chip in chips]:
            archetype = CHIP_SCORES.get(chip)
            if archetype:
                scores[archetype] += 3

    total_score = sum(scores.values())
    top_score = max(scores.values()) if scores else 0

    if enforce_quality and meaningful_count < 7:
        raise RippleSignalError("RIPPLE needs more meaningful responses before it can generate a profile.")

    if enforce_quality and chip_count < 5 and (total_score < 12 or top_score < 5):
        raise RippleSignalError("RIPPLE could not detect enough placement signal. Add more detail or choose signal chips.")

    ordered = sorted(scores.items(), key=lambda item: (-item[1], ARCHETYPE_ORDER.index(item[0])))
    primary = ordered[0][0]
    secondary = ordered[1][0]
    confidence_percent, confidence_label = build_confidence(scores, chip_count)

    return {
        "classification": primary,
        "secondary": secondary,
        "scores": scores,
        "profile": ARCHETYPES[primary],
        "secondaryProfile": ARCHETYPES[secondary],
        "paths": build_path_matches(scores),
        "responses": normalized_responses,
        "confidencePercent": confidence_percent,
        "confidenceLabel": confidence_label,
        "meaningfulResponses": meaningful_count,
    }


def demo_result_for(archetype):
    profile = ARCHETYPES[archetype]
    scores = {name: 2 for name in ARCHETYPE_ORDER}
    scores[archetype] = 12
    secondary = "Signal" if archetype != "Signal" else "Architect"

    return {
        "classification": archetype,
        "secondary": secondary,
        "scores": scores,
        "profile": profile,
        "secondaryProfile": ARCHETYPES[secondary],
        "paths": build_path_matches(scores),
        "responses": [],
        "confidencePercent": 72,
        "confidenceLabel": "Demo signal",
        "meaningfulResponses": 10,
    }


@app.route("/")
def splash():
    return render_template("index.html", title="RIPPLE Onboarding & Placement by VITRA")


@app.route("/access")
def access():
    return render_template("access.html", title="Access | RIPPLE")


@app.route("/welcome")
def welcome():
    return render_template("welcome.html", title="Welcome | RIPPLE")


@app.route("/questions")
def questions():
    return render_template("questions.html", title="Sequence | RIPPLE", questions=QUESTIONS)


@app.route("/assessment")
def assessment_redirect():
    return redirect(url_for("questions"))


@app.route("/processing")
def processing():
    return render_template("processing.html", title="Processing | RIPPLE")


@app.route("/results")
def results():
    return render_template("results.html", title="Employee Results | RIPPLE")


@app.route("/placement")
def placement():
    return render_template("placement.html", title="Placement Path | RIPPLE")


@app.route("/hr")
def hr_dashboard():
    completed = len([item for item in DEMO_CANDIDATES if item["status"] == "Completed"])
    breakdown = {name: 0 for name in ARCHETYPE_ORDER}
    for candidate in DEMO_CANDIDATES:
        breakdown[candidate["archetype"]] += 1
    selected = DEMO_CANDIDATES[0]
    return render_template(
        "hr_dashboard.html",
        title="HR Dashboard | RIPPLE",
        candidates=DEMO_CANDIDATES,
        completed=completed,
        pending=len(DEMO_CANDIDATES) - completed,
        breakdown=breakdown,
        selected=selected,
        archetypes=ARCHETYPES,
    )


@app.route("/hr/candidate/<candidate_id>")
def hr_report(candidate_id):
    candidate = next((item for item in DEMO_CANDIDATES if item["id"] == candidate_id), DEMO_CANDIDATES[0])
    result = demo_result_for(candidate["archetype"])
    return render_template("hr_report.html", title="HR Placement Report | RIPPLE", candidate=candidate, result=result)


@app.route("/pathways")
def old_pathways_redirect():
    return redirect(url_for("placement"))


@app.route("/about")
def about_redirect():
    return redirect(url_for("splash"))


@app.route("/api/score", methods=["POST"])
def api_score():
    payload = request.get_json(silent=True) or {}
    responses = payload.get("responses", [])

    if len(responses) != 10:
        return jsonify({"error": "Complete all 10 Ripple divisions before generating a profile."}), 400

    try:
        result = score_responses(responses)
    except RippleSignalError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
