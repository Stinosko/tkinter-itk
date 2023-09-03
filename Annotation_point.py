import tkinter as tk  
from Utils import  PatchedCanvas


class Annotation_point():
    def __init__(self, unique_id, serie_ID, coords: list = [], **kwargs) -> None:
        super().__init__(**kwargs)
        self.ITK_coords = coords
        self.serie_ID = serie_ID
        self.unique_id = unique_id
        self.size = 5

    def get_ITK_coords(self):
        return self.ITK_coords
        
    def get_serie_ID(self):
        return self.serie_ID
    
    def get_unique_id(self):
        return self.unique_id
    
    def set_ITK_coords(self, ITK_coords):
        self.ITK_coords = ITK_coords

    def place_annotation_on_canvas(self, canvas: PatchedCanvas| tk.Canvas, canvas_X: int, canvas_Y: int, color: str = "red", size: int = 5, **kwargs):
        kwargs["fill"] = color
        kwargs["outline"] = "black"
        kwargs["width"] = 1
        kwargs["activefill"] = "blue"
        self.size = size

        canvas_id = canvas.create_rectangle(canvas_X - self.size, canvas_Y - self.size, canvas_X + self.size, canvas_Y + self.size, **kwargs)
        return [canvas_id]
    
    def move_annotation_on_canvas(self, canvas: PatchedCanvas| tk.Canvas, canvas_X: int, canvas_Y: int, canvas_ids: int, **kwargs):
        canvas.coords(canvas_ids[0], canvas_X - self.size, canvas_Y - self.size, canvas_X + self.size, canvas_Y + self.size)
        return canvas_ids
    