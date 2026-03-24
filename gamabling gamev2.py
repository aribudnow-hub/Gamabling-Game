import random
import time
import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk

#remembers highscores after game it exitited.
def load_highscores():
    if os.path.exists('highscores.json'):
        with open('highscores.json', 'r') as f:
            data = json.load(f)
            # Convert old format {name: score} to {name: {'highscore': score, 'balance': 100}}
            for name, value in data.items():
                if isinstance(value, int):
                    data[name] = {'highscore': value, 'balance': 100}
            return data
    return {}

def save_highscores(highscores):
    with open('highscores.json', 'w') as f:
        json.dump(highscores, f, indent=4)
    
#main functions of the random slots.ab
class SlotMachineGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🎰 Slot Machine Game 🎰")
        self.root.geometry("500x500")
        self.root.configure(bg="#2E3440")  # Dark background

        style = ttk.Style()
        style.configure("TButton", font=("Arial", 14, "bold"), padding=10)
        style.configure("TLabel", background="#2E3440", foreground="#ECEFF4")

        self.player_name = None
        while not self.player_name:
            self.player_name = simpledialog.askstring("Player Name", "Enter your name (required):")
            if not self.player_name or self.player_name.strip() == "":
                messagebox.showerror("Error", "Name cannot be empty. Please enter a valid name.")
                self.player_name = None
    
            
        self.player_name = self.player_name.strip()

        self.highscores = load_highscores()
        player_data = self.highscores.get(self.player_name, {})
        self.current_highscore = player_data.get('highscore', 0)
        self.balance = player_data.get('balance', 100)
        self.max_balance = max(self.balance, self.current_highscore)  # Ensure max_balance is at least the loaded balance or highscore
        self.symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎']
        self.win_streak = 0
        self.admin_win_prob = 0.01  # Probability to force a win

        # GUI Elements
        self.main_frame = ttk.Frame(root, padding=20)
        self.main_frame.pack(expand=True, fill="both")

        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side="left", expand=True, fill="both")

        self.right_frame = ttk.Frame(self.main_frame, width=150)
        self.right_frame.pack(side="right", fill="y", padx=10)

        # Right menu
        ttk.Label(self.right_frame, text="Menu", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Button(self.right_frame, text="Leaderboard", command=self.view_highscores).pack(pady=5)
        ttk.Button(self.right_frame, text="Reset Balance", command=self.reset_balance).pack(pady=5)
        ttk.Button(self.right_frame, text="Lend Money", command=self.lend_money).pack(pady=5)
        ttk.Button(self.right_frame, text="Admin", command=self.open_admin).pack(pady=5)
        ttk.Button(self.right_frame, text="About", command=self.show_about).pack(pady=5)

        # Log area
        ttk.Label(self.right_frame, text="Game Log", font=("Arial", 12, "bold")).pack(pady=10)
        self.log_text = tk.Text(self.right_frame, height=10, width=25, bg="#3B4252", fg="#ECEFF4", font=("Arial", 10), state="disabled")
        self.log_text.pack(pady=5)

        self.label_name = ttk.Label(self.left_frame, text=f"Player: {self.player_name}", font=("Arial", 16, "bold"))
        self.label_name.pack(pady=5)

        self.label_highscore = ttk.Label(self.left_frame, text=f"High Score: ${self.current_highscore}", font=("Arial", 14))
        self.label_highscore.pack(pady=5)

        self.label_balance = ttk.Label(self.left_frame, text=f"Balance: ${self.balance}", font=("Arial", 18, "bold"), foreground="#88C0D0")
        self.label_balance.pack(pady=10)

        self.label_streak = ttk.Label(self.left_frame, text="Win Streak: 0", font=("Arial", 14), foreground="#EBCB8B")
        self.label_streak.pack(pady=5)

        self.reels_label = tk.Label(self.left_frame, text="[ ? ] [ ? ] [ ? ]", font=("Arial", 36), bg="#2E3440", fg="#ECEFF4", relief="sunken", bd=5)
        self.reels_label.pack(pady=20)

        self.bet_frame = ttk.Frame(self.left_frame)
        self.bet_frame.pack(pady=5)
        ttk.Label(self.bet_frame, text="Bet Amount:", font=("Arial", 12)).pack(side="left")
        self.bet_entry = ttk.Entry(self.bet_frame, font=("Arial", 12), width=10)
        self.bet_entry.pack(side="left", padx=5)
        self.bet_entry.insert(0, "10")

        self.spin_button = ttk.Button(self.left_frame, text="Spin!", command=self.spin, style="Spin.TButton")
        self.spin_button.pack(pady=10)

        self.quit_button = ttk.Button(self.left_frame, text="Quit Game", command=self.quit_game)
        self.quit_button.pack(pady=5)

        self.switch_button = ttk.Button(self.left_frame, text="Switch Player", command=self.switch_player)
        self.switch_button.pack(pady=5)


    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # Scroll to end
        self.log_text.config(state="disabled")

    def open_admin(self):
        pin = simpledialog.askstring("Admin PIN", "Enter PIN:", show="*")
        if pin == "1111":
            self.admin_window()
        else:
            messagebox.showerror("Access Denied", "Incorrect PIN.")

    def admin_window(self):
        admin_win = tk.Toplevel(self.root)
        admin_win.title("Admin Panel")
        admin_win.geometry("300x200")

        ttk.Label(admin_win, text="Win Probability (0.0-1.0):").pack(pady=5)
        prob_entry = ttk.Entry(admin_win)
        prob_entry.pack(pady=5)
        prob_entry.insert(0, str(self.admin_win_prob))

        def set_prob():
            try:
                prob = float(prob_entry.get())
                if 0.0 <= prob <= 1.0:
                    self.admin_win_prob = prob
                    self.log_message(f"Win probability set to {prob}")
                    admin_win.destroy()
                else:
                    messagebox.showerror("Error", "Probability must be between 0.0 and 1.0")
            except ValueError:
                messagebox.showerror("Error", "Invalid number")

        ttk.Button(admin_win, text="Set Probability", command=set_prob).pack(pady=5)

        ttk.Button(admin_win, text="Edit High Scores", command=self.edit_highscores).pack(pady=5)

    def edit_highscores(self):
        current_json = json.dumps(self.highscores, indent=4)
        edited = simpledialog.askstring("Edit High Scores", "Edit JSON:", initialvalue=current_json)
        if edited:
            try:
                new_scores = json.loads(edited)
                self.highscores = new_scores
                save_highscores(self.highscores)
                self.log_message("High scores updated.")
                # Update current highscore if player changed
                self.current_highscore = self.highscores.get(self.player_name, 0)
                self.label_highscore.config(text=f"High Score: ${self.current_highscore}")
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON")

    def view_highscores(self):
        if not self.highscores:
            messagebox.showinfo("Leaderboard", "No scores yet.")
            return
        # Sort by highscore descending
        sorted_scores = sorted(self.highscores.items(), key=lambda x: x[1]['highscore'], reverse=True)
        leaderboard = "🏆 Leaderboard 🏆\n\n"
        for i, (name, data) in enumerate(sorted_scores, 1):
            leaderboard += f"{i}. {name}: ${data['highscore']}\n"
        messagebox.showinfo("Leaderboard", leaderboard)

    def reset_balance(self):
        if messagebox.askyesno("Reset", "Reset balance to $100?"):
            self.balance = 100
            self.max_balance = 100
            self.win_streak = 0
            self.label_balance.config(text=f"Balance: ${self.balance}")
            self.label_streak.config(text="Win Streak: 0")
            self.log_message("Balance reset to $100.")
    def lend_money(self):
        recipient = simpledialog.askstring("Lend Money", "Enter recipient's name:")
        if not recipient or recipient.strip() == "":
            return
        recipient = recipient.strip()
        if recipient == self.player_name:
            messagebox.showerror("Error", "Cannot lend to yourself!")
            return
        try:
            amount = int(simpledialog.askstring("Lend Money", f"Enter amount to lend to {recipient}:"))
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive!")
                return
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Invalid amount!")
            return
        if amount > self.balance:
            messagebox.showerror("Error", "Not enough balance to lend!")
            return
        # Confirm
        if not messagebox.askyesno("Confirm", f"Lend ${amount} to {recipient}?"):
            return
        # Get recipient data
        if recipient not in self.highscores:
            self.highscores[recipient] = {'highscore': 0, 'balance': 100}
        recipient_balance = self.highscores[recipient]['balance']
        # Transfer
        self.balance -= amount
        self.highscores[recipient]['balance'] = recipient_balance + amount
        save_highscores(self.highscores)
        self.label_balance.config(text=f"Balance: ${self.balance}")
        self.log_message(f"Lent ${amount} to {recipient}. New balance: ${self.balance}")

    def show_about(self):
        messagebox.showinfo("About", "Slot Machine Game\nBuilt with Python & Tkinter\nEnjoy responsibly! We do not condone real gambling. And reserve the right to not be responsible for any outside influence on yourself.")

    def spin(self):
        try:
            bet = int(self.bet_entry.get())
            if bet <= 0:
                messagebox.showerror("Error", "Bet must be positive!")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid bet amount!")
            return

        self.animate_spin()
        self.root.after(1100, self.show_result, bet)  # After animation

    def animate_spin(self):
        self.spin_button.config(state="disabled")
        for i in range(10):
            spin1 = random.choice(self.symbols)
            spin2 = random.choice(self.symbols)
            spin3 = random.choice(self.symbols)
            self.reels_label.config(text=f"[{spin1}] [{spin2}] [{spin3}]")
            self.root.update()
            time.sleep(0.1)
        self.reel1 = random.choice(self.symbols)
        self.reel2 = random.choice(self.symbols)
        self.reel3 = random.choice(self.symbols)
        if random.random() < self.admin_win_prob:
            self.reel1 = self.reel2 = self.reel3 = random.choice(self.symbols)  # Force win

    def show_result(self, bet):
        self.reels_label.config(text=f"[{self.reel1}] [{self.reel2}] [{self.reel3}]")

        win = False
        if self.reel1 == self.reel2 == self.reel3:
            base_winnings = bet * 1.5
            win = True
            message = "Jackpot! All three match!"
        elif self.reel1 == self.reel2 or self.reel1 == self.reel3 or self.reel2 == self.reel3:
            base_winnings = bet * 1.5
            win = True
            message = "Two match!"
        else:
            win = False
            message = "No matches."

        if win:
            self.win_streak += 1
            multiplier = 1.3 ** self.win_streak
            winnings = int(base_winnings * multiplier)
            self.balance += winnings
            self.log_message(f"{message} You win ${winnings} (streak x{self.win_streak}: {multiplier:.1f}x multiplier)!")
        else:
            self.win_streak = 0
            self.balance -= bet
            self.log_message(f"{message} You lose ${bet}.")

        self.label_balance.config(text=f"Balance: ${self.balance}")
        self.label_streak.config(text=f"Win Streak: {self.win_streak}")

        if self.balance > self.max_balance:
            self.max_balance = self.balance

        if self.balance <= 0:
            self.log_message("You're out of money! Game over.")

        else:
            self.spin_button.config(state="normal")

    def switch_player(self):
        # Save current player's data
        self.highscores[self.player_name] = {
            'highscore': max(self.current_highscore, self.max_balance),
            'balance': self.balance
        }
        save_highscores(self.highscores)

        # Prompt for new player
        new_name = None
        while not new_name:
            new_name = simpledialog.askstring("Change Player", "Enter new player's name (required):")
            if not new_name or new_name.strip() == "":
                messagebox.showerror("Error", "Name cannot be empty. Please enter a valid name.")
                new_name = None
        new_name = new_name.strip()

        self.player_name = new_name
        player_data = self.highscores.get(self.player_name, {})
        self.current_highscore = player_data.get('highscore', 0)
        self.balance = player_data.get('balance', 100)
        self.max_balance = max(self.balance, self.current_highscore)
        self.win_streak = 0

        # Updating  labels
        self.label_name.config(text=f"Player: {self.player_name}")
        self.label_highscore.config(text=f"High Score: ${self.current_highscore}")
        self.label_balance.config(text=f"Balance: ${self.balance}")
        self.label_streak.config(text="Win Streak: 0")
        self.reels_label.config(text="[ ? ] [ ? ] [ ? ]")
        self.bet_entry.delete(0, tk.END)
        self.bet_entry.insert(0, "10")

        self.log_message(f"Switched to player: {self.player_name}")

    def quit_game(self):
        # Save current player's data
        self.highscores[self.player_name] = {
            'highscore': max(self.current_highscore, self.max_balance),
            'balance': self.balance
        }
        save_highscores(self.highscores)
        self.log_message(f"Final balance: ${self.balance}")
        self.root.quit()

def gambling_game():
    root = tk.Tk()
    SlotMachineGame(root)
    root.mainloop()

if __name__ == "__main__":
    gambling_game()