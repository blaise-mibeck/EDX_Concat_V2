import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from tkinter import ttk
import re
import numpy as np

class Model:
    def __init__(self):
        self.folder_path = ""
        self.df = pd.DataFrame()
        self.linescan_df = pd.DataFrame()

    def set_folder_path(self, path):
        self.folder_path = path

    def process_linescan(self, file_path, folder_name, measurement_type, edx_id):
        # Read CSV file
        csv_data = pd.read_csv(file_path)
        
        # Print debugging information
        print(f"Processing linescan file: {file_path}")
        print(f"Columns found: {csv_data.columns.tolist()}")
        
        # Get position values (columns are numeric indices)
        non_numeric_cols = ['Atomic number', 'Element symbol', 'Element name', 'Number of datapoints']
        position_columns = [col for col in csv_data.columns if col not in non_numeric_cols]
        
        # Create rows for each position and element
        data = []
        for pos_idx in position_columns:
            for _, row in csv_data.iterrows():
                data.append({
                    'EDX': edx_id,
                    'Position_Index': float(pos_idx) if isinstance(pos_idx, str) else pos_idx,
                    'Atomic_number': row['Atomic number'],
                    'Element_symbol': row['Element symbol'],
                    'Element_name': row['Element name'],
                    'Concentration': row[pos_idx],
                    'Datapoints': row['Number of datapoints']
                })
        
        # Create DataFrame
        position_df = pd.DataFrame(data)
        
        # Add metadata
        parts = folder_name.split('_')
        image = parts[0] + ' ' + parts[1]
        analysis = parts[2] + ' ' + parts[3]
        
        position_df['Image'] = image
        position_df['Analysis'] = analysis
        position_df['Type'] = measurement_type
        position_df['Path'] = file_path
        position_df['Folder'] = folder_name
        
        return position_df

    def scan_folder(self):
        regular_data = []
        linescan_data = []
        print("Starting folder scan...")
        
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('.csv'):
                    folder_name = os.path.basename(root)
                    file_parts = file.split('_')
                    folder_parts = folder_name.split('_') if folder_name else file_parts
                    
                    # Check if this is a linescan file
                    is_linescan = 'linescan' in file.lower() or (folder_parts and 'linescan' in folder_parts)
                    
                    if len(folder_parts) >= 2:
                        # Extract image and analysis info from either folder or filename
                        if folder_name:
                            image = folder_parts[0] + ' ' + folder_parts[1]
                            analysis = folder_parts[2] + ' ' + folder_parts[3]
                        else:
                            image = file_parts[0] + ' ' + file_parts[1]
                            analysis = file_parts[2] + ' ' + file_parts[3]
                        
                        file_path = os.path.join(root, file)
                        pattern = r'EDX1-\d{3}'
                            
                        match = re.search(pattern, file_path)

                        if match:
                            edx_id = match.group()
                            print(edx_id)  # Output: EDX1-230

                        if is_linescan:
                            print(f"Found linescan file: {file}")
                            if "atomic" in file.lower():
                                df = self.process_linescan(file_path, folder_name, "linescan_atomic", edx_id)
                                if df is not None and not df.empty:
                                    linescan_data.append(df)
                                    print(f"Successfully processed atomic linescan data: {len(df)} rows")
                            elif "weight" in file.lower():
                                df = self.process_linescan(file_path, folder_name, "linescan_weight", edx_id)
                                if df is not None and not df.empty:
                                    linescan_data.append(df)
                                    print(f"Successfully processed weight linescan data: {len(df)} rows")
                        elif file.endswith('quantification.csv'):
                            # For regular EDX data, determine measurement type from folder name
                            measurement_type = folder_parts[-1] if folder_parts else "unknown"
                            
                            # Handle regular EDX data
                            csv_data = pd.read_csv(file_path)
                            
                            

                            for _, row in csv_data.iterrows():
                                element_data = {
                                    "EDX": edx_id,
                                    'Image': image,
                                    'Analysis': analysis,
                                    'Type': measurement_type,
                                    'Path': file_path,
                                    'Folder': folder_name,
                                    'Atomic_number': row['Atomic number'],
                                    'Element_symbol': row['Element symbol'],
                                    'Element_name': row['Element name'],
                                    'Atomic_concentration': row['Atomic concentration percentage'],
                                    'Weight_concentration': row['Weight concentration percentage'],
                                    'Energy_level': row['Energy level']
                                }
                                regular_data.append(element_data)
        
        # Create separate DataFrames for regular and linescan data
        self.df = pd.DataFrame(regular_data)
        if linescan_data:
            self.linescan_df = pd.concat(linescan_data, ignore_index=True)

    def save_dataframe(self, file_path):
        base, ext = os.path.splitext(file_path)
        # Save regular data
        if not self.df.empty:
            self.df.to_csv(file_path, index=False)
        # Save linescan data with _linescan suffix
        if not self.linescan_df.empty:
            linescan_path = f"{base}_linescan{ext}"
            self.linescan_df.to_csv(linescan_path, index=False)

class View:
    def __init__(self, master):
        self.frame = tk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.choose_button = tk.Button(self.frame, text="Choose Folder")
        self.choose_button.pack(pady=10)

        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Regular data tab
        self.regular_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.regular_frame, text="Regular Data")
        self.listbox = tk.Listbox(self.regular_frame)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        # Linescan data tab
        self.linescan_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.linescan_frame, text="Linescan Data")
        self.linescan_listbox = tk.Listbox(self.linescan_frame)
        self.linescan_listbox.pack(fill=tk.BOTH, expand=True)

        self.show_df_button = tk.Button(self.frame, text="Show DataFrame")
        self.show_df_button.pack(pady=10)

        self.save_df_button = tk.Button(self.frame, text="Save DataFrame")
        self.save_df_button.pack(pady=10)

    def set_choose_callback(self, callback):
        self.choose_button.config(command=callback)

    def set_show_df_callback(self, callback):
        self.show_df_button.config(command=callback)

    def set_save_df_callback(self, callback):
        self.save_df_button.config(command=callback)

    def update_listbox(self, df, linescan_df):
        # Update regular data listbox
        self.listbox.delete(0, tk.END)
        if not df.empty:
            for _, row in df.drop_duplicates(subset=['Image', 'Analysis', 'Type']).iterrows():
                self.listbox.insert(tk.END, f"{row['Image']} - {row['Analysis']} - {row['Type']}")

        # Update linescan data listbox
        self.linescan_listbox.delete(0, tk.END)
        if not linescan_df.empty:
            for _, row in linescan_df.drop_duplicates(subset=['Image', 'Analysis', 'Type']).iterrows():
                self.linescan_listbox.insert(tk.END, f"{row['Image']} - {row['Analysis']} - {row['Type']}")

    def show_dataframe(self, df, linescan_df):
        if not df.empty or not linescan_df.empty:
            top = tk.Toplevel()
            top.title("Analysis DataFrame")
            
            notebook = ttk.Notebook(top)
            notebook.pack(fill=tk.BOTH, expand=True)

            # Regular data tab
            if not df.empty:
                regular_frame = ttk.Frame(notebook)
                notebook.add(regular_frame, text="Regular Data")
                
                tree = ttk.Treeview(regular_frame)
                tree["columns"] = list(df.columns)
                tree["show"] = "headings"

                for column in tree["columns"]:
                    tree.heading(column, text=column)
                    tree.column(column, width=100)

                for _, row in df.iterrows():
                    tree.insert("", "end", values=list(row))

                scrollbar_y = ttk.Scrollbar(regular_frame, orient="vertical", command=tree.yview)
                scrollbar_x = ttk.Scrollbar(regular_frame, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

                scrollbar_y.pack(side="right", fill="y")
                scrollbar_x.pack(side="bottom", fill="x")
                tree.pack(fill=tk.BOTH, expand=True)

            # Linescan data tab
            if not linescan_df.empty:
                linescan_frame = ttk.Frame(notebook)
                notebook.add(linescan_frame, text="Linescan Data")
                
                tree = ttk.Treeview(linescan_frame)
                tree["columns"] = list(linescan_df.columns)
                tree["show"] = "headings"

                for column in tree["columns"]:
                    tree.heading(column, text=column)
                    tree.column(column, width=100)

                for _, row in linescan_df.iterrows():
                    tree.insert("", "end", values=list(row))

                scrollbar_y = ttk.Scrollbar(linescan_frame, orient="vertical", command=tree.yview)
                scrollbar_x = ttk.Scrollbar(linescan_frame, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

                scrollbar_y.pack(side="right", fill="y")
                scrollbar_x.pack(side="bottom", fill="x")
                tree.pack(fill=tk.BOTH, expand=True)

class Controller:
    def __init__(self, root):
        self.model = Model()
        self.view = View(root)
        self.view.set_choose_callback(self.choose_folder)
        self.view.set_show_df_callback(self.show_dataframe)
        self.view.set_save_df_callback(self.save_dataframe)

    def choose_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.model.set_folder_path(folder_path)
            self.model.scan_folder()
            self.view.update_listbox(self.model.df, self.model.linescan_df)

    def show_dataframe(self):
        self.view.show_dataframe(self.model.df, self.model.linescan_df)

    def save_dataframe(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv")
        if file_path:
            self.model.save_dataframe(file_path)

def main():
    root = tk.Tk()
    root.title("EDX Concat")
    root.geometry("800x600")
    app = Controller(root)
    root.mainloop()

if __name__ == "__main__":
    main()