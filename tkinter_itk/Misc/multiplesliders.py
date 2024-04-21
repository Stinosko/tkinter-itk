import tkinter as tk
root = tk.Tk()
 
# Create a Scrollbar
vbar = tk.Scrollbar(root, orient = tk.VERTICAL)
vbar.grid(row=0, column=1, sticky='ns')
 
 
# Create a Canvas
canvas = tk.Canvas(root, 
                   height=200, 
                   width=300, 
                   background="lightblue", 
                   scrollregion=(0,0,500,500))
canvas.grid(row=0, column=0, sticky="news")
 
# Create wrapper frame
frame1 = tk.Frame(canvas, bg="blue")

# Configure Canvas and ScrollBar
vbar.config(command = canvas.yview)
canvas.create_window(0, 0, window=frame1, anchor="nw")
canvas.config(yscrollcommand=vbar.set)
 
 

 
 
# Create Frame 2 
frame2 = tk.Frame(frame1, bg="red")
for i in range(5):
    button = tk.Button(frame2, text="Click me!")
    button.pack(padx = 20, pady = 20)
frame2.pack(padx = 5, pady = 5)
 
 
# Create Frame 3
frame3 = tk.Frame(frame1, bg="green")
button = tk.Button(frame3, text="Click me!")
button.pack(padx = 20, pady = 20)
frame3.pack(padx = 5, pady = 5)
 
root.mainloop()