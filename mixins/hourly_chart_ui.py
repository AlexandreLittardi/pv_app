"""Grafico 24 ore interattivo: FV, domanda, fonte dei carichi e SOC."""
import datetime as dt
import tkinter as tk
from tkinter import messagebox, ttk

from battery_dispatch import BatterySettings, simulate_three_options
from self_consumption import timestamps


class HourlyChartMixin:
    def _open_annual_chart(self):
        if not self._require_current_energy():return
        win=tk.Toplevel(self.root);win.title('Annual energy comparison — monthly kWh')
        controls=ttk.Frame(win,padding=8);controls.pack(fill=tk.X)
        ttk.Label(controls,text='Storage').pack(side=tk.LEFT)
        selected=tk.StringVar(value='1 BESS')
        picker=ttk.Combobox(controls,textvariable=selected,values=['PV only','1 BESS','2 BESS'],state='readonly',width=12)
        picker.pack(side=tk.LEFT,padx=8)
        ttk.Label(controls,text='Monthly totals (MWh)').pack(side=tk.LEFT)
        canvas=tk.Canvas(win,bg='white',highlightthickness=0);canvas.pack(fill=tk.BOTH,expand=True)
        def draw(*args):
            canvas.delete('all');w=max(320,canvas.winfo_width());h=max(220,canvas.winfo_height())
            base=self.self_consumption_summary['monthly']
            summary={'PV only':self.self_consumption_summary,'1 BESS':self.bess_summary,'2 BESS':self.two_bess_summary}[selected.get()]['monthly']
            months=sorted(base)
            series=[('PV','#DA8A12',[base[m]['pv_kwh']/1000 for m in months]),
                    ('Load','#34516B',[base[m]['load_kwh']/1000 for m in months]),
                    ('Useful PV','#2B826D',[(summary[m].get('useful_self_kwh',summary[m].get('self_kwh',0)))/1000 for m in months]),
                    ('Grid import','#923C6F',[summary[m]['grid_kwh']/1000 for m in months]),
                    ('Export','#747A84',[summary[m]['export_kwh']/1000 for m in months])]
            maximum=max(1,max(v for _,_,values in series for v in values))*1.1
            x0=48;y0=65;bottom=h-40;right=w-20
            for i in range(5):
                value=maximum*i/4;y=bottom-(bottom-y0)*i/4
                canvas.create_line(x0,y,right,y,fill='#DFE5EA');canvas.create_text(x0-5,y,text=f'{value:.0f}',anchor='e')
            for j,(label,color,values) in enumerate(series):
                canvas.create_text(15+j*(w-30)/5,20,text=label,fill=color,anchor='w',font=('Arial',9,'bold'))
                points=[]
                for i,v in enumerate(values):points.extend((x0+i*(right-x0)/max(1,len(months)-1),bottom-v/maximum*(bottom-y0)))
                if len(points)>=4:canvas.create_line(*points,fill=color,width=2)
            for i,m in enumerate(months):
                canvas.create_text(x0+i*(right-x0)/max(1,len(months)-1),bottom+15,text=m[5:],font=('Arial',8))
        picker.bind('<<ComboboxSelected>>',draw);canvas.bind('<Configure>',draw)
        self._fit_dialog(win,980,540);win.after_idle(draw)

    def _open_hourly_chart(self):
        if not self._require_current_energy():return
        profile=getattr(self,'hourly_consumption_profile',None)
        pv=getattr(self,'hourly_pv_kwh',None)
        bess=getattr(self,'bess_summary',None)
        two=getattr(self,'two_bess_summary',None)
        if not profile or not pv or not bess or not two:
            messagebox.showwarning('Profilo mancante','Calcolare prima le tre opzioni.')
            return
        try:
            if any(abs(float(entry.get().replace(',','.'))-bess['battery_settings'][key])>1e-9
                   for key,entry in self.bess_entries.items()):
                messagebox.showwarning('Parametri cambiati','Ricalcolare le tre opzioni prima del grafico.')
                return
        except (KeyError,ValueError):
            messagebox.showwarning('Parametri non validi','Correggere i parametri BESS e ricalcolare.')
            return
        settings=BatterySettings(**bess['battery_settings'])
        compared=simulate_three_options(profile,pv,settings,self.grid_connection_settings["export_limit_kw"])
        rows_one=compared['one_bess']['rows']
        rows_two=compared['two_bess']['rows']
        dates=[stamp.date().isoformat() for stamp in timestamps(profile)[::24]]
        day_index={day:i for i,day in enumerate(dates)}
        win=tk.Toplevel(self.root)
        win.title('Volfrigo 516 — dettaglio orario, FV e rete')
        win.geometry('1060x670')
        controls=ttk.Frame(win,padding=8)
        controls.pack(fill=tk.X)
        ttk.Label(controls,text='Giorno:').pack(side=tk.LEFT)
        chosen=tk.StringVar(value='2025-06-21' if '2025-06-21' in day_index else dates[0])
        picker=ttk.Combobox(controls,textvariable=chosen,values=dates,width=13,state='readonly')
        picker.pack(side=tk.LEFT,padx=5)
        mode=tk.StringVar(value='uno')
        mode_label=tk.StringVar(value='1 BESS')
        scenario=ttk.Combobox(controls,textvariable=mode_label,values=['PV only','1 BESS','2 BESS'],state='readonly',width=9)
        scenario.pack(side=tk.LEFT,padx=4)
        scenario.bind('<<ComboboxSelected>>',lambda e:mode.set({'PV only':'senza','1 BESS':'uno','2 BESS':'due'}[mode_label.get()]))
        detail=ttk.Label(win,text='Click an hour for detailed values.',padding=8,wraplength=600)
        win.bind('<Configure>',lambda e:detail.configure(wraplength=max(280,win.winfo_width()-25)),add='+')
        detail.pack(fill=tk.X)
        canvas=tk.Canvas(win,bg='#ffffff',highlightthickness=0,height=515)
        canvas.pack(fill=tk.BOTH,expand=True,padx=10,pady=4)

        def move(delta):
            chosen.set(dates[max(0,min(len(dates)-1,day_index[chosen.get()]+delta))])
            draw()
        ttk.Button(controls,text='<',command=lambda:move(-1)).pack(side=tk.LEFT,padx=5)
        ttk.Button(controls,text='>',command=lambda:move(1)).pack(side=tk.LEFT,padx=5)
        state={'x0':70,'dx':38,'day_rows':[]}

        def clicked(event):
            i=round((event.x-state['x0'])/state['dx'])
            if not 0<=i<24:return
            stamp,load,solar,direct,charge,discharge,served,grid,export,soc,_=state['day_rows'][i]
            if mode.get()=='senza':
                discharge=0;grid=load-direct;charge=0
                export=min(solar-direct,self.grid_connection_settings['export_limit_kw'])
            detail.configure(text=f"{stamp[11:16]}–{(i+1)%24:02d}:00  •  "
                             f"FV {solar:.1f} kWh  •  Consumo {load:.1f} kWh  •  "
                             f"FV diretto {direct:.1f}  •  BESS {discharge:.1f}  •  "
                             f"Prelievo {grid:.1f} kWh  •  Immissione {export:.1f} kWh  •  Limitazione {max(0,solar-direct-charge-export):.1f} kWh" +
                             (f"  •  SOC {soc:.1f}%" if mode.get()!='senza' else ''))

        def draw(*_):
            if not canvas.winfo_exists():return
            canvas.delete('all')
            source=rows_two if mode.get()=='due' else rows_one
            day_rows=source[day_index[chosen.get()]*24:(day_index[chosen.get()]+1)*24]
            state['day_rows']=day_rows
            width=max(320,canvas.winfo_width())
            height=max(230,canvas.winfo_height())
            x0=50;dx=(width-x0-30)/23
            state['x0']=x0;state['dx']=dx
            top0,top1=55,height*.42
            bot0,bot1=height*.55,height-55
            max_top=max(1,*(max(r[1],r[2]) for r in day_rows))*1.10
            max_load=max(1,*(r[1] for r in day_rows))*1.16
            def ytop(v):return top1-(v/max_top)*(top1-top0)
            def ybottom(v):return bot1-(v/max_load)*(bot1-bot0)
            for i,row in enumerate(day_rows):
                x=x0+i*dx
                if row[2]<.001:
                    canvas.create_rectangle(x-dx*.47,top0,x+dx*.47,bot1,
                                            fill='#f0f2f4',outline='')
            for y0,y1,mx,label in ((top0,top1,max_top,'FV e consumo (kWh/ora)'),
                                    (bot0,bot1,max_load,'Copertura del consumo (kWh/ora)')):
                canvas.create_text(x0,y0-20,text=label,anchor='w',fill='#243640',font=('Arial',11,'bold'))
                for frac in (0,.5,1):
                    y=y1-frac*(y1-y0)
                    canvas.create_line(x0-5,y,width-30,y,fill='#d8dde0')
                    canvas.create_text(x0-10,y,text=f'{mx*frac:.0f}',anchor='e',fill='#44515a')
            for key,color in ((2,'#dd9c2e'),(1,'#3c749b')):
                points=[]
                for i,r in enumerate(day_rows):points.extend((x0+i*dx,ytop(r[key])))
                canvas.create_line(*points,fill=color,width=2.7,smooth=False)
            for i,r in enumerate(day_rows):
                x=x0+i*dx
                direct=r[3];battery=r[5] if mode.get()!='senza' else 0
                grid=r[7] if mode.get()!='senza' else r[1]-direct
                bottom=0
                for value,color in ((direct,'#eaaa40'),(battery,'#438e70'),(grid,'#52799e')):
                    if value>1e-8:
                        canvas.create_rectangle(x-dx*.38,ybottom(bottom+value),
                                                x+dx*.38,ybottom(bottom),fill=color,outline='')
                    bottom+=value
                if i%3==0:
                    canvas.create_text(x,bot1+18,text=f'{i:02d}:00',fill='#364650')
            if mode.get()!='senza':
                soc_points=[]
                for i,r in enumerate(day_rows):
                    soc_points.extend((x0+i*dx,bot1-r[9]/100*(bot1-bot0)))
                canvas.create_line(*soc_points,fill='#724585',width=2,dash=(5,3))
                canvas.create_text(width-28,bot0+3,text='100%',anchor='e',fill='#724585')
                canvas.create_text(width-28,bot1-3,text='0%',anchor='e',fill='#724585')
            canvas.create_text(x0,top0-41,anchor='w',fill='#394c55',
                               width=width-70,font=('Arial',8),text='FV prodotto (arancio)    Consumo (blu)    '
                                    'FV diretto (giallo)    BESS (verde)    Rete (blu scuro)    SOC (viola)')
            canvas.create_text(x0,bot1+44,anchor='w',fill='#5d6970',
                               width=width-65,font=('Arial',8),text='Le fasce grigie indicano le ore con FV = 0. '
                                    'Ogni barra suddivide il consumo dell’ora fra le tre fonti.')

        picker.bind('<<ComboboxSelected>>',draw)
        mode.trace_add('write',draw)
        canvas.bind('<Configure>',draw)
        canvas.bind('<Button-1>',clicked)
        win.after_idle(draw)
