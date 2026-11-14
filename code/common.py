"""Shared loading and definitions."""
import numpy as np, pandas as pd
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PRO=ROOT/'data/processed'; EXT=ROOT/'data/external'; TAB=ROOT/'output/tables'; FIG=ROOT/'output/figures'
EARLY=[2019,2021]   # FY2019-20 and FY2021-22; FY2020-21 skipped for COVID
RECENT=[2023,2024]  # FY2023-24 and FY2024-25, the last two full years in Ember
FUELS=['Bioenergy','Coal','Gas','Hydro','Nuclear','OtherFossil','OtherRE','Solar','Wind']
EF={'Coal':820,'Gas':490,'OtherFossil':700,'Wind':11,'Solar':48,'Bioenergy':230,'Hydro':24,'OtherRE':38,'Nuclear':12}
MONTHS=['Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan','Feb','Mar']
SHORT={'Dadra and Nagar Haveli and Daman and Diu':'DNH&DD','Jammu and Kashmir':'J&K+Ladakh','Arunachal Pradesh':'Arunachal','Himachal Pradesh':'Himachal','Madhya Pradesh':'MP','Uttar Pradesh':'UP','Andhra Pradesh':'Andhra','Tamil Nadu':'Tamil Nadu','West Bengal':'W Bengal'}
REGION={'NR':['Chandigarh','Delhi','Haryana','Himachal Pradesh','Jammu and Kashmir','Punjab','Rajasthan','Uttar Pradesh','Uttarakhand'],
'WR':['Chhattisgarh','Gujarat','Madhya Pradesh','Maharashtra','Dadra and Nagar Haveli and Daman and Diu','Goa'],
'SR':['Andhra Pradesh','Telangana','Karnataka','Kerala','Tamil Nadu','Puducherry'],
'ER':['Bihar','Jharkhand','Odisha','West Bengal','Sikkim'],
'NER':['Arunachal Pradesh','Assam','Manipur','Meghalaya','Mizoram','Nagaland','Tripura']}
ST2REG={s:r for r,l in REGION.items() for s in l}
def fy(idx): return idx.year-(idx.month<4)
def load(w=0.5):
    """w = share of DVC load given to Jharkhand; the rest goes to West Bengal."""
    dd=pd.read_csv(PRO/'demand_daily_wide.csv',parse_dates=['date'],index_col='date')
    dd['Jharkhand']=dd['Jharkhand']+w*dd['DVC']; dd['West Bengal']=dd['West Bengal']+(1-w)*dd['DVC']; dd=dd.drop(columns='DVC')
    e=pd.read_csv(PRO/'ember_panel.csv',parse_dates=['month']); e['fy']=e.month.dt.year-(e.month.dt.month<4)
    c=pd.read_csv(EXT/'state_context.csv').set_index('state')
    return dd,e,c
def pop(c,year_mid):
    """Geometric path between Census 2011 (1 Mar 2011) and the 2026 projection."""
    t=(year_mid-2011.17)/15.0
    return c.pop_2011*(c.pop_2026/c.pop_2011)**t
