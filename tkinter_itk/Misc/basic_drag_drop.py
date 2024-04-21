import tkinter

global grid
global widget


def clone_widget(widget, master=None):
    """
    https://stackoverflow.com/questions/46505982/is-there-a-way-to-clone-a-tkinter-widget
    Create a cloned version o a widget

    Parameters
    ----------
    widget : tkinter widget
        tkinter widget that shall be cloned.
    master : tkinter widget, optional
        Master widget onto which cloned widget shall be placed. If None, same master of input widget will be used. The
        default is None.

    Returns
    -------
    cloned : tkinter widget
        Clone of input widget onto master widget.

    """
    # Get main info
    parent = master if master else widget.master
    cls = widget.__class__

    # Clone the widget configuration
    cfg = {key: widget.cget(key) for key in widget.configure()}
    cloned = cls(parent, **cfg)

    # Clone the widget's children
    for child in widget.winfo_children():
        child_cloned = clone_widget(child, master=cloned)
        if child.grid_info():
            grid_info = {k: v for k, v in child.grid_info().items() if k not in {'in'}}
            child_cloned.grid(**grid_info)
        elif child.place_info():
            place_info = {k: v for k, v in child.place_info().items() if k not in {'in'}}
            child_cloned.place(**place_info)
        else:
            pack_info = {k: v for k, v in child.pack_info().items() if k not in {'in'}}
            child_cloned.pack(**pack_info)

    return cloned


# inspiration https://github.com/TechDudie/tkinterDnD/blob/main/tkinterDnD.py
def make_draggable(widget):
  widget.bind("<Button-1>", on_drag_start)
  widget.bind("<B1-Motion>", on_drag_motion)
  widget.bind("<ButtonRelease-1>", on_drag_release)

def on_drag_start(event):
  global widget
  widget = clone_widget(event.widget)
  widget._drag_start_x = event.x
  widget._drag_start_y = event.y

def on_drag_motion(event):
  global widget
  x = event.widget.winfo_x() + event.x - widget._drag_start_x
  y = event.widget.winfo_y() + event.y - widget._drag_start_y
  widget.place(x=x, y=y)

def on_drag_release(event):
  global widget, tk
  x = event.widget.winfo_x() + event.x + tk.winfo_rootx()
  y = event.widget.winfo_y() + event.y + tk.winfo_rooty()
  widget.place_forget()

  tk.update_idletasks()
  print(tk.winfo_containing(x,y))
  widget._nametowidget(tk.winfo_containing(x,y, displayof=".")).configure(bg = "blue")

  widget.destroy()
  
def set_grid(measure):
  global grid
  grid = measure


global tk
tk = tkinter.Tk()
tk.geometry("800x800")
tk.title("tkinterDnD")
frame = tkinter.Frame(tk, bd=4, height=64, width=64, bg="red")
frame.grid(row=0,column=0)
make_draggable(frame)
label = tkinter.Label(frame, text="Hello", bg="red", wraplength=64, justify=tkinter.CENTER)
label.config(highlightbackground="black")
label.grid(row=0,column=0)
# make_draggable_component(label)
frame = tkinter.Frame(tk, bd=4, height=64, width=64, bg="green")
frame.grid(row=0,column=1)
make_draggable(frame)
label = tkinter.Label(frame, text="World", bg="green", wraplength=64, justify=tkinter.CENTER)
label.config(highlightbackground="black")
label.grid(row=0,column=0)
# make_draggable_component(label)

grid = tkinter.Frame(tk)

# create label grid of 16x16
for i in range(16):
    for j in range(16):
        frame = tkinter.Frame(grid, bd=4, height=32, width=32, bg="white")
        frame.grid(row=i+1,column=j)
        label = tkinter.Label(frame, text="Hello", bg="white", wraplength=32, justify=tkinter.CENTER)
        label.config(highlightbackground="black")
        label.grid(row=0,column=0)
        # make_draggable_component(label)
        # label
grid.grid(row=1,column=0, columnspan=16)

tk.mainloop() 