"""
MindCheck Bot - Conversational Mental Health & Wellbeing Screening
===================================================================
A rule-based conversational screening tool for a student/project demo.
"""

import time
import sys

# ---------------------------------------------------------------------------
# 1. SAFETY LAYER
# ---------------------------------------------------------------------------

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "end it all", "want to die",
    "no reason to live", "hurt myself", "hurting myself", "self harm", "self-harm",
    "not worth living", "better off dead"
]

CRISIS_MESSAGE = """
I'm really glad you told me that, and I want to make sure you're safe right now.
I'm not able to provide the kind of support you may need in this moment, but
please reach out to someone who can:

  - If you're in immediate danger, call your local emergency number now.
  - US: call or text 988 (Suicide & Crisis Lifeline), available 24/7.
  - Outside the US: search "[your country] suicide crisis helpline" or visit
    https://findahelpline.com for a helpline near you.

You don't have to go through this alone, and talking to a real person who is
trained for this matters more than anything a screening tool can tell you.
"""

def safety_check(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in CRISIS_KEYWORDS)

def get_user_input(prompt: str) -> str:
    try:
        user_reply = input(prompt).strip()
        if user_reply.lower() in {"exit", "quit", "q"}:
            print("\nSession exited by user. Take care!")
            sys.exit(0)
        return user_reply
    except (KeyboardInterrupt, EOFError):
        print("\n\nSession ended cleanly. Take care!")
        sys.exit(0)


# ---------------------------------------------------------------------------
# 2. CONVERSATIONAL INTRO (ChatGPT-style dialogue)
# ---------------------------------------------------------------------------

CUE_KEYWORDS = {
    "sleep":     ["sleep", "insomnia", "can't sleep", "oversleep", "tired"],
    "appetite":  ["appetite", "eating", "overeat", "not hungry", "weight"],
    "energy":    ["exhausted", "no energy", "fatigue", "drained"],
    "interest":  ["no interest", "don't enjoy", "bored", "numb"],
    "isolation": ["alone", "isolat", "no one understands", "withdraw"],
    "mood":      ["sad", "down", "hopeless", "empty", "worthless"],
    "anxiety":   ["anxious", "worry", "panic", "nervous", "fear"],
    "stress":    ["overwhelmed", "stressed", "burnout", "pressure"]
}

def detect_cues(text: str, cue_bank: dict) -> set:
    lowered = text.lower()
    hits = set()
    for cue, keywords in CUE_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                hits.add(cue)
                cue_bank[cue] = cue_bank.get(cue, 0) + 1
                break
    return hits

INTRO_QUESTIONS = [
    "Before we start, how have the last couple of weeks been for you overall?",
    "Has anything in particular been on your mind or contributing to your stress lately?",
    "How would you describe your sleep pattern and energy levels recently, in your own words?",
]

def chat_intro_loop(user_name: str, cue_bank: dict) -> list:
    transcript = []
    print(f"\nBot: Hello {user_name}! I'm MindCheck. Let's do a short conversational check-in.")
    for question in INTRO_QUESTIONS:
        print(f"\nBot: {question}")
        user_reply = get_user_input("You: ")
        transcript.append(user_reply)

        if safety_check(user_reply):
            print(CRISIS_MESSAGE)
            sys.exit(0)

        detect_cues(user_reply, cue_bank)
        time.sleep(0.1)
    return transcript


# ---------------------------------------------------------------------------
# 3. EXPANDED QUESTION BANK (Up to 20 Questions)
# ---------------------------------------------------------------------------

MASTER_QUESTIONS = [
    {"text": "Little interest or pleasure in doing things you'd normally enjoy", "category": "interest"},
    {"text": "Feeling down, low, or hopeless", "category": "mood"},
    {"text": "Trouble falling/staying asleep, or sleeping much more than usual", "category": "sleep"},
    {"text": "Feeling tired or having little energy", "category": "energy"},
    {"text": "Poor appetite, or eating noticeably more than usual", "category": "appetite"},
    {"text": "Feeling bad about yourself, or that you're a failure", "category": "selfworth"},
    {"text": "Trouble concentrating on things like reading or conversations", "category": "cognition"},
    {"text": "Moving/speaking noticeably slower, or feeling restless/fidgety", "category": "psychomotor"},
    {"text": "Withdrawing from friends, family, or things you'd usually do socially", "category": "isolation"},
    {"text": "Feeling nervous, anxious, or on edge", "category": "anxiety"},
    {"text": "Not being able to stop or control worrying", "category": "anxiety"},
    {"text": "Worrying too much about different things", "category": "anxiety"},
    {"text": "Trouble relaxing or feeling restless", "category": "anxiety"},
    {"text": "Becoming easily annoyed or irritable", "category": "mood"},
    {"text": "Feeling afraid, as if something awful might happen", "category": "anxiety"},
    {"text": "Feeling overwhelmed by daily responsibilities or tasks", "category": "stress"},
    {"text": "Feeling disconnected or detached from your surroundings", "category": "cognition"},
    {"text": "Difficulty making decisions or thinking clearly", "category": "cognition"},
    {"text": "Feeling unmotivated or doubting your abilities", "category": "selfworth"},
    {"text": "Feeling lonely even when around other people", "category": "isolation"}
]

SCALE_HELP = """
Rate each statement for the LAST TWO WEEKS using:
  0 = Not at all
  1 = Several days
  2 = More than half the days
  3 = Nearly every day
(Type 'exit' at any prompt to quit)
"""

def run_quiz_loop(items: list) -> dict:
    print(SCALE_HELP)
    category_scores = {}
    total_score = 0

    for i, item in enumerate(items, start=1):
        while True:
            raw = get_user_input(f"\n{i}/{len(items)}. {item['text']}\n   Score (0=Not at all, 1=Several days, 2=>Half days, 3=Nearly every day): ")
            if safety_check(raw):
                print(CRISIS_MESSAGE)
                sys.exit(0)
            if raw in {"0", "1", "2", "3"}:
                score = int(raw)
                break
            print("   [!] Please enter a valid number from 0 to 3.")

        total_score += score
        cat = item["category"]
        category_scores[cat] = category_scores.get(cat, 0) + score

    return {"total": total_score, "max": len(items) * 3, "by_category": category_scores}


# ---------------------------------------------------------------------------
# 4. ANALYSIS & REPORT
# ---------------------------------------------------------------------------

def severity_band(total: int, max_score: int) -> str:
    pct = total / max_score if max_score > 0 else 0
    if pct <= 0.15: return "Minimal"
    elif pct <= 0.35: return "Mild"
    elif pct <= 0.55: return "Moderate"
    elif pct <= 0.75: return "Moderately severe"
    else: return "Severe"

def symptom_pattern(by_category: dict) -> str:
    if not by_category or max(by_category.values(), default=0) == 0:
        return "None detected (scores within normal range)"

    max_score = max(by_category.values())
    top_cats = [cat for cat, val in by_category.items() if val == max_score]

    pattern_map = {
        "sleep":       "Sleep/appetite-dominant pattern",
        "appetite":    "Sleep/appetite-dominant pattern",
        "energy":      "Low-energy / fatigue-dominant pattern",
        "interest":    "Anhedonia-dominant pattern",
        "mood":        "Mood-dominant pattern",
        "selfworth":   "Self-worth/cognitive-dominant pattern",
        "cognition":   "Self-worth/cognitive-dominant pattern",
        "psychomotor": "Psychomotor-dominant pattern",
        "isolation":   "Social-withdrawal-dominant pattern",
        "anxiety":     "Anxiety-dominant pattern",
        "stress":      "Stress & burnout pattern"
    }

    if len(top_cats) > 1:
        top_labels = list(dict.fromkeys([pattern_map.get(c, "Mixed") for c in top_cats]))
        return " & ".join(top_labels) if len(top_labels) > 1 else top_labels[0]

    return pattern_map.get(top_cats[0], "Mixed pattern")

def analyze(quiz_results: dict, cue_bank: dict) -> dict:
    total = quiz_results["total"]
    max_score = quiz_results["max"]
    band = severity_band(total, max_score)
    pattern = symptom_pattern(quiz_results["by_category"])

    convo_notes = [f"mentioned {cue}-related themes {count} time(s)"
                    for cue, count in sorted(cue_bank.items(), key=lambda x: -x[1])]

    return {
        "total_score": total,
        "max_score": max_score,
        "severity": band,
        "pattern": pattern,
        "convo_notes": convo_notes,
    }

def print_report(user_name: str, result: dict):
    print("\n" + "=" * 60)
    print(f"MINDCHECK SUMMARY FOR {user_name.upper()} (Educational Demo Only)")
    print("=" * 60)
    print(f"Total Score:             {result['total_score']} / {result['max_score']}")
    print(f"Severity Band:           {result['severity']}")
    print(f"Possible Symptom Pattern: {result['pattern']}")

    if result["convo_notes"]:
        print("\nFrom our conversation, keyword cues observed:")
        for note in result["convo_notes"]:
            print(f"  - {note}")

    print("""
--------------------------------------------------------------
IMPORTANT DISCLAIMER:
This tool is a class/portfolio project, not a medical device.
It does not diagnose depression or any mental health condition.
Screening scores like this are only meaningful when interpreted
by a qualified healthcare professional alongside your full history.
--------------------------------------------------------------
""")


# ---------------------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print(" MindCheck Bot - Conversational Screening & Wellbeing Demo ")
    print("=" * 60)

    # User Sign-In Stage
    user_name = get_user_input("Enter your name (or press Enter for Guest): ").strip()
    if not user_name:
        user_name = "Guest"

    print("\nSelect Question Mode:")
    print("  1. Standard Assessment (9 Questions - PHQ-9)")
    print("  2. Extended Assessment (15 Questions - Mood & Anxiety)")
    print("  3. Comprehensive Assessment (20 Questions - Full Wellbeing)")
    
    mode = get_user_input("Select mode (1, 2, or 3) [Default 1]: ").strip()
    if mode == "2":
        q_count = 15
    elif mode == "3":
        q_count = 20
    else:
        q_count = 9

    cue_bank = {}

    # Stage 1: Conversational Chat
    chat_intro_loop(user_name, cue_bank)

    # Stage 2: Scored Quiz
    items = MASTER_QUESTIONS[:q_count]
    print(f"\nBot: Thanks for sharing. Now let me ask {q_count} check-in questions.")
    quiz_results = run_quiz_loop(items)

    # Stage 3 & 4: Analysis & Report
    result = analyze(quiz_results, cue_bank)
    print_report(user_name, result)


if __name__ == "__main__":
    main()
