#!/usr/bin/env python3
"""gen_f90.py - the M view theme's layout, apps/cluster_themes/hud/layouts/f90.json.

    python3 tools/gen_f90.py

After the Live Cockpit's M view (photos of an M3 G80's and an M5 F90's cluster in Sport, straight on): the speed scale
left and the rev scale right, each one white line with rounded corners (a step down by the middle, along the bottom,
up the side, across the top) with the numbers inside it in wide square figures; from 0 up to the value the band
inside the line is lit grey, brightest at the needle, a red needle across the line with red dots behind it; the speed
and the gear over a line each, the M stripes at the top, fuel and oil temperature dials at the far left and right.
Black, opaque, so nothing of BMW's own gauges shows through; the middle is a window for the Waze map, cut
see-through only while the map shows (the map comes and goes without a rebuild: "mapLive").

The left scale's line is drawn by the f90dash shader from "path" (points along it, corners rounded here); the right
one is its mirror. Everything in target px (1920x720; the theme ends at 660, over BMW's bottom strip). The photo's
1280 px frame maps as x * 1.5, y as 15 + (y - 140) * 1.4.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'apps', 'cluster_themes')
W, H = 1920, 660

# the left scale's line, from its bottom end by the middle (after the step) to its top end; corners rounded
VERTS = [(880, 652), (790, 652), (752, 636), (205, 636), (30, 318), (300, 82), (742, 26)]
RADII = [10, 10, 210, 260, 320]
S0_AT_X = 430                # the scale's 0 above this x on the bottom line
S1_FROM_END = 22             # its top mark this far before the top end
LABEL_IN = 56                # the numbers' centres, px inside the line
SPEED = {'us': list(range(0, 201, 20)), 'metric': list(range(0, 331, 30))}
RPM = list(range(0, 9))
HOLE = [700, 112, 520, 500]  # the Waze map's window (the map is 1088x480 at 416,120)
LINE_Y = 398                 # the lines under the speed and the gear


def font(name):
    with open(os.path.join(APP, 'hud', 'fonts', name + '.json')) as f:
        return json.load(f)['cellHeight']


def rounded(verts, radii, per=7):
    """The polyline with each inner corner replaced by an arc (`per` segments, 2 for a small one)."""
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
        n_seg = 2 if r < 30 else per
        for k in range(n_seg + 1):
            aa = a1 + d * k / n_seg
            out.append((c[0] + r * math.cos(aa), c[1] + r * math.sin(aa)))
    out.append(verts[-1])
    return [(round(x, 1), round(y, 1)) for x, y in out]


PATH = rounded(VERTS, RADII)
CUM = [0.0]
for i in range(1, len(PATH)):
    CUM.append(CUM[-1] + math.hypot(PATH[i][0] - PATH[i - 1][0], PATH[i][1] - PATH[i - 1][1]))
TOTAL = CUM[-1]
assert len(PATH) <= 32, len(PATH)


def s_at_bottom(x):
    """The arc length where the bottom line (y = 636) passes x."""
    for i in range(1, len(PATH)):
        a, b = PATH[i - 1], PATH[i]
        if abs(a[1] - 636) < 0.5 and abs(b[1] - 636) < 0.5 and min(a[0], b[0]) <= x <= max(a[0], b[0]):
            return CUM[i - 1] + abs(a[0] - x)
    raise ValueError(x)


S0, S1 = s_at_bottom(S0_AT_X), TOTAL - S1_FROM_END


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
        d = text('%s%d' % (prefix, i), cx - 55, cy - hn / 2, 110, 'f_num', str(v), conn=1 if right else 0)
        if toggle: d['toggle'] = toggle
        out.append(d)
    return out


def main():
    dial = [200, 470, 196]       # the fuel dial: centre, radius (the oil dial is its mirror)
    dial_ang = [180, 125]        # its angle at full and at empty
    widgets = [{
        'id': 'f90', 'type': 'f90dash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
        'path': [list(p) for p in PATH], 'scale': [round(S0, 1), round(S1, 1)],
        'dial': dial, 'dialAng': dial_ang,
        # the line under the speed: from x to x at y; the bottom line runs on from the scale to x
        'line': [252, 700, LINE_Y, 940],
        'hole': HOLE, 'holeWhen': 'mapUp', 'holeInset': 0, 'holeRadius': 30,
    }]
    widgets += scale_labels('spd_us', SPEED['us'], False, 'units=us')
    widgets += scale_labels('spd_km', SPEED['metric'], False, '!units=us')
    widgets += scale_labels('rpm', RPM, True)
    hs, hg, hu = font('f_speed'), font('f_gear'), font('f_unit')
    widgets += [
        text('speed', 300, LINE_Y - 14 - hs, 330, 'f_speed', '{{speed}}', align='right'),
        text('speed_unit', 638, LINE_Y - 12 - hu, 100, 'f_unit', '{{u:speedLc}}', color='dim', align='left'),
        text('gear', W - 700, LINE_Y - 14 - hg, 260, 'f_gear', '{{gearnum}}', align='center', hotWhen='now', conn=1),
        text('rpm_unit', W - 760, 600, 240, 'f_unit', '1/min x1000', color='dim', conn=1),
        text('scale_unit', 520, 600, 140, 'f_unit', '{{u:speedLc}}', color='dim'),
        {'id': 'mstripe', 'type': 'stripe', 'z': 5, 'x': 900, 'y': 34, 'w': 120, 'h': 24},
    ]
    # the far dials' numbers: fuel 1, 1/2, 0 (top to bottom); oil temperature, its mirror, hot at the top
    cx, cy, r = dial
    a0, a1 = dial_ang
    for i, (f, lbl) in enumerate([(1, '1'), (0.5, '1/2'), (0, '0')]):
        a = math.radians(a1 + (a0 - a1) * f)
        x, y = cx + (r - 32) * math.cos(a), cy + (r - 32) * math.sin(a)
        widgets.append(text('fuel%d' % i, x - 20, y - hu / 2, 60, 'f_unit', lbl, align='left'))
        widgets.append(text('oil%d' % i, W - x - 70, y - hu / 2, 90, 'f_unit', '{{temp:%d}}' % (50 + 100 * f), align='right', conn=1))
    widgets.append({'id': 'fuel_icon', 'type': 'icon', 'icon': 'fuel', 'z': 5, 'x': 14, 'y': 612, 'w': 24, 'h': 28, 'color': 'dim'})
    widgets.append({'id': 'oil_icon', 'type': 'icon', 'icon': 'oilcan', 'z': 5, 'x': W - 52, 'y': 614, 'w': 36, 'h': 24, 'color': 'dim', 'conn': 1})
    widgets.append(text('oil_unit', W - 46, 412, 44, 'f_unit', '{{u:temp}}', color='dim', align='left', conn=1))

    layout = {
        'schemaVersion': 2, 'name': 'M view', 'theme': 'mdash', 'mapLive': True,
        '_about': 'After the Live Cockpit M view (an M3 G80 and an M5 F90 in Sport; generated by tools/gen_f90.py: edit '
                  'that and run it again). One f90dash effect layer draws the black backdrop, both scales (the right one '
                  'is the left one mirrored), the lit band up to the value, the needles, the red rev zone, the far dials '
                  'and the lines; the numbers are text widgets. The map window opens while the Waze map shows, without '
                  'a rebuild (mapLive).',
        'widgets': widgets,
    }
    out = os.path.join(APP, 'hud', 'layouts', 'f90.json')
    with open(out, 'w') as f:
        json.dump(layout, f, indent=1)
        f.write('\n')
    print('%s: %d widgets, path %d points, %.0f px long (scale %.0f..%.0f)' % (out, len(widgets), len(PATH), TOTAL, S0, S1))


if __name__ == '__main__':
    main()
