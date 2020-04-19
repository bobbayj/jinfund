# Standard imports
from pathlib import Path
import shutil

# Third-party imports
import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle

import tkinter as tk
from tkinter import filedialog

# Local imports
from portfolio.transactions import Transactions

# Global variables
DATA_PATH = Path.cwd() / 'data'

class MainGrid(GridLayout):
    def __init__(self, **kwargs):
        super(MainGrid, self).__init__(**kwargs)
        # Data
        self.fpaths = []
        self.brokers = []

        # Layout
        self.padding = 20
        self.cols = 1

        self.file_1 = FileGrid(broker=True)
        self.file_2 = FileGrid(broker=True)
        self.file_3 = FileGrid(broker=False)
        
        submit_btn = Button(text='Load .csv files')
        submit_btn.bind(on_release=self._update_data)

        self.add_widget(self.file_1)
        self.add_widget(RowSpacer())
        self.add_widget(self.file_2)
        self.add_widget(RowSpacer())
        self.add_widget(self.file_3)
        self.add_widget(RowSpacer())
        self.add_widget(submit_btn)

    def _update_data(self, instance):
        self.fpaths = [self.file_1.fpath, self.file_2.fpath, self.file_3.fpath]  # Can we make these programmatic?
        self.brokers = [self.file_1.broker_name, self.file_2.broker_name]  # Can we make these programmatic?

        for f in DATA_PATH.iterdir():  # Clear directory
            if f.stem != 'samples': f.unlink()

        for fpath in self.fpaths:
            if len(fpath) > 0:
                shutil.copy(fpath, DATA_PATH)
    
class FileGrid(GridLayout):
    def __init__(self, broker:bool, **kwargs):
        super(FileGrid, self).__init__(**kwargs)
        self.cols = 3
        self.fpath = ''
        self.broker_name = ''
        self.row_force_default=True
        self.row_default_height=100
        
        if broker:
            self.instruction = 'Broker Trade Filepath: '
            self.dropdown = DropDown()
            for broker in Transactions.brokers:
                btn = Button(text=broker.capitalize(), size_hint_y = None, height = 20)
                btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
                self.dropdown.add_widget(btn)
            
            broker_btn = Button(text='Select Broker', size_hint_x=None, width=150)
            broker_btn.bind(on_release=self.dropdown.open)
            self.dropdown.bind(on_select=lambda instance, x: [setattr(broker_btn,'text',x),self._update_broker_name(x)])
            self.add_widget(broker_btn)
        else:
            self.cols=2
            self.instruction = 'Dividends Filepath: '
        
        self.label_layout = GridLayout()
        self.label_layout.cols = 1
        
        self.fpath_lbl = Label(text='No file selected', padding_x=10)
        self.label_layout.add_widget(Label(text=self.instruction, size_hint_y = .5))
        self.label_layout.add_widget(self.fpath_lbl)

        self.csv_btn = Button(text='Select .csv')
        self.csv_btn.bind(on_release=self._set_path)
        
        self.add_widget(self.label_layout)
        self.add_widget(self.csv_btn)

    def _set_path(self, instance):
        root = tk.Tk()
        root.withdraw()
        self.fpath = filedialog.askopenfilename()
        self.fpath_lbl.text = self.fpath
        self._wrap_text(self.fpath_lbl)
    
    def _wrap_text(self, instance):
        instance.text_size = (instance.width, None)
        instance.height = instance.texture_size[1]

    def _update_broker_name(self, name):
        self.broker_name = name

class RowSpacer(GridLayout):
    def __init__(self, **kwargs):
        super(RowSpacer, self).__init__(**kwargs)
        self.cols = 1
        self.row_force_default=True
        self.row_default_height=10

        self.add_widget(Label())


class TaxJinie(App):
    def build(self):
        return MainGrid()



    
if __name__ == "__main__":
    TaxJinie().run()