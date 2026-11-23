"""'Murmuration': a flock of starlings at dusk over a marsh.

Thousands of small birds, each one placed on a twisting ribbon of flight and turned to follow it,
thick where the ribbon folds toward you and sparse where it stretches away. Nobody leads a murmuration;
each bird only watches its seven nearest neighbours. I like that.
"""
import math, random

random.seed(1123)  # Nov 23
W, H = 1600, 1000
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
       '<defs>',
       '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
       '<stop offset="0" stop-color="#1d2440"/><stop offset=".45" stop-color="#6b4a6e"/>'
       '<stop offset=".72" stop-color="#d9826a"/><stop offset=".86" stop-color="#f3c58a"/>'
       '<stop offset="1" stop-color="#f7dca6"/></linearGradient>',
       '<radialGradient id="sun" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff3d6"/>'
       '<stop offset=".35" stop-color="#ffd99a" stop-opacity=".9"/><stop offset="1" stop-color="#ffb37a" stop-opacity="0"/></radialGradient>',
       '<linearGradient id="water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e7b58a"/>'
       '<stop offset="1" stop-color="#3b3350"/></linearGradient>',
       '</defs>',
       f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
       f'<circle cx="1150" cy="835" r="260" fill="url(#sun)"/>',
       f'<circle cx="1150" cy="835" r="46" fill="#fff1cf" opacity=".95"/>']

# a few early stars
for _ in range(60):
    x, y = random.uniform(0, W), random.uniform(0, 260)
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{random.uniform(.4, 1.3):.2f}" fill="#fff" opacity="{random.uniform(.15, .6):.2f}"/>')

# the flock: points on a ribbon surface (centre curve + rotating width), seen in perspective
def centre(t):
    x = 280 + 1050 * t + 90 * math.sin(6.3 * t)
    y = 430 - 170 * math.sin(math.pi * t) + 70 * math.sin(11 * t + 0.6)
    return x, y

birds = []
for _ in range(9000):
    t = random.betavariate(1.6, 1.6)
    u = random.gauss(0, 0.42)                       # across the ribbon
    x, y = centre(t)
    x2, y2 = centre(t + 0.002)
    dx, dy = x2 - x, y2 - y
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L                         # normal to the flight path
    twist = math.cos(4.1 * t * math.pi + 0.8)        # ribbon turns: wide when face-on, thin when edge-on
    width = 25 + 115 * abs(twist)
    bx = x + nx * u * width + random.gauss(0, 5)
    by = y + ny * u * width * 0.8 + random.gauss(0, 5)
    ang = math.atan2(dy, dx) + random.gauss(0, 0.35)
    near = 0.55 + 0.45 * (1 - abs(twist))            # edge-on parts look denser and darker
    birds.append((bx, by, ang, near))

for bx, by, ang, near in birds:
    s = 1.1 + 1.4 * near * random.random()
    c, si = math.cos(ang), math.sin(ang)
    # a tiny bird: two short wing strokes in a shallow V
    w = s * 1.6
    pts = [(-w, -w * 0.45), (0, 0), (-w, w * 0.45)]
    p = " ".join(f"{bx + px * c - py * si:.1f},{by + px * si + py * c:.1f}" for px, py in pts)
    op = 0.45 + 0.5 * near
    out.append(f'<polyline points="{p}" fill="none" stroke="#1a1424" stroke-width="{0.7 + 0.5 * near:.2f}" '
               f'stroke-linecap="round" opacity="{op:.2f}"/>')

# a few stragglers catching up
for _ in range(40):
    x, y = random.uniform(120, 300), random.uniform(380, 560)
    out.append(f'<path d="M{x:.0f},{y:.0f} l-3,-1.5 M{x:.0f},{y:.0f} l-3,1.5" stroke="#1a1424" stroke-width=".9" opacity=".7"/>')

# marsh: water, then reeds against the light
out.append(f'<rect x="0" y="860" width="{W}" height="{H - 860}" fill="url(#water)"/>')
out.append(f'<rect x="1080" y="862" width="140" height="3" fill="#fff1cf" opacity=".6"/>')
out.append(f'<rect x="1110" y="872" width="80" height="2" fill="#fff1cf" opacity=".35"/>')
reeds = []
for i in range(520):
    x = random.uniform(-20, W + 20)
    h = random.uniform(30, 120) * (1.4 if random.random() < .12 else 1)
    lean = random.gauss(0, 8)
    base = 860 + random.uniform(0, 30)
    reeds.append(f'M{x:.1f},{base:.1f} q{lean / 2:.1f},{-h / 2:.1f} {lean:.1f},{-h:.1f}')
    if random.random() < .18:  # seed heads
        reeds.append(f'M{x + lean:.1f},{base - h:.1f} l{lean * .05:.1f},{-9:.1f}')
out.append(f'<path d="{" ".join(reeds)}" stroke="#20182b" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
out.append(f'<rect x="0" y="{H - 70}" width="{W}" height="70" fill="#1a1424"/>')

out.append(f'<text x="40" y="{H - 28}" font-family="Georgia, serif" font-size="20" fill="#e9d7c4" opacity=".85">murmuration</text>')
out.append(f'<text x="{W - 40}" y="{H - 28}" text-anchor="end" font-family="Georgia, serif" font-size="14" fill="#b9a8a0" opacity=".8">'
           f'no one leads; each bird watches seven neighbours</text>')
out.append('</svg>')
open(__file__.replace("make_murmuration.py", "murmuration.svg"), "w").write("\n".join(out))
print("wrote murmuration.svg")
