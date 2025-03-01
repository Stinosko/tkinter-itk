# https://stackoverflow.com/questions/74512081/tkinter-window-completly-freeze-when-you-move-it
from tkinter import *
from tkinter import ttk 
import time
import threading
import win32api

root = Tk()
root.geometry('800x438')
root.resizable(False,False)
root.configure(bg='gray')


label = Label(root, text='Display content', fg='yellow', bg='black', font=('Arial', 13), width=20)
label.place(relx=0.5,rely=0.3)

animationlabel = Label(root, text='', fg='yellow', bg='black', font=('Arial', 13), width=20)
animationlabel.place(relx=0.5,rely=0.5)




firstentryvar = StringVar()
secondentryvar = StringVar()



firstentry = Entry(root, textvariable=firstentryvar , justify=CENTER, font = ('Arial', 12))
secondentry = Entry(root, textvariable=secondentryvar, justify=CENTER, font = ('Arial', 12))





def displaycontent(*args): 

    firstentry.pack()
    secondentry.pack()
    label.bind('<Button-1>', hidecontent)



def hidecontent(*args): 

    firstentry.pack_forget()
    secondentry.pack_forget()
    label.bind('<Button-1>', displaycontent)


def animation(*args): 
    animation = "░▒▒▒▒▒"
    while True: 
        animationlabel['text'] = animation
        animation = animation[1:] + animation[0]
        root.update()
        time.sleep(0.1) # for some reason this makes the animation not freeze when moving it


label.bind('<Button-1>', displaycontent)

def function1(*args): 
    count = 0
    bool = False
    while count < 10:
        time.sleep(0.1)
        for i in firstentry.get(): 
            if bool == False: 
                count +=1 
                print(i)
                bool = True
            else: 
                bool = False


def function2(*args): 
   while True: 
    if win32api.GetKeyState(0x45) < 0: 
          
          print('you pressed e')
  
    

thread1 = threading.Thread(target = lambda : function1(), daemon=True)
thread1.start()

thread2 = threading.Thread(target = lambda : function2(), daemon=True)
thread2.start()

thread3 = threading.Thread(target = lambda : animation(), daemon=True)
thread3.start()


   
root.mainloop() 