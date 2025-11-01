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
    st.subheader("📘 Lexibox Quiz")

    words_ref = db.collection("words").stream()
    questions = []

    # Load all words safely
    for doc in words_ref:
        data = doc.to_dict()
        if "definition" not in data or "word" not in data:
            continue  # skip invalid entries

        # If options don't exist, auto-generate them
        if "options" not in data or not isinstance(data["options"], list) or len(data["options"]) < 2:
            # Grab random distractors from other words
            all_words = [d.id for d in db.collection("words").list_documents() if d.id != doc.id]
            random.shuffle(all_words)
            distractors = all_words[:3]
            options = [doc.id] + distractors
            random.shuffle(options)
        else:
            options = data["options"]

        questions.append({
            "word": doc.id,
            "definition": data["definition"],
            "options": options,
            "correct": data.get("correct", doc.id)
        })

    if not questions:
        st.error("No valid quiz data found in Firestore.")
        return

    # Quiz state
    if "q_index" not in st.session_state:
        st.session_state.q_index = 0
        st.session_state.score = 0

    q_index = st.session_state.q_index
    if q_index >= len(questions):
        st.success(f"✅ Quiz complete! You scored {st.session_state.score}/{len(questions)}")
        if st.button("Restart Quiz"):
            st.session_state.q_index = 0
            st.session_state.score = 0
        return

    q = questions[q_index]
    st.write(f"**Definition:** {q['definition']}")

    choice = st.radio("Choose the correct word:", q["options"], key=f"q{q_index}")

    if st.button("Submit", key=f"submit{q_index}"):
        if choice == q["correct"]:
            st.success("✅ Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Incorrect. The correct answer is: {q['correct']}")
        st.session_state.q_index += 1
        st.experimental_rerun()

# ---------- ROUTER ----------
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "quiz":
    show_quiz()