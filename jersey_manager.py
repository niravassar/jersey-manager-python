import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import re
import os
import random  # <--- Added Import

class JerseyManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GSSA Jersey Number Manager")
        self.root.geometry("600x400")

        # Variables
        self.vendor_file_path = tk.StringVar()
        self.team_file_path = tk.StringVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        # Layout
        self.create_widgets()

    def create_widgets(self):
        # Vendor File Selection
        frame_vendor = tk.Frame(self.root, pady=10)
        frame_vendor.pack(fill='x', padx=20)

        tk.Label(frame_vendor, text="1. Select Vendor Order Sheet (GSSA 2-9-26...):", font=("Arial", 10, "bold")).pack(anchor='w')
        entry_vendor = tk.Entry(frame_vendor, textvariable=self.vendor_file_path, width=50)
        entry_vendor.pack(side='left', padx=(0, 10))
        tk.Button(frame_vendor, text="Browse", command=self.browse_vendor).pack(side='left')

        # Team File Selection
        frame_team = tk.Frame(self.root, pady=10)
        frame_team.pack(fill='x', padx=20)

        tk.Label(frame_team, text="2. Select Team Assignment Sheet (U9+ Player...):", font=("Arial", 10, "bold")).pack(anchor='w')
        entry_team = tk.Entry(frame_team, textvariable=self.team_file_path, width=50)
        entry_team.pack(side='left', padx=(0, 10))
        tk.Button(frame_team, text="Browse", command=self.browse_team).pack(side='left')

        # Process Button
        frame_action = tk.Frame(self.root, pady=20)
        frame_action.pack()

        btn_process = tk.Button(frame_action, text="PROCESS FILES", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=self.process_files)
        btn_process.pack(pady=10, ipadx=20, ipady=5)

        # Status Label
        tk.Label(self.root, textvariable=self.status_var, fg="blue").pack()

    def browse_vendor(self):
        filename = filedialog.askopenfilename(title="Select Vendor File", filetypes=[("Excel/CSV Files", "*.xlsx *.csv")])
        if filename:
            self.vendor_file_path.set(filename)

    def browse_team(self):
        filename = filedialog.askopenfilename(title="Select Team File", filetypes=[("Excel/CSV Files", "*.xlsx *.csv")])
        if filename:
            self.team_file_path.set(filename)

    def load_file(self, path):
        """Helper to load either csv or xlsx"""
        if path.endswith('.csv'):
            return pd.read_csv(path)
        else:
            return pd.read_excel(path)

    def clean_name(self, val):
        """Parses 'Player First Name : John' to 'John'"""
        if pd.isna(val): return ""
        val = re.sub(r'Player\s*(First|Last)\s*Name\s*[:]\s*', '', str(val), flags=re.IGNORECASE)
        return val.strip()

    def extract_jersey_number(self, val):
        """Parses '[Player Number : 52]' to 52"""
        if pd.isna(val): return None
        match = re.search(r'Player Number\s*:\s*(\d+)', str(val))
        if match:
            return int(match.group(1))
        return None

    def process_files(self):
        vendor_path = self.vendor_file_path.get()
        team_path = self.team_file_path.get()

        if not vendor_path or not team_path:
            messagebox.showwarning("Missing Files", "Please select both files first.")
            return

        try:
            self.status_var.set("Loading files...")
            self.root.update_idletasks()

            df_vendor = self.load_file(vendor_path)
            df_team = self.load_file(team_path)

            df_vendor['Options Detail'] = df_vendor['Options Detail'].astype(str)
            df_team['Jersey'] = df_team['Jersey'].astype(str)

            df_orders = df_vendor[df_vendor['Product Name'] == 'GSSA Purple Game Jersey'].copy()

            df_orders['Clean_First'] = df_orders['Additional Info Question 1'].apply(self.clean_name)
            df_orders['Clean_Last'] = df_orders['Additional Info Question 2'].apply(self.clean_name)
            df_orders['Ordered_Jersey'] = df_orders['Options Detail'].apply(self.extract_jersey_number)

            df_team['Match_First'] = df_team['First Name'].astype(str).str.strip().str.lower()
            df_team['Match_Last'] = df_team['Last Name'].astype(str).str.strip().str.lower()
            df_team['Jersey_Clean'] = pd.to_numeric(df_team['Jersey'], errors='coerce')

            report_log = []

            for index, row in df_orders.iterrows():
                p_first = row['Clean_First']
                p_last = row['Clean_Last']
                ordered_num = row['Ordered_Jersey']

                match_first = p_first.lower()
                match_last = p_last.lower()

                player_record = df_team[
                    (df_team['Match_First'] == match_first) &
                    (df_team['Match_Last'] == match_last)
                    ]

                if player_record.empty:
                    report_log.append({
                        'First Name': p_first, 'Last Name': p_last, 'Team': 'N/A',
                        'Ordered': ordered_num, 'Final': 'N/A', 'Status': 'ERROR',
                        'Reason': 'Player not found in Team Assignment Sheet'
                    })
                    continue

                team_name = player_record.iloc[0]['Team Name']
                team_idx = player_record.index[0]

                team_roster = df_team[df_team['Team Name'] == team_name]
                taken_numbers = team_roster[team_roster.index != team_idx]['Jersey_Clean'].dropna().astype(int).tolist()

                final_number = ordered_num
                status = ""
                reason = ""

                if pd.isna(ordered_num):
                    status = "SKIPPED"
                    reason = "No number provided in order"
                    final_number = None
                elif ordered_num not in taken_numbers:
                    status = "KEPT"
                    reason = "Ordered number available"
                    final_number = ordered_num
                else:
                    status = "CHANGED"
                    reason = f"Conflict: #{ordered_num} taken on {team_name}"

                    # --- UPDATED RANDOM LOGIC ---
                    all_possible = list(range(1, 101))
                    available_choices = [n for n in all_possible if n not in taken_numbers]

                    if available_choices:
                        final_number = random.choice(available_choices)
                    else:
                        final_number = "N/A"
                    # -----------------------------

                report_log.append({
                    'First Name': p_first, 'Last Name': p_last, 'Team': team_name,
                    'Ordered': ordered_num, 'Final': final_number, 'Status': status,
                    'Reason': reason
                })

                if status == 'CHANGED':
                    val_str = f"CHANGED: {final_number}"
                else:
                    val_str = str(final_number)

                df_vendor.at[index, 'Options Detail'] = val_str
                df_team.at[team_idx, 'Jersey'] = val_str

            # --- FINAL UNIQUENESS CHECK ---
            # Group by Team and Jersey to find any duplicates
            # We only check players who actually have a jersey assigned
            mask = (df_team['Jersey'].notna()) & (df_team['Jersey'].astype(str).str.strip() != "")
            conflicts = df_team[mask].groupby(['Team Name', 'Jersey'])

            for (team_name, jersey_num), group in conflicts:
                if len(group) > 1:
                    # Duplicate found! Log every player involved in the conflict
                    for _, dup_row in group.iterrows():
                        report_log.append({
                            'Player': f"{dup_row['First Name']} {dup_row['Last Name']}",
                            'Team': team_name,
                            'Ordered': 'N/A',
                            'Final': jersey_num,
                            'Status': 'CONFLICT',
                            'Reason': f"DUPLICATE FOUND: Number {jersey_num} is assigned to multiple players on team {team_name}."
                        })

            df_report = pd.DataFrame(report_log)
            base_dir = os.path.dirname(vendor_path)
            out_vendor = os.path.join(base_dir, "UPDATED_Vendor_Orders.csv")
            out_team = os.path.join(base_dir, "UPDATED_Team_Assignments.csv")
            out_report = os.path.join(base_dir, "Process_Report.csv")

            df_vendor.to_csv(out_vendor, index=False)
            df_team.drop(columns=['Match_First', 'Match_Last', 'Jersey_Clean'], inplace=True, errors='ignore')
            df_team.to_csv(out_team, index=False)
            df_report.to_csv(out_report, index=False)

            self.status_var.set("Processing Complete!")
            messagebox.showinfo("Success", f"Files processed successfully!\n\nCreated:\n{out_vendor}\n{out_team}\n{out_report}")

        except Exception as e:
            self.status_var.set("Error Occurred")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            print(e)

if __name__ == "__main__":
    root = tk.Tk()
    app = JerseyManagerApp(root)
    root.mainloop()