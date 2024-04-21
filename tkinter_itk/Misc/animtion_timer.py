# https://pythonguides.com/python-tkinter-animation/
import time
from tkinter import *
from tkinter import messagebox

ws = Tk()

ws.geometry("300x300")

ws.title("Python Guides")

Hour=StringVar()
Minute=StringVar()
Second=StringVar()

Hour.set("00")
Minute.set("00")
Second.set("00")

Hour_entry= Entry(ws, width=3, font=("Arial",18,""),
				textvariable=Hour)
Hour_entry.place(x=80,y=20)

Minute_entry= Entry(ws, width=3, font=("Arial",18,""),
				textvariable=Minute)
Minute_entry.place(x=130,y=20)

Second_entry= Entry(ws, width=3, font=("Arial",18,""),
				textvariable=Second)
Second_entry.place(x=180,y=20)


def OK():
	try:
		
		temp = int(Hour.get())*3600 + int(Minute.get())*60 + int(Second.get())
	except:
		print("Please Input The Correct Value")
	while temp >-1:
		
		Mins,Secs = divmod(temp,60)

	
		Hours=0
		if Mins >60:
			
	
			Hours, Mins = divmod(Mins, 60)
		
		
		Hour.set("{0:2d}".format(Hours))
		Minute.set("{0:2d}".format(Mins))
		Second.set("{0:2d}".format(Secs))

		
		ws.update()
		time.sleep(1)

		
		if (temp == 0):
			messagebox.showinfo("Time Countdown", "Time up ")
		
		
		temp -= 1


button = Button(ws, text=' countdown', bd='5',
			command= OK)
button.place(x = 100,y = 110)

ws.mainloop()