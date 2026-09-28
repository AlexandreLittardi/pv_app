"""Both string terminals, using the supplied router and verified saved routes."""
import math
from single_line_516 import route_is_current
from project_validation import number
from mixins.notes_tools import calculate_dc_cable_size

class TwoPoleCablesMixin:
    def _route_signature(self):
        return {'strings':{sid:[f'{r},{c}' for r,c in coords] for sid,coords in self.strings.items()},
                'assignments':self.string_mppt_assignment.copy(),
                'inverter_positions':{k:[v['x'],v['y']] for k,v in self.inverter_positions.items()},
                'cable_paths':[{'id':p.get('id'),'points':[list(q) for q in p.get('points',[])]} for p in self.cable_paths],
                'roof_zones':self.roof_zones,'px_per_mm':self.px_per_mm,
                'panel_width_mm':self.panel_width_mm,'panel_height_mm':self.panel_height_mm,
                'routing_settings':self.routing_settings.copy()}

    def get_two_pole_route(self,sid):
        plan=self.electrical_route_plan_3d
        data=self._project_snapshot();data['electrical_route_plan_3d']=plan
        if route_is_current(data,sid):
            sig=plan.get('source_signature',{})
            if sig.get('routing_settings',self.routing_settings)==self.routing_settings:
                return plan['routes'][sid]
        return None

    def _calculate_two_pole_route(self,sid):
        saved=self.get_two_pole_route(sid)
        if saved:return saved
        coords=self.strings.get(sid,[])
        if not coords:return None
        a=self.string_mppt_assignment.get(sid,{})
        record={'inverter':a.get('block'),'mppt':a.get('mppt'),'modules':len(coords),
                'route_status':'ESTIMATE — routing and descent points require site validation'}
        for name,end in [('terminal_A',0),('terminal_B',-1)]:
            length,kind,points=super().compute_cable_route(sid,terminal=end)
            if length is None:return None
            idx=self._get_panel_zone_idx(coords[end])
            z=self.roof_zones[idx] if idx is not None else {}
            height=number(z.get('z_mm'))
            if height is None:return None  # no invented vertical length
            drop=abs(height/1000-self.routing_settings['inverter_height_m'])
            reserve=self.routing_settings['reserve_per_pole_m']
            record[name]={'length_m':length/1000+drop+reserve,'roof_points_px':points,'ground_points_px':[],
                          'vertical_drop_m':drop,'terminal_reserve_m':reserve,'method':kind,
                          'module_id':self.panels[coords[end]],'zone':idx+1 if idx is not None else None}
        record['loop_length_m']=record['terminal_A']['length_m']+record['terminal_B']['length_m']
        rows=self.material_categories.get('modules',{}).get('rows',[])
        spec=rows[0] if len(rows)==1 else {}
        imp=number(spec.get('Imp (A)'));vmp=number(spec.get('Vmp (V)'))
        record['working_section_mm2']=None;record['drop_at_working_section_pct']=None
        if imp and vmp:
            result=calculate_dc_cable_size(imp,vmp*len(coords),record['loop_length_m']/2,
                                          self.cable_calc_params['resistivity'],self.cable_calc_params['target_drop_pct'])
            record['working_section_mm2']=result['recommended_mm2']
            record['drop_at_working_section_pct']=result['actual_drop_pct']
        return record

    def compute_cable_length_mm(self,sid):
        rec=self._calculate_two_pole_route(sid)
        return (rec['loop_length_m']*1000,True) if rec else (None,False)

    def compute_all_cable_routes(self):
        import copy
        records={};self.cable_network_routes={};failed=[];direct=0
        for sid in self._get_sorted_string_keys():
            if not self.strings.get(sid):continue
            rec=self._calculate_two_pole_route(sid)
            if not rec:failed.append(sid);continue
            records[sid]=rec
            pa=rec['terminal_A'];pb=rec['terminal_B']
            points=pa['roof_points_px']+pa.get('ground_points_px',[])
            points_b=pb['roof_points_px']+pb.get('ground_points_px',[])
            fallback=any(p.get('method')=='direct' for p in (pa,pb))
            direct+=int(fallback)
            self.cable_network_routes[sid]={'points':points,'points_b':points_b,'length_m':rec['loop_length_m'],
                'pole_a_m':pa['length_m'],'pole_b_m':pb['length_m'],'route_kind':'A+B estimate' if fallback else 'A+B 3D',
                'block':rec['inverter'],'status':rec['route_status']}
        self.electrical_route_plan_3d={'routes':records,'source_signature':copy.deepcopy(self._route_signature()),
                                      'status':'PRELIMINARY — both conductors; no inter-module or AC cables'}
        lengths=[r['length_m'] for r in self.cable_network_routes.values()]
        return {'ok':len(records),'failed':failed,'total_m':sum(lengths),'max_m':max(lengths,default=0),'direct_count':direct}

    def _draw_cable_network_routes(self,zoom):
        if not self.show_cable_network_routes or self._get_active_tab_index()!=8:return
        # Never draw a stale route after a module, path or inverter edit.
        for sid,route in list(self.cable_network_routes.items()):
            if not self.get_two_pole_route(sid):self.cable_network_routes.pop(sid,None)
        super()._draw_cable_network_routes(zoom)
        for sid,route in self.cable_network_routes.items():
            pts=route.get('points_b',[])
            if len(pts)>1:self.canvas.create_line(*[c*zoom for p in pts for c in p],fill='#7B1FA2',width=2,dash=(5,3))
        selected=getattr(self,'selected_cable_route',None)
        x=self.canvas.canvasx(14);y=self.canvas.canvasy(14)
        self.canvas.create_rectangle(x,y,x+256,y+62,fill='#F7FBFF',outline='#66849C')
        self.canvas.create_line(x+9,y+18,x+34,y+18,fill='#E65100',width=3)
        self.canvas.create_text(x+42,y+18,anchor='w',text='Pole A · solid, inverter colour',fill='#18334A')
        self.canvas.create_line(x+9,y+41,x+34,y+41,fill='#7B1FA2',width=2,dash=(5,3))
        self.canvas.create_text(x+42,y+41,anchor='w',text='Pole B · dashed; total = A + B',fill='#18334A')
        if selected in self.cable_network_routes:
            route=self.cable_network_routes[selected]
            for suffix,key in [('A','points'),('B','points_b')]:
                points=route.get(key,[])
                if points:
                    px,py=points[0]
                    self.canvas.create_text(px*zoom+12,py*zoom-12,anchor='w',
                        text=f"{selected.replace('String ','S')} {suffix} · {route['pole_'+suffix.lower()+'_m']:.1f} m",
                        fill='#C43A18' if suffix=='A' else '#7B1FA2',font=('Arial',9,'bold'))
