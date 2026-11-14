"""Step 1. Clean each source, repair known breaks, build the monthly and daily panels."""
import numpy as np, pandas as pd, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data/raw'; EXT=ROOT/'data/external'; OUT=ROOT/'data/processed'; TAB=ROOT/'output/tables'
log=[]
def note(s): print(s); log.append(s)

# ---------- Ember ----------
e=pd.read_csv(RAW/'ember_india_monthly.csv',parse_dates=['Date'])
note(f'Ember rows {len(e)}, states {e.State.nunique()}, {e.Date.min():%Y-%m} to {e.Date.max():%Y-%m}')
g=e[(e.Category=='Electricity generation')&(e.Unit=='GWh')&(e.Subcategory.isin(['Fuel','Total']))]
c=e[(e.Category=='Capacity')&(e.Unit=='MW')&(e.Subcategory=='Fuel')]
gen=g.pivot_table(index=['State','Date'],columns='Variable',values='Value',aggfunc='first',dropna=False)
cap=c.pivot_table(index=['State','Date'],columns='Variable',values='Value',aggfunc='first',dropna=False).add_prefix('cap_')
# India Total check against sum of states
st=gen.drop(['India Total','Others'],level=0)
it=gen.xs('India Total',level=0)['Total Generation']
chk=(st['Total Generation'].groupby('Date').sum()-it).abs().max()
ot=gen.xs('Others',level=0)['Total Generation'].sum()/gen.xs('India Total',level=0)['Total Generation'].sum()
note(f'Ember: max gap between sum of states and India Total {chk:.1f} GWh; Others share {100*ot:.3f}%')
df=gen.join(cap).reset_index()
df=df[~df.State.isin(['India Total','Others'])]
# J&K + Ladakh merged. sum only observed
ren={'Ladakh':'Jammu and Kashmir'}
df['State']=df.State.replace(ren)
nums=[x for x in df.columns if x not in('State','Date')]
df=df.groupby(['State','Date'],as_index=False)[nums].sum(min_count=1)
miss=df[df.Date<='2025-03-01'][nums].isna().mean().round(3)
note('Ember missing share by variable, Apr 2019 scope:\n'+miss.to_string())
# after merge: fuel gen blank means none reported. treat missing fuel generation as zero only when the total exists
fuels=['Bioenergy','Coal','Gas','Hydro','Nuclear','Other Fossil','Other Renewables','Solar','Wind']
gmiss=df[fuels].isna().sum().sum(); df[fuels]=df[fuels].fillna(0)
df['sumfuels']=df[fuels].sum(axis=1); gap=(df.sumfuels-df['Total Generation']).abs()
note(f'Ember: {gmiss} blank fuel-months set to 0; {int((gap>1).sum())} state-months where fuels differ from total by >1 GWh, max {gap.max():.1f}')
capc=[f'cap_{f}' for f in fuels]; df[capc]=df[capc].fillna(0)
df=df.drop(columns='sumfuels').rename(columns={'State':'state','Date':'month','Total Generation':'gen_total','Other Fossil':'OtherFossil','Other Renewables':'OtherRE'})
df=df.rename(columns={'cap_Other Fossil':'cap_OtherFossil','cap_Other Renewables':'cap_OtherRE'})
df=df.drop(columns=[x for x in df.columns if x in('CO2 intensity','Total emissions')],errors='ignore')
df=df[~df.state.isin(['Lakshadweep','Andaman and Nicobar'])]
note(f'Ember panel: {df.state.nunique()} units')

# ---------- Grid-India daily ----------
d=pd.read_csv(RAW/'gridindia_daily_psp.csv',low_memory=False)
d['date']=pd.to_datetime(d.yyyymmdd,format='%Y%m%d'); d=d.set_index('date').sort_index()
d=d.loc['2019-04-01':'2026-10-31']
s=lambda n:d[f'{n}: EnergyMet']
nm={'Punjab':'Punjab','Haryana':'Haryana','Rajasthan':'Rajasthan','Delhi':'Delhi','UP':'Uttar Pradesh','Uttarakhand':'Uttarakhand','HP':'Himachal Pradesh','J&K(UT) & Ladakh(UT)':'Jammu and Kashmir','Chandigarh':'Chandigarh','Chhattisgarh':'Chhattisgarh','Gujarat':'Gujarat','MP':'Madhya Pradesh','Maharashtra':'Maharashtra','Goa':'Goa','Andhra Pradesh':'Andhra Pradesh','Karnataka':'Karnataka','Kerala':'Kerala','Tamil Nadu':'Tamil Nadu','Puducherry':'Puducherry','Bihar':'Bihar','DVC':'DVC','Jharkhand':'Jharkhand','Odisha':'Odisha','West Bengal':'West Bengal','Sikkim':'Sikkim','Arunachal Pradesh':'Arunachal Pradesh','Assam':'Assam','Manipur':'Manipur','Meghalaya':'Meghalaya','Mizoram':'Mizoram','Nagaland':'Nagaland','Tripura':'Tripura','Telangana':'Telangana'}
x=pd.DataFrame({v:s(k) for k,v in nm.items()})
x['Dadra and Nagar Haveli and Daman and Diu']=s('DD').fillna(0)+s('DNH').fillna(0)+s('DNHDDPDCL').fillna(0)
# Bulk loads (AMNSIL/Essar, RIL Jamnagar, BALCO, Railways, Bulk Consumer ISTS) have their own rows and stay out.
# Tested: adding AMNSIL+RIL to Gujarat and BALCO to Chhattisgarh widens the gap to CEA (see validation_bulk_addback.csv).
raw_guj=x['Gujarat'].copy(); raw_chh=x['Chhattisgarh'].copy()
test_guj=raw_guj+s('AMNSIL').fillna(0)+s('Essar steel').fillna(0)+s('RIL JAMNAGAR').fillna(0); test_chh=raw_chh+s('BALCO').fillna(0)
x=x.mask(x<=0)
x=x.mask(s('Punjab').isna())
nanday=int(x['Punjab'].isna().sum()); x=x.interpolate(limit=3)
note(f'Grid-India: {len(x)} days, {nanday} blank days interpolated, non-positive cells set blank and interpolated')
# outlier screen: a day under 40% or over 170% of its centred 15-day median
med=x.rolling(15,center=True,min_periods=8).median(); r=x/med
bad=(r<0.4)|(r>1.7)
big=[c for c in x.columns if x[c].mean()>20]
tab=bad[big].stack(); tab=tab[tab]; rows=[(i[0].date(),i[1],round(x.loc[i],1),round(med.loc[i],1)) for i in tab.index]
pd.DataFrame(rows,columns=['date','state','value_GWh','median15']).to_csv(TAB/'gridindia_outlier_days.csv',index=False)
note(f'Grid-India outlier screen, states over 20 GWh/day: {len(rows)} flagged days: {rows[:12]}')
fix=bad[big]; x[big]=x[big].mask(fix).interpolate(limit=3)
# ---------- monthly demand ----------
dm=x.resample('MS').sum()
dm['days']=dm.index.days_in_month
dm.to_csv(OUT/'demand_monthly_wide.csv'); x.to_csv(OUT/'demand_daily_wide.csv')

# ---------- validation: Grid-India energy met against CEA requirement ----------
cea=pd.read_csv(EXT/'cea_annual_state.csv').set_index('state')
fy=lambda i:i.year-(i.month<4)
ann=x.groupby(fy(x.index)).sum()
val=pd.DataFrame({'gi_1920':ann.loc[2019],'gi_2021':ann.loc[2020],'gi_2425':ann.loc[2024],'gi_2526':ann.loc[2025]}).join(cea,how='inner')
for a,b in [('1920','fy1920'),('2021','fy2021'),('2425','fy2425'),('2526','fy2526')]:
    val['pct_'+a]=100*(val['gi_'+a]/val['req_'+b]-1)
val.round(2).to_csv(TAB/'validation_gridindia_vs_cea.csv')
fyv=fy(test_guj.index); bb=[]
for nm_,raw_,tst_ in [('Gujarat',raw_guj,test_guj),('Chhattisgarh',raw_chh,test_chh)]:
    for y,c_ in [(2019,'req_fy1920'),(2020,'req_fy2021'),(2024,'req_fy2425'),(2025,'req_fy2526')]:
        bb.append((nm_,y,round(100*(raw_[fyv==y].sum()/cea.loc[nm_,c_]-1),1),round(100*(tst_[fyv==y].sum()/cea.loc[nm_,c_]-1),1)))
pd.DataFrame(bb,columns=['state','fy_start','gap_row_as_reported_pct','gap_with_addback_pct']).to_csv(TAB/'validation_bulk_addback.csv',index=False); print(bb)
pd.set_option('display.width',200); print(val[[c for c in val if c.startswith('pct')]].round(1).to_string())
for a in ['1920','2021','2425','2526']:
    v=val['pct_'+a]; note(f"GI vs CEA {a}: median abs gap {v.abs().median():.2f}%, within 2% in {int((v.abs()<2).sum())}/{len(v)}; all-units gap {100*(val['gi_'+a].sum()/val['req_fy'+a].sum()-1):.2f}%")

# ---------- Ember capacity vs MNRE official table, 31 March 2025 ----------
mn=pd.read_csv(EXT/'mnre_state_capacity_31mar2025.csv')
mn['state']=mn.state.replace({'Ladakh':'Jammu and Kashmir'}); mn=mn.groupby('state',as_index=False).sum(numeric_only=True)
mn=mn[~mn.state.isin(['Andaman and Nicobar','Lakshadweep'])]
cm=df[df.month=='2025-03-01'][['state','cap_Solar','cap_Wind']].merge(mn.rename(columns={'solar_total':'SolarTotal','wind':'mnre_wind'}),on='state')
cm[['state','cap_Solar','SolarTotal','cap_Wind','mnre_wind']].to_csv(TAB/'validation_capacity_mar2025.csv',index=False)
for a_,b_ in [('cap_Solar','SolarTotal'),('cap_Wind','mnre_wind')]:
    t=cm[cm[b_]>50]; p=100*(t[a_]/t[b_]-1)
    note(f'{a_} vs MNRE {b_} on 31.03.2025: {len(t)} states, median abs gap {p.abs().median():.2f}%, within 2%: {int((p.abs()<2).sum())}/{len(t)}, max {p.abs().max():.1f}%')
note(f'National: Ember solar {cm.cap_Solar.sum():.0f} MW vs MNRE {cm.SolarTotal.sum():.0f}; Ember wind {cm.cap_Wind.sum():.0f} vs MNRE {cm.mnre_wind.sum():.0f}')
df.to_csv(OUT/'ember_panel.csv',index=False)
(ROOT/'output/tables/prep_log.txt').write_text('\n'.join(log))
