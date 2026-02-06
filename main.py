import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.properties import StringProperty, ListProperty
from kivy.utils import get_color_from_hex

class TripApp(App):
    data_riwayat = ListProperty([])

    def build(self):
        self.title = "Trip Manager Pro v10"
        self.filename = "data_perjalanan.json"
        self.bulan_indo = {
            "1": "Januari", "2": "Februari", "3": "Maret", "4": "April",
            "5": "Mei", "6": "Juni", "7": "Juli", "8": "Agustus",
            "9": "September", "10": "Oktober", "11": "November", "12": "Desember"
        }
        self.data_riwayat = self.muat_data()
        self.selected_index = None

        # Main Layout
        root = BoxLayout(orientation='vertical', spacing=5, padding=10)
        
        # Header
        header = Label(text="TRIP MANAGER", size_hint_y=None, height=50, 
                       bold=True, color=(1,1,1,1))
        root.add_widget(header)

        # Form Input
        form = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=300)
        self.inputs = {
            'nama': TextInput(hint_text="Nama Karyawan", multiline=False),
            'driver': TextInput(hint_text="Driver", multiline=False),
            'tujuan': TextInput(hint_text="Tujuan", multiline=False),
            'tgl_p': TextInput(hint_text="Tgl Pergi (Contoh: 06226)", multiline=False),
            'jam_p': TextInput(hint_text="Jam Pergi (Contoh: 0800)", multiline=False),
            'tgl_k': TextInput(hint_text="Tgl Kembali (Kosongkan jika jalan)", multiline=False),
            'jam_k': TextInput(hint_text="Jam Kembali", multiline=False),
        }
        
        for key in self.inputs:
            form.add_widget(self.inputs[key])
        root.add_widget(form)

        # Buttons Control
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=5)
        btn_box.add_widget(Button(text="SIMPAN", background_color=get_color_from_hex('#27ae60'), on_press=self.simpan))
        btn_box.add_widget(Button(text="HAPUS", background_color=get_color_from_hex('#e74c3c'), on_press=self.hapus_terakhir))
        root.add_widget(btn_box)

        # History List
        self.history_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.history_layout)
        root.add_widget(scroll)

        self.refresh_list()
        return root

    def format_tgl(self, teks):
        if not teks or not teks.isdigit(): return teks
        day, month, year = "", "", "2026"
        if len(teks) == 4:
            day = teks[0].zfill(2); month = teks[1:2]; year = "20" + teks[2:]
        elif len(teks) == 6:
            day = teks[:2]; month = teks[2:3]
            year = teks[3:] if len(teks[3:]) == 4 else "20" + teks[4:]
        elif len(teks) >= 7:
            day = teks[:2]; month = str(int(teks[2:4])); year = teks[4:]
        
        if month in self.bulan_indo:
            return f"{day} {self.bulan_indo[month]} {year}"
        return teks

    def format_jam(self, teks):
        if teks.isdigit():
            if len(teks) == 3: return f"0{teks[0]}:{teks[1:]}"
            elif len(teks) == 4: return f
