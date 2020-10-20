"""
This type stub file was generated by pyright.
"""

from typing import Any, List
from PIL.Image import Image


EPD_WIDTH = 800
EPD_HEIGHT = 480
class EPD:
    def __init__(self) -> None:
        ...
    
    def reset(self):
        ...
    
    def send_command(self, command):
        ...
    
    def send_data(self, data):
        ...
    
    def ReadBusy(self):
        ...
    
    def init(self) -> None:
        ...
    
    def getbuffer(self, image: 'Image') -> List[int]:
        ...
    
    def display(self, image: List[int]) -> Any:
        ...
    
    def Clear(self) -> None:
        ...
    
    def sleep(self) -> None:
        ...
    
    def Dev_exit(self) -> None:
        ...
    


