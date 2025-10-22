import tkinter as tk
import json
import os
import random
from datetime import datetime

# ---------- Constants ----------
VOCAB_FILE = "words.json"
USER_FOLDER = "users"
BASE_POOL_SIZE = 20

# ---------- Load Vocab ----------
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
    return [file[:-5] for file in os.listdir(USER_FOLDER) if file.endswith(".json")]

def load_user(username):
    user_file = get_user_file(username)
    if not os.path.exists(user_file):
        return {"username": username, "xp": 0, "history": [], "words": {}, "active_pool": []}
    with open(user_file, "r") as f:
        return json.load(f)

def save_user(data):
    with open(get_user_file(data["username"]), "w") as f:
        json.dump(data, f, indent=4)

# ---------- Active Pool Logic ----------
def update_active_pool(user_data):
    xp = user_data.get("xp", 0)
    rank = max(1, xp // 100 + 1)
    pool_size = BASE_POOL_SIZE + (rank - 1) * 5
    pool_size = min(pool_size, len(vocab))

    active_words = user_data.get("active_pool", [])

    if len(active_words) < pool_size:
        unused = [w for w in vocab if w not in active_words]
        random.shuffle(unused)
        active_words += unused[:pool_size - len(active_words)]

    if len(active_words) > pool_size:
        active_words = active_words[:pool_size]

    user_data["active_pool"] = active_words

    for word in active_words:
        if word not in user_data["words"]:
            user_data["words"][word] = {
                "priority": 50,
                "true_priority": 50,
                "cooldown": 0,
                "correct": 0,
                "wrong": 0
            }

# ---------- Quiz Engine ----------
def reduce_cooldowns(user_data):
    for stats in user_data["words"].values():
        if stats["cooldown"] > 0:
            stats["cooldown"] -= 1
            if stats["cooldown"] == 0:
                stats["priority"] = stats["true_priority"]

def generate_quiz_words(user_data):
    pool = user_data["active_pool"]
    eligible = [w for w in pool if user_data["words"][w]["cooldown"] == 0]

    high = [w for w in eligible if user_data["words"][w]["priority"] >= 30]
    low = [w for w in eligible if user_data["words"][w]["priority"] < 30]

    selected = []
    num_high = min(8, len(high))
    num_low = min(2, len(low))

    selected += random.sample(high, num_high)
    selected += random.sample(low, num_low)
    random.shuffle(selected)

    return selected

def handle_answer(user_data, word, correct):
    stats = user_data["words"][word]
    if correct:
        stats["correct"] += 1
        stats["true_priority"] = max(10, stats["true_priority"] - 5)
    else:
        stats["wrong"] += 1
        stats["true_priority"] = min(100, stats["true_priority"] + 10)
    stats["priority"] = 10
    stats["cooldown"] = 2

# ---------- GUI ----------
root = tk.Tk()
root.title("Lexibox")
root.geometry("800x600")
root.configure(bg="black")

frames = {}
for name in ["profile", "menu", "quiz", "history"]:
    frames[name] = tk.Frame(root, bg="black")
    frames[name].grid(row=0, column=0, sticky="nsew")

player_name = ""
user_data = {}
quiz_words = []
current_word = ""
xp = 0
quiz_session = []
streak = 0
streak_label = None

def switch_frame(name):
    for f in frames.values():
        f.grid_forget()
    frames[name].grid(row=0, column=0, sticky="nsew")

def show_profile_screen():
    switch_frame("profile")
    frame = frames["profile"]
    for w in frame.winfo_children(): w.destroy()

    users = get_users()
    if users:
        tk.Label(frame, text="Select Profile", fg="white", bg="black", font=("Helvetica", 24)).pack(pady=20)
        selected = tk.StringVar(value=users[0])
        tk.OptionMenu(frame, selected, *users).pack()
        tk.Button(frame, text="Continue", command=lambda: load_profile(selected.get())).pack(pady=10)
        tk.Button(frame, text="❌ Delete", command=lambda: delete_profile(selected.get())).pack(pady=5)
    tk.Button(frame, text="Create New Profile", command=create_profile_screen).pack(pady=20)

def create_profile_screen():
    switch_frame("profile")
    frame = frames["profile"]
    for w in frame.winfo_children(): w.destroy()

    tk.Label(frame, text="New Profile Name", fg="white", bg="black", font=("Helvetica", 20)).pack(pady=20)
    entry = tk.Entry(frame, font=("Helvetica", 16))
    entry.pack(pady=10)

    def create():
        name = entry.get().strip()
        if not name: return
        data = {"username": name, "xp": 0, "history": [], "words": {}, "active_pool": []}
        save_user(data)
        load_profile(name)

    tk.Button(frame, text="Create", command=create).pack(pady=10)

def delete_profile(name):
    os.remove(get_user_file(name))
    show_profile_screen()

def load_profile(name):
    global player_name, user_data, xp
    player_name = name
    user_data = load_user(name)
    xp = user_data.get("xp", 0)
    update_active_pool(user_data)
    save_user(user_data)
    show_menu()

def show_menu():
    switch_frame("menu")
    frame = frames["menu"]
    for w in frame.winfo_children(): w.destroy()

    tk.Label(frame, text=f"👤 {player_name}", fg="white", bg="black", font=("Helvetica", 24)).pack(pady=30)
    tk.Label(frame, text=f"XP: {xp}", fg="gold", bg="black", font=("Helvetica", 18)).pack(pady=10)
    tk.Button(frame, text="▶ Start Quiz", command=start_quiz).pack(pady=10)
    tk.Button(frame, text="📜 History", command=show_history).pack(pady=10)
    tk.Button(frame, text="🔄 Switch Profile", command=show_profile_screen).pack(pady=10)

def start_quiz():
    global quiz_words, current_word, quiz_session, streak
    reduce_cooldowns(user_data)
    update_active_pool(user_data)
    quiz_words = generate_quiz_words(user_data)
    quiz_session = []
    streak = 0
    if not quiz_words:
        switch_frame("quiz")
        frame = frames["quiz"]
        for w in frame.winfo_children(): w.destroy()
        tk.Label(frame, text="🛑 No words available!", fg="red", bg="black", font=("Helvetica", 24)).pack(pady=30)
        tk.Button(frame, text="⬅ Back", command=show_menu).pack(pady=10)
        return
    ask_question()

def ask_question():
    global current_word, streak_label
    switch_frame("quiz")
    frame = frames["quiz"]
    for w in frame.winfo_children(): w.destroy()

    if not quiz_words:
        end_quiz()
        return

    current_word = quiz_words.pop()
    correct_meaning = vocab[current_word]
    options = [correct_meaning] + random.sample([v for k, v in vocab.items() if v != correct_meaning], 3)
    random.shuffle(options)

    tk.Label(frame, text=f"What does '{current_word}' mean?", fg="white", bg="black", font=("Helvetica", 20)).pack(pady=20)
    for opt in options:
        tk.Button(frame, text=opt, width=60, command=lambda o=opt: submit_answer(o == correct_meaning, o)).pack(pady=5)

    streak_label = tk.Label(frame, text="", fg="lightgreen", bg="black", font=("Helvetica", 16))
    streak_label.pack(pady=10)

def submit_answer(is_correct, selected_option):
    global xp, streak
    handle_answer(user_data, current_word, is_correct)

    if is_correct:
        streak += 1
        bonus = 0
        msg = ""
        if streak == 3:
            bonus, msg = 5, "You're getting the hang of it!"
        elif streak == 4:
            bonus, msg = 10, "🔥 You're on fire!"
        elif streak >= 5:
            bonus, msg = 15, "💥 You're a beast!"

        xp += 10 + bonus
        if streak_label:
            streak_label.config(text=msg)
    else:
        streak = 0
        xp -= 5
        if streak_label:
            streak_label.config(text="")

    user_data["xp"] = max(0, xp)
    quiz_session.append({
        "word": current_word,
        "your_answer": selected_option,
        "correct_answer": vocab[current_word],
        "correct": is_correct
    })
    ask_question()

def end_quiz():
    user_data["history"].append({
        "timestamp": datetime.now().isoformat(),
        "quiz": quiz_session
    })
    save_user(user_data)
    show_menu()

def show_history():
    switch_frame("history")
    frame = frames["history"]
    for w in frame.winfo_children(): w.destroy()

    tk.Label(frame, text="📜 Quiz History", fg="white", bg="black", font=("Helvetica", 24)).pack(pady=20)
    history = user_data.get("history", [])[-5:]

    for h in reversed(history):
        tk.Label(frame, text=h["timestamp"], fg="gray", bg="black", font=("Helvetica", 14)).pack()
        for q in h.get("quiz", []):
            status = "✅" if q["correct"] else "❌"
            line = f"{status} {q['word']} → You: {q['your_answer']} | Correct: {q['correct_answer']}"
            tk.Label(frame, text=line, fg="white", bg="black", font=("Helvetica", 10), wraplength=700, justify="left").pack()

    tk.Button(frame, text="⬅ Back", command=show_menu).pack(pady=20)

# ---------- Start ----------
show_profile_screen()
root.mainloop()