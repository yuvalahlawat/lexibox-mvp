import streamlit as st
import json
import random
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# ---------- Firebase Setup ----------
if not firebase_admin._apps:
    firebase_key = st.secrets["FIREBASE"]
    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------- Constants ----------
VOCAB_FILE = "words.json"
BASE_POOL_SIZE = 20

# ---------- Load Vocabulary ----------
def load_vocab():
    try:
        with open(VOCAB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

vocab = load_vocab()

# ---------- Firestore Utilities ----------
def get_user_ref(username):
    return db.collection("users").document(username)

def load_user(username):
    doc = get_user_ref(username).get()
    if doc.exists:
        return doc.to_dict()
    else:
        data = {"username": username, "xp": 0, "history": [], "words": {}, "active_pool": []}
        save_user(data)
        return data

def save_user(data):
    get_user_ref(data["username"]).set(data)

def delete_user(username):
    get_user_ref(username).delete()

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

# ---------- Streamlit App ----------
st.set_page_config(page_title="Lexibox", page_icon="🧠", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "profile"
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = {}

# ---------- Profile Screen ----------
def show_profile_screen():
    st.title("Lexibox 🧠")
    st.header("Select or Create Profile")

    usernames = [doc.id for doc in db.collection("users").stream()]
    if usernames:
        selected = st.selectbox("Choose a profile", usernames)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Continue ▶"):
                st.session_state.current_user = load_user(selected)
                st.session_state.page = "home"
        with col2:
            if st.button("❌ Delete"):
                delete_user(selected)
                st.success(f"Deleted profile: {selected}")
                st.rerun()
    st.divider()
    new_name = st.text_input("Or create new profile:")
    if st.button("Create Profile"):
        if new_name.strip():
            save_user({"username": new_name.strip(), "xp": 0, "history": [], "words": {}, "active_pool": []})
            st.session_state.current_user = load_user(new_name.strip())
            st.session_state.page = "home"
            st.rerun()

# ---------- Home Screen ----------
def show_home():
    user = st.session_state.current_user
    xp = user["xp"]
    rank = get_rank(xp)
    st.title(f"👤 {user['username']}")
    st.subheader(f"XP: {xp} | Rank: {rank}")
    st.progress(min((xp % 200) / 200, 1))
    st.divider()
    if st.button("▶ Start Quiz"):
        start_quiz("quiz")
    if st.button("🧩 Practice Weak Words"):
        start_quiz("practice")
    if st.button("📜 View History"):
        st.session_state.page = "history"
    if st.button("🔄 Switch Profile"):
        st.session_state.page = "profile"

# ---------- Quiz Logic ----------
def start_quiz(mode):
    vocab_keys = list(vocab.keys())
    if not vocab_keys:
        st.warning("No words available!")
        return

    user = st.session_state.current_user
    xp = user["xp"]
    pool_size = get_pool_size(xp)
    active_pool = vocab_keys[:pool_size]

    if mode == "practice":
        weak_words = [h["word"] for h in user["history"] if h["result"] == "Wrong"]
        quiz_words = list(set([w for w in weak_words if w in active_pool]))[:10]
        if not quiz_words:
            st.info("No weak words to practice right now. Do a normal quiz first.")
            return
    else:
        quiz_words = random.sample(active_pool, min(10, len(active_pool)))

    st.session_state.quiz_state = {
        "mode": mode,
        "words": quiz_words,
        "index": 0,
        "streak": 0,
    }
    st.session_state.page = "quiz"

def show_quiz():
    state = st.session_state.quiz_state
    user = st.session_state.current_user
    words = state["words"]
    index = state["index"]

    if index >= len(words):
        st.success("🎉 Quiz Finished!")
        if st.button("🏠 Back to Home"):
            st.session_state.page = "home"
        return

    word = words[index]
    correct = vocab[word]
    options = [correct] + random.sample([v for v in vocab.values() if v != correct], 3)
    random.shuffle(options)

    st.header(f"Q{index+1}: What is the meaning of '{word}'?")
    choice = st.radio("Choose one:", options, index=None)

    if st.button("Submit Answer"):
        correct_flag = (choice == correct)
        xp_change = 10 if correct_flag else -5
        if correct_flag:
            state["streak"] += 1
        else:
            state["streak"] = 0
        bonus, msg = get_streak_bonus(state["streak"])
        xp_change += bonus

        if state["mode"] == "quiz":
            user["xp"] = max(0, user["xp"] + xp_change)
        else:
            xp_change = 0  # practice mode gives no XP

        user["history"].append({
            "word": word,
            "selected": choice,
            "correct": correct,
            "result": "Correct" if correct_flag else "Wrong",
            "xp_gained": xp_change,
            "mode": state["mode"],
            "time": datetime.now().strftime("%H:%M:%S")
        })
        save_user(user)

        if msg:
            st.info(msg)
        st.write(f"✅ Correct answer: **{correct}**")
        st.write(f"XP change: {xp_change}")
        if st.button("Next Question ➡️"):
            state["index"] += 1
            st.rerun()
        st.button("🏠 Back to Home", on_click=lambda: st.session_state.update(page="home"))
        return

    st.button("🏠 Back to Home", on_click=lambda: st.session_state.update(page="home"))

# ---------- History Screen ----------
def show_history():
    st.title("📜 Quiz History")
    user = st.session_state.current_user
    history = user.get("history", [])[-30:]
    for h in reversed(history):
        status = "✅" if h["result"] == "Correct" else "❌"
        st.write(f"{status} **{h['word']}** | You: {h['selected']} | Correct: {h['correct']} | XP: {h['xp_gained']} | Mode: {h['mode']} | {h['time']}")
    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"

# ---------- Navigation ----------
if st.session_state.page == "profile":
    show_profile_screen()
elif st.session_state.page == "home":
    show_home()
elif st.session_state.page == "quiz":
    show_quiz()
elif st.session_state.page == "history":
    show_history()