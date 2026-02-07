import json
import os
import uuid
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
# 
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock

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
        self.padding = [10, 12]
        self.font_size = '14sp'
        self.write_tab = False 

class TripAppKivy(App):
    def build(self):
        self.title = "Fleet Tracker v31 Rounded-UI"
        self.filename = "data_perjalanan.json"
        
        # --- DATA MASTER ---
        self.list_karyawan = sorted(["Asep", "Muklis", "Rehan", "Fachrul", "Alfin", "Luthfi", "Yohanes"])
        self.list_driver = sorted(["Andik", "Rosi", "Adi", "Agus", "Indrayana", "Arif", "Yusuf", "Huda", "Yayah"])
        self.list_tgl = [str(i).zfill(2) for i in range(1, 32)]
        self.list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        self.list_thn = ["2025", "2026", "2027", "2028", "2029", "2030"]
        self.list_jam = [str(i).zfill(2) for i in range(24)]
        self.list_menit = [str(i).zfill(2) for i in range(60)]
        
        self.dropdown_objects = {}
        self.is_auto_opening = True 
        self.undo_stack = None 
        self.current_edit_id = None 
        
        self.data_riwayat = self.muat_dan_konversi_data()
        self.filtered_data = list(self.data_riwayat)
        self.check_states = {}

        self.main_layout = BoxLayout(orientation='vertical', padding=[15, 10, 15, 10], spacing=8)
        self.main_layout.add_widget(Label(text="PERJALANAN", size_hint_y=None, height=40, color=get_color_from_hex("#0277bd"), font_size='22sp', bold=True))

        # Form Input
        form = GridLayout(cols=2, spacing=8, size_hint_y=None, height=330)
        self.ent_nama = ModernInput(); self.setup_dropdown(self.ent_nama, self.list_karyawan)
        form.add_widget(self.create_label("Karyawan")); form.add_widget(self.ent_nama)
        self.ent_driver = ModernInput(); self.setup_dropdown(self.ent_driver, self.list_driver)
        form.add_widget(self.create_label("Driver")); form.add_widget(self.ent_driver)
        self.ent_tujuan = ModernInput(); form.add_widget(self.create_label("Tujuan")); form.add_widget(self.ent_tujuan)

        # Baris Pergi & Kembali
        for label, prefix in [("Pergi", "p"), ("Kembali", "k")]:
            form.add_widget(self.create_label(label))
            box = BoxLayout(spacing=4)
            for part, list_data, width in [("tgl", self.list_tgl, 0.2), ("bln", self.list_bln, 0.35), ("thn", self.list_thn, 0.2), ("jam", self.list_jam, 0.15), ("mnt", self.list_menit, 0.15)]:
                inp = ModernInput(hint_text=part.capitalize(), size_hint_x=width)
                setattr(self, f"{prefix}_{part}", inp)
                self.setup_dropdown(inp, list_data); box.add_widget(inp)
            form.add_widget(box)
        self.main_layout.add_widget(form)

        self.input_list = [self.ent_nama, self.ent_driver, self.ent_tujuan, self.p_tgl, self.p_bln, self.p_thn, self.p_jam, self.p_mnt, self.k_tgl, self.k_bln, self.k_thn, self.k_jam, self.k_mnt]
        for i, widget in enumerate(self.input_list):
            widget.bind(on_text_validate=lambda x, idx=i: self.handle_enter(idx))
            widget.bind(on_touch_down=self.on_input_click)
        Window.bind(on_key_down=self.on_global_key_down)

        # Tombol Bulat Memanjang
        btn_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.add_btn(btn_box, "SAVE", "#0288d1", self.simpan)
        self.add_btn(btn_box, "EDIT", "#f57c00", self.edit_terpilih)
        self.add_btn(btn_box, "UNDO", "#9c27b0", self.undo_action)
        self.add_btn(btn_box, "DEL", "#d32f2f", self.hapus)
        self.main_layout.add_widget(btn_box)

        self.search_input = ModernInput(hint_text="🔍 Cari Riwayat...", size_hint_y=None, height=55)
        self.search_input.bind(text=self.filter_data); self.main_layout.add_widget(self.search_input)

        self.scroll = ScrollView()
        self.history_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.history_list.bind(minimum_height=self.history_list.setter('height'))
        self.scroll.add_widget(self.history_list); self.main_layout.add_widget(self.scroll)

        footer = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.add_btn(footer, "COPY SELECTED", "#546e7a", self.salin_terpilih)
        self.add_btn(footer, "COPY ALL", "#1565c0", self.salin_semua)
        self.main_layout.add_widget(footer)

        self.refresh()
        return self.main_layout

    def muat_dan_konversi_data(self):
        if not os.path.exists(self.filename): return []
        try:
            with open(self.filename, 'r') as f: raw = json.load(f)
            if raw and isinstance(raw[0], list):
                return [{"id": str(uuid.uuid4()), "nama": r[0], "driver": r[1], "tujuan": r[2], "tgl_p": r[3], "jam_p": r[4], "tgl_k": r[5], "jam_k": r[6]} for r in raw]
            return raw
        except: return []

    def setup_dropdown(self, target, items):
        dd = DropDown(auto_dismiss=True, scroll_timeout=200, bar_width=10, max_height=250)
        for i in items:
            btn = Button(text=str(i), size_hint_y=None, height=45, background_normal="", background_color=get_color_from_hex("#e1f5fe"), color=get_color_from_hex("#01579b"))
            btn.bind(on_release=lambda b: dd.select(b.text)); dd.add_widget(btn)
        self.dropdown_objects[target] = dd
        target.bind(focus=lambda inst, foc: self.check_open_dropdown(inst, foc))
        dd.bind(on_select=lambda instance, x: self.on_select_flow(target, x))

    def check_open_dropdown(self, inst, foc):
        if foc and self.is_auto_opening:
            if inst in self.dropdown_objects:
                Window.release_all_keyboards()
                Clock.schedule_once(lambda dt: self.dropdown_objects[inst].open(inst), 0.1)
        elif not foc:
            if inst in self.dropdown_objects: self.dropdown_objects[inst].dismiss()

    def on_input_click(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.is_auto_opening = True

    def on_select_flow(self, target, val):
        target.text = val; self.focus_next(self.input_list.index(target))

    def handle_enter(self, idx):
        if self.input_list[idx] in self.dropdown_objects: self.dropdown_objects[self.input_list[idx]].dismiss()
        self.focus_next(idx)

    def focus_next(self, idx):
        if idx < len(self.input_list) - 1:
            self.is_auto_opening = True; self.input_list[idx+1].focus = True
        else: self.simpan()

    def on_global_key_down(self, window, key, scancode, codepoint, modifier):
        for i, widget in enumerate(self.input_list):
            if widget.focus and key == 8 and widget.text == "" and i > 0:
                self.is_auto_opening = True; self.input_list[i-1].focus = True; return True
        return False

    def create_label(self, text):
        return Label(text=text, color=get_color_from_hex("#01579b"), font_size='13sp', bold=True, size_hint_x=0.2, halign='left')

    def add_btn(self, parent, text, color, cmd):
        # Tombol Bulat Horizontal (Capsule Style)
        btn = Button(text=text, background_normal="", background_color=(0,0,0,0), font_size='13sp', bold=True)
        with btn.canvas.before:
            Color(rgb=get_color_from_hex(color))
            self.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[25])
        btn.bind(pos=self._update_btn_rect, size=self._update_btn_rect)
        btn.bind(on_release=lambda x: cmd()); parent.add_widget(btn)

    def _update_btn_rect(self, instance, value):
        for instr in instance.canvas.before.children:
            if isinstance(instr, RoundedRectangle):
                instr.pos = instance.pos
                instr.size = instance.size

    def filter_data(self, instance, value):
        q = value.lower()
        self.filtered_data = [r for r in self.data_riwayat if q in r['nama'].lower() or q in r['driver'].lower() or q in r['tujuan'].lower() or q in r['tgl_p'].lower()]
        self.refresh(use_filtered=True)

    def simpan(self):
        tgl_p, jam_p = f"{self.p_tgl.text} {self.p_bln.text} {self.p_thn.text}", f"{self.p_jam.text}:{self.p_mnt.text}"
        tgl_k = f"{self.k_tgl.text} {self.k_bln.text} {self.k_thn.text}" if self.k_tgl.text else "DALAM PERJALANAN"
        jam_k = f"{self.k_jam.text}:{self.k_mnt.text}" if self.k_jam.text else "-"
        new_data = {"id": self.current_edit_id if self.current_edit_id else str(uuid.uuid4()), "nama": self.ent_nama.text, "driver": self.ent_driver.text, "tujuan": self.ent_tujuan.text, "tgl_p": tgl_p, "jam_p": jam_p, "tgl_k": tgl_k, "jam_k": jam_k}
        if self.current_edit_id:
            for i, item in enumerate(self.data_riwayat):
                if item['id'] == self.current_edit_id:
                    self.undo_stack = ("EDIT", item.copy()); self.data_riwayat[i] = new_data; break
            self.current_edit_id = None
        else:
            self.data_riwayat.append(new_data); self.undo_stack = ("ADD", new_data['id']) 
        self.simpan_ke_file(); self.refresh(); self.reset()

    def refresh(self, use_filtered=False):
        self.history_list.clear_widgets()
        disp = self.filtered_data if use_filtered else self.data_riwayat
        self.check_states = {}
        for r in disp:
            card = BoxLayout(size_hint_y=None, height=155, padding=[10, 10], spacing=10)
            with card.canvas.before:
                Color(rgb=get_color_from_hex("#ffffff")); RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
            card.bind(pos=self._update_card, size=self._update_card)
            cb = CheckBox(size_hint=(None, None), size=("40dp", "40dp"), color=get_color_from_hex("#0288d1"), pos_hint={'center_y': .5})
            cb.bind(active=lambda inst, val, rid=r['id']: self.update_cb(rid, val))
            details = GridLayout(cols=3, spacing=[2, 2])
            def add_detail(label, value):
                l = Label(text=f"[b]{label}[/b]", markup=True, color=get_color_from_hex("#0288d1"), font_size='12sp', size_hint_x=0.22, halign='left')
                l.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
                details.add_widget(l); details.add_widget(Label(text=":", color=get_color_from_hex("#0288d1"), font_size='12sp', size_hint_x=0.03))
                v = Label(text=str(value), color=get_color_from_hex("#01579b"), font_size='12sp', size_hint_x=0.75, halign='left')
                v.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
                details.add_widget(v)
            for lbl, k in [("Karyawan", "nama"), ("Driver", "driver"), ("Tujuan", "tujuan")]: add_detail(lbl, r[k])
            add_detail("Pergi", f"{r['tgl_p']} ({r['jam_p']})"); add_detail("Kembali", f"{r['tgl_k']} ({r['jam_k']})")
            card.add_widget(cb); card.add_widget(details); self.history_list.add_widget(card)

    def _update_card(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before: Color(rgb=get_color_from_hex("#ffffff")); RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])

    def update_cb(self, rid, val): self.check_states[rid] = val
    def get_checked_id(self):
        for rid, active in self.check_states.items():
            if active: return rid
        return None

    def edit_terpilih(self):
        rid = self.get_checked_id()
        if rid:
            item = next((x for x in self.data_riwayat if x['id'] == rid), None)
            if item:
                self.current_edit_id = rid; self.ent_nama.text = item['nama']; self.ent_driver.text = item['driver']; self.ent_tujuan.text = item['tujuan']
                try:
                    p = item['tgl_p'].split(); self.p_tgl.text, self.p_bln.text, self.p_thn.text = p[0], p[1], p[2]
                    pt = item['jam_p'].split(':'); self.p_jam.text, self.p_mnt.text = pt[0], pt[1]
                except: pass
                self.is_auto_opening = False; self.ent_nama.focus = True

    def hapus(self):
        rid = self.get_checked_id()
        if rid:
            item = next((x for x in self.data_riwayat if x['id'] == rid), None)
            if item: self.undo_stack = ("DELETE", item); self.data_riwayat.remove(item)
        self.simpan_ke_file(); self.refresh()

    def undo_action(self):
        if not self.undo_stack: return
        mode, data = self.undo_stack
        if mode == "DELETE": self.data_riwayat.append(data)
        elif mode == "EDIT":
            for i, item in enumerate(self.data_riwayat):
                if item['id'] == data['id']: self.data_riwayat[i] = data; break
        self.undo_stack = None; self.simpan_ke_file(); self.refresh()

    def reset(self):
        for e in self.input_list: e.text = ""
        self.is_auto_opening = False; self.ent_nama.focus = True

    def simpan_ke_file(self):
        with open(self.filename, 'w') as f: json.dump(self.data_riwayat, f)

    def format_copy(self, item):
        return f"Nama: {item['nama']}\nDriver: {item['driver']}\nTujuan: {item['tujuan']}\nPergi: {item['tgl_p']} ({item['jam_p']})\nKembali: {item['tgl_k']} ({item['jam_k']})\n--------------------------"

    def salin_terpilih(self):
        rid = self.get_checked_id()
        if rid:
            item = next((x for x in self.data_riwayat if x['id'] == rid), None)
            if item: Clipboard.copy(self.format_copy(item))

    def salin_semua(self):
        if not self.data_riwayat: return
        out = ""
        for r in self.data_riwayat: out += self.format_copy(r) + "\n"
        Clipboard.copy(out.strip())

if __name__ == "__main__":
    TripAppKivy().run()
        
