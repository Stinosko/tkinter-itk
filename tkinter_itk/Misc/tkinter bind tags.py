import tkinter
# https://stackoverflow.com/questions/11456631/how-to-capture-events-on-tkinter-child-widgets

def on_frame_click(e):
    print(e.widget)
    print("frame clicked")

def retag(tag, widget):
    '''Add the given tag as the first bindtag for every widget passed in'''
    "Binds an event to a widget and all its descendants."

    widget.bindtags((tag,) + widget.bindtags())

    for child in widget.children.values():
        retag(tag, child)

tk = tkinter.Tk()

class MyFrame(tkinter.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
frame = MyFrame(tk, bg="red", padx=20, pady=20)

a_frame = tkinter.Frame(frame, bg="red", padx=20, pady=20)
a_label = tkinter.Label(a_frame, text="A Label")
a_button = tkinter.Button(a_frame, text="click me!")
a_frame.pack()
a_label.pack()
a_button.pack()
tk.protocol("WM_DELETE_WINDOW", tk.destroy)
retag("special", a_frame)
tk.bind_class("special", "<Button>", on_frame_click)

b_frame = tkinter.Frame(frame, bg="blue", padx=20, pady=20)
b_label = tkinter.Label(b_frame, text="B Label")
b_button = tkinter.Button(b_frame, text="click me!")
b_frame.pack()
b_label.pack()
b_button.pack()
retag("special", b_frame)

frame.pack()

tk.mainloop()