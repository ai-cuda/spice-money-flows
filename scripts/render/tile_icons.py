# Usage: python3 -I scripts/render/tile_icons.py <apktool_dir> <out.json>
# Renders the home-tile vector drawables (nd_tile_*) to SVG data URIs via layout2html, keyed by the short names
# the prototypes use in their ICONS object. Add a key here when a new flow needs another tile icon
# (find the drawable via KotlinCommonUtilityKt.q() for BBPS category ids, or the tile's icon in DashboardTileAdapter).
import sys, json, os
RES = os.path.join(sys.argv[1], 'res'); OUT = sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = ['x', RES, os.path.dirname(os.path.abspath(OUT))]
import layout2html as L
names = {'cw': 'nd_tile_cw', 'ms': 'nd_tile_ms', 'cd': 'nd_tile_cd', 'be': 'nd_tile_be', 'ucp': 'nd_tile_acpt_upi_pay', 'atm': 'nd_tile_atm', 'dmt': 'nd_tile_money_transfer', 'axis': 'nd_tile_axis_banking', 'nsdl': 'nd_tile_nsdl_banking', 'loans': 'nd_tile_loans', 'suraksha': 'nd_tile_shop_insurance', 'cc': 'nd_bbps_cc',
         'mob': 'nd_tile_mobile_recharge', 'loan': 'nd_tile_bbps_loan', 'elec': 'nd_tile_bbps_bulb', 'dth': 'nd_tile_bbps_dth_recharge', 'agent': 'nd_tile_bbps_agent_collect', 'fastag': 'nd_tile_bbps_fastage', 'nhai': 'nd_nhai_', 'edu': 'nd_tile_education_fee',
         'water': 'nd_tile_bbps_water', 'gas': 'nd_tile_gas_lpg', 'housing': 'nd_tile_bbps_housing', 'ins': 'nd_tile_bbps_insurance', 'mtax': 'nd_tile_municipal_tax', 'bb': 'nd_tile_bbps_broadband', 'landline': 'nd_tile_bbps_landine', 'lic': 'nd_tile_lic_payments', 'edubbps': 'nd_tile_bbps_education_fee'}
out = {}
for k, n in names.items():
    cand = [f for f in os.listdir(RES + '/drawable') if f.startswith(n)] if n.endswith('_') else [n + '.xml']
    n2 = cand[0][:-4] if cand else n
    d = L.drawable('@drawable/' + n2)
    out[k] = d[1] if d and d[0] == 'img' else None
    print(k, n2, 'ok' if out[k] else 'MISSING')
json.dump(out, open(OUT, 'w'))
