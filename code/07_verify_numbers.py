"""Checks headline numbers quoted in the report against the output tables."""
from common import *
import json
a=json.load(open(TAB/'sq1_results.json')); b=json.load(open(TAB/'sq2_results.json')); c=json.load(open(TAB/'sq3_results.json'))
n=pd.read_csv(TAB/'sq2_national.csv',index_col=0); s=pd.read_csv(TAB/'sq1_state_summary.csv',index_col=0); t=pd.read_csv(TAB/'sq2_state_fy2425.csv',index_col=0); m=pd.read_csv(TAB/'sq2_consumption_mix.csv',index_col=0); g=pd.read_csv(TAB/'sq3_group_summary.csv',index_col=0)
chk=[('vre gen 19',n.vre_share[2019],8.3),('vre gen 24',n.vre_share[2024],12.5),('vre cap 19',n.vre_cap_share[2019],19.5),('vre cap 24',n.vre_cap_share[2024],32.7),('coal cf19',n.coal_cf[2019],55.7),('coal cf24',n.coal_cf[2024],69.5),('coal share19',n.coal_share[2019],71.9),('coal share24',n.coal_share[2024],73.1),
('coal incr %',b['increment']['coal_pct'],77),('vre incr %',b['increment']['vre_pct'],26),('gen incr',b['increment']['gen'],440),('ci19',b['ci_gen']['2019'],614),('ci24',b['ci_gen']['2024'],616),('peak cagr',a['cagr_peak_1924'],6.3),('energy cagr',a['cagr_energy_1924'],5.6),('state cagr',a['cagr_total'],5.4),
('Bihar g',s.cagr['Bihar'],7.2),('Delhi g',s.cagr['Delhi'],3.0),('Punjab kwh',s.kwh_pc2425['Punjab'],2529),('Bihar kwh',s.kwh_pc2425['Bihar'],343),('Nat kwh',a['national_kwh_pc'],1201),('slope',a['income']['slope'],.76),('r2',a['income']['r2'],.43),('Punjab swing',s.swing_r['Punjab'],2.37),('Gujarat swing',s.swing_r['Gujarat'],1.24),
('swing med e',a['swing']['median_e'],1.34),('swing med r',a['swing']['median_r'],1.37),('swing p',a['swing']['p'],.72),('flat p',a['flat']['p'],.68),('strength med',a['strength_median'],.74),('moved',a['n_peak_moved'],18),('lf 25',a['nat_lf']['2025'],79.4),
('Raj cf',t.cf_solar['Rajasthan'],22.7),('Mah cf',t.cf_solar['Maharashtra'],10.9),('Guj wind',t.cf_wind['Gujarat'],23.7),('Raj cap sh',t.cap_vre_share['Rajasthan'],68.8),('roof r',b['cf_roof']['pearson'],-.76),('roof rho',b['cf_roof']['spearman'],-.90),('wind extra',b['whatif_cf']['extra_wind_TWh'],6.1),('roof gw',b['whatif_cf']['roof_gw'],18.6),('hidden pct',b['whatif_cf']['hidden_pct_of_solar'],17),
('Delhi ci',m.ci_cons['Delhi'],618),('Delhi coal',m.coal_cons['Delhi'],68),('Kerala ci',m.ci_cons['Kerala'],498),('nat ci',b['consmix']['ci_nat'],616),('sd prod',b['consmix']['ci_sd_prod'],284),('sd cons',b['consmix']['ci_sd_cons'],206),('added',b['whatif_plateau']['added_fy2425'],28.0),('added avg',b['whatif_plateau']['added_avg5'],16.7),('blend cf',100*b['whatif_plateau']['cf_blended'],18.5),
('raj vre add',b['added']['raj_pct'],37),('top4 vre',b['added']['vre_top4_pct'],82),('top6 coal',b['added']['coal_top6_pct'],59),('n coal>vre',b['added']['n_coal_exceeds_vre'],18),
('coal cf up',b['coal_cf_state']['up'],15),('odisha cf',b['coal_cf_state']['top']['Odisha'],81.8),('haryana chg',b['coal_cf_state']['chg_top']['Haryana'],30.3),
('coal 2029 at 28',b['coal_paths_2029']['28'],1665),('coal 2029 at 62',b['coal_paths_2029']['62'],1390),('coal 2029 at 80',b['coal_paths_2029']['80'],1244),('coal 2024',b['coal_2024'],1332),
('shape corr e',a['shape_corr_e'],.25),('shape corr r',a['shape_corr_r'],.15),('short 19',a['shortage_pct']['2019'],.38),('short 24',a['shortage_pct']['2024'],.06),
('match neg',b['match']['neg'],8),('net flip',b['net']['flip'],13),('always imp',b['net']['always_import'],14),('always exp',b['net']['always_export'],6),
('pc1',100*c['evr'][0],26),('pc2',100*c['evr'][1],19),('pcs',c['pcs_for_80'],5)]
bad=0
for k,v,w in chk:
    d=abs(w); tol=0.5*10**(-(len(str(w).split('.')[1]) if '.' in str(w) else 0)); ok=abs(v-w)<=tol+1e-9
    if not ok: bad+=1; print('MISMATCH',k,v,w)
print(len(chk),'numbers checked,',bad,'mismatches')
