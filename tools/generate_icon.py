from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "solodesk.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)

def make_icon(size):
    scale = size / 256
    im = Image.new("RGBA", (size, size), (13, 20, 32, 255))
    d = ImageDraw.Draw(im)
    def box(coords, radius, fill, outline=None, width=1):
        coords = tuple(round(v * scale) for v in coords)
        d.rounded_rectangle(coords, radius=max(1, round(radius * scale)), fill=fill, outline=outline, width=max(1, round(width * scale)))
    # Independent SoloDesk identity: a workspace card and a simple desk mark.
    box((18, 18, 238, 238), 52, "#172A40", "#395779", 5)
    box((48, 47, 208, 207), 28, "#203B58", "#527BA6", 4)
    # document/workspace panel
    box((77, 68, 179, 177), 14, "#DCEBFF")
    d.line((round(99*scale),round(97*scale),round(157*scale),round(97*scale)), fill="#6F9FE0", width=max(2,round(8*scale)))
    d.line((round(99*scale),round(119*scale),round(145*scale),round(119*scale)), fill="#8BAED8", width=max(2,round(7*scale)))
    # desk surface and legs
    d.line((round(91*scale),round(148*scale),round(165*scale),round(148*scale)), fill="#2E648F", width=max(3,round(9*scale)))
    d.line((round(103*scale),round(150*scale),round(103*scale),round(166*scale)), fill="#2E648F", width=max(3,round(8*scale)))
    d.line((round(153*scale),round(150*scale),round(153*scale),round(166*scale)), fill="#2E648F", width=max(3,round(8*scale)))
    # small teal status detail
    d.ellipse((round(167*scale),round(77*scale),round(185*scale),round(95*scale)), fill="#65D2CE")
    return im

sizes = [make_icon(n) for n in (256, 128, 64, 48, 32, 16)]
sizes[0].save(OUT, format="ICO", sizes=[(n, n) for n in (256, 128, 64, 48, 32, 16)])
sizes[0].save(OUT.with_suffix(".png"), format="PNG")
print("Created", OUT)
