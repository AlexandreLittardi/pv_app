"""Run with an active Tk display to verify editor persistence and responsive pages."""
import json,sys,tkinter as tk,tempfile
from pathlib import Path
from tkinter import ttk,messagebox,filedialog
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import PVLayoutRibbonApp
errors=[]
messagebox.showerror=lambda *a,**kw:errors.append((a,kw))
messagebox.showwarning=lambda *a,**kw:None
messagebox.showinfo=lambda *a,**kw:None
r=tk.Tk();r.report_callback_exception=lambda *args:errors.append(args)
a=PVLayoutRibbonApp(r)
project=ROOT/'pv_projects/Volfrigo_516_autoconsumo.json'
a._load_project_file(str(project));r.update();a.ribbon_notebook.select(7);r.update()
a._show_detailed_electrical_editor();r.update()
w=a._detailed_editor_window
w.geometry('640x480+0+0');r.update();r.update()
def walk(parent):
 for ch in parent.winfo_children():
  yield ch
  yield from walk(ch)
page=next(ch for ch in w.winfo_children() if isinstance(ch,ttk.Notebook))
for idx in range(5):
 page.select(idx);r.update();assert w.winfo_width()==640
for combo in [ch for ch in walk(w) if isinstance(ch,ttk.Combobox)]:
 if tuple(combo['values'])==('0','1','2'):
  combo.set('1');break
else:raise AssertionError('Missing BESS choices')
with tempfile.TemporaryDirectory() as folder:
 a.current_project_filepath=str(Path(folder)/'detailed.json')
 b=next(ch for ch in walk(w) if isinstance(ch,ttk.Button) and ch.cget('text')=='Save settings and project')
 b.invoke();r.update()
 data=json.loads(Path(a.current_project_filepath).read_text())
 assert data['electrical_design']['bess_count']==1
 assert data['electrical_design']['battery']['1']['cluster_1_to']=='INV1'
 assert data['electrical_design']['source_fingerprint']
 from detailed_electrical import source_fingerprint
 assert data['electrical_design']['source_fingerprint']==source_fingerprint(a._detailed_project_snapshot())
 target=str(Path(folder)/'wiring.svg');real=filedialog.asksaveasfilename;filedialog.asksaveasfilename=lambda **k:target
 try:a._export_detailed_electrical_svg()
 finally:filedialog.asksaveasfilename=real
 assert Path(target).exists()
 a._load_project_file(a.current_project_filepath);r.update();assert a.electrical_design['bess_count']==1
assert not errors,errors
print('Editor 640x480, save/reload and SVG export OK')
r.destroy()
