import streamlit as st
import json
import os
import random
from datetime import datetime

# ---------- Constants ----------
VOCAB_FILE = "words.json"
USER_FOLDER = "users"
BASE_POOL_SIZE = 20

# ---------- Ensure folders ----------
os.makedirs(USER_FOLDER, exist_ok=True)

# ---------- Load vocab ----------
def load_vocab():
    if not os.path.exists(VOCAB_FILE):
        return {}
    with open(VOCAB_FILE, "r") as f:
        return json.load(f)

vocab = load_vocab()

# ---------- User utilities ----------
def get_user_file(username):
    return os.path.join(USER_FOLDER, f"{username}.json")

def load_user(username):
    path = get_user_file(username)
    if not os.path.exists(path):
        return {"username": username, "xp": 0, "history": [], "words": {}, "active_pool": []}
    with open(path, "r") as f:
        return json.load(f)

def save_user(user_data):
    with open(get_user_file(user_data["username"]), "w") as f:
        json.dump(user_data, f, indent=4)

def get_users():
    return [f[:-5] for f in os.listdir(USER_FOLDER) if f.endswith(".json")]

# ---------- XP + Rank ----------
def get_rank(xp):
    return xp // 200 + 1

def get_pool_size(xp):
    return BASE_POOL_SIZE + (get_rank(xp) - 1) * 5

# ---------- Streak Bonus ----------
def get_streak_bonus(streak):
    if streak == 3:
        return 5, "🔥 You're on fire!"
    elif streak == 4:
        return 10, "⚡ Unstoppable!"
    elif streak >= 5:
        return 15, "💀 God mode!"
    return 0, ""

# ---------- Session state setup ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "mode" not in st.session_state:
    st.session_state.mode = None
if "quiz_words" not in st.session_state:
    st.session_state.quiz_words = []
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None
if "options" not in st.session_state:
    st.session_state.options = []
if "current_word" not in st.session_state:
    st.session_state.current_word = None

# ---------- UI ----------
st.set_page_config(page_title="Lexibox", page_icon="📘", layout="centered")
st.title("📘 Lexibox")

# ---------- Profile Selection ----------
if st.session_state.user is None:
    st.subheader("Select or Create Profile")
    users = get_users()

    if users:
        selected = st.selectbox("Existing Profiles", users)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Continue"):
                st.session_state.user = load_user(selected)
                st.session_state.mode = None
                st.session_state.question_index = 0
                st.session_state.streak = 0
                st.session_state.quiz_words = []
                st.session_state.selected_answer = None
                st.session_state.options = []
                st.session_state.current_word = None
                st.rerun()
        with col2:
            if st.button("❌ Delete Profile"):
                os.remove(get_user_file(selected))
                st.rerun()

    st.write("or create a new profile:")
    new_name = st.text_input("Enter new username")
    if st.button("Create Profile"):
        if new_name.strip():
            st.session_state.user = {"username": new_name.strip(), "xp": 0, "history": [], "words": {}, "active_pool": []}
            save_user(st.session_state.user)
            st.session_state.mode = None
            st.session_state.question_index = 0
            st.session_state.streak = 0
            st.session_state.quiz_words = []
            st.session_state.selected_answer = None
            st.session_state.options = []
            st.session_state.current_word = None
            st.rerun()
    st.stop()

# ---------- Home ----------
user = st.session_state.user
xp = user["xp"]
rank = get_rank(xp)
progress = min((xp % 200) / 200, 1)

st.subheader(f"👤 {user['username']}")
st.progress(progress)
st.caption(f"XP: {xp} | Rank: {rank}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("▶ Start Quiz"):
        st.session_state.mode = "quiz"
        st.session_state.streak = 0
        st.session_state.question_index = 0
        pool_size = get_pool_size(user["xp"])
        active_words = user.get("active_pool", [])
        if not active_words:
            active_words = random.sample(list(vocab.keys()), min(pool_size, len(vocab)))
            user["active_pool"] = active_words
            save_user(user)
        st.session_state.quiz_words = random.sample(active_words, min(10, len(active_words)))
        st.session_state.selected_answer = None
        st.session_state.options = []
        st.session_state.current_word = None
        st.rerun()
with col2:
    if st.button("🧠 Practice Mode"):
        st.session_state.mode = "practice"
        st.session_state.streak = 0
        st.session_state.question_index = 0
        active_words = user.get("active_pool", [])
        if not active_words:
            active_words = random.sample(list(vocab.keys()), min(get_pool_size(user["xp"]), len(vocab)))
            user["active_pool"] = active_words
            save_user(user)
        mistakes = [h["word"] for h in user.get("history", []) if h["result"]=="Wrong" and h["word"] in active_words]
        st.session_state.quiz_words = list(set(mistakes)) if mistakes else random.sample(active_words, min(10, len(active_words)))
        st.session_state.selected_answer = None
        st.session_state.options = []
        st.session_state.current_word = None
        st.rerun()
with col3:
    if st.button("📜 History"):
        st.session_state.mode = "history"
        st.rerun()
with col4:
    if st.button("🗣 Give Feedback"):
        st.markdown("[Click here to fill feedback form](https://docs.google.com/forms/d/e/1FAIpQLScLoWb9xACa7Cvj5kD26updKZhr4qMRGUW_EVIjmpPcfIlcvg/viewform?usp=publish-editor)")

# ---------- Back to Home Button ----------
if st.session_state.mode in ["quiz", "practice", "history"]:
    if st.button("⬅ Back to Home"):
        st.session_state.mode = None
        st.session_state.question_index = 0
        st.session_state.streak = 0
        st.session_state.selected_answer = None
        st.session_state.options = []
        st.session_state.current_word = None
        st.rerun()

# ---------- Quiz / Practice ----------
if st.session_state.mode in ["quiz", "practice"]:
    mode = st.session_state.mode
    st.subheader("Practice Mode (XP unaffected)" if mode=="practice" else "Quiz Mode")

    if st.session_state.question_index >= len(st.session_state.quiz_words):
        st.success("🎉 Session Complete!")
        st.stop()

    word = st.session_state.quiz_words[st.session_state.question_index]
    correct = vocab[word]

    # --- Stable options ---
    if st.session_state.current_word != word:
        options = [correct] + random.sample([v for k,v in vocab.items() if v != correct], min(3, len(vocab)-1))
        random.shuffle(options)
        st.session_state.options = options
        st.session_state.current_word = word

    options = st.session_state.options

    # --- Radio buttons ---
    st.session_state.selected_answer = st.radio(f"### What is the meaning of '{word}'?", options, 
        index=options.index(st.session_state.selected_answer) if st.session_state.selected_answer in options else 0)
    
    if st.button("Submit Answer"):
        selected = st.session_state.selected_answer
        correct_answer = (selected == correct)
        gained = 10 if correct_answer else -5
        msg = ""

        if correct_answer:
            st.session_state.streak +=1
            bonus, msg = get_streak_bonus(st.session_state.streak)
            gained += bonus
        else:
            st.session_state.streak =0

        if mode=="quiz":
            user["xp"] = max(0, user["xp"] + gained)

        user["history"].append({
            "word": word,
            "selected": selected,
            "correct": correct,
            "result": "Correct" if correct_answer else "Wrong",
            "xp_gained": gained if mode=="quiz" else 0,
            "mode": mode,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        save_user(user)
        st.session_state.question_index +=1
        st.session_state.selected_answer = None
        st.session_state.options = []
        st.session_state.current_word = None
        if correct_answer:
            st.success(f"✅ Correct! +{gained} XP" if mode=="quiz" else "✅ Correct!")
        else:
            st.error(f"❌ Wrong! Correct answer: {correct}")
        if msg:
            st.info(msg)
        st.rerun()

# ---------- History ----------
elif st.session_state.mode=="history":
    st.subheader("📜 Quiz History (last 30)")
    history = user.get("history", [])[-30:]
    if not history:
        st.write("No history yet.")
    else:
        for h in reversed(history):
            status = "✅" if h["result"]=="Correct" else "❌"
            st.write(f"{status} **{h['word']}** | You: {h['selected']} | Correct: {h['correct']} | XP: {h['xp_gained']} | Mode: {h['mode']} | {h['time']}")