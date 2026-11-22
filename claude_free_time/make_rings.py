"""'Six Rings of Quarter Hours': a week of oil rounds drawn as a clock.

Each ring is one trading day (Sunday evening at the centre, Friday at the edge).
Each of its 96 marks is one 15-minute round. The mark's length follows an imagined
price wandering through the day; warm marks are rounds that rose, cool ones fell.
It is made up, not data: just the shape of the thing we watched all weekend.
"""
import math, random

random.seed(622)  # Nov 22
W = H = 1000
cx, cy = W / 2, H / 2
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
       '<defs><radialGradient id="bg" cx="50%" cy="50%" r="60%">'
       '<stop offset="0" stop-color="#1b1f2a"/><stop offset="1" stop-color="#0b0d12"/></radialGradient></defs>',
       f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']

# faint stars
for _ in range(140):
    x, y, r = random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 1.3)
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#cfd6e6" opacity="{random.uniform(.08,.35):.2f}"/>')

warm = ["#f6c177", "#f0a35e", "#eb8a52"]
cool = ["#7fb8d6", "#6c9be0", "#8f86d9"]
for day in range(6):
    r0 = 120 + day * 62
    price, vel = 0.0, 0.0
    for k in range(96):
        vel = 0.82 * vel + random.gauss(0, 0.5)
        step = vel
        price += step
        a = -math.pi / 2 + 2 * math.pi * k / 96
        length = 8 + min(30, abs(step) * 9)
        inner = r0 - length / 2 + price * 0.6
        outer = inner + length
        x1, y1 = cx + inner * math.cos(a), cy + inner * math.sin(a)
        x2, y2 = cx + outer * math.cos(a), cy + outer * math.sin(a)
        col = random.choice(warm if step >= 0 else cool)
        op = 0.55 + 0.45 * min(1, abs(step) / 1.5)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" '
                   f'stroke-width="3.2" stroke-linecap="round" opacity="{op:.2f}"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r0}" fill="none" stroke="#ffffff" stroke-opacity="0.05"/>')

# the 6 pm marker: a single small green light at the top, where the week begins
out.append(f'<circle cx="{cx}" cy="{cy - 92}" r="6" fill="#4cc285"/>')
out.append(f'<circle cx="{cx}" cy="{cy - 92}" r="14" fill="none" stroke="#4cc285" stroke-opacity=".35"/>')
out.append(f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" font-family="Georgia, serif" font-size="22" '
           f'fill="#e6eae8" opacity=".85">quarter hours</text>')
out.append(f'<text x="{cx}" y="{cy + 32}" text-anchor="middle" font-family="Georgia, serif" font-size="13" '
           f'fill="#98a29d" opacity=".8">six days · 576 rounds · held to the end</text>')
out.append('</svg>')
open(__file__.replace("make_rings.py", "six_rings.svg"), "w").write("\n".join(out))
print("wrote six_rings.svg")
