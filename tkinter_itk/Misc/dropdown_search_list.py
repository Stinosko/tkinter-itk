import tkinter as tk
from PIL import Image, ImageTk
import time
# https://coderslegacy.com/searchable-combobox-in-tkinter/ 

class SearchableComboBox(tk.Frame):
    def __init__(self, options, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dropdown_id = None
        self.options = options
        self.timeout = 2000 # 2 seconds
        self.time_last_activity = 0

        # Create a Text widget for the entry field
        # wrapper = tk.Frame(root)
        # wrapper.grid(row=0, column=0)

        self.entry = tk.Entry(self, width=24)
        self.entry.bind("<KeyRelease>", self.on_entry_key)
        self.entry.bind("<FocusIn>", self.show_dropdown) 
        self.entry.bind("<Return>", lambda event: self.add_option(self.entry.get(), show_dropdown=True))
        self.entry.bind("<FocusOut>", lambda event: self.hide_dropdown)
        self.entry.bind("<Button-1>", self.show_dropdown)
        self.entry.bind("<Escape>", lambda event: self.hide_dropdown)
        self.entry.grid(row=0, column=0, sticky="ew")

        self.entry2 = tk.Entry(self, width=24)
        self.entry2.grid(row=1, column=0, sticky="ew")

        # Dropdown icon/button
        # self.icon = ImageTk.PhotoImage(Image.open(r"C:\Users\sschatte00\Downloads\Projects\tkinter-itk\tkinter_itk\Misc\dopdown_arrow.jpg").resize((16,16)))
        tk.Button(self, command=self.show_dropdown).grid(row=0, column=1, sticky="ew")

        # Create a Listbox widget for the dropdown menu
        self.listbox = tk.Listbox(self.master, height=5, width=30)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Double-Button-1>", lambda event: self.on_select(event, hide_dropdown=True))
        self.listbox.bind("<Motion>", self.event_activity)
        for option in self.options:
            self.listbox.insert(tk.END, option)

    def on_entry_key(self, event):
            self.time_last_activity = time.time()
            typed_value = event.widget.get().strip().lower()
            if not typed_value:
                # If the entry is empty, display all options
                self.listbox.delete(0, tk.END)
                for option in self.options:
                    self.listbox.insert(tk.END, option)
            else:
                # Filter options based on the typed value
                self.listbox.delete(0, tk.END)
                filtered_options = [option for option in self.options if option.lower().startswith(typed_value)]
                for option in filtered_options:
                    self.listbox.insert(tk.END, option)
            self.show_dropdown()

    def on_select(self, event, hide_dropdown=False):
            self.time_last_activity = time.time()
            selected_index = self.listbox.curselection()
            if selected_index:
                selected_option = self.listbox.get(selected_index)
                self.entry.delete(0, tk.END)
                self.entry.insert(0, selected_option)
                if hide_dropdown:
                    self.hide_dropdown(force=True)
            self.event_generate("<<ComboboxSelected>>")
    def show_dropdown(self, event=None):
            self.time_last_activity = time.time()
            self.listbox.place(x=self.entry.winfo_x(), y=self.entry.winfo_y() + self.entry.winfo_height())
            self.listbox.lift()

            # Show dropdown for 2 seconds
            if self.dropdown_id: # Cancel any old events
                self.listbox.after_cancel(self.dropdown_id)
            self.dropdown_id = self.listbox.after(self.timeout, self.hide_dropdown)

    def add_option(self, option, show_dropdown=False):
        self.time_last_activity = time.time()
        if option == "":
            return
        if option not in self.options:
            self.options.append(option)
            self.update_dropdown()
            if show_dropdown:
               self.show_dropdown()

    def update_dropdown(self):
        self.time_last_activity = time.time()
        typed_value = self.entry.get().strip().lower()
        self.listbox.delete(0, tk.END)
        for option in self.options:
            if option.lower().startswith(typed_value):
                self.listbox.insert(tk.END, option)

    def update_options(self, options):
        self.time_last_activity = time.time()
        self.options = options
        self.update_dropdown()

    def event_activity(self, event):
        self.time_last_activity = time.time()


    def hide_dropdown(self, force=False):
        if force:
            self.time_last_activity = 0
            self.listbox.place_forget()
        ms_since_last_activity = (time.time() - self.time_last_activity) * 1000
        print(f"Time since last activity: {ms_since_last_activity}")
        if ms_since_last_activity > self.timeout:
            print("Hiding dropdown")
            self.time_last_activity = 0
            self.listbox.place_forget()
        else:
            print(self.timeout - ms_since_last_activity)
            self.listbox.after(int(self.timeout - ms_since_last_activity), self.hide_dropdown)

# Create the main window
root = tk.Tk()
root.title("Searchable Dropdown")

options = ["Apple", "Banana", "Cherry", "Date", "Grapes", "Kiwi", "Mango", "Orange", "Peach", "Pear"]
search = SearchableComboBox(options, root)
search.grid(row=0, column=0)

label = tk.Label(root, text="Placeholder")
label.grid(row=1, column=0)

def on_select(event):
    print(event)
    print(search.entry.get())

search.bind("<<ComboboxSelected>>", on_select)


# Run the Tkinter event loop
root.geometry('220x150')
root.mainloop()