# https://stackoverflow.com/questions/70568464/tkinter-in-a-custom-widget-how-do-i-set-the-value-of-a-custom-variable-through

from tkinter import *


class My_Entry(Entry):
    # tuple of supported custom option names
    custom_options = ("my_custom_var",)

    def __init__(self, parent, *args, my_custom_var='', **kwargs):
        super().__init__(parent)
        self.configure(my_custom_var=my_custom_var, **kwargs)

    def configure(self, **kwargs):
        for key in self.custom_options:
            if key in kwargs:
                setattr(self, key, kwargs.pop(key))
        if kwargs:
            super().configure(**kwargs)

    def cget(self, key):
        if key in self.custom_options:
            return getattr(self, key)
        else:
            return super().cget(key)

#--------------


class Mainframe(Tk):
    def __init__(self):
        Tk.__init__(self)

        #self.ent1 = My_Entry(self, my_custom_var='teste')
        self.ent1 = My_Entry(self)
        self.ent1.configure(show='7')
        #self.ent1.configure(show='*', my_custom_var='teste')
        self.ent1.pack()
        return


if __name__== '__main__':
    app = Mainframe()
    app.mainloop()


