import customtkinter as ctk
import json
import os
import random
from datetime import datetime

# ---------- Constants ----------
VOCAB_FILE = "words.json"
USER_FOLDER = "users"
BASE_POOL_SIZE = 20

# ---------- Vocab ----------
def load_vocab():
    if not os.path.exists(VOCAB_FILE):
        return {}
    with open(VOCAB_FILE, "r") as f:
        return json.load(f)

vocab = load_vocab()

# ---------- User Utilities ----------
def ensure_user_folder():
    if not os.path.exists(USER_FOLDER):
        os.makedirs(USER_FOLDER)

def get_user_file(username):
    return os.path.join(USER_FOLDER, f"{username}.json")

def get_users():
    ensure_user_folder()
    return [f[:-5] for f in os.listdir(USER_FOLDER) if f.endswith(".json")]

def load_user(username):
    path = get_user_file(username)
    if not os.path.exists(path):
        return {"username": username, "xp": 0, "history": [], "words": {}, "active_pool": []}
    with open(path, "r") as f:
        return json.load(f)

def save_user(user_data):
    with open(get_user_file(user_data["username"]), "w") as f:
        json.dump(user_data, f, indent=4)

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

# ---------- Weak Words ----------
def get_weak_words(user_data, vocab, active_pool, limit=20):
    words_info = user_data.get("words", {})
    # only consider words in active pool
    scored = sorted(
        [(w, info) for w, info in words_info.items() if w in active_pool],
        key=lambda x: (x[1].get("wrong_count", 0) - x[1].get("correct_count", 0)),
        reverse=True
    )
    weak_words = [w for w, _ in scored[:limit]]
    if not weak_words:
        weak_words = random.sample(active_pool, min(limit, len(active_pool)))
    return weak_words

# ---------- App ----------
class LexiboxApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lexibox")
        self.geometry("800x600")

        self.current_user = None
        self.quiz_words = []
        self.current_question = None
        self.current_answer = None
        self.streak = 0
        self.question_index = 0
        self.max_questions = 10
        self.is_practice = False

        self.show_profile_screen()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ---------- Profile ----------
    def show_profile_screen(self):
        self.clear()
        ctk.CTkLabel(self, text="Select Profile", font=("Arial", 24)).pack(pady=20)

        users = get_users()
        if users:
            selected = ctk.StringVar(value=users[0])
            ctk.CTkOptionMenu(self, variable=selected, values=users).pack(pady=10)
            ctk.CTkButton(self, text="Continue", command=lambda: self.load_profile(selected.get())).pack(pady=5)
            ctk.CTkButton(self, text="❌ Delete", command=lambda: self.delete_profile(selected.get())).pack(pady=5)

        ctk.CTkButton(self, text="Create New Profile", command=self.create_profile_screen).pack(pady=20)

    def create_profile_screen(self):
        self.clear()
        ctk.CTkLabel(self, text="New Profile Name", font=("Arial", 20)).pack(pady=20)
        entry = ctk.CTkEntry(self)
        entry.pack(pady=10)

        def create():
            name = entry.get().strip()
            if not name:
                return
            user_data = {"username": name, "xp": 0, "history": [], "words": {}, "active_pool": []}
            save_user(user_data)
            self.load_profile(name)

        ctk.CTkButton(self, text="Create", command=create).pack(pady=10)

    def delete_profile(self, name):
        os.remove(get_user_file(name))
        self.show_profile_screen()

    def load_profile(self, name):
        self.current_user = load_user(name)
        save_user(self.current_user)
        self.show_home()

    # ---------- Home ----------
    def show_home(self):
        self.clear()
        xp = self.current_user["xp"]
        rank = get_rank(xp)

        ctk.CTkLabel(self, text=f"👤 {self.current_user['username']}", font=("Arial", 24)).pack(pady=20)
        ctk.CTkLabel(self, text=f"XP: {xp} | Rank: {rank}", font=("Arial", 18)).pack(pady=10)

        progress = min((xp % 200) / 200, 1)
        xp_bar = ctk.CTkProgressBar(self, width=400)
        xp_bar.set(progress)
        xp_bar.pack(pady=5)

        ctk.CTkButton(self, text="▶ Start Quiz", command=self.start_quiz).pack(pady=10)
        ctk.CTkButton(self, text="🧩 Practice Mode", command=self.start_practice).pack(pady=10)
        ctk.CTkButton(self, text="📜 History", command=self.show_history).pack(pady=10)
        ctk.CTkButton(self, text="🔄 Switch Profile", command=self.show_profile_screen).pack(pady=10)

    # ---------- Quiz ----------
    def start_quiz(self):
        self.is_practice = False
        self.streak = 0
        self.question_index = 0
        pool_size = get_pool_size(self.current_user["xp"])
        all_words = list(vocab.keys())
        if not all_words:
            self.show_empty_message()
            return
        active_pool = random.sample(all_words, min(pool_size, len(all_words)))
        self.current_user["active_pool"] = active_pool
        save_user(self.current_user)
        self.quiz_words = random.sample(active_pool, min(self.max_questions, len(active_pool)))
        self.show_question()

    def start_practice(self):
        self.is_practice = True
        self.streak = 0
        self.question_index = 0
        active_pool = self.current_user.get("active_pool", [])
        if not active_pool:
            self.show_empty_message()
            return
        weak_words = get_weak_words(self.current_user, vocab, active_pool)
        self.quiz_words = weak_words
        self.show_question()

    def show_empty_message(self):
        self.clear()
        ctk.CTkLabel(self, text="No words available!", font=("Arial", 18)).pack(pady=20)
        ctk.CTkButton(self, text="Back to Home", command=self.show_home).pack(pady=10)

    def show_question(self):
        self.clear()
        if self.question_index >= len(self.quiz_words):
            ctk.CTkLabel(self, text="🎉 Session Finished!", font=("Arial", 18)).pack(pady=20)
            ctk.CTkButton(self, text="Back to Home", command=self.show_home).pack(pady=10)
            return

        word = self.quiz_words[self.question_index]
        correct = vocab[word]
        options = [correct] + random.sample([v for k, v in vocab.items() if v != correct], 3)
        random.shuffle(options)

        self.current_question = word
        self.current_answer = correct

        ctk.CTkLabel(self, text=f"What is the meaning of '{word}'?", font=("Arial", 16)).pack(pady=20)

        self.option_buttons = []
        for opt in options:
            btn = ctk.CTkButton(self, text=opt, command=lambda o=opt: self.check_answer(o))
            btn.pack(pady=5)
            self.option_buttons.append(btn)

        xp = self.current_user["xp"]
        rank = get_rank(xp)
        progress = min((xp % 200) / 200, 1)
        ctk.CTkLabel(self, text=f"XP: {xp} | Rank: {rank}").pack(pady=10)
        xp_bar = ctk.CTkProgressBar(self, width=400)
        xp_bar.set(progress)
        xp_bar.pack(pady=5)

        ctk.CTkButton(self, text="Back to Home", command=self.show_home).pack(pady=10)

    def check_answer(self, selected):
        for btn in self.option_buttons:
            if btn.cget("text") == self.current_answer:
                btn.configure(fg_color="green")
            elif btn.cget("text") == selected:
                btn.configure(fg_color="red")
            btn.configure(state="disabled")

        correct = (selected == self.current_answer)
        gained = 0 if self.is_practice else (10 if correct else -5)

        if not self.is_practice:
            if correct:
                self.streak += 1
            else:
                self.streak = 0
            bonus, msg = get_streak_bonus(self.streak)
            gained += bonus
            self.current_user["xp"] = max(0, self.current_user["xp"] + gained)
        else:
            bonus, msg = (0, "")

        # Update word stats
        word_data = self.current_user["words"].setdefault(self.current_question, {"correct_count": 0, "wrong_count": 0})
        if correct:
            word_data["correct_count"] += 1
        else:
            word_data["wrong_count"] += 1

        # Log history
        self.current_user["history"].append({
            "word": self.current_question,
            "selected": selected,
            "correct": self.current_answer,
            "result": "Correct" if correct else "Wrong",
            "xp_gained": gained,
            "streak": self.streak if not self.is_practice else 0,
            "time": datetime.now().strftime("%H:%M:%S"),
            "mode": "practice" if self.is_practice else "quiz"
        })
        save_user(self.current_user)

        if msg and not self.is_practice:
            ctk.CTkLabel(self, text=msg, text_color="orange").pack(pady=5)

        self.question_index += 1
        ctk.CTkButton(self, text="Next", command=self.show_question).pack(pady=10)

    # ---------- History ----------
    def show_history(self):
        self.clear()
        ctk.CTkLabel(self, text="📜 Quiz History", font=("Arial", 24)).pack(pady=20)

        footer_frame = ctk.CTkFrame(self, height=50)
        footer_frame.pack(fill="x", side="bottom", pady=5)
        ctk.CTkButton(footer_frame, text="Back to Home", command=self.show_home).pack(pady=5)

        frame = ctk.CTkScrollableFrame(self, width=700, height=450)
        frame.pack(pady=(0, 10), fill="both", expand=True)

        history = self.current_user.get("history", [])[-100:]
        for h in reversed(history):
            status = "✅" if h["result"] == "Correct" else "❌"
            mode = "(PRACTICE)" if h.get("mode") == "practice" else "(QUIZ)"
            line = f"{mode} {status} {h['word']} | You: {h['selected']} | Correct: {h['correct']} | XP: {h['xp_gained']} | {h['time']}"
            ctk.CTkLabel(frame, text=line, anchor="w", justify="left").pack(fill="x", pady=2)


# ---------- Run ----------
if __name__ == "__main__":
    app = LexiboxApp()
    app.mainloop()