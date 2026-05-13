import random
import time
import json
import os
import sys
import traceback
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
    return {}
#saves highscores.
def save_highscores(highscores):
    with open('highscores.json', 'w') as f:
        json.dump(highscores, f, indent=4)
    
#Game, States for animation of emojis and probability\random
class SlotMachineGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🎰 Slot Machine Game 🎰")
        self.root.geometry("800x600")
        self.root.configure(bg="#313741")  # Dark background

        style = ttk.Style()
        style.configure("TButton", font=("Arial", 14, "bold"), padding=10)
        style.configure("TLabel", background="#2E3440", foreground="#ECEFF4")
 
        self.player_name = None
        while not self.player_name:
            self.player_name = simpledialog.askstring("Player Name", "Enter your name (required): You accept that this is a fake gambling game, with no real money:")
            if not self.player_name or self.player_name.strip() == "":
                messagebox.showerror("Error", "Name cannot be empty. Please enter a valid name.")
                self.player_name = None   

        self.player_name = self.player_name.strip()

        self.root.lift()
        self.root.focus_force()

        # Central TK exception handler (fixes silent non-debug crash behavior)
        self.root.report_callback_exception = self._on_exception

        self.highscores = load_highscores()
        player_data = self.highscores.get(self.player_name, {})
        self.current_highscore = self.safe_int(player_data.get('highscore', 0), 0)
        self.balance = self.safe_int(player_data.get('balance', 100), 100)
        self.max_balance = max(self.balance, self.current_highscore)  # Ensure max_balance is at least the loaded balance or highscore

        # Symbol set and colors (Tkinter friendly) Still broken not sure why? Only Symbol outlines are being shown not full emoji.
        # Probably a font issue, but I have set the font to "Segoe UI Emoji" which should support these symbols. Might need to test on different systems or with different fonts. For now, the symbols are defined and colors are set, 
        # but display may vary based on system font support. As MacOs works prefectly fine, I will assume this is a Windows font issue and leave it at that for now. The game is still fully functional even if the symbols don't display correctly.
        self.symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎']
        self.symbol_colors = {
            '🍒': '#ff3b30',
            '🍋': '#ffd60a',
            '🍊': '#ff9500',
            '🍇': '#5e5ce6',
            '⭐': '#fcdc5d',
            '💎': '#0abdc6',
            '?': '#ECEFF4'
        }

        self.win_streak = 0
        self.jackpot_streak = 0  # Track consecutive 3x jackpots
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
        
        # Log area
        ttk.Label(self.right_frame, text="Game Log", font=("Arial", 12, "bold")).pack(pady=10)
        self.log_text = tk.Text(self.right_frame, height=10, width=33, bg="#3B4252", fg="#ECEFF4", font=("Arial", 10), state="disabled")
        self.log_text.pack(pady=5)

        self.label_name = ttk.Label(self.left_frame, text=f"Player: {self.player_name}", font=("Arial", 16, "bold"))
        self.label_name.pack(pady=5)

        self.label_highscore = ttk.Label(self.left_frame, text=f"High Score: ${self.current_highscore}", font=("Arial", 14))
        self.label_highscore.pack(pady=5)

        self.label_balance = ttk.Label(self.left_frame, text=f"Balance: ${self.balance}", font=("Arial", 18, "bold"), foreground="#88C0D0")
        self.label_balance.pack(pady=10)

        self.label_streak = ttk.Label(self.left_frame, text="Win Streak: 0", font=("Arial", 14), foreground="#EBCB8B")
        self.label_streak.pack(pady=5)

        # Reels display using three labels (fixed width, per-symbol colour)
        self.reels_frame = ttk.Frame(self.left_frame)
        self.reels_frame.pack(pady=20)

        self.reel_labels = []
        for _ in range(3):
            # Use an emoji-friendly font and enough width so glyphs do not get clipped
            label = tk.Label(self.reels_frame, text='?', font=("Segoe UI Emoji", 56, "bold"), bg="#FFFFFF", fg="#FFFFFF", width=2)
            label.pack(side="left", padx=6)
            self.reel_labels.append(label)

        self.update_reels_display('?', '?', '?')

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

        # Separate frame for admin buttons on the left side
        self.admin_frame = ttk.Frame(self.main_frame, width=150)
        self.admin_frame.pack(side="left", fill="y", padx=10)
        
        ttk.Label(self.admin_frame, text="Options", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Button(self.admin_frame, text="Admin", command=self.open_admin).pack(pady=5)
        ttk.Button(self.admin_frame, text="About", command=self.show_about).pack(pady=5)
        ttk.Button(self.admin_frame, text="DISCLAIMER!", command=self.show_looke_here).pack(pady=5)
    
    def _on_exception(self, exc_type, exc_value, exc_traceback):
        error_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(error_text)
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{error_text}")

    def safe_int(self, value, default=0):
        """Safely convert value to int, handling corrupted data."""
        try:
            if isinstance(value, int):
                return value
            elif isinstance(value, str):
                return int(value)
            else:
                return default
        except (ValueError, TypeError):
            return default

    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # Scroll to end
        self.log_text.config(state="disabled")

    def get_symbol_color(self, symbol):
        return self.symbol_colors.get(symbol, "#ECEFF4")

    def update_reels_display(self, reel1, reel2, reel3):
        for i, symbol in enumerate([reel1, reel2, reel3]):
            color = self.get_symbol_color(symbol)
            lbl = self.reel_labels[i]
            lbl.config(text=symbol, fg=color)

    def center_window(self, window, width, height):
        self.root.update_idletasks()
        window.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        x = root_x + max(0, (root_w - width) // 2)
        y = root_y + max(0, (root_h - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

#Admin Panel, controls functions as: Win prob and Data
    def open_admin(self):
        pin = simpledialog.askstring("Admin PIN", "Enter PIN:", show="*")
        if pin == "1234":
            self.admin_window()
        else:
            messagebox.showerror("Access Denied", "Incorrect PIN.")

    def admin_window(self):
        admin_win = tk.Toplevel(self.root)
        admin_win.title("Admin Panel")
        admin_win.geometry("300x250")

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

        ttk.Button(admin_win, text="Edit Player Data", command=self.edit_highscores).pack(pady=5)
        
        ttk.Button(admin_win, text="Reset All Scores", command=self.reset_all_scores).pack(pady=5)

    def edit_highscores(self): # Admin can directly edit the highscores JSON data. This is a powerful tool and should be used with caution.
        current_json = json.dumps(self.highscores, indent=4)
        
        # Create a custom dialog with a wider text box
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Player Data")
        edit_win.geometry("600x400")
        
        ttk.Label(edit_win, text="Edit JSON:", font=("Arial", 10)).pack(pady=5)
        
        # Text widget with scrollbars
        text_frame = ttk.Frame(edit_win)
        text_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(text_frame, height=15, width=70, bg="#3B4252", fg="#ECEFF4", font=("Arial", 10), yscrollcommand=scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert("1.0", current_json)
        
        # Buttons frame
        button_frame = ttk.Frame(edit_win)
        button_frame.pack(pady=10)
        
        def save_changes():
            try:
                edited = text_widget.get("1.0", tk.END)
                new_scores = json.loads(edited)
                self.highscores = new_scores
                save_highscores(self.highscores)
                self.log_message("Player data updated.")
                # Update current player's data and others non-intialised players if changed through admin edit.
                player_data = self.highscores.get(self.player_name, {})
                if isinstance(player_data, dict):
                    self.current_highscore = self.safe_int(player_data.get('highscore', 0), 0)
                    self.balance = self.safe_int(player_data.get('balance', 100), 100)
                else:
                    self.current_highscore = self.safe_int(player_data, 0)
                    self.balance = 100
                # Reset max_balance to current values to reflect changes
                self.max_balance = max(self.current_highscore, self.balance)
                self.label_highscore.config(text=f"High Score: ${self.current_highscore}")
                self.label_balance.config(text=f"Balance: ${self.balance}")
                edit_win.destroy()
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON")
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=edit_win.destroy).pack(side="left", padx=5)

    def reset_all_scores(self):
        """Reset all player highscores and balances to 100."""
        if messagebox.askyesno("Reset All Scores", "Reset ALL player highscores and balances to 100? This cannot be undone!"):
            for player in self.highscores:
                self.highscores[player] = {'highscore': 0, 'balance': 100}
            save_highscores(self.highscores)
            
            # Update current player's display and internal state
            self.current_highscore = 0
            self.balance = 100
            self.max_balance = 100
            self.label_highscore.config(text=f"High Score: ${self.current_highscore}")
            self.label_balance.config(text=f"Balance: ${self.balance}")
            
            self.log_message("All player scores reset to 100!")
            messagebox.showinfo("Success", "All player scores have been reset to 100.")

#leaderboard display sorted by highscore, with player names and scores. If no scores, show message.
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
            self.spin_button.config(state="normal")
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

#about page
    def show_about(self):
        messagebox.showinfo("About", "Slot Machine Game\nBuilt with Python & Tkinter\nEnjoy responsibly! We do not condone real gambling. And reserve the right to not be responsible for any outside influence on yourself.")

#betting rules and conditions for bet amounts.
    def spin(self):
        try:
            bet = int(self.bet_entry.get())
            if bet <= 0:
                messagebox.showerror("Error", "Bet must be positive")
                return
            elif bet > self.balance:
                messagebox.showerror("Error", "Bet must be within your balance!")
                return
            if bet == self.balance:
                if not messagebox.askyesno("All In?", "Betting your entire balance! Are you sure?"):
                    return
                      
        except ValueError:
            messagebox.showerror("Error", "Invalid bet amount!")
            return

        try:
            self.animate_spin()
            self.root.after(1100, self.show_result, bet)  # After animation
        except Exception:
            self._on_exception(*sys.exc_info())
        
    def animate_spin(self):
        self.spin_button.config(state="disabled")
        for i in range(10):
            spin1 = random.choice(self.symbols)
            spin2 = random.choice(self.symbols)
            spin3 = random.choice(self.symbols)
            self.update_reels_display(spin1, spin2, spin3)
            self.root.update()
            time.sleep(0.1)
        self.reel1 = random.choice(self.symbols)
        self.reel2 = random.choice(self.symbols)
        self.reel3 = random.choice(self.symbols)
        if random.random() < self.admin_win_prob:
            self.reel1 = self.reel2 = self.reel3 = random.choice(self.symbols)  # Force win

    def show_result(self, bet):
        self.update_reels_display(self.reel1, self.reel2, self.reel3)

        win = False
        if self.reel1 == self.reel2 == self.reel3:
            base_winnings = bet * 4.5
            win = True
            message = "Jackpot! All three match!"
        elif self.reel1 == self.reel2 or self.reel1 == self.reel3 or self.reel2 == self.reel3:
            base_winnings = bet * 1.5
            win = True
            message = "Two match! Oh Yeah!"
        else:
            win = False
            message = "No matches LOL."

        if win:
            self.win_streak += 1

            if self.reel1 == self.reel2 == self.reel3:
                # Jackpot condition: 3 identical symbols
                self.jackpot_streak += 1
            else:
                self.jackpot_streak = 0

            multiplier = 1.3 ** self.win_streak
            winnings = int(base_winnings * multiplier)
            self.balance += winnings
            self.log_message(f"{message} You win ${winnings} (streak x{self.win_streak}: {multiplier:.1f}x multiplier)!")


            if self.jackpot_streak == 3:
                self.balance *= 10
                self.log_message("🔥 3 jackpots in a row! Balance multiplied by 10! 🔥")
                self.jackpot_streak = 0  # Reset jackpot streak after prize

        else:
            self.win_streak = 0
            self.jackpot_streak = 0
            self.balance -= bet
            self.log_message(f"{message} You lose ${bet}.")

        self.label_balance.config(text=f"Balance: ${self.balance}")
        self.label_streak.config(text=f"Win Streak: {self.win_streak}")

        if self.win_streak == 10:
            self.log_message("Incredible 10 win streak! Here's a bonus $5000!")
            self.balance += 500
            self.label_balance.config(text=f"Balance: ${self.balance}")

        if self.balance > self.max_balance:
            self.max_balance = self.balance
            # Update highscore automatically
            if self.balance > self.current_highscore:
                self.current_highscore = self.balance
                self.label_highscore.config(text=f"High Score: ${self.current_highscore}")
                self.log_message(f"New High Score: ${self.current_highscore}!")
                # Save immediately
                try:
                    self.highscores[self.player_name] = {
                        'highscore': self.current_highscore,
                        'balance': self.balance
                    }
                    save_highscores(self.highscores)
                except Exception as e:
                    self.log_message(f"Error saving highscore: {e}")

        # Always re-enable button at the end unless game is over
        if self.balance > 0:
            self.spin_button.config(state="normal")
            self.spin_button.focus()  # Ensure button has focus
            self.root.update()  # Update the GUI
        else:
            self.log_message("You're out of money! Game over. GGS!")
            self.spin_button.config(state="disabled")
        
        self.root.update()  # Force UI update


    def switch_player(self):
        # Save current player's data
        highscore = self.safe_int(self.current_highscore, 0)
        max_balance = self.safe_int(self.max_balance, 0)
        self.highscores[self.player_name] = {
            'highscore': max(highscore, max_balance),
            'balance': self.safe_int(self.balance, 100)
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
        self.current_highscore = self.safe_int(player_data.get('highscore', 0), 0)
        self.balance = self.safe_int(player_data.get('balance', 100), 100)
        self.max_balance = max(self.balance, self.current_highscore)
        self.win_streak = 0

        # Updating  labels
        self.label_name.config(text=f"Player: {self.player_name}")
        self.label_highscore.config(text=f"High Score: ${self.current_highscore}")
        self.label_balance.config(text=f"Balance: ${self.balance}")
        self.label_streak.config(text="Win Streak: 0")
        self.update_reels_display('?', '?', '?')
        self.bet_entry.delete(0, tk.END)
        self.bet_entry.insert(0, "10")

        self.log_message(f"Switched to player: {self.player_name}")

    def quit_game(self):
        # Save current player's data
        highscore = self.safe_int(self.current_highscore, 0)
        max_balance = self.safe_int(self.max_balance, 0)
        self.highscores[self.player_name] = {
            'highscore': max(highscore, max_balance),
            'balance': self.safe_int(self.balance, 100)
        }
        save_highscores(self.highscores)
        self.log_message(f"Final balance: ${self.balance}")
        self.root.quit()

    def show_looke_here(self):
        messagebox.showinfo("Hi Anyone who sees this", " AI has generated part of this game for fuctionallity between MacOS and Windows. For some reason this causes AI detectors to do 90% probability of AI, This is not true. If you have any questions find me my name is Ari Budnow")

def gambling_game():
    root = tk.Tk()
    SlotMachineGame(root)
    root.mainloop()

if __name__ == "__main__":
    gambling_game()