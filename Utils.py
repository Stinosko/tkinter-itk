import tkinter as tk  
import logging
import functools
# https://stackoverflow.com/questions/38329996/enable-mouse-wheel-in-spinbox-tk-python
class Spinbox(tk.Spinbox):
    def __init__(self, *args, **kwargs):
        tk.Spinbox.__init__(self, *args, **kwargs)
        self.bind('<MouseWheel>', self.mouseWheel)
        self.bind('<Button-4>', self.mouseWheel)
        self.bind('<Button-5>', self.mouseWheel)

    def mouseWheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.invoke('buttondown')
        elif event.num == 4 or event.delta == 120:
            self.invoke('buttonup')

from timeit import default_timer as timer



def timer_func(FPS_target=30):
    def decorator(func):
        def wrapper(*args, **kwargs):
            t1 = timer()
            result = func(*args, **kwargs)
            t2 = timer()
            if t2-t1 > 1/FPS_target: #30 FPS
                logging.info(f'{func.__name__} from {func.__module__} executed in {(t2-t1):.6f}s')
            return result
        return wrapper
    return decorator

class PatchedLabel(tk.Label):
    def unbind(self, sequence, funcid=None):
        '''
        See:
            http://stackoverflow.com/questions/6433369/
            deleting-and-changing-a-tkinter-event-binding-in-python
        '''

        if not funcid:
            self.tk.call('bind', self._w, sequence, '')
            return
        func_callbacks = self.tk.call(
            'bind', self._w, sequence, None).split('\n')
        new_callbacks = [
            l for l in func_callbacks if l[6:6 + len(funcid)] != funcid]
        self.tk.call('bind', self._w, sequence, '\n'.join(new_callbacks))
        self.deletecommand(funcid)

class PatchedFrame(tk.Frame):
    def unbind(self, sequence, funcid=None):
        '''
        See:
            http://stackoverflow.com/questions/6433369/
            deleting-and-changing-a-tkinter-event-binding-in-python
        '''

        if not funcid:
            self.tk.call('bind', self._w, sequence, '')
            return
        func_callbacks = self.tk.call(
            'bind', self._w, sequence, None).split('\n')
        new_callbacks = [
            l for l in func_callbacks if l[6:6 + len(funcid)] != funcid]
        self.tk.call('bind', self._w, sequence, '\n'.join(new_callbacks))
        self.deletecommand(funcid)

# https://stackoverflow.com/questions/43731784/tkinter-canvas-scrollbar-with-grid
class HoverButton(tk.Button):
    """ Button that changes color to activebackground when mouse is over it. """

    def __init__(self, master, **kw):
        super().__init__(master=master, **kw)
        self.default_Background = self.cget('background')
        self.hover_Background = self.cget('activebackground')
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, e):
        self.config(background=self.hover_Background)

    def on_leave(self, e):
        self.config(background=self.default_Background)