import streamlit as st
import random
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------- Firebase Setup ----------------
firebase_key = dict(st.secrets["FIREBASE"])

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------- Utility Functions ----------------
def get_user_data(username):
    doc = db.collection("users").document(username).get()
    if doc.exists:
        return doc.to_dict()
    else:
        data = {"xp": 0, "words_learned": [], "quiz_history": []}
        db.collection("users").document(username).set(data)
        return data

def save_user_data(username, data):
    db.collection("users").document(username).set(data)

def delete_profile(username):
    db.collection("users").document(username).delete()

# ---------------- Word Bank (You can replace this) ----------------
WORDS = {
    "eloquent": "fluent or persuasive in speaking or writing",
    "benevolent": "well meaning and kindly",
    "candid": "truthful and straightforward",
    "meticulous": "showing great attention to detail",
    "vigilant": "keeping careful watch for danger or difficulties",
    "lucid": "expressed clearly; easy to understand",
    "transient": "lasting only for a short time",
    "audacious": "showing a willingness to take bold risks",
    "innate": "inborn; natural",
    "arduous": "involving or requiring strenuous effort"
}

# ---------------- Quiz Logic ----------------
def quiz(username):
    st.subheader(f"🔥 Lexibox Quiz for {username}")
    user_data = get_user_data(username)
    xp = user_data["xp"]

    words = list(WORDS.items())
    random.shuffle(words)
    score = 0

    for word, meaning in words:
        st.write(f"### What is the meaning of **{word}**?")
        options = [meaning] + random.sample([m for w, m in WORDS.items() if m != meaning], 3)
        random.shuffle(options)

        answer = st.radio("Choose an option:", options, key=word)
        if st.button("Submit", key=f"submit_{word}"):
            if answer == meaning:
                st.success("✅ Correct!")
                xp += 10
                score += 1
            else:
                st.error(f"❌ Incorrect! The correct answer is: {meaning}")

            user_data["xp"] = xp
            user_data["quiz_history"].append({
                "word": word,
                "selected": answer,
                "correct": meaning,
                "result": answer == meaning
            })
            save_user_data(username, user_data)

    st.write(f"### 🧠 Quiz Complete! Your score: {score}/{len(words)}")
    st.write(f"### ⭐ Total XP: {xp}")

    if st.button("💾 Force Save Progress"):
        save_user_data(username, user_data)
        st.success("Progress saved successfully!")

    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"

# ---------------- Profile Page ----------------
def profile(username):
    user_data = get_user_data(username)
    st.title(f"👤 {username}'s Profile")
    st.write(f"**XP:** {user_data['xp']}")
    st.write(f"**Words Learned:** {len(user_data['words_learned'])}")
    st.write(f"**Quiz Attempts:** {len(user_data['quiz_history'])}")

    if st.button("🗑️ Delete Profile"):
        delete_profile(username)
        st.success("Profile deleted successfully!")
        st.session_state.page = "login"

    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"

# ---------------- Home Page ----------------
def home(username):
    st.title("📚 Welcome to Lexibox!")
    st.write(f"Hello, **{username}**! Ready to learn some new words?")

    if st.button("🚀 Start Quiz"):
        st.session_state.page = "quiz"

    if st.button("👤 View Profile"):
        st.session_state.page = "profile"

# ---------------- Login Page ----------------
def login():
    st.title("🔐 Lexibox Login")
    username = st.text_input("Enter your username:")
    if st.button("Login"):
        if username.strip():
            st.session_state.username = username.strip()
            st.session_state.page = "home"
        else:
            st.warning("Please enter a valid username.")

# ---------------- Page Controller ----------------
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login()
elif st.session_state.page == "home":
    home(st.session_state.username)
elif st.session_state.page == "quiz":
    quiz(st.session_state.username)
elif st.session_state.page == "profile":
    profile(st.session_state.username)