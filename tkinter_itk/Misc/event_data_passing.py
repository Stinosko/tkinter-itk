from tkinter import *
#  https://stackoverflow.com/questions/16369947/python-tkinterhow-can-i-fetch-the-value-of-data-which-was-set-in-function-eve

def handle_it(event):
    # print "event handler"
    print(event.data, type(event.data))
    

def bind_event_data(widget, sequence, func, add = None):
    def _substitute(*args, **kwargs):
        e = lambda: None #simplest object with __dict__
        print(args)
        e.data = args[0] # Convert string to python object
        e.widget = widget
        return (e,)

    funcid = widget._register(func, _substitute, needcleanup=1)
    cmd = '{0}if {{"[{1} %d]" == "break"}} break\n'.format('+' if add else '', funcid)
    widget.tk.call('bind', widget._w, sequence, cmd)
    return funcid # Needed to unbind the event later

root = Tk()

# unfortunately, does not work with my snippet (the data argument is eval-ed)
# you can adapt it to handle raw string.
root.after(100, lambda : root.event_generate('<<test>>', data="hi there"))
# works, but definitely looks too hacky
root.after(200, lambda : root.event_generate('<<test>>', data="'hi there'"))
# the way I typically use it
root.after(300, lambda : root.event_generate('<<test>>', data={"content": "hi there"}))
# Passing any object as data
root.after(400, lambda : root.event_generate('<<test>>', data=Widget))
# Passing multiple arguments
root.after(500, lambda : root.event_generate('<<test>>', y = 3, data=Widget, x = 1))
# Passing multiple arguments
root.after(700, lambda : root.event_generate('<<test>>', data="This should not work, unbind not work after 600ms"))

#should be:
#  root.bind('<<test>>', handle_it)
bind = bind_event_data(root, '<<test>>', handle_it)

print(bind)

root.after(600, lambda:  root.unbind('<<test>>', bind))

# self destruction
root.after(1500, root.destroy)

root.mainloop()