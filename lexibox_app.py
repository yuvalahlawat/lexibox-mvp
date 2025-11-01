import streamlit as st
import json, random, os
from datetime import datetime

# ---------------- CONSTANTS ----------------
VOCAB_FILE = "words.json"
USER_FOLDER = "users"
os.makedirs(USER_FOLDER, exist_ok=True)

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
    vocab = load_json(VOCAB_FILE, {})
    if not vocab:
        st.error("⚠️ Vocab file empty or missing. Please upload a valid words.json.")
        st.stop()
    st.session_state.vocab = vocab

# ---------------- AUTH ----------------
if "username" not in st.session_state:
    st.title("🔐 Lexibox Login")
    username = st.text_input("Enter username")
    if st.button("Start"):
        if not username.strip():
            st.warning("Please enter a valid username.")
            st.stop()
        st.session_state.username = username.strip()
        st.session_state.user_file = os.path.join(USER_FOLDER, f"{st.session_state.username}.json")
        user_data = load_json(st.session_state.user_file, {
            "xp": 0,
            "rank": "Beginner",
            "streak": 0,
            "history": [],
            "cooldowns": {}
        })
        st.session_state.user = user_data
        st.session_state.mode = "home"
        st.rerun()

# ---------------- HELPERS ----------------
def get_rank(xp):
    if xp < 100: return "Beginner"
    elif xp < 250: return "Learner"
    elif xp < 500: return "Adept"
    elif xp < 1000: return "Pro"
    else: return "Master"

def get_question():
    vocab = st.session_state.vocab
    user = st.session_state.user

    available = [w for w in vocab if w not in user["cooldowns"] or user["cooldowns"][w] <= 0]
    if not available:
        for w in list(user["cooldowns"].keys()):
            user["cooldowns"][w] = max(0, user["cooldowns"][w] - 1)
        available = list(vocab.keys())

    if not available:
        st.error("No vocab available. Please check your words.json.")
        st.stop()

    word = random.choice(available)
    correct_meaning = vocab[word]  # <-- direct string value

    all_meanings = list(vocab.values())
    all_meanings = list(set(all_meanings))
    options = [correct_meaning]
    while len(options) < 4 and len(all_meanings) > 1:
        choice = random.choice(all_meanings)
        if choice not in options:
            options.append(choice)
    random.shuffle(options)
    return word, correct_meaning, options

def update_cooldowns(word, correct):
    user = st.session_state.user
    if correct:
        user["cooldowns"][word] = 3
    else:
        user["cooldowns"][word] = 0

def award_xp(correct):
    user = st.session_state.user
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
        return f"✅ +{xp} XP  | Streak {user['streak']}"
    else:
        user["streak"] = 0
        return "❌ Wrong! Streak reset."

# ---------------- MAIN SCREENS ----------------
def show_home():
    user = st.session_state.user
    st.title(f"🏠 Lexibox — {st.session_state.username}")
    st.subheader(f"Rank: {user['rank']}")
    st.progress(min((user["xp"] % 1000) / 1000, 1.0))
    st.write(f"XP: {user['xp']}")
    st.write(f"Streak: {user['streak']} 🔥")

    if st.button("▶️ Start Quiz"):
        st.session_state.mode = "quiz"
        st.session_state.quiz_state = {"word": None, "correct": None, "options": [], "answered": False, "feedback": ""}
        st.rerun()

    if st.button("🗑️ Delete Profile"):
        os.remove(st.session_state.user_file)
        for k in ["username", "mode", "user", "user_file", "quiz_state"]:
            if k in st.session_state:
                del st.session_state[k]
        st.success("Profile deleted. Refresh to restart.")
        st.stop()

def show_quiz():
    user = st.session_state.user
    state = st.session_state.quiz_state

    if not state["word"]:
        state["word"], state["correct"], state["options"] = get_question()

    st.header(f"Word: **{state['word']}**")
    for opt in state["options"]:
        if st.button(opt, disabled=state["answered"]):
            correct = opt == state["correct"]
            feedback = award_xp(correct)
            update_cooldowns(state["word"], correct)
            user["rank"] = get_rank(user["xp"])
            user["history"].append({
                "word": state["word"],
                "selected": opt,
                "correct": state["correct"],
                "result": "✅" if correct else "❌",
                "time": datetime.now().strftime("%H:%M:%S"),
            })
            save_json(st.session_state.user_file, user)
            state["answered"] = True
            state["feedback"] = feedback
            st.rerun()

    if state["answered"]:
        st.success(state["feedback"])
        if st.button("➡️ Next"):
            st.session_state.quiz_state = {"word": None, "correct": None, "options": [], "answered": False, "feedback": ""}
            st.rerun()

    if st.button("🏠 Back to Home"):
        st.session_state.mode = "home"
        save_json(st.session_state.user_file, user)
        st.rerun()

# ---------------- MAIN APP ----------------
if "mode" in st.session_state:
    if st.session_state.mode == "home":
        show_home()
    elif st.session_state.mode == "quiz":
        show_quiz()