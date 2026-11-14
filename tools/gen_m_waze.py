#!/usr/bin/env python3
"""gen_m_waze.py - the "M + Waze map" layout, apps/cluster_themes/hud/layouts/m_waze.json, made from m.json.

    python3 tools/gen_m_waze.py

M as it is while the Waze map shows inside it (the rev blades out at the sides, the gear and speed under the map),
kept that way: the map window opens and closes as the map comes and goes without the theme being built again
("mapLive"; m.json swaps its whole layout then, which takes seconds on the car). Run it again after m.json changes.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUTS = os.path.join(ROOT, 'apps', 'cluster_themes', 'hud', 'layouts')

with open(os.path.join(LAYOUTS, 'm.json')) as f:
    m = json.load(f)
widgets = []
for w in m['widgets']:
    t = w.get('toggle')
    if t == '!mapUp':
        continue
    w = dict(w)
    if t == 'mapUp':
        del w['toggle']
    widgets.append(w)
assert not any('mapUp' in str(w.get('toggle', '')) for w in widgets)
out = dict(m, name='M + Waze map', mapLive=True, widgets=widgets,
           _about='M laid out as with the Waze map inside it, always (generated from m.json by tools/gen_m_waze.py): '
                  'the map window opens and closes without a rebuild. ' + m.get('_about', ''))
with open(os.path.join(LAYOUTS, 'm_waze.json'), 'w') as f:
    json.dump(out, f, indent=1)
    f.write('\n')
print('m_waze.json: %d widgets (m.json %d)' % (len(widgets), len(m['widgets'])))
