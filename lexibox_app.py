import streamlit as st
import random
import json
import firebase_admin
from firebase_admin import credentials, firestore

# ---------- FIREBASE INIT ----------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------- LOAD WORDS ----------
with open("words.json", "r") as f:
    VOCAB = json.load(f)

# ---------- SESSION STATE ----------
defaults = {
    "page": "home",
    "index": 0,
    "score": 0,
    "xp": 0,
    "streak": 0,
    "questions": [],
    "answered": False,
    "user": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- FIREBASE HELPERS ----------
def load_user(uid):
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    else:
        db.collection("users").document(uid).set({
            "xp": 0,
            "streak": 0,
            "total_answered": 0
        })
        return {"xp": 0, "streak": 0, "total_answered": 0}

def save_user(uid, data):
    db.collection("users").document(uid).set(data, merge=True)

def delete_user(uid):
    db.collection("users").document(uid).delete()
    st.session_state.clear()
    st.rerun()

# ---------- XP & STREAK ----------
def calculate_bonus(streak):
    if streak >= 5:
        return 15, "🔥 You're unstoppable!"
    elif streak == 4:
        return 10, "⚡ On a roll!"
    elif streak == 3:
        return 5, "🔥 You’re on fire!"
    else:
        return 0, ""

# ---------- HOME PAGE ----------
def show_home():
    st.title("🏠 Lexibox")
    st.subheader("Expand your vocabulary. One word at a time.")
    username = st.text_input("Enter your username to start:")
    if st.button("Start Quiz ▶️"):
        if username.strip() == "":
            st.warning("Please enter a valid username.")
        else:
            st.session_state.user = username.strip()
            user_data = load_user(username)
            st.session_state.xp = user_data["xp"]
            st.session_state.streak = user_data["streak"]
            st.session_state.page = "quiz"
            reset_quiz()
            st.rerun()

    if st.session_state.user:
        if st.button("🗑️ Delete Profile"):
            delete_user(st.session_state.user)

# ---------- RESET QUIZ ----------
def reset_quiz():
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.questions = random.sample(list(VOCAB.items()), 5)
    st.session_state.answered = False

# ---------- QUIZ PAGE ----------
def show_quiz():
    st.title("🧠 Lexibox Quiz")

    st.write(f"**User:** {st.session_state.user}")
    st.write(f"**XP:** {st.session_state.xp} | **Streak:** {st.session_state.streak}")

    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    if st.session_state.index < len(st.session_state.questions):
        word, data = st.session_state.questions[st.session_state.index]
        options = data["options"]
        correct = data["answer"]

        st.subheader(f"Word {st.session_state.index + 1}: {word}")

        if not st.session_state.answered:
            for opt in options:
                if st.button(opt):
                    st.session_state.answered = True
                    st.session_state.index_answer = opt
                    if opt == correct:
                        st.session_state.score += 1
                        st.session_state.streak += 1
                        base_xp = 10
                        bonus, msg = calculate_bonus(st.session_state.streak)
                        gained = base_xp + bonus
                        st.session_state.xp += gained
                        st.success(f"✅ Correct! +{gained} XP {msg}")
                    else:
                        st.session_state.streak = 0
                        st.error(f"❌ Wrong! Correct answer: {correct}")
                    save_user(st.session_state.user, {
                        "xp": st.session_state.xp,
                        "streak": st.session_state.streak,
                        "total_answered": firestore.Increment(1)
                    })
                    st.rerun()
        else:
            if st.button("Next ➡️"):
                st.session_state.index += 1
                st.session_state.answered = False
                st.rerun()

    else:
        st.header("🎯 Quiz Complete!")
        st.write(f"Your Score: {st.session_state.score}/{len(st.session_state.questions)}")
        if st.button("Restart 🔁"):
            reset_quiz()
            st.rerun()

# ---------- ROUTER ----------
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "quiz":
    show_quiz()