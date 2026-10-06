import sqlite3
import hashlib
import random
import customtkinter as ctk
from tkinter import Canvas, messagebox
import webbrowser

# --- Modern Dark Purple Theme ---
ctk.set_appearance_mode("Dark")

# UI Palette Configuration
BG_COLOR = "#0D0714"          # Deep Midnight Purple
CARD_BG = "#1A0F2A"           # Dark Violet
CARD_BG_SECONDARY = "#130A21" # Deep Plum Fill
ACCENT_PURPLE = "#A855F7"     # Bright Purple Accent
ACCENT_PURPLE_HOVER = "#9333EA"
ACCENT_BLUE = "#6366F1"       # Indigo Accent
ACCENT_GREEN = "#10B981"      # Emerald Accent
ACCENT_GREEN_HOVER = "#059669"
ACCENT_ORANGE = "#F59E0B"     # Amber Accent
ACCENT_RED = "#EF4444"        # Rose Accent
TEXT_PRIMARY = "#F8FAFC"      # Bright White
TEXT_SECONDARY = "#C084FC"    # Soft Light Purple

def center_window(win, width=None, height=None):
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    
    if width is None:
        width = screen_w
    if height is None:
        height = screen_h

    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# =========================================================
# 1. BACKEND DATABASE SETUP (SQLite)
# =========================================================
def init_db():
    conn = sqlite3.connect("vtu_app.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_text TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    if not username or not password:
        return False, "Fields cannot be empty."
    conn = sqlite3.connect("vtu_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                       (username.strip(), hash_password(password)))
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists."

def authenticate_user(username, password):
    conn = sqlite3.connect("vtu_app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username.strip(),))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[1] == hash_password(password):
        return user[0]
    return None

def save_user_task(user_id, task_text):
    conn = sqlite3.connect("vtu_app.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, task_text) VALUES (?, ?)", (user_id, task_text))
    conn.commit()
    conn.close()

def fetch_user_tasks(user_id):
    conn = sqlite3.connect("vtu_app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT task_text FROM tasks WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


# =========================================================
# 2. FRONTEND GUI APPLICATION
# =========================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VTU Student Utility Hub")
        self.configure(fg_color=BG_COLOR)

        # Full screen viewport configuration
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.after(100, lambda: self.state("zoomed"))

        self.current_user_id = None
        self.current_username = None

        # --- ANIMATED STARFIELD BACKGROUND CANVAS ---
        self.canvas = Canvas(self, bg=BG_COLOR, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.dots = []
        self.init_shining_dots(num_dots=85)
        self.animate_dots()

        # UI Container overlay positioned above canvas
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_login_screen()

    # --- SHINING DOTS ENGINE ---
    def init_shining_dots(self, num_dots=85):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        colors = ["#E9D5FF", "#C084FC", "#A855F7", "#818CF8", "#FFFFFF"]

        for _ in range(num_dots):
            x = random.randint(0, sw)
            y = random.randint(0, sh)
            radius = random.uniform(1.5, 3.5)
            speed_y = random.uniform(-0.4, -0.1)
            color = random.choice(colors)
            
            dot_id = self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=color, outline=""
            )
            self.dots.append({
                "id": dot_id,
                "x": x,
                "y": y,
                "radius": radius,
                "speed_y": speed_y,
                "max_y": sh,
                "max_x": sw
            })

    def animate_dots(self):
        for dot in self.dots:
            dot["y"] += dot["speed_y"]
            if dot["y"] < 0:
                dot["y"] = dot["max_y"]
                dot["x"] = random.randint(0, dot["max_x"])

            r = dot["radius"]
            self.canvas.coords(
                dot["id"], 
                dot["x"] - r, dot["y"] - r, 
                dot["x"] + r, dot["y"] + r
            )

        self.after(30, self.animate_dots)

    # --- SCREEN 1: SPLIT LOGIN SCREEN ---
    def show_login_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        wrapper = ctk.CTkFrame(self.container, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        outer_card = ctk.CTkFrame(
            wrapper, 
            fg_color=CARD_BG, 
            corner_radius=24, 
            border_width=1, 
            border_color="#3B1260", 
            width=900, 
            height=540
        )
        outer_card.pack(padx=20, pady=20)
        outer_card.pack_propagate(False)

        # Left Hero Panel
        left_hero = ctk.CTkFrame(outer_card, fg_color=CARD_BG_SECONDARY, corner_radius=18, border_width=1, border_color="#2A0E47")
        left_hero.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            left_hero, 
            text="🎓 VTU ACADEMIC SUITE", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color=ACCENT_PURPLE
        ).pack(pady=(40, 10), padx=30, anchor="w")

        ctk.CTkLabel(
            left_hero, 
            text="Smart SGPA &\nStudent Portal", 
            font=ctk.CTkFont(size=28, weight="bold"), 
            text_color=TEXT_PRIMARY,
            justify="left"
        ).pack(pady=(0, 15), padx=30, anchor="w")

        ctk.CTkLabel(
            left_hero, 
            text="Compute credit SGPA, access official university portals, and organize your daily study tasks.", 
            font=ctk.CTkFont(size=12), 
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=340
        ).pack(pady=(0, 30), padx=30, anchor="w")

        # Visual Badges
        features_frame = ctk.CTkFrame(left_hero, fg_color="transparent")
        features_frame.pack(padx=30, fill="x")

        feats = [
            ("🧮", "Credit SGPA Engine", "Calculates scheme-based GP"),
            ("📚", "Official Resources", "Direct VTU web access"),
            ("📌", "Task Reminders", "SQLite database persistence")
        ]

        for icon, title, desc in feats:
            f_row = ctk.CTkFrame(features_frame, fg_color="#180A2B", corner_radius=12, border_width=1, border_color="#311252")
            f_row.pack(fill="x", pady=6)

            ctk.CTkLabel(f_row, text=icon, font=ctk.CTkFont(size=20)).pack(side="left", padx=(12, 8), pady=10)
            
            txt_box = ctk.CTkFrame(f_row, fg_color="transparent")
            txt_box.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(txt_box, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(txt_box, text=desc, font=ctk.CTkFont(size=10), text_color=TEXT_SECONDARY, anchor="w").pack(anchor="w")

        # Right Form Panel
        right_form = ctk.CTkFrame(outer_card, fg_color="transparent")
        right_form.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            right_form, 
            text="Welcome Back", 
            font=ctk.CTkFont(size=24, weight="bold"), 
            text_color=TEXT_PRIMARY
        ).pack(pady=(30, 4), anchor="center")

        ctk.CTkLabel(
            right_form, 
            text="Sign in to your account", 
            font=ctk.CTkFont(size=12), 
            text_color=TEXT_SECONDARY
        ).pack(pady=(0, 25), anchor="center")

        username_entry = ctk.CTkEntry(
            right_form, 
            placeholder_text="Username", 
            height=46, 
            corner_radius=12,
            fg_color="#12081F",
            border_color="#3B1260",
            text_color=TEXT_PRIMARY
        )
        username_entry.pack(pady=8, padx=25, fill="x")

        password_entry = ctk.CTkEntry(
            right_form, 
            placeholder_text="Password", 
            show="•", 
            height=46, 
            corner_radius=12,
            fg_color="#12081F",
            border_color="#3B1260",
            text_color=TEXT_PRIMARY
        )
        password_entry.pack(pady=8, padx=25, fill="x")

        def handle_login(event=None):
            user_id = authenticate_user(username_entry.get(), password_entry.get())
            if user_id:
                self.current_user_id = user_id
                self.current_username = username_entry.get()
                self.show_dashboard()
            else:
                messagebox.showerror("Login Error", "Invalid username or password.")

        def handle_signup():
            success, msg = register_user(username_entry.get(), password_entry.get())
            if success:
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Sign Up Error", msg)

        # Keyboard Navigation Bindings
        username_entry.bind("/t ", lambda event: password_entry.focus())
        password_entry.bind("/t ", handle_login)

        btn_login = ctk.CTkButton(
            right_form, 
            text="Sign In", 
            height=46, 
            corner_radius=12,
            fg_color=ACCENT_PURPLE, 
            hover_color=ACCENT_PURPLE_HOVER, 
            cursor="hand2",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=handle_login
        )
        btn_login.pack(pady=(25, 10), padx=25, fill="x")

        btn_signup = ctk.CTkButton(
            right_form, 
            text="Create Account", 
            height=46, 
            corner_radius=12,
            fg_color="transparent", 
            border_width=1,
            border_color="#581C87",
            hover_color="#3B1260", 
            cursor="hand2",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=handle_signup
        )
        btn_signup.pack(pady=5, padx=25, fill="x")

        username_entry.focus()

    # --- SCREEN 2: MAIN DASHBOARD ---
    def show_dashboard(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        main_layout = ctk.CTkFrame(self.container, fg_color="transparent")
        main_layout.place(relx=0.5, rely=0.5, anchor="center")

        dashboard_card = ctk.CTkFrame(
            main_layout, 
            fg_color=CARD_BG, 
            corner_radius=24, 
            border_width=1, 
            border_color="#3B1260",
            width=920,
            height=580
        )
        dashboard_card.pack(padx=20, pady=20)
        dashboard_card.pack_propagate(False)

        # Header
        header_frame = ctk.CTkFrame(dashboard_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=35, pady=(30, 20))

        ctk.CTkLabel(
            header_frame, 
            text=f"👋 Welcome back, {self.current_username}", 
            font=ctk.CTkFont(size=24, weight="bold"), 
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame, 
            text="Visvesvaraya Technological University • Student Dashboard", 
            font=ctk.CTkFont(size=12), 
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        # Stat Cards
        stats_frame = ctk.CTkFrame(dashboard_card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=35, pady=(0, 25))

        stats = [
            ("📊", "Current Target", "9.00 SGPA", ACCENT_PURPLE),
            ("👨‍🎓", "Student Status", "Active", ACCENT_GREEN),
            ("📑", "VTU Scheme", "Credit Based", ACCENT_BLUE)
        ]

        for icon, title, value, color in stats:
            s_card = ctk.CTkFrame(stats_frame, fg_color=CARD_BG_SECONDARY, corner_radius=16, border_width=1, border_color="#3B1260")
            s_card.pack(side="left", fill="both", expand=True, padx=6)

            ctk.CTkLabel(s_card, text=icon, font=ctk.CTkFont(size=22)).pack(anchor="w", padx=15, pady=(12, 0))
            ctk.CTkLabel(s_card, text=title, font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).pack(anchor="w", padx=15)
            ctk.CTkLabel(s_card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w", padx=15, pady=(0, 12))

        # Action Buttons
        actions_grid = ctk.CTkFrame(dashboard_card, fg_color="transparent")
        actions_grid.pack(fill="both", expand=True, padx=35, pady=(0, 25))

        # Row 1
        r1 = ctk.CTkFrame(actions_grid, fg_color="transparent")
        r1.pack(fill="x", pady=6)

        btn_sgpa = ctk.CTkButton(
            r1, 
            text="   📊   Calculate Credit SGPA", 
            fg_color=ACCENT_PURPLE, 
            hover_color=ACCENT_PURPLE_HOVER, 
            height=52, 
            corner_radius=14, 
            font=ctk.CTkFont(size=14, weight="bold"), 
            cursor="hand2",
            command=self.open_semester_selector
        )
        btn_sgpa.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_notes = ctk.CTkButton(
            r1, 
            text="   🌐   VTU Official Portal", 
            fg_color=ACCENT_BLUE, 
            hover_color="#4F46E5", 
            height=52, 
            corner_radius=14, 
            font=ctk.CTkFont(size=14, weight="bold"), 
            cursor="hand2",
            command=lambda: webbrowser.open("https://vtu.ac.in/")
        )
        btn_notes.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Row 2
        r2 = ctk.CTkFrame(actions_grid, fg_color="transparent")
        r2.pack(fill="x", pady=6)

        btn_task = ctk.CTkButton(
            r2, 
            text="   📝   Add Quick Reminder", 
            fg_color=ACCENT_ORANGE, 
            hover_color="#D97706", 
            height=52, 
            corner_radius=14, 
            font=ctk.CTkFont(size=14, weight="bold"), 
            cursor="hand2",
            command=self.open_task_dialog
        )
        btn_task.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_view_tasks = ctk.CTkButton(
            r2, 
            text="   📋   View Saved Reminders", 
            fg_color=ACCENT_GREEN, 
            hover_color=ACCENT_GREEN_HOVER, 
            height=52, 
            corner_radius=14, 
            font=ctk.CTkFont(size=14, weight="bold"), 
            cursor="hand2",
            command=self.view_tasks
        )
        btn_view_tasks.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Logout
        btn_logout = ctk.CTkButton(
            actions_grid, 
            text="   🚪   Sign Out", 
            fg_color="transparent", 
            border_width=1,
            border_color="#EF4444",
            hover_color="#7F1D1D",
            text_color=ACCENT_RED,
            height=52, 
            corner_radius=14, 
            font=ctk.CTkFont(size=14, weight="bold"), 
            cursor="hand2",
            command=self.show_login_screen
        )
        btn_logout.pack(fill="x", pady=(10, 0))

    # --- SGPA SEMESTER SELECTOR ---
    def open_semester_selector(self):
        sem_win = ctk.CTkToplevel(self)
        sem_win.title("Select Semester")
        sem_win.resizable(False, False)
        sem_win.configure(fg_color=BG_COLOR)
        sem_win.transient(self)
        sem_win.grab_set()

        center_window(sem_win, 380, 280)

        ctk.CTkLabel(
            sem_win, 
            text="Choose Semester", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(pady=(28, 4))

        ctk.CTkLabel(
            sem_win, 
            text="Select your semester to load credit scheme", 
            font=ctk.CTkFont(size=12), 
            text_color=TEXT_SECONDARY
        ).pack(pady=(0, 22))

        btn1 = ctk.CTkButton(
            sem_win, 
            text="1st Semester Scheme", 
            height=46, 
            corner_radius=12,
            fg_color=ACCENT_PURPLE, 
            hover_color=ACCENT_PURPLE_HOVER,
            cursor="hand2",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: [sem_win.destroy(), self.open_subject_marks_form("1st Semester")]
        )
        btn1.pack(pady=6, padx=35, fill="x")

        btn2 = ctk.CTkButton(
            sem_win, 
            text="2nd Semester Scheme", 
            height=46, 
            corner_radius=12,
            fg_color=ACCENT_GREEN, 
            hover_color=ACCENT_GREEN_HOVER,
            cursor="hand2",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: [sem_win.destroy(), self.open_subject_marks_form("2nd Semester")]
        )
        btn2.pack(pady=10, padx=35, fill="x")

    # --- SUBJECT MARKS FORM & RESULT VIEW ---
    def open_subject_marks_form(self, sem_name):
        calc_win = ctk.CTkToplevel(self)
        calc_win.title(f"{sem_name} Calculator")
        calc_win.resizable(False, False)
        calc_win.configure(fg_color=BG_COLOR)
        calc_win.transient(self)
        calc_win.grab_set()

        center_window(calc_win, 460, 620)

        if sem_name == "1st Semester":
            subjects = [
                ("Physics", 4),
                ("C-Programming", 3),
                ("C-Programming Lab", 1),
                ("Maths", 4),
                ("IME", 3),
                ("CAED", 3),
                ("Soft Skill", 0),
                ("IDT", 1),
                ("Kannada", 1)
            ]
        else:
            subjects = [
                ("Maths", 4),
                ("Chemistry", 4),
                ("IAI", 3),
                ("Building Science", 3),
                ("Communication Skills", 1),
                ("Indian Constitution", 0),
                ("IDPBL", 1),
                ("Python", 4)
            ]

        ctk.CTkLabel(
            calc_win, 
            text=f"🧮  {sem_name} Evaluation", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(pady=(20, 5))

        scroll_frame = ctk.CTkScrollableFrame(
            calc_win, 
            fg_color=CARD_BG, 
            corner_radius=16,
            border_width=1,
            border_color="#3B1260",
            width=390, 
            height=440
        )
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        entries = []

        for sub_name, credits in subjects:
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=6, padx=5)

            lbl = ctk.CTkLabel(
                row_frame, 
                text=f"{sub_name}  ({credits} Cr)", 
                font=ctk.CTkFont(size=13, weight="bold"), 
                text_color=TEXT_PRIMARY,
                anchor="w", 
                width=230
            )
            lbl.pack(side="left", padx=5)

            entry = ctk.CTkEntry(
                row_frame, 
                placeholder_text="0-100", 
                width=85,
                height=36,
                corner_radius=8,
                fg_color="#12081F",
                border_color="#3B1260",
                text_color=TEXT_PRIMARY
            )
            entry.pack(side="right", padx=5)

            entries.append((entry, credits, sub_name))

        def calculate_sgpa():
            total_credits = 0
            weighted_points = 0

            def mark_to_gp(m):
                if m >= 90: return 10
                elif m >= 80: return 9
                elif m >= 70: return 8
                elif m >= 60: return 7
                elif m >= 50: return 6
                elif m >= 45: return 5
                elif m >= 40: return 4
                return 0

            try:
                for entry_widget, credits, sub_name in entries:
                    val = entry_widget.get().strip()
                    if val == "":
                        messagebox.showwarning("Missing Input", f"Please enter marks for {sub_name}.")
                        return
                    
                    marks = float(val)
                    if marks < 0 or marks > 100:
                        messagebox.showerror("Invalid Input", f"Marks for {sub_name} must be between 0 and 100.")
                        return

                    if credits > 0:
                        gp = mark_to_gp(marks)
                        weighted_points += gp * credits
                        total_credits += credits

                sgpa = weighted_points / total_credits if total_credits > 0 else 0.0

                calc_win.destroy()
                self.show_celebration_page(sem_name, sgpa)

            except ValueError:
                messagebox.showerror("Error", "Please enter valid numeric marks.")

        ctk.CTkButton(
            calc_win, 
            text="Compute Final SGPA", 
            fg_color=ACCENT_GREEN, 
            hover_color=ACCENT_GREEN_HOVER, 
            height=46,
            corner_radius=12,
            cursor="hand2",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=calculate_sgpa
        ).pack(pady=(10, 20), padx=25, fill="x")

    # --- CELEBRATION RESULT SCREEN ---
    def show_celebration_page(self, sem_name, sgpa):
        res_win = ctk.CTkToplevel(self)
        res_win.title("Performance Result")
        res_win.resizable(False, False)
        res_win.configure(fg_color=BG_COLOR)
        res_win.transient(self)
        res_win.grab_set()

        center_window(res_win, 400, 380)

        card = ctk.CTkFrame(res_win, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color="#3B1260")
        card.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(
            card, 
            text="🎉  HURRAY!  🎉", 
            font=ctk.CTkFont(size=24, weight="bold"), 
            text_color=ACCENT_GREEN
        ).pack(pady=(25, 5))

        score_frame = ctk.CTkFrame(card, fg_color="#12081F", corner_radius=12, border_width=1, border_color="#3B1260")
        score_frame.pack(pady=12, padx=30, fill="x")

        ctk.CTkLabel(
            score_frame, 
            text=f"{sgpa:.2f}", 
            font=ctk.CTkFont(size=36, weight="bold"), 
            text_color=TEXT_PRIMARY
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            score_frame, 
            text=f"Calculated SGPA ({sem_name})", 
            font=ctk.CTkFont(size=12), 
            text_color=TEXT_SECONDARY
        ).pack(pady=(0, 10))

        btn_dash = ctk.CTkButton(
            card, 
            text="Back to Dashboard", 
            height=42, 
            corner_radius=10,
            fg_color=ACCENT_PURPLE, 
            hover_color=ACCENT_PURPLE_HOVER,
            cursor="hand2",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=res_win.destroy
        )
        btn_dash.pack(pady=(10, 5), padx=30, fill="x")

        def logout_from_result():
            res_win.destroy()
            self.show_login_screen()

        btn_logout = ctk.CTkButton(
            card, 
            text="Sign Out", 
            height=42, 
            corner_radius=10,
            fg_color="transparent", 
            border_width=1,
            border_color="#EF4444",
            hover_color="#7F1D1D",
            cursor="hand2",
            text_color=ACCENT_RED,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=logout_from_result
        )
        btn_logout.pack(pady=5, padx=30, fill="x")

    # --- DASHBOARD DIALOGS ---
    def open_task_dialog(self):
        dialog = ctk.CTkInputDialog(text="Type your reminder / task:", title="Add Task")
        task = dialog.get_input()
        if task and task.strip():
            save_user_task(self.current_user_id, task.strip())
            messagebox.showinfo("Saved", "Task saved to database!")

    def view_tasks(self):
        tasks = fetch_user_tasks(self.current_user_id)
        task_win = ctk.CTkToplevel(self)
        task_win.title("Saved Reminders")
        task_win.configure(fg_color=BG_COLOR)
        task_win.transient(self)
        task_win.grab_set()

        center_window(task_win, 360, 380)

        ctk.CTkLabel(
            task_win, 
            text=f"Reminders for {self.current_username}", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(pady=(20, 10))

        textbox = ctk.CTkTextbox(
            task_win, 
            width=300, 
            height=250, 
            fg_color=CARD_BG, 
            text_color=TEXT_PRIMARY,
            corner_radius=12,
            border_width=1,
            border_color="#3B1260"
        )
        textbox.pack(pady=5, padx=20)

        if tasks:
            for idx, task in enumerate(tasks, 1):
                textbox.insert("end", f"  {idx}.  {task}\n\n")
        else:
            textbox.insert("end", "\n  No tasks saved yet.")
        textbox.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()


