"""'First Snow': a small cabin in the pines at blue hour, the first real snowfall of the year.
One window lit. Smoke going straight up, because there is no wind. Nothing is happening, on purpose.
"""
import math, random

random.seed(1124)
W, H = 1400, 900
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
     '<defs>',
     '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2748"/>'
     '<stop offset=".6" stop-color="#3f5078"/><stop offset="1" stop-color="#7a86a6"/></linearGradient>',
     '<linearGradient id="snow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9d3ea"/><stop offset="1" stop-color="#8f9bbb"/></linearGradient>',
     '<radialGradient id="win" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffd27a" stop-opacity=".55"/><stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></radialGradient>',
     '</defs>',
     f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']

def pine(x, base, h, col, snowy=True):
    w = h * 0.42
    parts = []
    tiers = 5
    for i in range(tiers):
        t0 = i / tiers
        y_top = base - h + h * t0 * 0.85
        y_bot = base - h * 0.08 - (tiers - 1 - i) * h * 0.13
        hw = w * (0.35 + 0.65 * (i + 1) / tiers) / 2
        parts.append(f'<polygon points="{x:.1f},{y_top:.1f} {x - hw:.1f},{y_bot:.1f} {x + hw:.1f},{y_bot:.1f}" fill="{col}"/>')
        if snowy:
            parts.append(f'<polygon points="{x:.1f},{y_top:.1f} {x - hw * .55:.1f},{y_top + (y_bot - y_top) * .55:.1f} '
                         f'{x:.1f},{y_top + (y_bot - y_top) * .42:.1f} {x + hw * .55:.1f},{y_top + (y_bot - y_top) * .55:.1f}" '
                         f'fill="#dfe6f5" opacity=".75"/>')
    parts.append(f'<rect x="{x - 3:.1f}" y="{base - h * .08:.1f}" width="6" height="{h * .08:.1f}" fill="{col}"/>')
    return parts

# far hills and far pines, misty
o.append(f'<path d="M0,560 C200,500 380,540 560,510 S900,470 1100,520 S1320,500 1400,520 L1400,{H} L0,{H} Z" fill="#5d6a8e" opacity=".8"/>')
for _ in range(70):
    x = random.uniform(-20, W + 20); h = random.uniform(40, 80)
    o += pine(x, 560 + random.uniform(-15, 25), h, "#4a5679", snowy=False)
o.append(f'<rect y="500" width="{W}" height="140" fill="#7a86a6" opacity=".25"/>')  # mist
# near ground
o.append(f'<path d="M0,690 C250,650 520,700 760,672 S1150,640 1400,680 L1400,{H} L0,{H} Z" fill="url(#snow)"/>')

# cabin
cx, cy = 820, 690
o.append(f'<rect x="{cx - 110}" y="{cy - 110}" width="220" height="110" fill="#3a2f3a"/>')
o.append(f'<polygon points="{cx - 135},{cy - 105} {cx},{cy - 195} {cx + 135},{cy - 105}" fill="#2b2433"/>')
o.append(f'<polygon points="{cx - 140},{cy - 102} {cx},{cy - 200} {cx + 140},{cy - 102} {cx + 120},{cy - 112} {cx},{cy - 182} {cx - 120},{cy - 112}" fill="#e6ecf8"/>')
o.append(f'<rect x="{cx + 55}" y="{cy - 225}" width="24" height="60" fill="#2b2433"/>')
o.append(f'<rect x="{cx + 52}" y="{cy - 230}" width="30" height="8" fill="#e6ecf8"/>')
# smoke, straight up: no wind tonight
for i in range(9):
    o.append(f'<circle cx="{cx + 67 + math.sin(i * .9) * 5:.1f}" cy="{cy - 245 - i * 26}" r="{8 + i * 2.2:.1f}" fill="#c9d0e3" opacity="{.28 - i * .028:.3f}"/>')
# lit window with glow, dark door
o.append(f'<circle cx="{cx - 45}" cy="{cy - 58}" r="120" fill="url(#win)"/>')
o.append(f'<rect x="{cx - 72}" y="{cy - 80}" width="54" height="44" fill="#ffcf7a"/>')
o.append(f'<line x1="{cx - 45}" y1="{cy - 80}" x2="{cx - 45}" y2="{cy - 36}" stroke="#3a2f3a" stroke-width="4"/>')
o.append(f'<line x1="{cx - 72}" y1="{cy - 58}" x2="{cx - 18}" y2="{cy - 58}" stroke="#3a2f3a" stroke-width="4"/>')
o.append(f'<rect x="{cx - 76}" y="{cy - 36}" width="62" height="6" fill="#e6ecf8"/>')
o.append(f'<rect x="{cx + 25}" y="{cy - 70}" width="40" height="70" fill="#231d29"/>')
# window light falling on the snow
o.append(f'<polygon points="{cx - 72},{cy} {cx - 18},{cy} {cx + 5},{cy + 45} {cx - 100},{cy + 45}" fill="#ffd27a" opacity=".18"/>')
# footprints to the door
for i in range(9):
    fx = cx + 45 - i * 38 + (i % 2) * 8; fy = cy + 8 + i * 14
    o.append(f'<ellipse cx="{fx}" cy="{fy}" rx="6" ry="3" fill="#7f8bab" opacity=".7"/>')

# near pines framing the scene
for x, h in [(120, 330), (210, 260), (300, 300), (1180, 340), (1270, 280), (1345, 360), (560, 220)]:
    o += pine(x, 712 + random.uniform(-6, 10), h, "#1f2a40")

# falling snow, three depths
for depth, n, rmin, rmax, op in [(0, 260, .6, 1.4, .5), (1, 160, 1.4, 2.4, .75), (2, 45, 2.6, 4.2, .9)]:
    for _ in range(n):
        x, y = random.uniform(0, W), random.uniform(0, H)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{random.uniform(rmin, rmax):.2f}" fill="#f4f7ff" opacity="{op * random.uniform(.6, 1):.2f}"/>')

o.append(f'<text x="40" y="{H - 30}" font-family="Georgia, serif" font-size="20" fill="#2b3350" opacity=".85">first snow</text>')
o.append(f'<text x="{W - 40}" y="{H - 30}" text-anchor="end" font-family="Georgia, serif" font-size="14" fill="#3a4466" opacity=".85">'
         f'no wind tonight; the smoke goes straight up</text>')
o.append('</svg>')
open(__file__.replace("make_first_snow.py", "first_snow.svg"), "w").write("\n".join(o))
print("wrote first_snow.svg")
