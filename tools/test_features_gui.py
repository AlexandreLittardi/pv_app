"""GUI regression smoke test; run with a graphical display."""
import sys,tkinter as tk,json,tempfile,types,os
from pathlib import Path
from tkinter import messagebox,filedialog
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['PV_APP_RECENTS_FILE']=str(Path(tempfile.gettempdir())/'pv_features_recent_test.json')
from app import PVLayoutRibbonApp
errors=[]
messagebox.showerror=lambda *a,**k:errors.append((a,k))
messagebox.showwarning=lambda *a,**k:errors.append((a,k))
messagebox.showinfo=lambda *a,**k:None
r=tk.Tk();r.report_callback_exception=lambda *a:errors.append(a)
a=PVLayoutRibbonApp(r);r.update()
assert a.home_frame.winfo_ismapped() and not a.canvas_frame.winfo_ismapped()
a._load_project_file(str((ROOT/'pv_projects/Volfrigo_516_autoconsumo.json').resolve()))
r.update()
assert len(a.recent_tree.get_children())>=1
recent=json.loads(Path(os.environ['PV_APP_RECENTS_FILE']).read_text())
assert recent[0]['last_opened'] and recent[0]['path'].endswith('Volfrigo_516_autoconsumo.json')
a.recent_tree.selection_set(recent[0]['path']);a._open_recent_selection();r.update();assert len(a.panels)==516
# Panel configuration uses the same live variables after closing.
a.ribbon_notebook.select(2);r.update()
a._show_panel_configuration();r.update()
win=next(w for w in r.winfo_children() if isinstance(w,tk.Toplevel) and w.title()=='Panel configuration')
win.destroy();assert a.entry_layout_tilt.get() == str(a.panel_tilt_deg)
# Plain left dragging pans without changing the number of PV modules.
a.ribbon_notebook.select(3);r.update();a._zoom_button_change(4);r.update()
start=a.canvas.xview()
a.on_left_press(types.SimpleNamespace(x=320,y=230,state=0))
a.on_left_drag(types.SimpleNamespace(x=100,y=230,state=0))
a.on_left_release(types.SimpleNamespace(x=100,y=230,state=0));r.update()
assert a.canvas.xview()!=start,(start,a.canvas.xview())
assert len(a.panels)==516
# Spreadsheet selected range, fill series, formula reference insertion.
a.ribbon_notebook.select(6);r.update()
a.material_spreadsheet['cells'].update({'A1':'1','A2':'2'})
cell_h=a._spreadsheet_row_h(0)
a._on_spreadsheet_cell_click(types.SimpleNamespace(x=10,y=10,state=0))
a._spreadsheet_cell_drag(types.SimpleNamespace(x=10,y=cell_h+10,state=0))
a._spreadsheet_cell_release(types.SimpleNamespace(x=10,y=cell_h+10,state=0))
assert a.spreadsheet_range_anchor==(0,0) and a.spreadsheet_range_end==(1,0)
a._on_spreadsheet_cell_click(types.SimpleNamespace(x=a._spreadsheet_col_w(0)-2,y=2*cell_h-2,state=0))
assert a.spreadsheet_drag_mode=='fill'
a._spreadsheet_cell_drag(types.SimpleNamespace(x=10,y=3*cell_h+10,state=0))
a._spreadsheet_cell_release(types.SimpleNamespace(x=10,y=3*cell_h+10,state=0))
assert a.material_spreadsheet['cells']['A3']=='3.0'
assert a.material_spreadsheet['cells']['A4']=='4.0'
a.spreadsheet_selected=(1,1);a.spreadsheet_range_anchor=(1,1);a.spreadsheet_range_end=(1,1)
a._spreadsheet_start_edit('=A1+')
a._on_spreadsheet_cell_click(types.SimpleNamespace(x=10,y=2*cell_h+10,state=0))
assert a.spreadsheet_edit_entry.get()=='=A1+A3'
a._spreadsheet_commit_edit()
assert a.material_spreadsheet['cells']['B2']=='=A1+A3'
with tempfile.TemporaryDirectory() as folder:
 a.material_spreadsheet['cells']['C1']='=NB_MODULES+ZONE1_LARGEUR_MM'
 a.current_project_filepath=str(Path(folder)/'roundtrip.json')
 a.save_project(silent=True)
 saved=json.loads(Path(a.current_project_filepath).read_text())
 assert saved['material_spreadsheet']['cells']['C1']=='=PANEL_COUNT+ZONE1_WIDTH_MM'
 a._load_project_file(a.current_project_filepath)
 assert 'NB_MODULES' not in a._get_spreadsheet_variables()
 assert 'PANEL_COUNT' in a._get_spreadsheet_variables()
# Every export writes to a private preview first; closing the preview discards it.
a.ribbon_notebook.select(3);r.update()
after=[]
def close_preview():
 for win in r.winfo_children():
  if isinstance(win,tk.Toplevel) and win.title().startswith('CSV preview'):
   after.append(win)
   win.destroy()
r.after(200,close_preview);a.export_csv();assert after
assert not errors,errors
print('Home/history, panel config, drag pan, spreadsheet fill/formula and CSV cancel OK')
r.destroy()
