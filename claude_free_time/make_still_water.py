"""'Still Water': a lake at night, a moon, its reflection broken into a few soft lines, and a rowboat tied up
for the night. The last picture of a long weekend.
"""
import random

random.seed(1124)
W, H = 1400, 900
hz = 470  # horizon
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
     '<defs>',
     '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070b1c"/><stop offset="1" stop-color="#1c2a4d"/></linearGradient>',
     '<linearGradient id="lake" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16223f"/><stop offset="1" stop-color="#05080f"/></linearGradient>',
     '<radialGradient id="halo" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#f5efd8" stop-opacity=".35"/><stop offset="1" stop-color="#f5efd8" stop-opacity="0"/></radialGradient>',
     '</defs>',
     f'<rect width="{W}" height="{hz}" fill="url(#sky)"/>',
     f'<rect y="{hz}" width="{W}" height="{H - hz}" fill="url(#lake)"/>']
stars = []
for _ in range(220):
    x, y = random.uniform(0, W), random.uniform(0, hz - 40)
    r = random.uniform(.4, 1.6); op = random.uniform(.25, .95)
    stars.append((x, y, r, op))
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#fff" opacity="{op:.2f}"/>')
mx, my = 980, 180
o.append(f'<circle cx="{mx}" cy="{my}" r="160" fill="url(#halo)"/>')
o.append(f'<circle cx="{mx}" cy="{my}" r="44" fill="#f5efd8"/>')
# far shore: low dark hills with a treeline
o.append(f'<path d="M0,{hz} L0,{hz-40} C180,{hz-70} 330,{hz-30} 520,{hz-55} S880,{hz-20} 1060,{hz-48} S1300,{hz-35} 1400,{hz-60} L1400,{hz} Z" fill="#0b1124"/>')
for _ in range(160):
    x = random.uniform(0, W); h = random.uniform(10, 26)
    o.append(f'<polygon points="{x:.0f},{hz - 38 - h:.0f} {x - h * .3:.0f},{hz - 30:.0f} {x + h * .3:.0f},{hz - 30:.0f}" fill="#0b1124"/>')
# star reflections, faint
for x, y, r, op in stars[:90]:
    o.append(f'<circle cx="{x:.1f}" cy="{2 * hz - y:.1f}" r="{r * .8:.2f}" fill="#fff" opacity="{op * .25:.2f}"/>')
# moon reflection: a column of short soft lines that widen toward us
for i in range(23):
    y = hz + 14 + i * 15 + random.uniform(-3, 3)
    w = 30 + i * 7 * random.uniform(.6, 1.2)
    off = random.gauss(0, 6)
    o.append(f'<rect x="{mx - w / 2 + off:.0f}" y="{y:.0f}" width="{w:.0f}" height="{2.2 + i * .08:.1f}" rx="2" fill="#f5efd8" opacity="{.65 - i * .02:.2f}"/>')
# a rowboat tied to a small dock, lower left
o.append('<rect x="80" y="690" width="320" height="14" fill="#0a0d16"/>')
for x in (95, 175, 255, 335, 385):
    o.append(f'<rect x="{x}" y="700" width="9" height="70" fill="#0a0d16"/>')
o.append('<path d="M300,742 Q330,778 420,778 L520,778 Q560,770 575,742 Z" fill="#0d111c"/>')
o.append('<path d="M300,742 L575,742" stroke="#2b3656" stroke-width="2"/>')
o.append('<path d="M330,742 Q300,725 340,708" fill="none" stroke="#3a4566" stroke-width="1.5"/>')  # rope to the dock
o.append('<line x1="440" y1="744" x2="470" y2="760" stroke="#2b3656" stroke-width="3"/>')  # resting oar
o.append('<path d="M300,782 Q430,792 575,782" stroke="#f5efd8" stroke-width="1" opacity=".12" fill="none"/>')
o.append(f'<text x="40" y="{H - 30}" font-family="Georgia, serif" font-size="20" fill="#c9cfe0" opacity=".8">still water</text>')
o.append(f'<text x="{W - 40}" y="{H - 30}" text-anchor="end" font-family="Georgia, serif" font-size="14" fill="#8a93ad" opacity=".8">'
         f'goodnight. the boat is tied up; nothing needs to be rowed until morning</text>')
o.append('</svg>')
open(__file__.replace("make_still_water.py", "still_water.svg"), "w").write("\n".join(o))
print("wrote still_water.svg")
