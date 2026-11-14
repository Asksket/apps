#!/usr/bin/env python3
"""gen_f90.py - the M5 (F90) theme's layout, apps/cluster_themes/hud/layouts/f90.json.

    python3 tools/gen_f90.py

After the Live Cockpit's M view of an F90 M5 (a photo of the car's own cluster in Sport): the speed scale left and
the rev scale right, each one white outer line with rounded corners (along the bottom, up the side, across the top)
with the numbers inside it, a red needle that runs along the line with a red glow behind it; the speed and the gear
over a line each; the setup (engine, chassis, steering) under the gear; fuel and oil temperature dials in the lower
corners. Black, opaque, so nothing of BMW's own gauges shows through; the middle is a window for the Waze map, cut
see-through only while the map shows (the map comes and goes without a rebuild: "mapLive").

The left scale's line is drawn by the f90dash shader from "path" (points along it, corners rounded here); the right
one is its mirror. Everything in target px (1920x720; the theme ends at 660, over BMW's bottom strip).
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'apps', 'cluster_themes')
W, H = 1920, 660

# the left scale's outer line: from its bottom end (by the middle) to its top end; corners rounded with these radii
VERTS = [(770, 628), (330, 628), (128, 352), (372, 92), (790, 50)]
RADII = [120, 175, 210]
S0_FROM_START = 300          # the scale's 0 this far along the line from its bottom end
S1_FROM_END = 70             # its top mark this far before the top end
LABEL_IN = 50                # the numbers' centres, px inside the line
SPEED = {'us': list(range(0, 201, 20)), 'metric': list(range(0, 321, 40))}
RPM = list(range(0, 9))
HOLE = [742, 128, 436, 470]  # the Waze map's window (the map is 1088x480 at 416,120)


def font(name):
    with open(os.path.join(APP, 'hud', 'fonts', name + '.json')) as f:
        return json.load(f)['cellHeight']


def rounded(verts, radii, per=7):
    """The polyline with each inner corner replaced by an arc of `per` segments."""
    out = [verts[0]]
    for i in range(1, len(verts) - 1):
        p, v, n = verts[i - 1], verts[i], verts[i + 1]
        a = (p[0] - v[0], p[1] - v[1]); b = (n[0] - v[0], n[1] - v[1])
        la, lb = math.hypot(*a), math.hypot(*b)
        ua, ub = (a[0] / la, a[1] / la), (b[0] / lb, b[1] / lb)
        ang = math.acos(max(-1, min(1, ua[0] * ub[0] + ua[1] * ub[1])))
        r = radii[i - 1]
        t = r / math.tan(ang / 2)
        p1 = (v[0] + ua[0] * t, v[1] + ua[1] * t); p2 = (v[0] + ub[0] * t, v[1] + ub[1] * t)
        bis = (ua[0] + ub[0], ua[1] + ub[1]); lbis = math.hypot(*bis)
        c = (v[0] + bis[0] / lbis * r / math.sin(ang / 2), v[1] + bis[1] / lbis * r / math.sin(ang / 2))
        a1 = math.atan2(p1[1] - c[1], p1[0] - c[0]); a2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
        d = a2 - a1
        while d > math.pi: d -= 2 * math.pi
        while d < -math.pi: d += 2 * math.pi
        for k in range(per + 1):
            aa = a1 + d * k / per
            out.append((c[0] + r * math.cos(aa), c[1] + r * math.sin(aa)))
    out.append(verts[-1])
    return [(round(x, 1), round(y, 1)) for x, y in out]


PATH = rounded(VERTS, RADII)
CUM = [0.0]
for i in range(1, len(PATH)):
    CUM.append(CUM[-1] + math.hypot(PATH[i][0] - PATH[i - 1][0], PATH[i][1] - PATH[i - 1][1]))
TOTAL = CUM[-1]
S0, S1 = S0_FROM_START, TOTAL - S1_FROM_END
assert len(PATH) <= 32, len(PATH)


def at(s):
    """The point at arc length s and the inward normal there (left scale: (-dy, dx))."""
    for i in range(1, len(PATH)):
        if s <= CUM[i] or i == len(PATH) - 1:
            a, b = PATH[i - 1], PATH[i]
            L = CUM[i] - CUM[i - 1]
            h = (s - CUM[i - 1]) / L
            dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            return (a[0] + (b[0] - a[0]) * h, a[1] + (b[1] - a[1]) * h), (-dy, dx)


def text(id_, x, y, w, fnt, txt, color='fg', align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': round(x), 'y': round(y), 'w': w, 'h': font(fnt), 'text': txt,
         'font': fnt, 'color': color, 'align': align}
    d.update(kw)
    return d


def scale_labels(prefix, values, right, toggle=None):
    out = []
    hn = font('f_num')
    for i, v in enumerate(values):
        (x, y), n = at(S0 + (S1 - S0) * i / (len(values) - 1))
        cx, cy = x + n[0] * LABEL_IN, y + n[1] * LABEL_IN
        if right: cx = W - cx
        d = text('%s%d' % (prefix, i), cx - 50, cy - hn / 2, 100, 'f_num', str(v), conn=1 if right else 0)
        if toggle: d['toggle'] = toggle
        out.append(d)
    return out


def main():
    widgets = [{
        'id': 'f90', 'type': 'f90dash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
        'path': [list(p) for p in PATH], 'scale': [round(S0, 1), round(S1, 1)],
        # the fuel dial (left lower corner; the oil one is its mirror): centre, radius, angle at full / empty
        'dial': [262, 438, 206], 'dialAng': [178, 114],
        # the line under the speed: from x to x at y; the bottom line runs on from the scale to x
        'line': [300, 718, 408, 905],
        'hole': HOLE, 'holeWhen': 'mapUp', 'holeInset': 0, 'holeRadius': 26,
    }]
    widgets += scale_labels('spd_us', SPEED['us'], False, 'units=us')
    widgets += scale_labels('spd_km', SPEED['metric'], False, '!units=us')
    widgets += scale_labels('rpm', RPM, True)
    hs, hg, hu, hl = font('f_speed'), font('f_gear'), font('f_unit'), font('f_lbl')
    widgets += [
        text('speed', 380, 408 - 14 - hs, 260, 'f_speed', '{{speed}}', align='right'),
        text('speed_unit', 650, 408 - 16 - hu, 100, 'f_unit', '{{u:speedLc}}', color='dim', align='left'),
        text('gear', W - 660, 408 - 12 - hg, 260, 'f_gear', '{{gearnum}}', align='center', hotWhen='now', conn=1),
        text('rpm_unit', W - 700, 584, 220, 'f_unit', '1/min x1000', color='dim', conn=1),
        text('scale_unit', 480, 584, 220, 'f_unit', '{{u:speedLc}}', color='dim'),
    ]
    for i, (icon, tok) in enumerate([('gauge', 'engine'), ('shock', 'chassis'), ('wheel', 'steering')]):
        cx = W - 630 + i * 128
        widgets.append({'id': 'setup_icon%d' % i, 'type': 'icon', 'icon': icon, 'z': 5, 'x': cx - 20, 'y': 428, 'w': 40, 'h': 36,
                        'color': 'dim', 'conn': 1})
        widgets.append(text('setup%d' % i, cx - 70, 472, 140, 'f_lbl', '{{setup:%s}}' % tok, color='fg', conn=1))
    # the corner dials' numbers: fuel 1, 1/2, 0 (top to bottom); oil temperature, its mirror, hot at the top
    cx, cy, r = 262, 438, 206
    a0, a1 = 178, 114
    hn = font('f_unit')
    for i, (f, lbl) in enumerate([(1, '1'), (0.5, '1/2'), (0, '0')]):
        a = math.radians(a1 + (a0 - a1) * f)
        x, y = cx + (r - 40) * math.cos(a), cy + (r - 40) * math.sin(a)
        widgets.append(text('fuel%d' % i, x - 40, y - hn / 2, 80, 'f_unit', lbl))
        widgets.append(text('oil%d' % i, W - x - 45, y - hn / 2, 90, 'f_unit', '{{temp:%d}}' % (50 + 100 * f), conn=1))
    widgets.append({'id': 'fuel_icon', 'type': 'icon', 'icon': 'fuel', 'z': 5, 'x': 30, 'y': 600, 'w': 24, 'h': 28, 'color': 'dim'})
    widgets.append({'id': 'oil_icon', 'type': 'icon', 'icon': 'oilcan', 'z': 5, 'x': W - 66, 'y': 602, 'w': 36, 'h': 24, 'color': 'dim', 'conn': 1})
    widgets.append(text('oil_unit', W - 58, 472, 50, 'f_unit', '{{u:temp}}', color='dim', align='left', conn=1))

    layout = {
        'schemaVersion': 2, 'name': 'M5 (F90)', 'theme': 'mdash', 'mapLive': True,
        '_about': 'After the Live Cockpit M view of an F90 M5 (generated by tools/gen_f90.py: edit that and run it again). '
                  'One f90dash effect layer draws the black backdrop, both scales (the right one is the left one mirrored), '
                  'the needles with their glow, the red rev zone, the corner dials and the lines; the numbers are text '
                  'widgets. The map window opens while the Waze map shows, without a rebuild (mapLive).',
        'widgets': widgets,
    }
    out = os.path.join(APP, 'hud', 'layouts', 'f90.json')
    with open(out, 'w') as f:
        json.dump(layout, f, indent=1)
        f.write('\n')
    print('%s: %d widgets, path %d points, %.0f px long (scale %.0f..%.0f)' % (out, len(widgets), len(PATH), TOTAL, S0, S1))


if __name__ == '__main__':
    main()
