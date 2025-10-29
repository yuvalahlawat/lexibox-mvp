# lexibox_app.py
import streamlit as st
import random
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# ---------- Firebase Setup ----------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")  # Replace with your Firebase key
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------- Constants ----------
MAX_QUESTIONS = 10

# ---------- Sample Vocabulary ----------
vocab = {
    "Aberration": "A departure from what is normal",
    "Capitulate": "Cease to resist an opponent",
    "Debacle": "A sudden failure",
    "Enervate": "Cause someone to feel drained",
    "Fervent": "Having passionate intensity",
    "Garrulous": "Excessively talkative",
    "Harangue": "A lengthy and aggressive speech",
    "Impetuous": "Acting quickly without thought",
    "Juxtapose": "Place side by side for contrast",
    "Knavery": "Dishonest or unscrupulous behavior"
}

# ---------- Helper Functions ----------
def get_rank(xp):
    return xp // 200 + 1

def get_streak_bonus(streak):
    if streak == 3:
        return 5, "🔥 You're on fire!"
    elif streak == 4:
        return 10, "⚡ Unstoppable!"
    elif streak >= 5:
        return 15, "💀 God mode!"
    return 0, ""

# ---------- Firebase Functions ----------
def save_user(user_data):
    db.collection("users").document(user_data["username"]).set(user_data)

def load_user(username):
    doc_ref = db.collection("users").document(username)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {"username": username, "xp": 0, "history": [], "words": {}}

# ---------- Session State Initialization ----------
state_vars = ["current_user", "quiz_words", "question_index", "streak",
              "mode", "selected_option", "answer_submitted"]
for var in state_vars:
    if var not in st.session_state:
        if var == "mode":
            st.session_state[var] = "normal"
        else:
            st.session_state[var] = None

# ---------- UI Functions ----------
def show_profile_screen():
    st.title("Lexibox - Select Profile")
    usernames = [doc.id for doc in db.collection("users").stream()]
    
    selected = st.selectbox("Choose Profile", options=usernames if usernames else [""])
    new_user_name = st.text_input("Or create new username")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load Profile"):
            if selected:
                st.session_state.current_user = load_user(selected)
                st.session_state.mode = "normal"
                reset_quiz_state()
    with col2:
        if new_user_name and st.button("Create New Profile"):
            st.session_state.current_user = {
                "username": new_user_name,
                "xp": 0,
                "history": [],
                "words": {}
            }
            save_user(st.session_state.current_user)
            st.session_state.mode = "normal"
            reset_quiz_state()

def reset_quiz_state():
    st.session_state.quiz_words = []
    st.session_state.question_index = 0
    st.session_state.streak = 0
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    # Clear stored options
    for key in list(st.session_state.keys()):
        if key.startswith("options_"):
            del st.session_state[key]

def show_home():
    user = st.session_state.current_user
    st.title(f"👤 {user['username']}")
    st.write(f"XP: {user['xp']} | Rank: {get_rank(user['xp'])}")
    st.progress(min((user["xp"] % 200)/200, 1))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ Start Quiz"):
            start_quiz("normal")
    with col2:
        if st.button("📝 Practice Mode"):
            start_quiz("practice")
    with col3:
        if st.button("📜 History"):
            show_history()
    
    if st.button("🔄 Switch Profile"):
        st.session_state.current_user = None
    if st.button("💾 Force Save User"):
        save_user(user)
        st.success(f"Saved {user['username']} to Firestore!")

def start_quiz(mode="normal"):
    user = st.session_state.current_user
    st.session_state.mode = mode
    reset_quiz_state()
    
    all_words = list(vocab.keys())
    if mode == "practice":
        weak_words = [w for w, data in user.get("words", {}).items() if data.get("wrong_count", 0) >= 2]
        st.session_state.quiz_words = weak_words if weak_words else random.sample(all_words, min(MAX_QUESTIONS, len(all_words)))
    else:
        st.session_state.quiz_words = random.sample(all_words, min(MAX_QUESTIONS, len(all_words)))

def show_question():
    user = st.session_state.current_user
    idx = st.session_state.question_index
    
    if idx >= len(st.session_state.quiz_words):
        st.success("🎉 Quiz Finished!")
        save_user(user)
    else:
        word = st.session_state.quiz_words[idx]
        correct = vocab[word]

        # Persist options so they don’t reshuffle
        if f"options_{idx}" not in st.session_state:
            options = [correct] + random.sample([v for k,v in vocab.items() if v != correct], 3)
            random.shuffle(options)
            st.session_state[f"options_{idx}"] = options
        else:
            options = st.session_state[f"options_{idx}"]

        st.header(f"Question {idx+1}: What is the meaning of '{word}'?")

        # Answer selection
        if not st.session_state.answer_submitted:
            st.session_state.selected_option = st.radio("Select an option", options, key=f"radio_{idx}")
            if st.button("Submit Answer", key=f"submit_{idx}"):
                st.session_state.answer_submitted = True
                is_correct = st.session_state.selected_option == correct
                gained = 10 if is_correct else (-5 if st.session_state.mode=="normal" else 0)
                if is_correct:
                    st.session_state.streak +=1
                else:
                    st.session_state.streak = 0
                bonus, msg = get_streak_bonus(st.session_state.streak)
                gained += bonus
                if st.session_state.mode=="normal":
                    user["xp"] = max(0, user["xp"] + gained)
                if word not in user["words"]:
                    user["words"][word] = {"correct_count":0,"wrong_count":0}
                if is_correct:
                    user["words"][word]["correct_count"] +=1
                else:
                    user["words"][word]["wrong_count"] +=1
                user["history"].append({
                    "word": word,
                    "selected": st.session_state.selected_option,
                    "correct": correct,
                    "result":"Correct" if is_correct else "Wrong",
                    "xp_gained": gained,
                    "mode": st.session_state.mode,
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                save_user(user)
                if msg:
                    st.info(msg)
    
        else:
            # Feedback
            for opt in options:
                if opt == correct:
                    st.success(f"{opt} ✅ Correct Answer")
                elif opt == st.session_state.selected_option:
                    st.error(f"{opt} ❌ Your Choice")
                else:
                    st.write(opt)
            if st.button("Next Question", key=f"next_{idx}"):
                st.session_state.question_index += 1
                st.session_state.selected_option = None
                st.session_state.answer_submitted = False

    # ---------- Always Visible Buttons ----------
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Home", key="quiz_home"):
            reset_quiz_state()
            return
    with col2:
        if st.button("❌ Delete Profile", key="delete_profile_quiz"):
            db.collection("users").document(user["username"]).delete()
            st.session_state.current_user = None
            reset_quiz_state()
            return

def show_history():
    user = st.session_state.current_user
    st.title("📜 Quiz History")
    history = user.get("history", [])[-30:]
    for h in reversed(history):
        status = "✅" if h["result"]=="Correct" else "❌"
        st.write(f"{status} **{h['word']}** | You: {h['selected']} | Correct: {h['correct']} | XP: {h['xp_gained']} | Mode: {h['mode']} | {h['time']}")
    if st.button("Back to Home"):
        return

# ---------- Main ----------
if st.session_state.current_user is None:
    show_profile_screen()
else:
    show_home()
    if st.session_state.quiz_words:
        show_question()