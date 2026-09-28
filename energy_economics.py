"""Value useful PV and grid exports without double-counting battery charging.

This is an economic evaluation of the existing energy dispatch. It does not
send commands to site equipment or optimise against hourly market forecasts.
"""
import csv
from math import isfinite

DEFAULTS = {'import_eur_kwh':0.25,'export_low_eur_kwh':0.07,
            'export_high_eur_kwh':0.08,'pv_capex_eur':250000.,
            'bess_capex_each_eur':50000.}

def validate_settings(settings=None):
    values=dict(DEFAULTS)
    values.update(settings or {})
    values={key:float(values[key]) for key in DEFAULTS}
    if not all(isfinite(v) for v in values.values()):
        raise ValueError('Valori economici non finiti')
    if values['import_eur_kwh']<=0 or min(values.values())<0:
        raise ValueError('Prezzo acquisto positivo; altri valori non negativi')
    if values['export_low_eur_kwh']>values['export_high_eur_kwh']:
        raise ValueError('Prezzo minimo di vendita superiore al massimo')
    return values

def evaluate_options(annuals, settings=None):
    settings=validate_settings(settings)
    if len(annuals)!=3:raise ValueError('Servono i tre bilanci 0 / 1 / 2 BESS')
    results=[]
    for tariff in (settings['export_low_eur_kwh'],settings['export_high_eur_kwh']):
        previous=None
        for n,a in enumerate(annuals):
            useful=a['self_kwh'] if n==0 else a['useful_self_kwh']
            grid=a['grid_kwh']; export=a['export_kwh'];load=a['load_kwh']
            if min(useful,grid,export,load)<0 or abs(load-useful-grid)>0.01:
                raise ValueError('Bilancio dei carichi non coerente')
            avoided=useful*settings['import_eur_kwh']
            revenue=export*tariff
            purchases=grid*settings['import_eur_kwh']
            benefit=avoided+revenue
            capex=settings['pv_capex_eur']+n*settings['bess_capex_each_eur']
            delta=None if previous is None else benefit-previous['total_benefit_eur']
            lost=None if previous is None else previous['export_revenue_eur']-revenue
            results.append({'bess_count':n,'export_eur_kwh':tariff,'useful_pv_kwh':useful,
                'export_kwh':export,'grid_kwh':grid,'avoided_purchases_eur':avoided,
                'export_revenue_eur':revenue,'grid_purchases_eur':purchases,
                'net_energy_outlay_eur':purchases-revenue,'total_benefit_eur':benefit,
                'capex_eur':capex,'simple_payback_years':capex/benefit if benefit>0 else None,
                'incremental_benefit_eur':delta,'foregone_export_eur':lost,
                'incremental_payback_years':settings['bess_capex_each_eur']/delta if delta is not None and delta>0 else None})
            previous=results[-1]
    return results

def write_economic_csv(path, rows):
    if not rows:raise ValueError('Nessun risultato economico')
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def storage_margin_per_charge_kwh(settings, round_trip_efficiency):
    """Gross incremental value per kWh charged and later used by the load."""
    s=validate_settings(settings)
    eta=float(round_trip_efficiency)
    if not 0<eta<=1:raise ValueError('Rendimento di ciclo non valido')
    return {p:eta*s['import_eur_kwh']-p for p in
            (s['export_low_eur_kwh'],s['export_high_eur_kwh'])}
