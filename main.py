import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

class TripApp(App):
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
        root = BoxLayout(orientation='vertical', spacing=0)
        
        # Header
        header = Label(
            text="TRIP MANAGER", 
            size_hint_y=None, height=dp(50),
            bold=True, font_size='18sp',
            canvas_before=True
        )
        with header.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(rgb=get_color_from_hex("#2c3e50"))
            self.rect = Rectangle(size=header.size, pos=header.pos)
        header.bind(size=self._update_rect, pos=self._update_rect)
        root.add_widget(header)

        # Form Container
        form = GridLayout(cols=1, spacing=dp(5), padding=dp(10), size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))

        self.inputs = {}
        fields = [
            ("Karyawan", "nama"), ("Driver", "driver"), ("Tujuan", "tujuan"),
            ("Tgl Pergi (TglBlnThn)", "tgl_p"), ("Jam Pergi (HHMM)", "jam_p"),
            ("Tgl Kembali", "tgl_k"), ("Jam Kembali", "jam_k")
        ]

        for label_text, key in fields:
            form.add_widget(Label(text=label_text, color=(0,0,0,1), size_hint_y=None, height=dp(20), halign='left', text_size=(dp(580), None)))
            ti = TextInput(multiline=False, size_hint_y=None, height=dp(40), font_size='16sp')
            # Auto format logic on focus loss
            if key in ['tgl_p', 'tgl_k']: ti.bind(focus=self.on_tgl_focus)
            if key in ['jam_p', 'jam_k']: ti.bind(focus=self.on_jam_focus)
            form.add_widget(ti)
            self.inputs[key] = ti

        root.add_widget(form)

        # Buttons Action
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5), padding=[dp(10), 0])
        btn_save = Button(text="SIMPAN", background_color=get_color_from_hex("#27ae60"), background_normal='')
        btn_save.bind(on_release=self.simpan)
        btn_edit = Button(text="EDIT", background_color=get_color_from_hex("#f39c12"), background_normal='')
        btn_edit.bind(on_release=self.edit_terpilih)
        btn_del = Button(text="HAPUS", background_color=get_color_from_hex("#e74c3c"), background_normal='')
        btn_del.bind(on_release=self.hapus)
        
        btn_layout.add_widget(btn_save)
        btn_layout.add_widget(btn_edit)
        btn_layout.add_widget(btn_del)
        root.add_widget(btn_layout)

        # History List
        root.add_widget(Label(text="RIWAYAT TERSEMPAN", color=(0,0,0,1), bold=True, size_hint_y=None, height=dp(30)))
        
        self.history_list = GridLayout(cols=1, spacing=dp(2), size_hint_y=None, padding=dp(5))
        self.history_list.bind(minimum_height=self.history_list.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 1), bar_width=dp(10))
        scroll.add_widget(self.history_list)
        root.add_widget(scroll)

        # Copy Buttons
        copy_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5), padding=dp(10))
        btn_copy_sel = Button(text="SALIN TERPILIH", background_color=get_color_from_hex("#34495e"), background_normal='')
        btn_copy_sel.bind(on_release=self.salin_terpilih)
        btn_copy_all = Button(text="SALIN SEMUA", background_color=get_color_from_hex("#0984e3"), background_normal='')
        btn_copy_all.bind(on_release=self.salin_semua)
        
        copy_layout.add_widget(btn_copy_sel)
        copy_layout.add_widget(btn_copy_all)
        root.add_widget(copy_layout)

        self.refresh_list()
        return root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    # --- Logika Data (Sama dengan kode asli) ---

    def muat_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f: return json.load(f)
            except: return []
        return []

    def simpan_ke_file(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data_riwayat, f)

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
            elif len(teks) == 4: return f"{teks[:2]}:{teks[2:]}"
        return teks

    def hitung_durasi(self, tgl_p, jam_p, tgl_k, jam_k):
        try:
            if tgl_k == "DALAM PERJALANAN" or tgl_k == "-": return "-"
            def parse_dt(t_str, j_str):
                d, m_nama, y = t_str.split()
                m = next(k for k, v in self.bulan_indo.items() if v == m_nama)
                j, menit = j_str.split(":")
                return datetime(int(y), int(m), int(d), int(j), int(menit))
            start = parse_dt(tgl_p, jam_p)
            end = parse_dt(tgl_k, jam_k)
            diff = end - start
            hari, jam = diff.days, diff.seconds // 3600
            res = []
            if hari > 0: res.append(f"{hari} Hari")
            if jam > 0: res.append(f"{jam} Jam")
            return " ".join(res) if res else "0 Jam"
        except: return "-"

    # --- Event Handlers ---

    def on_tgl_focus(self, instance, value):
        if not value: instance.text = self.format_tgl(instance.text)

    def on_jam_focus(self, instance, value):
        if not value: instance.text = self.format_jam(instance.text)

    def simpan(self, *args):
        d = [self.inputs[k].text.strip() for k in ["nama", "driver", "tujuan", "tgl_p", "jam_p", "tgl_k", "jam_k"]]
        if "" in d[:3]: return
        
        if d[5] == "" or d[6] == "":
            d[5] = "DALAM PERJALANAN"; d[6] = "-"
        
        durasi = self.hitung_durasi(d[3], d[4], d[5], d[6])
        d.append(durasi)

        if self.selected_index is not None:
            self.data_riwayat[self.selected_index] = d
            self.selected_index = None
        else:
            self.data_riwayat.append(d)
            
        self.simpan_ke_file()
        self.refresh_list()
        for k in self.inputs: self.inputs[k].text = ""

    def refresh_list(self):
        self.history_list.clear_widgets()
        self.check_boxes = []
        for i, r in enumerate(self.data_riwayat):
            row = BoxLayout(size_hint_y=None, height=dp(100), padding=dp(5))
            cb = CheckBox(size_hint_x=None, width=dp(40), color=(0,0,0,1))
            cb.group = 'history' # Allow only one selection for edit
            self.check_boxes.append(cb)
            
            txt = (f"Karyawan: {r[0]} | Driver: {r[1]}\nTujuan: {r[2]}\n"
                   f"Pergi: {r[3]} ({r[4]})\nKembali: {r[5]} ({r[6]})\nDurasi: {r[7]}")
            
            lbl = Label(text=txt, color=(0,0,0,1), font_size='12sp', halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            
            row.add_widget(cb)
            row.add_widget(lbl)
            self.history_list.add_widget(row)

    def get_selected(self):
        for i, cb in enumerate(self.check_boxes):
            if cb.active: return i
        return None

    def edit_terpilih(self, *args):
        idx = self.get_selected()
        if idx is not None:
            self.selected_index = idx
            data = self.data_riwayat[idx]
            keys = ["nama", "driver", "tujuan", "tgl_p", "jam_p", "tgl_k", "jam_k"]
            for i, k in enumerate(keys):
                val = data[i]
                self.inputs[k].text = "" if val in ["DALAM PERJALANAN", "-"] else val

    def hapus(self, *args):
        if self.data_riwayat:
            self.data_riwayat.pop()
            self.simpan_ke_file()
            self.refresh_list()

    def salin_terpilih(self, *args):
        from kivy.core.clipboard import Clipboard
        idx = self.get_selected()
        if idx is not None:
            r = self.data_riwayat[idx]
            text = f"Karyawan : {r[0]}\nDriver   : {r[1]}\nTujuan   : {r[2]}\nPergi    : {r[3]} ({r[4]})\nKembali  : {r[5]} ({r[6]})\nDurasi   : {r[7]}\n"
            Clipboard.copy(text)

    def salin_semua(self, *args):
        from kivy.core.clipboard import Clipboard
        text = ""
        for i, r in enumerate(self.data_riwayat):
            text += f"[{i+1}]\nKaryawan : {r[0]}\nDriver   : {r[1]}\nTujuan   : {r[2]}\nPergi    : {r[3]} ({r[4]})\nKembali  : {r[5]} ({r[6]})\nDurasi   : {r[7]}\n{'-'*20}\n"
        Clipboard.copy(text)

if __name__ == "__main__":
    from kivy.core.window import Window
    Window.clear_color = get_color_from_hex("#f0f2f5")
    TripApp().run()
    
