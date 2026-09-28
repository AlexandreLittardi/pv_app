"""Single-row ribbon with accessible overflow, no whole-window scrollbars."""
import tkinter as tk
from tkinter import ttk

class ResponsiveUIMixin:
    def _on_ribbon_tab_changed(self,event):
        if hasattr(self,'canvas_frame') and not self.canvas_frame.winfo_manager():
            self.canvas_frame.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        return super()._on_ribbon_tab_changed(event)

    def _build_root_scroller(self):
        # Keep the historical method name for callers, remove the scrolling shell.
        self.ui_content=ttk.Frame(self.root)
        self.ui_content.pack(fill=tk.BOTH,expand=True)

    def _install_responsive_ui(self):
        # Keep the actual tab strip. The selector remains available when the
        # screen is too narrow to display every tab.
        self.ribbon_notebook.pack_forget()
        self.workspace_selector=ttk.Combobox(self.ribbon_frame,state='readonly',width=18)
        self.workspace_selector['values']=[self.ribbon_notebook.tab(t,'text').strip() for t in self.ribbon_notebook.tabs()]
        self.workspace_selector.current(0)
        self.workspace_selector.pack(side=tk.LEFT,padx=4,pady=4)
        self.workspace_selector.bind('<<ComboboxSelected>>',lambda e:self.ribbon_notebook.select(self.workspace_selector.current()))
        self._auto_fit=True
        self.panel_toggle=ttk.Button(self.ribbon_frame,text='Panel',width=6,command=self._toggle_responsive_panel)
        self.panel_toggle.pack(side=tk.RIGHT,padx=3)
        self.ribbon_notebook.pack(side=tk.LEFT,fill=tk.X,expand=True)
        self._install_compact_zoom()
        self._toolbars={};self._panels_hidden=False;self._resize_job=None
        for ident in self.ribbon_notebook.tabs():
            tab=self.root.nametowidget(ident)
            items=[]
            for w in tab.winfo_children():
                if w.winfo_manager()=='pack':items.append((w,dict(w.pack_info())))
            more=ttk.Menubutton(tab,text='More ▾',width=7)
            menu=tk.Menu(more,tearoff=False);more.configure(menu=menu)
            self._toolbars[str(tab)]=(tab,items,more,menu)
            tab.bind('<Configure>',self._schedule_responsive,add='+')
        self.ribbon_notebook.bind('<<NotebookTabChanged>>',self._responsive_tab_changed,add='+')
        self.root.bind('<Configure>',self._schedule_responsive,add='+')
        self.root.bind_all('<Map>',self._cap_mapped_dialog,add='+')
        self.root.after_idle(self._layout_responsive)

    def _paginate_shadow_panel(self):
        pass  # Shadow parameters remain in one scrollable left sidebar.

    def _install_compact_zoom(self):
        for ident in self.ribbon_notebook.tabs():
            tab=self.root.nametowidget(ident)
            zoom=next((w for w in tab.winfo_children() if isinstance(w,ttk.Menubutton)
                       and 'Zoom' in str(w.cget('text'))),None)
            if zoom is None:continue
            zoom.pack_forget();zoom.destroy()
            group=ttk.Frame(tab)
            spreadsheet=tab is self.tab_material
            commands=((lambda:self._zoom_spreadsheet(1/1.2),lambda:self._reset_spreadsheet_zoom,
                       lambda:self._zoom_spreadsheet(1.2)) if spreadsheet else
                      (lambda:self._zoom_button_change(1/1.2),self._reset_zoom,
                       lambda:self._zoom_button_change(1.2)))
            for label,command in zip(('-', '⤾', '+'),commands):
                ttk.Button(group,text=label,width=2,command=command).pack(side=tk.LEFT)
            group.pack(side=tk.RIGHT,padx=2)

    def _responsive_tab_changed(self,event=None):
        self.workspace_selector.current(self._get_active_tab_index())
        self._panels_hidden=(self.root.winfo_width()<1000 and self._get_active_tab_index() in (3,4))
        self._schedule_responsive()

    def _schedule_responsive(self,event=None):
        if not hasattr(self,'_toolbars'):return
        if self._resize_job is not None:self.root.after_cancel(self._resize_job)
        self._resize_job=self.root.after(70,self._layout_responsive)

    def _layout_responsive(self):
        self._resize_job=None
        for tab,items,more,menu in self._toolbars.values():
            if not tab.winfo_ismapped():continue
            width=tab.winfo_width()-12
            required=sum(w.winfo_reqwidth()+12 for w,_ in items)
            overflow=required>width
            available=width-(more.winfo_reqwidth()+12 if overflow else 0)
            for w,_ in items:w.pack_forget()
            more.pack_forget();menu.delete(0,'end')
            hidden=[];used=0
            for w,info in items:
                # Informational labels yield space to controls; they appear in More.
                cost=w.winfo_reqwidth()+12
                if used+cost<=available and not (overflow and isinstance(w,ttk.Label)):
                    info.pop('in',None);info['padx']=3
                    w.pack(**info);used+=cost
                else:hidden.append(w)
            if hidden:
                more.pack(side=tk.RIGHT,padx=3)
                for w in hidden:self._add_overflow_item(menu,w)
                menu.add_separator();menu.add_command(label='Fields and selectors…',command=lambda t=tab:self._show_toolbar_fields(t))
        width=self.main_container.winfo_width()
        active=[]
        for name in ('stringing','equipment','shadow','material','diagram','notes'):
            panel=getattr(self,'side_panel_'+name,None)
            if panel is None:continue
            panel.pack_propagate(False)
            panel.configure(width=width if width<1000 else (430 if name=='material' else 360))
            if self._panels_hidden:panel.pack_forget()
            if panel.winfo_manager()=='pack':
                active.append(panel)
                panel.pack_configure(fill=tk.BOTH if width<1000 else tk.Y,expand=width<1000)
                for child in panel.winfo_children():
                    if isinstance(child,ttk.Label) and child.cget('wraplength'):
                        child.configure(wraplength=max(200,panel.winfo_width()-20))
        if width<1000 and active:
            self.canvas_frame.pack_forget()
        elif self._get_active_tab_index() not in (0,9) and not self.canvas_frame.winfo_manager():
            options={'side':tk.LEFT,'fill':tk.BOTH,'expand':True}
            if active:options['before']=active[0]
            self.canvas_frame.pack(**options)
        if hasattr(self,'stats_frame'):
            if width<900:self.stats_frame.place_forget()
            elif self._get_active_tab_index()!=6:self.stats_frame.place(relx=1.,rely=1.,anchor='se',x=-15,y=-15)
        if self._auto_fit and self.canvas_frame.winfo_manager() and self._get_active_tab_index()!=7:
            self.root.after_idle(self._apply_roof_fit)

    def _fit_roof_to_window(self):
        self._auto_fit=True
        self._apply_roof_fit()

    def _apply_roof_fit(self):
        if not self.roof_pil_img or self.canvas.winfo_width()<50:return
        zoom=min((self.canvas.winfo_width()-10)/self.roof_pil_img.width,
                 (self.canvas.winfo_height()-10)/self.roof_pil_img.height)
        zoom=max(.03,min(3.,zoom))
        if abs(zoom-self.zoom_level)>.002:
            self.zoom_level=zoom;self.cell_size_px=max(1,int(40*zoom));self.draw_grid()
            self.canvas.xview_moveto(0);self.canvas.yview_moveto(0)

    def _zoom_button_change(self,factor):
        self._auto_fit=False
        return super()._zoom_button_change(factor)

    def _zoom_at_pointer(self,event,delta):
        self._auto_fit=False
        return super()._zoom_at_pointer(event,delta)

    def _toggle_responsive_panel(self):
        if self._panels_hidden:
            self._panels_hidden=False;self._on_ribbon_tab_changed(None)
        else:self._panels_hidden=True
        self._layout_responsive()

    def _add_overflow_item(self,menu,w):
        label=str(w.cget('text')) if 'text' in w.keys() else ''
        if isinstance(w,ttk.Menubutton):
            if str(w.cget('menu')):menu.add_cascade(label=label,menu=w.cget('menu'))
        elif isinstance(w,(ttk.Button,ttk.Checkbutton,ttk.Radiobutton)):
            menu.add_command(label=label,command=w.invoke)
        elif isinstance(w,ttk.Label) and label:menu.add_command(label=label,state='disabled')
        elif isinstance(w,(ttk.Frame,ttk.LabelFrame)):
            for child in w.winfo_children():self._add_overflow_item(menu,child)

    def _show_toolbar_fields(self,tab):
        win=tk.Toplevel(self.root);win.title('Toolbar fields')
        body=ttk.Frame(win,padding=10);body.pack(fill=tk.BOTH,expand=True)
        widgets=[]
        def visit(parent):
            for w in parent.winfo_children():
                if isinstance(w,(ttk.Entry,ttk.Combobox,ttk.Checkbutton,ttk.Radiobutton,ttk.Scale,tk.Scale)):widgets.append(w)
                elif isinstance(w,(ttk.Frame,ttk.LabelFrame)):visit(w)
        visit(tab)
        self._field_dialog_vars=getattr(self,'_field_dialog_vars',[])
        pages=ttk.Notebook(body) if len(widgets)>6 else None
        if pages is not None:pages.pack(fill=tk.BOTH,expand=True)
        field_parent=body
        for row,w in enumerate(widgets):
            if pages is not None and row%6==0:
                field_parent=ttk.Frame(pages,padding=6)
                pages.add(field_parent,text=f'{row+1}–{min(row+6,len(widgets))}')
            display_row=row%6 if pages is not None else row
            siblings=w.master.winfo_children();idx=siblings.index(w)
            label=str(w.cget('text')) if 'text' in w.keys() else ''
            if not label and idx and isinstance(siblings[idx-1],ttk.Label):label=siblings[idx-1].cget('text')
            ttk.Label(field_parent,text=label or f'Value {row+1}',wraplength=250).grid(row=display_row,column=0,sticky='w',pady=4)
            key='textvariable' if isinstance(w,ttk.Entry) else 'variable'
            variable=str(w.cget(key))
            if not variable:
                var=tk.StringVar(value=w.get());self._field_dialog_vars.append(var);w.configure(**{key:var});variable=var
            if isinstance(w,ttk.Combobox):
                clone=ttk.Combobox(field_parent,textvariable=variable,values=w.cget('values'),state=w.cget('state'),width=18)
                clone.bind('<<ComboboxSelected>>',lambda e,original=w:original.event_generate('<<ComboboxSelected>>'))
            elif isinstance(w,ttk.Entry):
                clone=ttk.Entry(field_parent,textvariable=variable,width=18)
                clone.bind('<Return>',lambda e,original=w:original.event_generate('<Return>'))
                clone.bind('<FocusOut>',lambda e,original=w:original.event_generate('<FocusOut>'))
            elif isinstance(w,(ttk.Checkbutton,ttk.Radiobutton)):
                clone=ttk.Button(field_parent,text='Toggle / select',command=w.invoke)
            else:
                clone=ttk.Scale(field_parent,variable=variable,from_=w.cget('from'),to=w.cget('to'),command=w.cget('command'))
            clone.grid(row=display_row,column=1,padx=6,sticky='ew')
        if not widgets:ttk.Label(body,text='All actions are available from the More menu.').pack()
        ttk.Button(win,text='Close',command=win.destroy).pack(pady=6)
        self._fit_dialog(win,530,120+min(6,len(widgets))*42)

    def _fit_dialog(self,window,width,height):
        sw=self.root.winfo_screenwidth();sh=self.root.winfo_screenheight()
        width=min(width,max(300,sw-40));height=min(height,max(250,sh-80))
        window.geometry(f'{width}x{height}+{max(0,(sw-width)//2)}+{max(0,(sh-height)//2)}')
        window.minsize(min(420,width),min(280,height))

    def _cap_mapped_dialog(self,event):
        w=event.widget
        if not isinstance(w,tk.Toplevel):return
        self.root.after_idle(lambda:self._fit_dialog(w,w.winfo_width(),w.winfo_height()) if w.winfo_exists() else None)
