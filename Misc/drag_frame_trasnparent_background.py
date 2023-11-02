# https://stackoverflow.com/questions/37280004/tkinter-how-to-drag-and-drop-widgets
import tkinter as tk
from PIL import Image, ImageTk
import os


def make_draggable(widget):
    widget.bind("<Button-1>", on_drag_start)
    widget.bind("<B1-Motion>", on_drag_motion)

def on_drag_start(event):
    widget = event.widget
    widget._drag_start_x = event.x
    widget._drag_start_y = event.y

def on_drag_motion(event):
    widget = event.widget
    x = widget.winfo_x() - widget._drag_start_x + event.x
    y = widget.winfo_y() - widget._drag_start_y + event.y
    widget.place(x=x, y=y)


class DragDropMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        make_draggable(self)


# As always when it comes to mixins, make sure to
# inherit from DragDropMixin FIRST!
class DnDFrame(DragDropMixin, tk.Frame):
    pass

# This wouldn't work:
# class DnDFrame(tk.Frame, DragDropMixin):
#     pass
class DnDLabel(DragDropMixin, tk.Label):
    pass

main = tk.Tk()
main.geometry("800x800")
main.config(bg = 'red')

image_label = DnDLabel(main, bg = 'white')
image = ImageTk.PhotoImage(Image.open(os.path.join(os.getcwd(), "images", "twitter.png")))
image_label.config(image=image)
image_label.place(x=10, y=10)

main.wm_attributes("-transparentcolor", 'white')
main.mainloop()