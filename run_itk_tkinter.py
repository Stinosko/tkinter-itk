import tkinter as tk
from tkinter_itk import ITK_viewer
import SimpleITK as sitk
import asyncio

if __name__ == "__main__":
    mainwindow = ITK_viewer.MainWindow(tk.Tk(), threading=False)
    mainwindow.mainloop()