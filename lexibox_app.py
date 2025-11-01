import streamlit as st
import json, random, os
from datetime import datetime

# ---------------- CONSTANTS ----------------
VOCAB_FILE = "words.json"
USER_FILE = "user_data.json"

# ---------------- UTILITIES ----------------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- INITIALIZATION ----------------
if "vocab" not in st.session_state:
    st.session_state.vocab = load_json(VOCAB_FILE, {})

if "user" not in st.session_state:
    st.session_state.user = load_json(USER_FILE, {
        "xp": 0,
        "rank": "Beginner",
        "streak": 0,
        "history": [],
        "cooldowns": {},
    })

vocab = st.session_state.vocab
user = st.session_state.user

# ---------------- HELPERS ----------------
def get_rank(xp):
    if xp < 100: return "Beginner"
    elif xp < 250: return "Learner"
    elif xp < 500: return "Adept"
    elif xp < 1000: return "Pro"
    else: return "Master"

def get_question():
    available = [w for w in vocab if w not in user["cooldowns"] or user["cooldowns"][w] <= 0]
    if not available:
        for w in user["cooldowns"]:
            user["cooldowns"][w] = max(0, user["cooldowns"][w] - 1)
        available = list(vocab.keys())
    word = random.choice(available)
    options = [vocab[word]["meaning"]]
    while len(options) < 4:
        choice = random.choice(list(vocab.values()))["meaning"]
        if choice not in options:
            options.append(choice)
    random.shuffle(options)
    return word, options

def update_cooldowns(word, correct):
    if correct:
        user["cooldowns"][word] = 3
    else:
        user["cooldowns"][word] = 0

def award_xp(correct):
    if correct:
        user["streak"] += 1
        bonus = 0
        if user["streak"] >= 5:
            bonus = 15
        elif user["streak"] == 4:
            bonus = 10
        elif user["streak"] == 3:
            bonus = 5
        xp = 10 + bonus
        user["xp"] += xp
        return f"+{xp} XP (Streak {user['streak']})"
    else:
        user["streak"] = 0
        return "Wrong! Streak reset."

# ---------------- MAIN SCREENS ----------------
def show_home():
    st.title("🧠 Lexibox")
    st.subheader(f"Rank: {user['rank']}")
    st.progress(min(user["xp"] % 1000 / 1000, 1.0))
    st.write(f"XP: {user['xp']}")
    st.write(f"Streak: {user['streak']} 🔥")

    if st.button("Start Quiz"):
        st.session_state.mode = "quiz"
        st.session_state.quiz_state = {
            "word": None,
            "options": [],
            "answered": False,
            "feedback": "",
        }

def show_quiz():
    state = st.session_state.quiz_state
    if not state["word"]:
        state["word"], state["options"] = get_question()

    st.header(f"Word: {state['word']}")
    for opt in state["options"]:
        if st.button(opt, disabled=state["answered"]):
            correct = opt == vocab[state["word"]]["meaning"]
            feedback = award_xp(correct)
            update_cooldowns(state["word"], correct)
            user["rank"] = get_rank(user["xp"])
            user["history"].append({
                "word": state["word"],
                "selected": opt,
                "correct": vocab[state["word"]]["meaning"],
                "result": "✅" if correct else "❌",
                "time": datetime.now().strftime("%H:%M:%S"),
            })
            save_json(USER_FILE, user)
            state["answered"] = True
            state["feedback"] = feedback
            st.rerun()

    if state["answered"]:
        st.success(state["feedback"])
        if st.button("Next"):
            st.session_state.quiz_state = {"word": None, "options": [], "answered": False, "feedback": ""}
            st.rerun()

    if st.button("🏠 Back to Home"):
        st.session_state.mode = "home"
        save_json(USER_FILE, user)
        st.rerun()

# ---------------- MAIN APP ----------------
if "mode" not in st.session_state:
    st.session_state.mode = "home"

if st.session_state.mode == "home":
    show_home()
elif st.session_state.mode == "quiz":
    show_quiz()