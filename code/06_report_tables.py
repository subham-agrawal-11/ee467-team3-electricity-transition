"""Writes the appendix state table for the report directly from the output tables."""
from common import *
A=pd.read_csv(TAB/'sq3_clusters.csv',index_col=0); r=A[A.window=='recent']
L=pd.read_csv(ROOT/'code/group_names.csv'); name={int(r.loc[x.anchor,'cluster']):x.name for x in L.itertuples()}
s=pd.read_csv(TAB/'sq1_state_summary.csv',index_col=0); t=pd.read_csv(TAB/'sq2_state_fy2425.csv',index_col=0); n=pd.read_csv(TAB/'sq2_net_position.csv',index_col=0); c=pd.read_csv(TAB/'sq2_consumption_mix.csv',index_col=0)
o=['Renewable-led','Coal-based','Peaky importers','Flat-load importers','Hydro exporters','Low-demand importers']
rows=[]
for g in o:
    k=[a for a,b in name.items() if b==g][0]; rows.append(r'\multicolumn{10}{l}{\textit{%s}}\\'%g)
    for st in sorted(r[r.cluster==k].index):
        rows.append(f"{SHORT.get(st,st).replace('&',chr(92)+'&')} & {s.kwh_pc2425[st]:,.0f} & {s.cagr[st]:.1f} & {s.swing_r[st]:.2f} & {s.peak_r[st]} & {c.coal_prod[st]:.0f} & {c.vre_prod[st]:.1f} & {n.net_fy2425[st]:.2f} & {c.ci_prod[st]:.0f} & {c.ci_cons[st]:.0f}\\\\")
head=r'''\begin{tabular}{lrrrlrrrrr}
\toprule
State & kWh per & Growth & Swing & Peak & Coal & S+W & Net & CI & CI\\
 & person & \% & & month & \% & \% & & gen & use\\
\midrule
'''
(ROOT/'report/tab_state.tex').write_text(head+'\n'.join(rows)+'\n\\bottomrule\n\\end{tabular}\n')
