import tkinter as tk
import json
import os
import random
from datetime import datetime

# ---------- Constants ----------
VOCAB_FILE = "words.json"
USER_FOLDER = "users"
ACTIVE_POOL_SIZE = 20  # Will expand with user rank later

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

# ---------- Priority Engine ----------
def update_word_stats(user_data):
    for word in vocab:
        if word not in user_data["words"]:
            user_data["words"][word] = {
                "priority": 50,
                "cooldown": 0,
                "correct": 0,
                "wrong": 0,
                "true_priority": 50
            }

def update_active_pool(user_data):
    if "active_pool" not in user_data:
        user_data["active_pool"] = []
    available = [w for w in vocab if w not in user_data["active_pool"]]
    while len(user_data["active_pool"]) < ACTIVE_POOL_SIZE and available:
        w = random.choice(available)
        user_data["active_pool"].append(w)
        available.remove(w)

def generate_quiz_words(user_data):
    pool = user_data["active_pool"]
    eligible = [w for w in pool if user_data["words"][w]["cooldown"] == 0]

    high_priority = [w for w in eligible if user_data["words"][w]["priority"] >= 30]
    low_priority = [w for w in eligible if user_data["words"][w]["priority"] < 30]

    num_high = int(0.8 * 10)
    num_low = 10 - num_high

    selected = random.sample(high_priority, min(num_high, len(high_priority)))
    selected += random.sample(low_priority, min(num_low, len(low_priority)))
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

def reduce_cooldowns(user_data):
    for word, stats in user_data["words"].items():
        if stats["cooldown"] > 0:
            stats["cooldown"] -= 1
            if stats["cooldown"] == 0:
                stats["priority"] = stats["true_priority"]

# ---------- GUI ----------
root = tk.Tk()
root.title("Lexibox: Vocabulary Boxing Trainer")
root.geometry("800x600")
root.configure(bg="black")

frames = {}
for name in ["profile", "menu", "quiz", "history"]:
    frames[name] = tk.Frame(root, bg="black")
    frames[name].grid(row=0, column=0, sticky="nsew")

# ---------- State ----------
player_name = ""
user_data = {}
quiz_words = []
current_word = ""
xp = 0
quiz_results = []

# ---------- GUI Functions ----------
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

    tk.Button(frame, text="Create New Profile", command=create_profile_screen).pack(pady=10)

def create_profile_screen():
    switch_frame("profile")
    frame = frames["profile"]
    for w in frame.winfo_children(): w.destroy()
    tk.Label(frame, text="Enter New Profile Name", fg="white", bg="black", font=("Helvetica", 20)).pack(pady=20)
    entry = tk.Entry(frame, font=("Helvetica", 16))
    entry.pack(pady=10)
    def create():
        name = entry.get().strip()
        if not name: return
        data = {"username": name, "xp": 0, "history": [], "words": {}, "active_pool": []}
        save_user(data)
        load_profile(name)
    tk.Button(frame, text="Create", command=create).pack(pady=10)

def load_profile(name):
    global player_name, user_data, xp
    player_name = name
    user_data = load_user(name)
    update_word_stats(user_data)
    update_active_pool(user_data)
    xp = user_data.get("xp", 0)
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
    global quiz_words, current_word, quiz_results
    reduce_cooldowns(user_data)
    quiz_words = generate_quiz_words(user_data)
    quiz_results = []
    if not quiz_words:
        switch_frame("quiz")
        frame = frames["quiz"]
        for w in frame.winfo_children(): w.destroy()
        tk.Label(frame, text="🛑 No words available!", fg="red", bg="black", font=("Helvetica", 24)).pack(pady=30)
        tk.Button(frame, text="⬅ Back to Home", command=show_menu).pack(pady=10)
        return
    ask_question()

def ask_question():
    global current_word
    switch_frame("quiz")
    frame = frames["quiz"]
    for w in frame.winfo_children(): w.destroy()
    if not quiz_words:
        end_quiz()
        return
    current_word = quiz_words.pop()
    correct = vocab[current_word]
    options = [correct] + random.sample([v for k, v in vocab.items() if v != correct], 3)
    random.shuffle(options)

    tk.Label(frame, text=f"What does '{current_word}' mean?", fg="white", bg="black", font=("Helvetica", 20)).pack(pady=20)
    for opt in options:
        tk.Button(frame, text=opt, width=60, command=lambda o=opt: submit_answer(o == correct)).pack(pady=5)

def submit_answer(correct):
    global xp
    handle_answer(user_data, current_word, correct)
    xp += 10 if correct else -5
    user_data["xp"] = max(xp, 0)
    quiz_results.append({"word": current_word, "correct": correct})
    ask_question()

def end_quiz():
    user_data["history"].append({
        "timestamp": datetime.now().isoformat(),
        "results": quiz_results
    })
    save_user(user_data)
    show_menu()

def show_history():
    switch_frame("history")
    frame = frames["history"]
    for w in frame.winfo_children(): w.destroy()
    tk.Label(frame, text="📜 Quiz History", fg="white", bg="black", font=("Helvetica", 24)).pack(pady=20)

    for quiz in reversed(user_data.get("history", [])[-5:]):
        tk.Label(frame, text=quiz["timestamp"], fg="yellow", bg="black", font=("Helvetica", 14)).pack()
        for result in quiz.get("results", []):
            word = result["word"]
            status = "✅" if result["correct"] else "❌"
            tk.Label(frame, text=f"{status} {word}", fg="white", bg="black", font=("Helvetica", 12)).pack()

        tk.Label(frame, text="―" * 50, fg="gray", bg="black").pack(pady=5)

    tk.Button(frame, text="⬅ Back to Home", command=show_menu).pack(pady=20)

# ---------- Start ----------
show_profile_screen()
root.mainloop()
