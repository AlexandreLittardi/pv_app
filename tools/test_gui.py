"""Integration smoke test: run with a working display, e.g. xvfb-run -a python tools/test_gui.py."""
import sys,tkinter as tk,time,json,tempfile
from pathlib import Path
from tkinter import messagebox
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import PVLayoutRibbonApp
errors=[]
messagebox.showerror=lambda *a,**k:errors.append(('message',a))
messagebox.showwarning=lambda *a,**k:print('WARN',a)
messagebox.showinfo=lambda *a,**k:None
r=tk.Tk();r.report_callback_exception=lambda *a:errors.append(('callback',str(a)))
a=PVLayoutRibbonApp(r)
def pump():
 for _ in range(5):r.update();time.sleep(.04)
pump()
for path in (ROOT/'pv_projects').glob('*.json'):
 a._load_project_file(str(path.resolve()));pump()
 assert a.roof_pil_img is not None,path
 assert a.panel_pmax_w==720
 assert sorted(a.panels.values())==list(range(1,len(a.panels)+1))
 for sid,assign in a.string_mppt_assignment.items():
  target=f"mppt::{assign['block']}::{assign['mppt']}"
  assert any(l['a']=='str::'+sid and l['b']==target for l in a.diagram_links)
 print('Loaded',path.name,len(a.panels))
a._load_project_file(str((ROOT/'pv_projects/Volfrigo_516_autoconsumo.json').resolve()));pump()
for w,h in [(640,480),(800,600),(1024,768),(1366,768)]:
 r.geometry(f'{w}x{h}');pump()
 for idx in range(10):
  a.ribbon_notebook.select(idx);pump()
  assert a.ribbon_frame.winfo_height()<90,(w,idx,a.ribbon_frame.winfo_height())
  assert a.main_container.winfo_width()<=w
  if idx == 0:
   assert a.home_frame.winfo_ismapped() and not a.canvas_frame.winfo_ismapped()
  elif idx not in (3,4,5,6,7,8):assert a.canvas.winfo_width()>150,(w,idx,a.canvas.winfo_width())
 print('Viewport',w,h,'OK')
print('Callback errors',errors)
assert not errors
summary=a.compute_all_cable_routes();print('Routes',summary)
assert summary['ok']==31
assert all(v['pole_a_m']>0 and v['pole_b_m']>0 for v in a.cable_network_routes.values())
# Save and reload into a new folder tests portable roof-image paths and fields.
with tempfile.TemporaryDirectory() as temp:
 a.current_project_filepath=str(Path(temp)/'roundtrip.json');a.save_project(silent=True)
 saved=json.loads(Path(a.current_project_filepath).read_text());assert saved['grid_connection_settings']['export_limit_kw']==300
 a._load_project_file(a.current_project_filepath);pump();assert a.roof_pil_img is not None
# All overflow fields remain accessible and do not raise Tk callback errors.
for ident in a.ribbon_notebook.tabs():
 a._show_toolbar_fields(r.nametowidget(ident));pump()
 for win in r.winfo_children():
  if isinstance(win,tk.Toplevel) and win.title()=='Toolbar fields':win.destroy()
assert not errors,errors
print('Save/load, overflow controls and two-pole routing OK')
r.destroy()
