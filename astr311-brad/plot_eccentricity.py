"""
plot_eccentricity.py — read measure.py output and produce interactive
Plotly charts.

Outputs:
  eccentricity_comparison.html — all planets' eccentricity on a shared
                                  y-axis + barycentre distance from the Sun
  orbits_{Planet}.html         — animated arc walkthrough with eccentricity
                                  overlay and barycentre panel

All pages share a tab bar for easy navigation.

Usage:
    python measure.py > output.txt
    python plot_eccentricity.py output.txt
"""

import sys
import re
import math
from collections import defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def parse_results(path):
    """
    planet_name -> list of orbit dicts with keys:
        time, ecc, orbit_num, period, r_min, r_max, r_avg
    """
    raw = defaultdict(list)

    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if not line or re.fullmatch(r'[=\- ]+', line):
                continue
            if line.lstrip().startswith('Planet'):
                continue
            if '\u2014' in line:
                continue
            parts = line.split()
            if len(parts) not in (6, 8):
                continue
            try:
                planet       = parts[0]
                orbit_num    = int(parts[1])
                period_yr    = float(parts[2])
                r_min        = float(parts[3])
                r_max        = float(parts[4])
                eccentricity = float(parts[5])
                angle_min    = float(parts[6]) if len(parts) == 8 else None
                angle_max    = float(parts[7]) if len(parts) == 8 else None
            except (ValueError, IndexError):
                continue
            raw[planet].append((orbit_num, period_yr, r_min, r_max, eccentricity,
                                 angle_min, angle_max))

    result = {}
    for planet, rows in raw.items():
        cumulative = 0.0
        points = []
        for orbit_num, period, r_min, r_max, ecc, angle_min, angle_max in rows:
            cumulative += period
            points.append({
                'time':      round(cumulative, 4),
                'ecc':       ecc,
                'orbit_num': orbit_num,
                'period':    period,
                'r_min':     r_min,
                'r_max':     r_max,
                'r_avg':     (r_min + r_max) / 2,
                'angle_min': angle_min,
                'angle_max': angle_max,
            })
        result[planet] = points

    return result


# ---------------------------------------------------------------------------
# shared constants
# ---------------------------------------------------------------------------

PLANET_COLOURS = {
    'Mercury': '#a8a8a8',
    'Venus':   '#e8cda0',
    'Earth':   '#4fa3e0',
    'Mars':    '#c1440e',
    'Jupiter': '#c88b3a',
    'Saturn':  '#e4d191',
    'Uranus':  '#7de8e8',
    'Neptune': '#5b7fde',
}

PLANET_ORDER = ['Mercury', 'Venus', 'Earth', 'Mars',
                'Jupiter', 'Saturn', 'Uranus', 'Neptune']

DARK_LAYOUT = dict(
    plot_bgcolor='#0e1117',
    paper_bgcolor='#0e1117',
    font=dict(color='#cccccc'),
    legend=dict(
        bgcolor='rgba(0,0,0,0.4)',
        bordercolor='rgba(255,255,255,0.15)',
        borderwidth=1,
        font=dict(color='#cccccc'),
    ),
)

AXIS_STYLE = dict(
    showgrid=True,
    gridcolor='rgba(255,255,255,0.08)',
    zeroline=False,
    color='#cccccc',
)

RANGE_BUTTONS = [
    dict(count=50,  label='50 yr',  step='year', stepmode='backward'),
    dict(count=100, label='100 yr', step='year', stepmode='backward'),
    dict(count=200, label='200 yr', step='year', stepmode='backward'),
    dict(step='all', label='All'),
]


def hex_to_rgba(hex_colour, alpha=0.15):
    h = hex_colour.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


# ---------------------------------------------------------------------------
# nav bar
# ---------------------------------------------------------------------------

def _nav_html(nav_pages, current_filename):
    """Return CSS + HTML for a sticky top nav bar."""
    items = []
    for label, href in nav_pages:
        cls = ' class="active"' if href == current_filename else ''
        items.append(f'<a href="{href}"{cls}>{label}</a>')
    return (
        '<style>'
        'body{margin:0}'
        '#topnav{position:sticky;top:0;z-index:9999;background:#0a0d13;'
        'padding:7px 14px;border-bottom:1px solid #2a2d35;'
        'display:flex;flex-wrap:wrap;gap:6px;font-family:system-ui,sans-serif;}'
        '#topnav a{color:#999;text-decoration:none;padding:4px 11px;'
        'border-radius:4px;font-size:12px;border:1px solid #2a2d35;white-space:nowrap;}'
        '#topnav a:hover{background:#1a1d24;color:#fff;border-color:#555;}'
        '#topnav a.active{background:#1e2230;color:#e0e0e0;border-color:#555;font-weight:600;}'
        '</style>'
        '<nav id="topnav">' + ''.join(items) + '</nav>'
    )


def _write_with_nav(fig, filename, nav_pages, include_plotlyjs='cdn'):
    """Write fig to filename with the nav bar injected after <body>."""
    html = fig.to_html(include_plotlyjs=include_plotlyjs, full_html=True)
    nav  = _nav_html(nav_pages, filename)
    html = html.replace('<body>', '<body>' + nav, 1)
    with open(filename, 'w') as f:
        f.write(html)


# ---------------------------------------------------------------------------
# chart 1: comparison page — all planets + barycentre distance
# ---------------------------------------------------------------------------

def make_comparison_figure(data, planets):
    """
    4-row × 2-col grid of planet eccentricities (shared y-axis range) with a
    full-width barycentre distance panel below.
    """
    # Global y ceiling — same for every planet panel so they're directly comparable
    all_eccs = [p['ecc'] for planet in planets
                         if planet in data
                         for p in data[planet]]
    y_max = max(all_eccs) * 1.10 if all_eccs else 0.1

    t_max = max(
        data[planet][-1]['time']
        for planet in planets if data.get(planet)
    )

    # Barycentre distance — uniform 800-point sample across the full run
    N_BARY = 800
    bary_times = [t_max * i / (N_BARY - 1) for i in range(N_BARY)]
    bary_dists = [
        math.sqrt(sum(v**2 for v in _estimate_barycentre(t, data)))
        for t in bary_times
    ]

    # 5 rows: 4 × (planet pair) + 1 full-width barycentre
    specs = [
        [{}, {}],
        [{}, {}],
        [{}, {}],
        [{}, {}],
        [{'colspan': 2}, None],
    ]
    subplot_titles = list(planets) + ['Barycentre Distance from Sun (AU)']

    fig = make_subplots(
        rows=5, cols=2,
        specs=specs,
        subplot_titles=subplot_titles,
        vertical_spacing=0.055,
        horizontal_spacing=0.08,
    )

    for idx, planet in enumerate(planets):
        row = idx // 2 + 1
        col = idx % 2 + 1
        colour = PLANET_COLOURS.get(planet, '#888')
        pts    = data.get(planet, [])

        if not pts:
            continue

        times      = [p['time']      for p in pts]
        eccs       = [p['ecc']       for p in pts]
        orbit_nums = [p['orbit_num'] for p in pts]
        periods    = [p['period']    for p in pts]

        hover = [
            f'<b>{planet} orbit {o}</b><br>'
            f't = {t:.2f} yr<br>'
            f'e = {e:.5f}<br>'
            f'period = {pd:.4f} yr'
            for o, t, e, pd in zip(orbit_nums, times, eccs, periods)
        ]

        fig.add_trace(go.Scatter(
            x=times, y=eccs,
            mode='lines',
            line=dict(color=colour, width=1.4),
            fill='tozeroy',
            fillcolor=hex_to_rgba(colour, 0.12),
            showlegend=False,
            name=planet,
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover,
        ), row=row, col=col)

        fig.update_yaxes(
            range=[0, y_max], tickformat='.4f', title='e',
            showgrid=True, gridcolor='rgba(255,255,255,0.07)',
            color='#cccccc', zeroline=False,
            row=row, col=col,
        )
        fig.update_xaxes(
            title='Time (yr)' if row == 4 else '',
            showgrid=True, gridcolor='rgba(255,255,255,0.07)',
            color='#cccccc', zeroline=False,
            row=row, col=col,
        )

    # Barycentre panel (row 5, full width)
    fig.add_trace(go.Scatter(
        x=bary_times, y=bary_dists,
        mode='lines',
        line=dict(color='rgba(200,180,255,0.85)', width=1.4),
        fill='tozeroy',
        fillcolor='rgba(150,130,255,0.10)',
        showlegend=False,
        name='Barycentre distance',
        hovertemplate='t = %{x:.2f} yr<br>dist = %{y:.6f} AU<extra></extra>',
    ), row=5, col=1)

    fig.update_xaxes(
        title='Time (yr)',
        showgrid=True, gridcolor='rgba(255,255,255,0.07)',
        color='#cccccc', zeroline=False,
        rangeslider=dict(visible=True, bgcolor='#1a1d24', thickness=0.03),
        rangeselector=dict(
            buttons=RANGE_BUTTONS,
            bgcolor='#1a1d24', activecolor='#444',
            font=dict(color='#cccccc', size=11),
        ),
        row=5, col=1,
    )
    fig.update_yaxes(
        title='Distance (AU)', tickformat='.5f',
        showgrid=True, gridcolor='rgba(255,255,255,0.07)',
        color='#cccccc', zeroline=False,
        row=5, col=1,
    )

    fig.update_layout(
        title=dict(
            text='Solar System — Orbital Eccentricity Comparison',
            font=dict(size=18, color='#cccccc'),
            x=0.5,
        ),
        hovermode='x',
        height=1100,
        margin=dict(l=70, r=30, t=80, b=60),
        **DARK_LAYOUT,
    )

    return fig


# ---------------------------------------------------------------------------
# chart 2: orbital arc walkthrough
# ---------------------------------------------------------------------------

# Solar-system masses in M☉ (IAU nominal values)
_PLANET_MASSES = {
    'Mercury': 1.652e-7,
    'Venus':   2.447e-6,
    'Earth':   3.003e-6,
    'Mars':    3.213e-7,
    'Jupiter': 9.543e-4,
    'Saturn':  2.857e-4,
    'Uranus':  4.365e-5,
    'Neptune': 5.150e-5,
}
_SUN_MASS   = 1.0
_TOTAL_MASS = _SUN_MASS + sum(_PLANET_MASSES.values())
_R_SUN_AU   = 0.00465   # solar radius in AU


def _estimate_barycentre(t, all_data):
    """
    Estimate the barycentre position (AU) relative to the Sun at the origin,
    using planet angles and r_avg at time t.  Returns (bx, by).
    """
    bx = by = 0.0
    for planet, pts in all_data.items():
        m = _PLANET_MASSES.get(planet, 0.0)
        if m == 0.0 or not pts:
            continue
        angle = _angle_at_time(pts, t) % (2 * math.pi)
        _, orb = _orbit_at_time(pts, t)
        r = orb['r_avg']
        bx += m * r * math.cos(angle)
        by += m * r * math.sin(angle)
    return bx / _TOTAL_MASS, by / _TOTAL_MASS

def _angle_at_time(points, t):
    """
    Cumulative angle (radians) for a planet at simulation time t.
    Each completed orbit = 2π. Linearly interpolated within the current orbit.
    """
    prev = 0.0
    for i, p in enumerate(points):
        if t <= p['time']:
            frac = (t - prev) / p['period'] if p['period'] > 0 else 0.0
            return (i + frac) * 2 * math.pi
        prev = p['time']
    # Extrapolate past last recorded orbit
    last = points[-1]
    extra = (t - last['time']) / last['period'] if last['period'] > 0 else 0.0
    return (len(points) + extra) * 2 * math.pi


def _orbit_at_time(points, t):
    """Return the orbit record (dict) and orbit index active at time t."""
    prev = 0.0
    for i, p in enumerate(points):
        if t <= p['time']:
            return i, p
        prev = p['time']
    return len(points) - 1, points[-1]


def _arc_xy(r_avg, angle_start, angle_span, n=120):
    """x, y coordinates for an arc (or full circle if |span| >= 2π)."""
    if abs(angle_span) >= 2 * math.pi:
        angles = [2 * math.pi * i / n for i in range(n + 1)]
    else:
        steps  = max(n, int(abs(angle_span) / (2 * math.pi) * n) + 2)
        angles = [angle_start + angle_span * i / (steps - 1) for i in range(steps)]
    return ([r_avg * math.cos(a) for a in angles],
            [r_avg * math.sin(a) for a in angles])


def _build_static_orbit_traces(all_data, planets):
    """
    Faint full-circle reference rings, one per planet.
    Static background — never updated in animation frames.
    """
    traces = []
    for planet in planets:
        colour = PLANET_COLOURS.get(planet, '#888')
        pts    = all_data[planet]
        r_avg  = sum(p['r_avg'] for p in pts) / len(pts)

        x, y = _arc_xy(r_avg, 0, 2 * math.pi)

        traces.append(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color=hex_to_rgba(colour, 0.15), width=0.8, dash='dot'),
            hoverinfo='skip', showlegend=False, name=f'{planet} orbit ref',
        ))

    return traces


def _build_arc_traces(focal_planet, focal_point, all_data, planets):
    """
    Return one Scatter trace per planet showing the arc it traced during the
    given orbit of the focal planet.
    """
    t_end    = focal_point['time']
    t_start  = t_end - focal_point['period']
    p_focal  = focal_point['period']

    traces = []
    for planet in planets:
        colour = PLANET_COLOURS.get(planet, '#888')
        pts    = all_data[planet]

        angle_start = _angle_at_time(pts, t_start)
        _, orb      = _orbit_at_time(pts, t_start)
        r_avg       = orb['r_avg']
        p_planet    = orb['period']

        angle_span  = 2 * math.pi * p_focal / p_planet
        full_orbits = int(angle_span / (2 * math.pi))
        partial_deg = math.degrees(angle_span % (2 * math.pi))
        is_focal    = (planet == focal_planet)

        if full_orbits >= 1:
            arc_label = f'{full_orbits} full orbit{"s" if full_orbits > 1 else ""} + {partial_deg:.1f}°'
        else:
            arc_label = f'{math.degrees(angle_span):.1f}°'

        x, y = _arc_xy(r_avg, angle_start, angle_span)

        traces.append(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color=colour, width=3 if is_focal else 1.8),
            name=planet,
            hovertemplate=(
                f'<b>{planet}</b><br>'
                f'Arc: {arc_label}<br>'
                f'r ≈ {r_avg:.3f} AU'
                '<extra></extra>'
            ),
            showlegend=True,
        ))

    return traces


def _periapsis_apoapsis_traces(focal_planet, focal_point, angle_start):
    """
    Two marker traces for the focal planet's perihelion and aphelion,
    placed at the actual angles where r_min and r_max were recorded.
    Falls back to angle_start / angle_start+π if angles weren't recorded.
    """
    r_min  = focal_point['r_min']
    r_max  = focal_point['r_max']
    colour = PLANET_COLOURS.get(focal_planet, '#fff')

    a_min = focal_point['angle_min'] if focal_point.get('angle_min') is not None else angle_start
    a_max = focal_point['angle_max'] if focal_point.get('angle_max') is not None else angle_start + math.pi

    peri_x = r_min * math.cos(a_min)
    peri_y = r_min * math.sin(a_min)
    apo_x  = r_max * math.cos(a_max)
    apo_y  = r_max * math.sin(a_max)

    peri = go.Scatter(
        x=[peri_x], y=[peri_y],
        mode='markers+text',
        marker=dict(size=9, color='#ff5252', symbol='circle',
                    line=dict(color='white', width=1.5)),
        text=['Perihelion'], textposition='top center',
        textfont=dict(size=9, color='#ff9090'),
        showlegend=False,
        hovertemplate=(
            f'<b>Perihelion</b><br>'
            f'r = {r_min:.5f} AU<br>'
            f'e = {focal_point["ecc"]:.5f}'
            '<extra></extra>'
        ),
        name='_peri',
    )
    apo = go.Scatter(
        x=[apo_x], y=[apo_y],
        mode='markers+text',
        marker=dict(size=9, color='#4fa3e0', symbol='circle',
                    line=dict(color='white', width=1.5)),
        text=['Aphelion'], textposition='top center',
        textfont=dict(size=9, color='#90c8f0'),
        showlegend=False,
        hovertemplate=(
            f'<b>Aphelion</b><br>'
            f'r = {r_max:.5f} AU<br>'
            f'e = {focal_point["ecc"]:.5f}'
            '<extra></extra>'
        ),
        name='_apo',
    )
    return peri, apo


def make_position_figure(focal_planet, all_data):
    focal_pts = all_data.get(focal_planet, [])
    if not focal_pts:
        return None

    planets  = [p for p in PLANET_ORDER if p in all_data and all_data[p]]
    colour   = PLANET_COLOURS.get(focal_planet, '#fff')

    # Sample orbits — cap at MAX_FRAMES to keep file size reasonable
    sampled    = focal_pts

    # ── eccentricity series ───────────────────────────────────────────────
    ecc_times = [p['time'] for p in focal_pts]
    eccs      = [p['ecc']  for p in focal_pts]
    e_min, e_max = min(eccs), max(eccs)
    e_pad = (e_max - e_min) * 0.12 or 0.001

    # ── precompute barycentre positions for all sampled frames ────────────
    bary_xy = [_estimate_barycentre(fp['time'], all_data) for fp in sampled]
    bary_xs = [b[0] for b in bary_xy]
    bary_ys = [b[1] for b in bary_xy]
    bary_r_max = max(math.sqrt(x**2 + y**2) for x, y in bary_xy) or 0.001
    view_b = max(bary_r_max * 1.6, _R_SUN_AU * 2.5)   # barycentre panel range

    # ── 2×2 subplot layout ───────────────────────────────────────────────
    # Col 1 spans both rows: solar system arc view
    # Row 1, Col 2: eccentricity graph
    # Row 2, Col 2: barycentre close-up
    fig = make_subplots(
        rows=2, cols=2,
        specs=[
            [{'rowspan': 2}, {}],
            [None,           {}],
        ],
        column_widths=[0.58, 0.42],
        row_heights=[0.58, 0.42],
        subplot_titles=[
            'Orbital Positions (AU)',
            f'{focal_planet} — Eccentricity',
            '',                                 # placeholder for rowspan gap
            'Barycentre (relative to Sun)',
        ],
        horizontal_spacing=0.06,
        vertical_spacing=0.12,
    )

    # ── static: solar system panel (col 1, rows 1-2) ─────────────────────
    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode='markers',
        marker=dict(size=14, color='#FFD700'),
        hovertemplate='<b>Sun</b><extra></extra>',
        showlegend=False, name='Sun',
    ), row=1, col=1)

    for planet in planets:
        pc     = PLANET_COLOURS.get(planet, '#888')
        pts    = all_data[planet]
        r_mean = sum(p['r_avg'] for p in pts) / len(pts)
        rx, ry = _arc_xy(r_mean, 0, 2 * math.pi)
        fig.add_trace(go.Scatter(
            x=rx, y=ry, mode='lines',
            line=dict(color=hex_to_rgba(pc, 0.22), width=0.6, dash='dot'),
            hoverinfo='skip', showlegend=False, name=f'{planet} ring',
        ), row=1, col=1)
        lx = r_mean * math.cos(math.pi / 4)
        ly = r_mean * math.sin(math.pi / 4)
        fig.add_trace(go.Scatter(
            x=[lx], y=[ly], mode='text', text=[planet],
            textfont=dict(size=9, color=hex_to_rgba(pc, 0.7)),
            hoverinfo='skip', showlegend=False, name=f'{planet} label',
        ), row=1, col=1)

    # ── static: eccentricity line (row 1, col 2) ─────────────────────────
    fig.add_trace(go.Scatter(
        x=ecc_times, y=eccs,
        mode='lines',
        line=dict(color=hex_to_rgba(colour, 0.55), width=1.2),
        fill='tozeroy', fillcolor=hex_to_rgba(colour, 0.08),
        showlegend=False, name='Eccentricity',
        hovertemplate='t = %{x:.2f} yr<br>e = %{y:.5f}<extra></extra>',
    ), row=1, col=2)

    # ── static: barycentre panel (row 2, col 2) ──────────────────────────
    # Sun circle
    sx, sy = _arc_xy(_R_SUN_AU, 0, 2 * math.pi, n=80)
    fig.add_trace(go.Scatter(
        x=sx, y=sy, mode='lines',
        line=dict(color='rgba(255,215,0,0.5)', width=1.2),
        fill='toself', fillcolor='rgba(255,215,0,0.08)',
        hoverinfo='skip', showlegend=False, name='Sun (bary panel)',
    ), row=2, col=2)

    # Circle at max barycentre excursion radius (reference)
    cx, cy = _arc_xy(bary_r_max, 0, 2 * math.pi, n=80)
    fig.add_trace(go.Scatter(
        x=cx, y=cy, mode='lines',
        line=dict(color='rgba(200,200,200,0.18)', width=0.8, dash='dot'),
        hoverinfo='skip', showlegend=False, name='Bary excursion ring',
    ), row=2, col=2)

    # Full barycentre trajectory (all sampled frames, static)
    fig.add_trace(go.Scatter(
        x=bary_xs, y=bary_ys, mode='lines',
        line=dict(color='rgba(200,200,200,0.20)', width=0.8),
        hoverinfo='skip', showlegend=False, name='Bary trajectory',
    ), row=2, col=2)

    # ── count static traces ───────────────────────────────────────────────
    n_planets = len(planets)
    # 1 sun (sys) + P rings + P labels + 1 ecc + 1 sun circle + 1 ref ring + 1 bary traj
    n_static = 5 + 2 * n_planets

    # ── initial dynamic traces ────────────────────────────────────────────
    initial_arcs = _build_arc_traces(focal_planet, sampled[0], all_data, planets)
    for arc in initial_arcs:
        fig.add_trace(arc, row=1, col=1)

    fp0   = sampled[0]
    t0    = fp0['time']
    bx0, by0 = bary_xy[0]
    peri0, apo0 = _periapsis_apoapsis_traces(focal_planet, fp0, None)
    fig.add_trace(peri0, row=1, col=1)
    fig.add_trace(apo0,  row=1, col=1)

    fig.add_trace(go.Scatter(          # vertical time marker on ecc graph
        x=[t0, t0], y=[e_min - e_pad, e_max + e_pad],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.65)', width=1.5, dash='dash'),
        showlegend=False, hoverinfo='skip', name='_vline',
    ), row=1, col=2)

    fig.add_trace(go.Scatter(          # dot on ecc curve
        x=[t0], y=[fp0['ecc']],
        mode='markers',
        marker=dict(size=8, color='white', symbol='circle',
                    line=dict(color=colour, width=2)),
        showlegend=False,
        hovertemplate=f't = {t0:.2f} yr<br>e = {fp0["ecc"]:.5f}<extra></extra>',
        name='_dot',
    ), row=1, col=2)

    fig.add_trace(go.Scatter(          # moving barycentre dot
        x=[bx0], y=[by0],
        mode='markers',
        marker=dict(size=10, color='white', symbol='cross',
                    line=dict(color='rgba(150,150,255,0.9)', width=2)),
        showlegend=False,
        hovertemplate=f'Barycentre<br>x = {bx0:.5f} AU<br>y = {by0:.5f} AU<extra></extra>',
        name='_bary',
    ), row=2, col=2)

    # n_dynamic = P (arcs) + 2 (peri, apo) + 3 (vline, dot, bary dot)
    dynamic_indices = list(range(n_static, n_static + n_planets + 5))

    # ── frames ───────────────────────────────────────────────────────────
    frames = []
    for i, fp in enumerate(sampled):
        t_s = fp['time'] - fp['period']
        t_e = fp['time']
        bx, by = bary_xy[i]

        arc_traces = _build_arc_traces(focal_planet, fp, all_data, planets)
        peri, apo  = _periapsis_apoapsis_traces(focal_planet, fp, None)

        vline = go.Scatter(
            x=[t_e, t_e], y=[e_min - e_pad, e_max + e_pad],
            mode='lines',
            line=dict(color='rgba(255,255,255,0.65)', width=1.5, dash='dash'),
            showlegend=False, hoverinfo='skip',
        )
        dot = go.Scatter(
            x=[t_e], y=[fp['ecc']],
            mode='markers',
            marker=dict(size=8, color='white', symbol='circle',
                        line=dict(color=colour, width=2)),
            showlegend=False,
            hovertemplate=f't = {t_e:.2f} yr<br>e = {fp["ecc"]:.5f}<extra></extra>',
        )
        bary_dot = go.Scatter(
            x=[bx], y=[by],
            mode='markers',
            marker=dict(size=10, color='white', symbol='cross',
                        line=dict(color='rgba(150,150,255,0.9)', width=2)),
            showlegend=False,
            hovertemplate=f'Barycentre<br>x = {bx:.5f} AU<br>y = {by:.5f} AU<extra></extra>',
        )

        frames.append(go.Frame(
            data=arc_traces + [peri, apo, vline, dot, bary_dot],
            traces=dynamic_indices,
            name=str(fp['orbit_num']),
            layout=go.Layout(title_text=(
                f'<b>{focal_planet}</b> — Orbit {fp["orbit_num"]}  '
                f'({t_s:.2f} → {t_e:.2f} yr,  '
                f'period = {fp["period"]:.4f} yr,  '
                f'e = {fp["ecc"]:.5f})'
            )),
        ))

    # ── slider ───────────────────────────────────────────────────────────
    slider_steps = [
        dict(
            args=[[str(fp['orbit_num'])],
                  {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}],
            label=f'{fp["time"]:.1f}',
            method='animate',
        )
        for fp in sampled
    ]

    # ── layout ───────────────────────────────────────────────────────────
    r0     = focal_pts[0]['r_avg']
    view_r = max(r0 * 3.0, 1.5)
    t0_s   = fp0['time'] - fp0['period']

    fig.update_layout(
        title=dict(
            text=(
                f'<b>{focal_planet}</b> — Orbit {fp0["orbit_num"]}  '
                f'({t0_s:.2f} → {fp0["time"]:.2f} yr,  '
                f'period = {fp0["period"]:.4f} yr,  '
                f'e = {fp0["ecc"]:.5f})'
            ),
            font=dict(size=13, color=colour),
            x=0.5,
        ),
        plot_bgcolor='#080c12',
        paper_bgcolor='#0e1117',
        font=dict(color='#cccccc'),
        height=700,
        margin=dict(l=20, r=20, t=70, b=110),
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.15)',
            borderwidth=1,
            font=dict(color='#cccccc', size=10),
            x=1.01, y=1, xanchor='left',
        ),
        updatemenus=[dict(
            type='buttons', showactive=False,
            x=0.5, y=-0.13, xanchor='center',
            buttons=[
                dict(label='▶ Play', method='animate',
                     args=[None, {'frame': {'duration': 120, 'redraw': True},
                                  'fromcurrent': True, 'transition': {'duration': 0}}]),
                dict(label='⏸ Pause', method='animate',
                     args=[[None], {'frame': {'duration': 0, 'redraw': False},
                                    'mode': 'immediate'}]),
            ],
        )],
        sliders=[dict(
            active=0, steps=slider_steps,
            currentvalue=dict(
                prefix='Time (yr): ',
                font=dict(size=11, color='#cccccc'),
                visible=True, xanchor='center',
            ),
            pad=dict(t=50),
            bgcolor='#1a1d24', bordercolor='#444',
            font=dict(color='#cccccc', size=9),
        )],
    )

    # Solar system axes — equal aspect, no ticks
    fig.update_xaxes(
        range=[-view_r, view_r], scaleanchor='y', scaleratio=1,
        showgrid=False, zeroline=False, showticklabels=False,
        row=1, col=1,
    )
    fig.update_yaxes(
        range=[-view_r, view_r],
        showgrid=False, zeroline=False, showticklabels=False,
        row=1, col=1,
    )

    # Eccentricity axes
    fig.update_xaxes(
        title='Time (yr)',
        showgrid=True, gridcolor='rgba(255,255,255,0.07)',
        color='#cccccc', zeroline=False,
        row=1, col=2,
    )
    fig.update_yaxes(
        title='Eccentricity', tickformat='.5f',
        showgrid=True, gridcolor='rgba(255,255,255,0.07)',
        color='#cccccc', zeroline=False,
        range=[e_min - e_pad, e_max + e_pad],
        row=1, col=2,
    )

    # Barycentre panel axes — equal aspect, AU scale
    fig.update_xaxes(
        range=[-view_b, view_b], scaleanchor='y3', scaleratio=1,
        showgrid=True, gridcolor='rgba(255,255,255,0.06)',
        zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
        color='#cccccc', tickformat='.4f', title='AU',
        row=2, col=2,
    )
    fig.update_yaxes(
        range=[-view_b, view_b],
        showgrid=True, gridcolor='rgba(255,255,255,0.06)',
        zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
        color='#cccccc', tickformat='.4f', title='AU',
        row=2, col=2,
    )

    fig.frames = frames
    return fig


# ---------------------------------------------------------------------------
# orchestrate
# ---------------------------------------------------------------------------

def plot_all(data):
    planets = [p for p in PLANET_ORDER if p in data]
    for p in data:
        if p not in planets:
            planets.append(p)

    planets_with_data = [p for p in planets if data.get(p)]

    # Build nav page list upfront so every page gets the same bar
    nav_pages = [('Eccentricity Comparison', 'eccentricity_comparison.html')]
    for planet in planets_with_data:
        nav_pages.append((planet, f'orbits_{planet}.html'))

    saved = []

    # Comparison page
    fig_cmp = make_comparison_figure(data, planets)
    _write_with_nav(fig_cmp, 'eccentricity_comparison.html', nav_pages)
    print(f"  Comparison       →  eccentricity_comparison.html")
    saved.append('eccentricity_comparison.html')

    # Orbit walkthrough pages
    for planet in planets:
        if not data.get(planet):
            print(f"  {planet:8s}: no completed orbits — skipping")
            continue
        fig_orb = make_position_figure(planet, data)
        if fig_orb is not None:
            out = f'orbits_{planet}.html'
            _write_with_nav(fig_orb, out, nav_pages)
            print(f"  {planet:8s}: {len(data[planet]):>4} orbits  →  {out}")
            saved.append(out)

    print(f"\nSaved {len(saved)} chart(s).")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python plot_eccentricity.py <output_file.txt>")
        sys.exit(1)

    path = sys.argv[1]
    data = parse_results(path)

    if not data:
        print(f"No orbital data found in '{path}'.")
        sys.exit(1)

    total  = sum(len(v) for v in data.values())
    t_max  = max(pts[-1]['time'] for pts in data.values() if pts)
    print(f"Loaded {total} orbit records across {len(data)} planets "
          f"(up to {t_max:.1f} yr)\n")

    plot_all(data)
