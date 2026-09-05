"""
MindCheck Bot - Localhost Web Application Backend (FastAPI)
===========================================================
"""

import sys
import webbrowser
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="MindCheck Bot Web Server")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# DATA & ALGORITHMS (Preserved from mindcheck_bot.py)
# ---------------------------------------------------------------------------

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "end it all", "want to die",
    "no reason to live", "hurt myself", "hurting myself", "self harm", "self-harm",
    "not worth living", "better off dead"
]

CRISIS_MESSAGE = {
    "title": "Immediate Support Available",
    "body": "I'm really glad you reached out, and I want to make sure you're safe right now. I cannot provide emergency support, but help is available 24/7:",
    "helplines": [
        {"region": "United States", "contact": "Call or Text 988 (Suicide & Crisis Lifeline)"},
        {"region": "United Kingdom", "contact": "Call 111 (NHS) or 116 123 (Samaritans)"},
        {"region": "Canada", "contact": "Call or Text 988"},
        {"region": "India", "contact": "Call 9152987821 (KIRAN) or 14416 (Tele-MANAS)"},
        {"region": "International", "contact": "Visit https://findahelpline.com"}
    ]
}

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

INTRO_QUESTIONS = [
    "Before we start, how have the last couple of weeks been for you overall?",
    "Has anything in particular been on your mind or contributing to your stress lately?",
    "How would you describe your sleep pattern and energy levels recently, in your own words?"
]

MASTER_QUESTIONS = [
    {"id": 1, "text": "Little interest or pleasure in doing things you'd normally enjoy", "category": "interest"},
    {"id": 2, "text": "Feeling down, low, or hopeless", "category": "mood"},
    {"id": 3, "text": "Trouble falling/staying asleep, or sleeping much more than usual", "category": "sleep"},
    {"id": 4, "text": "Feeling tired or having little energy", "category": "energy"},
    {"id": 5, "text": "Poor appetite, or eating noticeably more than usual", "category": "appetite"},
    {"id": 6, "text": "Feeling bad about yourself, or that you're a failure", "category": "selfworth"},
    {"id": 7, "text": "Trouble concentrating on things like reading or conversations", "category": "cognition"},
    {"id": 8, "text": "Moving/speaking noticeably slower, or feeling restless/fidgety", "category": "psychomotor"},
    {"id": 9, "text": "Withdrawing from friends, family, or things you'd usually do socially", "category": "isolation"},
    {"id": 10, "text": "Feeling nervous, anxious, or on edge", "category": "anxiety"},
    {"id": 11, "text": "Not being able to stop or control worrying", "category": "anxiety"},
    {"id": 12, "text": "Worrying too much about different things", "category": "anxiety"},
    {"id": 13, "text": "Trouble relaxing or feeling restless", "category": "anxiety"},
    {"id": 14, "text": "Becoming easily annoyed or irritable", "category": "mood"},
    {"id": 15, "text": "Feeling afraid, as if something awful might happen", "category": "anxiety"},
    {"id": 16, "text": "Feeling overwhelmed by daily responsibilities or tasks", "category": "stress"},
    {"id": 17, "text": "Feeling disconnected or detached from your surroundings", "category": "cognition"},
    {"id": 18, "text": "Difficulty making decisions or thinking clearly", "category": "cognition"},
    {"id": 19, "text": "Feeling unmotivated or doubting your abilities", "category": "selfworth"},
    {"id": 20, "text": "Feeling lonely even when around other people", "category": "isolation"}
]

def safety_check(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in CRISIS_KEYWORDS)

def detect_cues(text: str, cue_bank: dict) -> List[str]:
    lowered = text.lower()
    hits = []
    for cue, keywords in CUE_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                hits.append(cue)
                cue_bank[cue] = cue_bank.get(cue, 0) + 1
                break
    return hits

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


# ---------------------------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/config")
async def get_config():
    return {
        "intro_questions": INTRO_QUESTIONS,
        "master_questions": MASTER_QUESTIONS
    }

@app.post("/api/check-safety")
async def api_check_safety(payload: Dict[str, Any]):
    text = payload.get("text", "")
    is_crisis = safety_check(text)
    return {
        "is_crisis": is_crisis,
        "crisis_info": CRISIS_MESSAGE if is_crisis else None
    }

@app.post("/api/analyze-intro")
async def api_analyze_intro(payload: Dict[str, Any]):
    messages = payload.get("messages", [])
    cue_bank = {}
    is_crisis = False
    
    for msg in messages:
        if safety_check(msg):
            is_crisis = True
            break
        detect_cues(msg, cue_bank)

    cues_summary = [
        {"cue": cue, "count": count}
        for cue, count in sorted(cue_bank.items(), key=lambda x: -x[1])
    ]

    return {
        "is_crisis": is_crisis,
        "crisis_info": CRISIS_MESSAGE if is_crisis else None,
        "cue_bank": cue_bank,
        "cues_summary": cues_summary
    }

@app.post("/api/submit-assessment")
async def api_submit_assessment(payload: Dict[str, Any]):
    user_name = payload.get("user_name", "Guest") or "Guest"
    answers = payload.get("answers", {}) # {question_id: score}
    q_count = payload.get("q_count", 9)
    cue_bank = payload.get("cue_bank", {})

    items = MASTER_QUESTIONS[:q_count]
    category_scores = {}
    total_score = 0

    for item in items:
        qid_str = str(item["id"])
        score = int(answers.get(qid_str, 0))
        total_score += score
        cat = item["category"]
        category_scores[cat] = category_scores.get(cat, 0) + score

    max_score = len(items) * 3
    band = severity_band(total_score, max_score)
    pattern = symptom_pattern(category_scores)

    convo_notes = [
        f"Mentioned {cue}-related themes ({count} time{'s' if count > 1 else ''})"
        for cue, count in sorted(cue_bank.items(), key=lambda x: -x[1])
    ]

    return {
        "user_name": user_name,
        "total_score": total_score,
        "max_score": max_score,
        "severity": band,
        "pattern": pattern,
        "category_scores": category_scores,
        "convo_notes": convo_notes
    }


if __name__ == "__main__":
    print("Starting MindCheck Bot Localhost Web App on http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
