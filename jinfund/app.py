# Standard imports
from pathlib import Path
import shutil
from datetime import datetime

# Third-party imports
import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle

import tkinter as tk
from tkinter import filedialog

# Local imports
from .portfolio.transactions import DataPath, Transactions
from .analysis.tax import AutoTax

# Global variables
DATA_PATH = Path.cwd() / 'jinfund' / 'data'     # Do not change or set to directory with other files,
                                                # AS THIS WILL DELETE EVERYTHING IN THAT FOLDER
DATA_PATH.mkdir(parents=True,exist_ok=True)
DataPath.data_path = DATA_PATH

OUTPUT_PATH = Path.cwd() / 'jinfund' / 'output'
OUTPUT_PATH.mkdir(parents=True,exist_ok=True)
AutoTax.OUTPUT_PATH = OUTPUT_PATH

class MainGrid(GridLayout):
    def __init__(self, **kwargs):
        super(MainGrid, self).__init__(**kwargs)
        self.cols = 1

        self.add_widget(SettingsGrid())
        self.add_widget(ReportingGrid())

class ReportingGrid(GridLayout):
    def __init__(self, **kwargs):
        super(ReportingGrid, self).__init__(**kwargs)
        # Data
        self.fy = 2020

        # Layout
        self.padding = 10
        self.cols = 1

        self.inside = GridLayout()
        self.inside.cols = 2
        self.fy_input = TextInput(text=str(self.fy), multiline=False, size_hint=(0.5,None), height=60)  # Enter FY
        self.fy_input.bind(on_text_validate=self._update_fy)
        self.inside.add_widget(WrappedLabel(text='Enter the financial year for your report (YYYY): (Hit "Enter" to confirm)'))
        self.inside.add_widget(self.fy_input)

        self.cgt_report_btn = Button(text='Generate CGT Report', halign='center', size_hint_y=None, height=60)  # Generate CGT Report button
        self.cgt_report_btn.count = 0
        self.cgt_report_btn.bind(on_release=self._get_cgt_report)
        # Label to say exported + time

        self.cgt_details_btn = Button(text='Export CGT Details', halign='center', size_hint_y=None, height=60)  # Export CGT Details button
        self.cgt_details_btn.count = 0
        self.cgt_details_btn.bind(on_release=self._get_cgt_details)
        # Label to say exported + time

        self.add_widget(RowSpacer())
        self.add_widget(RowSpacer())
        self.add_widget(self.inside)
        self.add_widget(RowSpacer())
        self.add_widget(self.cgt_report_btn)
        self.add_widget(self.cgt_details_btn)
    
    def _get_cgt_report(self, instance):
        tax = AutoTax(financial_year=self.fy)
        tax.cgt_report()
        instance.count += 1
        instance.text = f'Generate CGT Report\nCGT Report Generated! ({instance.count})'

    def _get_cgt_details(self, instance):
        tax = AutoTax(financial_year=self.fy)
        tax.cgt_details()
        instance.count += 1
        instance.text = f'Export CGT Details\nCGT Details Exported!  ({instance.count})'
    
    def _update_fy(self, instance):
        try: fy = int(instance.text)
        except:
            instance.text = 'Must be numeric!'
            return
        
        if fy < 2015: instance.text = 'Must be 2015 or later' ; return
        if fy > datetime.today().year + 1: instance.text = 'Must be before current/next FY' ; return
        self.fy = fy

class SettingsGrid(GridLayout):
    def __init__(self, **kwargs):
        super(SettingsGrid, self).__init__(**kwargs)
        # Data
        self.fpaths = []
        self.brokers = []

        # Layout
        self.padding = 10
        self.cols = 1

        self.file_1 = FileGrid(select_type = 'broker', num=1)
        self.file_2 = FileGrid(select_type = 'broker', num=2)
        self.file_3 = FileGrid(select_type = 'dividend')
        self.output_control = FileGrid(select_type = 'output_path')
        
        submit_btn = Button(text='Load .csv files')
        submit_btn.count = 0
        submit_btn.bind(on_release=self._update_data)

        self.add_widget(self.file_1)
        self.add_widget(RowSpacer())
        self.add_widget(self.file_2)
        self.add_widget(RowSpacer())
        self.add_widget(self.file_3)
        self.add_widget(RowSpacer())
        self.add_widget(submit_btn)
        self.add_widget(RowSpacer())
        self.add_widget(self.output_control)

    def _update_data(self, instance):
        self.fpaths = [self.file_1.fpath, self.file_2.fpath, self.file_3.fpath]  # Can we make these programmatic?
        self.brokers = [self.file_1.broker_name, self.file_2.broker_name]  # Can we make these programmatic?
        instance.count += 1
        instance.text=f'Files loaded ({instance.count})'

        for f in DATA_PATH.iterdir():  # Clear data directory
            if f.stem != 'samples': f.unlink()

        for fpath in self.fpaths:  # Copy data to data directory
            if len(fpath) > 0:
                end_path = shutil.copy(fpath, DATA_PATH)
            else:
                continue
            
            broker_name = self.brokers.pop(0)
            if len(self.brokers) > 1:
                new_fname = f'{broker_name.lower()}.csv'
                new_fpath = DATA_PATH / new_fname
                Path(end_path).rename(new_fpath)
            
class FileGrid(GridLayout):
    def __init__(self, select_type:str, num:int=1, **kwargs):
        super(FileGrid, self).__init__(**kwargs)
        # Data
        self.broker_name = ''
        self.fpath = ''
        self.instruction = ''
        self.fpath_lbl_txt = 'No file selected'
        self.file_btn_txt = 'Select .csv'
        self.broker_btn_txt = 'Select Broker #1\n(Required)'

        # Layout
        self.cols = 3
        self.row_default_height=60
        
        self.select_type = select_type
        if select_type == 'output_path':
            self.file_btn_txt = 'Select output path'
            self.fpath = OUTPUT_PATH
            self.fpath_lbl_txt = str(OUTPUT_PATH)
            self.instruction = 'Output Path: '
        elif select_type == 'broker':
            if num == 2:
                self.broker_btn_txt = 'Select Broker #2\n(Optional)'
            self._add_broker_dropdown()
            self.instruction = 'Broker Trades Filepath: '
        elif select_type == 'dividend':
            self.cols=2
            self.instruction = 'Dividends Filepath (Required): '
        
        self.label_layout = GridLayout()
        self.label_layout.cols = 1
        
        self.fpath_lbl = WrappedLabel(text=self.fpath_lbl_txt)
        self.label_layout.add_widget(WrappedLabel(text=self.instruction, size_hint_y = .5))
        self.label_layout.add_widget(self.fpath_lbl)

        self.file_btn = Button(text=self.file_btn_txt)
        self.file_btn.bind(on_release=self._set_path)
        
        self.add_widget(self.label_layout)
        self.add_widget(self.file_btn)

    def _add_broker_dropdown(self):
        self.instruction = 'Broker Trade Filepath: '
        self.dropdown = DropDown()
        for broker in Transactions.brokers:
            btn = Button(text=broker.capitalize(), size_hint_y = None, height = 20)
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)
        
        broker_btn = Button(text=self.broker_btn_txt, halign='center', size_hint_x=None, width=150)
        broker_btn.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: [setattr(broker_btn,'text',x),self._update_broker_name(x)])
        self.add_widget(broker_btn)

    def _set_path(self, instance):
        root = tk.Tk()
        root.withdraw()
        if self.select_type == 'output_path':
            self.fpath = filedialog.askdirectory()
            AutoTax.output_path = Path(self.fpath)
        else:
            self.fpath = filedialog.askopenfilename()
        self.fpath_lbl.text = self.fpath

    def _update_broker_name(self, name):
        self.broker_name = name

class RowSpacer(GridLayout):
    def __init__(self, **kwargs):
        super(RowSpacer, self).__init__(**kwargs)

class WrappedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = (10,10)
        self.bind(
            width=lambda *x:
            self.setter('text_size')(self, (self.width, None)),
            texture_size=lambda *x: self.setter('height')(self, self.texture_size[1]))

class TaxJinie(App):
    def build(self):
        return MainGrid()