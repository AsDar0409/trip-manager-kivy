import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.core.clipboard import Clipboard

# TEMA: BIRU MUDA
Window.clearcolor = get_color_from_hex("#e3f2fd")

class ModernInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.background_normal = ""
        self.background_active = ""
        self.background_color = get_color_from_hex("#ffffff")
        self.foreground_color = get_color_from_hex("#01579b")
        self.cursor_color = get_color_from_hex("#0288d1")
        self.padding = [15, 12]
        self.font_size = '16sp'
        self.write_tab = False 

class TripAppKivy(App):
    def build(self):
        self.title = "Modern Trip Manager v11 Blue"
        self.filename = "data_perjalanan.json"
        self.bulan_indo = {
            "1": "Januari", "2": "Februari", "3": "Maret", "4": "April",
            "5": "Mei", "6": "Juni", "7": "Juli", "8": "Agustus",
            "9": "September", "10": "Oktober", "11": "November", "12": "Desember"
        }
        self.data_riwayat = self.muat_data()
        self.check_states = []

        Window.bind(on_key_down=self.on_global_key_down)

        self.main_layout = BoxLayout(orientation='vertical', padding=[15, 20, 15, 15], spacing=15)

        header = Label(text="PERJALANAN", size_hint_y=None, height=60,
                      color=get_color_from_hex("#0277bd"), font_size='26sp', bold=True)
        self.main_layout.add_widget(header)

        input_container = BoxLayout(orientation='vertical', size_hint_y=None, height=350, spacing=10)
        form = GridLayout(cols=2, spacing=12, size_hint_y=None, height=340)
        
        self.ent_nama = self.add_modern_item(form, "Karyawan")
        self.ent_driver = self.add_modern_item(form, "Driver")
        self.ent_tujuan = self.add_modern_item(form, "Tujuan")

        form.add_widget(self.create_label("Pergi"))
        box_p = BoxLayout(spacing=8)
        self.ent_tgl_p = ModernInput(size_hint_x=0.65)
        self.ent_jam_p = ModernInput(size_hint_x=0.35)
        box_p.add_widget(self.ent_tgl_p); box_p.add_widget(self.ent_jam_p)
        form.add_widget(box_p)

        form.add_widget(self.create_label("Kembali"))
        box_k = BoxLayout(spacing=8)
        self.ent_tgl_k = ModernInput(size_hint_x=0.65)
        self.ent_jam_k = ModernInput(size_hint_x=0.35)
        box_k.add_widget(self.ent_tgl_k); box_k.add_widget(self.ent_jam_k)
        form.add_widget(box_k)
        
        input_container.add_widget(form)
        self.main_layout.add_widget(input_container)

        self.input_list = [self.ent_nama, self.ent_driver, self.ent_tujuan, self.ent_tgl_p, self.ent_jam_p, self.ent_tgl_k, self.ent_jam_k]
        for i, widget in enumerate(self.input_list):
            widget.bind(on_text_validate=lambda x, idx=i: self.next_focus(idx))

        btn_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.add_btn(btn_box, "SAVE DATA", "#0288d1", self.simpan)
        self.add_btn(btn_box, "EDIT", "#f57c00", self.edit_terpilih)
        self.add_btn(btn_box, "DELETE", "#d32f2f", self.hapus)
        self.main_layout.add_widget(btn_box)

        self.scroll = ScrollView()
        self.history_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=12)
        self.history_list.bind(minimum_height=self.history_list.setter('height'))
        self.scroll.add_widget(self.history_list)
        self.main_layout.add_widget(self.scroll)

        copy_box = BoxLayout(size_hint_y=None, height=70, spacing=10)
        self.add_btn(copy_box, "COPY SELECTED", "#546e7a", self.salin_terpilih)
        self.add_btn(copy_box, "COPY ALL", "#1565c0", self.salin_semua)
        self.main_layout.add_widget(copy_box)

        self.refresh()
        return self.main_layout

    def on_global_key_down(self, window, key, scancode, codepoint, modifier):
        for i, widget in enumerate(self.input_list):
            if widget.focus:
                if key == 273 and i > 0:
                    self.input_list[i-1].focus = True
                    return True
                elif key == 274 and i < len(self.input_list) - 1:
                    self.input_list[i+1].focus = True
                    return True
                elif key == 8 and widget.text == "":
                    if i > 0:
                        self.input_list[i-1].focus = True
                        return True
        return False

    def create_label(self, text):
        return Label(text=text, color=get_color_from_hex("#01579b"), 
                    font_size='14sp', bold=True, halign='left', valign='middle', size_hint_x=0.25)

    def add_modern_item(self, parent, label_text):
        parent.add_widget(self.create_label(label_text))
        inp = ModernInput(size_hint_x=0.75)
        parent.add_widget(inp)
        return inp

    def add_btn(self, parent, text, color, cmd):
        btn = Button(text=text, background_normal="", background_color=get_color_from_hex(color),
                     font_size='18sp', bold=True)
        btn.bind(on_release=lambda x: cmd())
        parent.add_widget(btn)

    def next_focus(self, idx):
        if idx in [3, 5]: self.input_list[idx].text = self.format_tgl_modern(self.input_list[idx].text)
        if idx in [4, 6]: self.input_list[idx].text = self.format_jam_modern(self.input_list[idx].text)
        if idx < len(self.input_list) - 1:
            self.input_list[idx+1].focus = True
        else:
            self.simpan()

    # --- LOGIKA TANGGAL CERDAS (FIX 10, 11, 12) ---
    def format_tgl_modern(self, teks):
        teks = teks.strip()
        if not teks.isdigit(): return teks
        
        d, m, y = "", "", ""
        length = len(teks)
        
        if length == 5: # Contoh: 61126
            d = teks[0].zfill(2)
            m = teks[1:3] # Coba ambil 2 digit bulan (10, 11, 12)
            if m not in ["10", "11", "12"]:
                m = teks[1] # Jika bukan 10-12, ambil 1 digit
                y = "20" + teks[2:]
            else:
                y = "20" + teks[3:]
        elif length == 4: # Contoh: 6226
            d, m, y = teks[0].zfill(2), teks[1], "20"+teks[2:]
        elif length == 6: # Contoh: 061126
            d, m, y = teks[:2], teks[2:4].lstrip('0'), "20"+teks[4:]
        elif length == 8: # Contoh: 06112026
            d, m, y = teks[:2], teks[2:4].lstrip('0'), teks[4:]
            
        if m in self.bulan_indo:
            return f"{d} {self.bulan_indo[m]} {y}"
        return teks

    def format_jam_modern(self, teks):
        teks = "".join(filter(str.isdigit, teks))
        if len(teks) == 3: return f"0{teks[0]} : {teks[1:]}"
        elif len(teks) == 4: return f"{teks[:2]} : {teks[2:]}"
        return teks

    def hitung_durasi(self, tgl_p, jam_p, tgl_k, jam_k):
        try:
            if tgl_k in ["DALAM PERJALANAN", "-", ""]: return "-"
            def parse_dt(t_str, j_str):
                parts = t_str.split()
                d, m_nama, y = parts[0], parts[1], parts[2]
                m = next(k for k, v in self.bulan_indo.items() if v == m_nama)
                j, menit = j_str.replace(" ", "").split(":")
                return datetime(int(y), int(m), int(d), int(j), int(menit))
            start, end = parse_dt(tgl_p, jam_p), parse_dt(tgl_k, jam_k)
            diff = end - start
            h, j = diff.days, diff.seconds // 3600
            res = []
            if h > 0: res.append(f"{h} hari")
            if j > 0: res.append(f"{j} jam")
            return " ".join(res) if res else "0 jam"
        except: return "-"

    def muat_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f: return json.load(f)
            except: return []
        return []

    def simpan_ke_file(self):
        with open(self.filename, 'w') as f: json.dump(self.data_riwayat, f)

    def simpan(self):
        self.ent_tgl_p.text = self.format_tgl_modern(self.ent_tgl_p.text)
        self.ent_tgl_k.text = self.format_tgl_modern(self.ent_tgl_k.text)
        self.ent_jam_p.text = self.format_jam_modern(self.ent_jam_p.text)
        self.ent_jam_k.text = self.format_jam_modern(self.ent_jam_k.text)
        d = [e.text.strip() for e in self.input_list]
        if not d[0]: return 
        if not d[5]: d[5] = "DALAM PERJALANAN"; d[6] = "-"
        durasi = self.hitung_durasi(d[3], d[4], d[5], d[6])
        d.append(durasi)
        idx = self.get_checked_index()
        if idx is not None: self.data_riwayat[idx] = d
        else: self.data_riwayat.append(d)
        self.simpan_ke_file(); self.refresh(); self.reset()

    def refresh(self):
        self.history_list.clear_widgets()
        self.check_states = [False] * len(self.data_riwayat)
        for i, r in enumerate(self.data_riwayat):
            item = BoxLayout(size_hint_y=None, height=190, padding=12)
            with item.canvas.before:
                Color(rgb=get_color_from_hex("#ffffff"))
                RoundedRectangle(pos=item.pos, size=item.size, radius=[10])
            item.bind(pos=self._update_rect, size=self._update_rect)

            cb = CheckBox(size_hint_x=0.08, color=get_color_from_hex("#0288d1"))
            cb.bind(active=lambda inst, val, idx=i: self.update_cb(idx, val))
            
            txt_container = GridLayout(cols=2, size_hint_x=0.92, padding=[10, 0])
            def add_data_row(label, value, color="#01579b"):
                lbl = Label(text=f"[b]{label}[/b]", markup=True, color=get_color_from_hex("#0288d1"),
                            font_size='16sp', size_hint_x=0.3, halign='left', valign='middle')
                lbl.bind(size=lbl.setter('text_size'))
                val = Label(text=f":  {value}", markup=True, color=get_color_from_hex(color),
                            font_size='16sp', size_hint_x=0.7, halign='left', valign='middle')
                val.bind(size=val.setter('text_size'))
                txt_container.add_widget(lbl)
                txt_container.add_widget(val)

            add_data_row("Karyawan", r[0])
            add_data_row("Driver", r[1])
            add_data_row("Pergi", f"{r[3]} ({r[4]})")
            add_data_row("Kembali", f"{r[5]} ({r[6]})")
            add_data_row("Durasi", r[7], "#2e7d32")
            
            item.add_widget(cb)
            item.add_widget(txt_container)
            self.history_list.add_widget(item)

    def _update_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(rgb=get_color_from_hex("#ffffff"))
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10])

    def update_cb(self, idx, val): self.check_states[idx] = val
    def get_checked_index(self):
        for i, s in enumerate(self.check_states):
            if s: return i
        return None

    def edit_terpilih(self):
        idx = self.get_checked_index()
        if idx is not None:
            data = self.data_riwayat[idx]
            self.reset()
            for i in range(len(self.input_list)):
                val = data[i]
                if val in ["DALAM PERJALANAN", "-"]: val = ""
                self.input_list[i].text = str(val)

    def hapus(self):
        idx = self.get_checked_index()
        if idx is not None: self.data_riwayat.pop(idx)
        elif self.data_riwayat: self.data_riwayat.pop()
        self.simpan_ke_file(); self.refresh()

    def reset(self):
        for e in self.input_list: e.text = ""
        self.ent_nama.focus = True

    def salin_terpilih(self):
        text = ""
        for i, s in enumerate(self.check_states):
            if s:
                r = self.data_riwayat[i]
                text += f"Karyawan: {r[0]} | Driver: {r[1]} | Durasi: {r[7]}\n"
        if text: Clipboard.copy(text)

    def salin_semua(self):
        text = ""
        for r in self.data_riwayat:
            text += f"Karyawan: {r[0]} | Driver: {r[1]} | Durasi: {r[7]}\n"
        if text: Clipboard.copy(text)

if __name__ == "__main__":
    TripAppKivy().run()
        
