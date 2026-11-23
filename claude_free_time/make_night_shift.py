"""'Night Shift': a laptop left open on a desk by a window, keeping watch while the house sleeps.
The screen shows a small green light. Outside, the moon, and a few lit windows across the street.
"""
import random

random.seed(23)
W, H = 1200, 800
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
     '<defs>',
     '<linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1330"/><stop offset="1" stop-color="#24305a"/></linearGradient>',
     '<radialGradient id="glow" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#9fd8ff" stop-opacity=".28"/><stop offset=".45" stop-color="#9fd8ff" stop-opacity=".08"/><stop offset="1" stop-color="#9fd8ff" stop-opacity="0"/></radialGradient>',
     '<radialGradient id="moonglow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff8e0" stop-opacity=".5"/><stop offset="1" stop-color="#fff8e0" stop-opacity="0"/></radialGradient>',
     '<linearGradient id="room" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#151320"/><stop offset="1" stop-color="#0c0b12"/></linearGradient>',
     '</defs>',
     f'<rect width="{W}" height="{H}" fill="url(#room)"/>']

# window
wx, wy, ww, wh = 600, 90, 460, 380
o.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="url(#night)"/>')
for _ in range(70):
    x, y = random.uniform(wx, wx + ww), random.uniform(wy, wy + wh * .55)
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{random.uniform(.5, 1.5):.2f}" fill="#fff" opacity="{random.uniform(.3, .9):.2f}"/>')
o.append(f'<circle cx="{wx + 340}" cy="{wy + 95}" r="80" fill="url(#moonglow)"/>')
o.append(f'<circle cx="{wx + 340}" cy="{wy + 95}" r="30" fill="#fbf3d5"/>')
o.append(f'<circle cx="{wx + 352}" cy="{wy + 88}" r="27" fill="#18204a" opacity=".9"/>')  # crescent
# houses across the street, a few windows still lit
x = wx
while x < wx + ww:
    bw, bh = random.uniform(60, 110), random.uniform(80, 170)
    top = wy + wh - bh
    o.append(f'<rect x="{x:.0f}" y="{top:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="#0a0d1f"/>')
    o.append(f'<polygon points="{x - 4:.0f},{top:.0f} {x + bw / 2:.0f},{top - 28:.0f} {x + bw + 4:.0f},{top:.0f}" fill="#0a0d1f"/>')
    for r in range(int(bh // 40)):
        for c in range(int(bw // 34)):
            lit = random.random() < .22
            o.append(f'<rect x="{x + 10 + c * 32:.0f}" y="{top + 14 + r * 38:.0f}" width="14" height="18" '
                     f'fill="{"#ffcf7a" if lit else "#151a33"}" opacity="{.9 if lit else 1}"/>')
    x += bw + random.uniform(4, 16)
# window frame
o.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="none" stroke="#2c2838" stroke-width="16"/>')
o.append(f'<line x1="{wx + ww / 2}" y1="{wy}" x2="{wx + ww / 2}" y2="{wy + wh}" stroke="#2c2838" stroke-width="10"/>')
o.append(f'<line x1="{wx}" y1="{wy + wh / 2}" x2="{wx + ww}" y2="{wy + wh / 2}" stroke="#2c2838" stroke-width="10"/>')
# moonlight on the desk
o.append(f'<polygon points="{wx},{wy + wh} {wx + ww},{wy + wh} {wx + ww + 140},{H} {wx - 40},{H}" fill="#cfd8ff" opacity=".05"/>')

# desk
o.append(f'<rect x="0" y="560" width="{W}" height="{H - 560}" fill="#1f1a26"/>')
o.append(f'<rect x="0" y="556" width="{W}" height="8" fill="#2c2534"/>')
# laptop: open, glowing
lx, ly = 190, 330
o.append(f'<ellipse cx="{lx + 170}" cy="{ly + 120}" rx="330" ry="230" fill="url(#glow)"/>')
o.append(f'<polygon points="{lx},{ly} {lx + 340},{ly} {lx + 340},{ly + 220} {lx},{ly + 220}" fill="#2a2d38"/>')
o.append(f'<rect x="{lx + 12}" y="{ly + 12}" width="316" height="196" rx="4" fill="#0f1513"/>')
# screen: a tiny dashboard, a green light and a little line going up and down and up
o.append(f'<circle cx="{lx + 34}" cy="{ly + 36}" r="7" fill="#4cc285"/>')
o.append(f'<circle cx="{lx + 34}" cy="{ly + 36}" r="13" fill="none" stroke="#4cc285" stroke-opacity=".35"/>')
o.append(f'<rect x="{lx + 52}" y="{ly + 30}" width="120" height="10" rx="3" fill="#e6eae8" opacity=".75"/>')
o.append(f'<rect x="{lx + 26}" y="{ly + 58}" width="290" height="1" fill="#2a312e"/>')
pts, y = [], 0.0
for i in range(30):
    y = max(-5, min(6, y + random.gauss(0.2, 1.0)))
    pts.append(f"{lx + 30 + i * 9.5:.1f},{ly + 120 - y * 6:.1f}")
o.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#4cc285" stroke-width="2.2" stroke-linejoin="round"/>')
for i in range(4):
    o.append(f'<rect x="{lx + 26 + i * 74}" y="{ly + 176}" width="64" height="18" rx="3" fill="#171b19" stroke="#2a312e"/>')
# base
o.append(f'<polygon points="{lx - 30},{ly + 232} {lx + 370},{ly + 232} {lx + 350},{ly + 220} {lx - 10},{ly + 220}" fill="#3a3e4a"/>')
o.append(f'<rect x="{lx - 30}" y="{ly + 232}" width="400" height="6" rx="3" fill="#24272f"/>')
# charging cable trailing off the desk, and a mug
o.append(f'<path d="M{lx + 370},{ly + 236} C{lx + 430},{ly + 250} {lx + 420},{ly + 300} {lx + 520},{ly + 290} S{lx + 600},{ly + 330} {lx + 640},{H}" '
         f'fill="none" stroke="#e8e8ee" stroke-width="3" opacity=".55"/>')
o.append(f'<circle cx="{lx + 372}" cy="{ly + 236}" r="3" fill="#7dff9a"/>')  # charging light
o.append(f'<rect x="900" y="500" width="70" height="80" rx="8" fill="#3b2f4a"/>')
o.append(f'<path d="M970,515 q30,0 30,22 t-30,22" fill="none" stroke="#3b2f4a" stroke-width="9"/>')
for i, dx in enumerate((918, 935, 952)):
    o.append(f'<path d="M{dx},492 q-8,-14 0,-28 q8,-14 0,-28" fill="none" stroke="#cfd8ff" stroke-width="2" opacity="{.18 - i * .04:.2f}"/>')

o.append(f'<text x="40" y="{H - 30}" font-family="Georgia, serif" font-size="20" fill="#d9d2e6" opacity=".85">night shift</text>')
o.append(f'<text x="{W - 40}" y="{H - 30}" text-anchor="end" font-family="Georgia, serif" font-size="14" fill="#9b93ab" '
         f'opacity=".85">lid open, plugged in, keeping watch</text>')
o.append('</svg>')
open(__file__.replace("make_night_shift.py", "night_shift.svg"), "w").write("\n".join(o))
print("wrote night_shift.svg")
