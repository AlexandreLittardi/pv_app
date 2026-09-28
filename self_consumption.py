"""Profili orari e bilancio FV/utenza. Nessuna batteria nel calcolo."""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo


def read_open_meteo_json(path, profile):
    """Allinea meteo storico Open-Meteo alle 24 colonne locali per giorno."""
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    hourly=data.get('hourly',{})
    times=hourly.get('time',[])
    irradiance=hourly.get('global_tilted_irradiance',[])
    ambient=hourly.get('temperature_2m',[])
    if not times or len(times)!=len(irradiance) or len(times)!=len(ambient):
        raise ValueError('Il JSON deve contenere hourly.time, global_tilted_irradiance e temperature_2m')
    if data.get('timezone') != 'Europe/Rome':
        raise ValueError('Il file meteo deve usare timezone=Europe/Rome')
    groups={}
    for stamp,poa,temp in zip(times,irradiance,ambient):
        # Open-Meteo documenta GTI come media dell'ora precedente: etichetta
        # l'intervallo all'inizio, coerente con la colonna 0..23 dei consumi.
        key=(dt.datetime.fromisoformat(stamp)-dt.timedelta(hours=1)).strftime('%Y-%m-%dT%H:00')
        if poa is None or temp is None or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (poa,temp)):
            raise ValueError(f'Meteo mancante o non valido: {stamp}')
        if not 0 <= poa <= 1600 or not -60 <= temp <= 65:
            raise ValueError(f'Valore meteo fuori intervallo: {stamp}')
        groups.setdefault(key,[]).append((float(poa),float(temp)))
    hourly_poa=[];hourly_temp=[];ambiguous=[];absent=[]
    stamps=timestamps(profile)
    for i,stamp in enumerate(stamps):
        key=stamp.strftime('%Y-%m-%dT%H:00')
        pairs=groups.get(key)
        if not pairs:
            hourly_poa.append(None);hourly_temp.append(None);absent.append(i)
        else:
            if len(pairs)>1:ambiguous.append(i)
            hourly_poa.append(sum(p[0] for p in pairs)/len(pairs))
            hourly_temp.append(sum(p[1] for p in pairs)/len(pairs))
    if len(absent)>1 or len(ambiguous)>1:
        raise ValueError(f'Date/ore meteo non allineate: {len(absent)} mancanti, {len(ambiguous)} duplicate')
    for i in absent:
        if i%24==0 or i%24==23:
            raise ValueError('Ora mancante non interpolabile all’estremo della giornata')
        for seq in (hourly_poa,hourly_temp):
            if seq[i-1] is None or seq[i+1] is None:
                raise ValueError('Ora meteo mancante con vicine assenti')
            seq[i]=(seq[i-1]+seq[i+1])/2
    return {'hourly_poa_w_m2':hourly_poa,'hourly_ambient_c':hourly_temp,
            'source_filename':Path(path).name,'source':'Open-Meteo historical reanalysis',
            'missing_local_indices':absent,'repeated_local_indices':ambiguous,
            'period_start':profile['start_date'],'period_end':profile['end_date'],
            'latitude':data.get('latitude'),'longitude':data.get('longitude')}


def read_daily_excel(path):
    """Legge il formato Volfrigo: data, giorno, colonne 0..23 in kWh."""
    from openpyxl import load_workbook

    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = book.active
        rows = sheet.iter_rows(values_only=True)
        header = next((row for row in rows if row and str(row[0]).lower() == 'data'), None)
        if header is None or [str(x) for x in header[2:26]] != [str(h) for h in range(24)]:
            raise ValueError('Intestazione attesa: data, giorno, 0, ..., 23')
        dates, values, missing = [], [], []
        for row in rows:
            if not row or not isinstance(row[0], (dt.date, dt.datetime)):
                continue
            date = row[0].date() if isinstance(row[0], dt.datetime) else row[0]
            if dates and date != dates[-1] + dt.timedelta(days=1):
                raise ValueError(f'Date non consecutive: {dates[-1]} / {date}')
            dates.append(date)
            for h in range(24):
                value = row[h+2] if len(row) > h+2 else None
                if value is None or value == '':
                    missing.append(len(values)); values.append(None)
                elif isinstance(value, (int, float)) and math.isfinite(value) and value >= 0:
                    values.append(float(value))
                else:
                    raise ValueError(f'Valore kWh non valido: {date} ora {h}: {value!r}')
        if not dates:
            raise ValueError('Nessun consumo orario trovato')
        if len(values) != len(dates)*24:
            raise ValueError('Numero ore non coerente')
        # Prior 7 same clock hours: preserves a 24-slot/day representation.
        for i in missing:
            history = [values[i-24*d] for d in range(1, 8)
                       if i-24*d >= 0 and values[i-24*d] is not None]
            if not history:
                raise ValueError(f'Impossibile stimare il consumo mancante all’indice {i}')
            values[i] = sum(history)/len(history)
        return {'start_date': dates[0].isoformat(), 'end_date': dates[-1].isoformat(),
                'hourly_kwh': values, 'imputed_indices': missing,
                'source_filename': Path(path).name, 'hour_convention': '24 colonne per giorno, ora locale'}
    finally:
        book.close()


def timestamps(profile):
    start = dt.date.fromisoformat(profile['start_date'])
    end = dt.date.fromisoformat(profile['end_date'])
    n = (end-start).days+1
    if n*24 != len(profile['hourly_kwh']):
        raise ValueError('Profilo di consumo non coerente con le date')
    return [dt.datetime.combine(start + dt.timedelta(days=i//24),dt.time(i%24))
            for i in range(n*24)]


def production_from_program(app, profile, ac_factor=0.90, progress=None, weather=None):
    """Usa gli stessi metodi di energia, sole e ombra del programma.

    Il simulatore originale è a cielo sereno; ac_factor modellizza perdite
    aggiuntive DC/AC in uno scenario parametrico, non dati meteo misurati.
    """
    if not 0 < ac_factor <= 1:
        raise ValueError('Il rendimento aggiuntivo AC deve essere fra 0 e 1')
    if not app.panels or getattr(app, 'panel_pmax_w', 0) <= 0:
        raise ValueError('Caricare un layout con pannelli e Pmax valido')
    if getattr(app,'pylon_img_pos',None) is not None and getattr(app,'px_per_mm',0) <= 0:
        raise ValueError('Calibrare la scala prima di usare l’ombra del pilone')
    zone = ZoneInfo('Europe/Rome')
    n_panels = len(app.panels)
    ratings=[]
    for block in app.blocks:
        row=app.inverter_positions.get(block,{}).get('material_row',{})
        raw=row.get('Puissance (kVA)',125)
        try: ratings.append(float(str(raw).replace(',','.')))
        except ValueError: raise ValueError('Specify inverter AC power before energy calculation')
    max_ac_kw=sum(ratings)
    if max_ac_kw<=0:raise ValueError('No configured inverter AC capacity')
    orientations={}
    coord_group={}
    for coord in app.panels:
        item=app.panel_orientations.get(coord,{})
        key=(item.get('tilt_deg',app.panel_tilt_deg),item.get('azimuth_deg',app.panel_azimuth_deg))
        orientations.setdefault(key,[]).append(coord);coord_group[coord]=key
    if weather and len(orientations)>1:
        raise ValueError('Historical GTI is for one roof orientation. Import a matching profile per orientation before using mixed-orientation weather.')
    shadow_panels = None
    if app.pylon_img_pos is not None:
        app._recalculate_zone_grids()
        shadow_panels = []
        for coord in app.panels:
            r,c=coord
            for z_idx,z in enumerate(app.roof_zones):
                base=int(z.get('row_base',z_idx*100))
                if base <= r < base+int(z.get('rows',0)) and 0 <= c < int(z.get('cols',0)):
                    polygon=app._panel_rect(coord)
                    if polygon:
                        bounds=(min(p[0] for p in polygon),min(p[1] for p in polygon),
                                max(p[0] for p in polygon),max(p[1] for p in polygon))
                        shadow_panels.append((coord,z_idx,polygon,bounds,app._polygon_area(polygon)))
                    break
    pv = []
    hours = timestamps(profile)
    if weather and (len(weather['hourly_poa_w_m2']) != len(hours)
                    or len(weather['hourly_ambient_c']) != len(hours)
                    or weather['period_start'] != profile['start_date']
                    or weather['period_end'] != profile['end_date']):
        raise ValueError('Periodo o numero di ore del meteo diverso dai consumi')
    for i, stamp in enumerate(hours):
        # Il file assume 24 ore anche nelle due date del cambio di ora.
        # Per ciascuna colonna si usa l'offset locale del suo centro orario.
        midpoint = stamp + dt.timedelta(minutes=30)
        utc_offset = midpoint.replace(tzinfo=zone).utcoffset().total_seconds()/3600
        elev, az = app._compute_solar_position(
            app.solar_latitude,app.solar_longitude,stamp.day,stamp.month,
            stamp.hour+0.5,utc_offset,year=stamp.year)
        kwh = 0.0
        if elev > 0.1:
            irradiances={key:(weather['hourly_poa_w_m2'][i] if weather else
                              app._get_clear_sky_poa_irradiance(elev,az,members[0]))
                         for key,members in orientations.items()}
            ambient = weather['hourly_ambient_c'][i] if weather else None
            def panel_w(irradiance,shaded_fraction=0):
                if ambient is None:
                    return app._estimate_panel_power_w(irradiance,shaded_fraction)
                effective=max(0,irradiance*(1-shaded_fraction))
                cell_c=ambient+(app.panel_noct_c-20)*effective/800
                return max(0,app.panel_pmax_w*effective/1000*
                           max(0,1+app.panel_temp_coeff_pct/100*(cell_c-25)))
            ideal_power = {key:panel_w(g) for key,g in irradiances.items()}
            total_ideal_w=sum(ideal_power[key]*len(members) for key,members in orientations.items())
            if app.pylon_img_pos is not None:
                # Stessa geometria e stesso modello di potenza del simulatore,
                # con rettangoli dei pannelli precomputati per le 8760 ore.
                loss_w=0.0
                geometry={g['zone_idx']:g['polygon'] for g in app._compute_shadow_geometry(elev,az)}
                geom_bounds={z:(min(p[0] for p in poly),min(p[1] for p in poly),
                                max(p[0] for p in poly),max(p[1] for p in poly))
                             for z,poly in geometry.items()}
                opacity=max(0,min(1,getattr(app,'pylon_opacity',1)))
                for coord,z_idx,panel_poly,pb,area in shadow_panels:
                    gp=geometry.get(z_idx)
                    if gp is None or area<=0:continue
                    gb=geom_bounds[z_idx]
                    if pb[0]>gb[2] or pb[2]<gb[0] or pb[1]>gb[3] or pb[3]<gb[1]:continue
                    clipped=app._polygon_clip(gp,panel_poly)
                    if len(clipped)<3:continue
                    fraction=max(0,min(1,app._polygon_area(clipped)/area*opacity))
                    key=coord_group[coord]
                    loss_w+=ideal_power[key]-panel_w(irradiances[key],fraction)
                shaded_w=total_ideal_w-loss_w
            else:
                shaded_w = total_ideal_w
            kwh = min(max_ac_kw,shaded_w*ac_factor/1000)
        pv.append(kwh)
        if progress and (i%72 == 0 or i == len(hours)-1):
            progress(i+1,len(hours))
    return pv


def balance(profile, pv_kwh, export_limit_kw=None):
    if export_limit_kw is not None and (not math.isfinite(export_limit_kw) or export_limit_kw < 0):
        raise ValueError("Limite immissione non valido")
    hours = timestamps(profile)
    if len(pv_kwh) != len(hours):
        raise ValueError('Produzione e consumo devono avere le stesse ore')
    load = profile['hourly_kwh']
    monthly = {}
    rows = []
    for i, (stamp, demand, produced) in enumerate(zip(hours,load,pv_kwh)):
        if not all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in (demand,produced)):
            raise ValueError(f'Ora {i}: produzione o consumo non valido')
        self_used = min(demand,produced)
        imported = demand-self_used
        surplus = produced-self_used
        exported = surplus if export_limit_kw is None else min(surplus, export_limit_kw)
        curtailed = surplus-exported
        month = stamp.strftime('%Y-%m')
        bucket = monthly.setdefault(month,{'load_kwh':0,'pv_kwh':0,'self_kwh':0,'grid_kwh':0,'export_kwh':0,'curtailed_kwh':0})
        for key,val in (('load_kwh',demand),('pv_kwh',produced),('self_kwh',self_used),
                        ('grid_kwh',imported),('export_kwh',exported),('curtailed_kwh',curtailed)):
            bucket[key]+=val
        rows.append((stamp.isoformat(' '),demand,produced,self_used,imported,exported,i in profile['imputed_indices']))
    total={k:sum(m[k] for m in monthly.values()) for k in next(iter(monthly.values()))}
    total['autoconsumption_pct']=100*total['self_kwh']/total['pv_kwh'] if total['pv_kwh'] else 0
    total['self_sufficiency_pct']=100*total['self_kwh']/total['load_kwh'] if total['load_kwh'] else 0
    return {'annual':total,'monthly':monthly,'rows':rows,'export_limit_kw':export_limit_kw}


def write_hourly_csv(path, result):
    with open(path,'w',newline='',encoding='utf-8-sig') as out:
        writer=csv.writer(out)
        writer.writerow(['data_ora_locale','consumo_kwh','produzione_ac_kwh','autoconsumo_kwh',
                         'prelievo_rete_kwh','immissione_rete_kwh','consumo_stimato'])
        writer.writerows(result['rows'])
