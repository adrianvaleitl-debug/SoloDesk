from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "solodesk.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)

def make_icon(size):
    k = size / 256
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def box(v):
        return tuple(round(x * k) for x in v)
    def width(v):
        return max(1, round(v * k))
    d.rounded_rectangle(box((8, 8, 248, 248)), radius=width(58), fill="#1A2D43")
    d.rounded_rectangle(box((48, 48, 208, 208)), radius=width(25), fill="#EAF2FF")
    d.rounded_rectangle(box((70, 76, 186, 180)), radius=width(15), fill="#F7FAFF")
    d.line([box((70, 103)), box((186, 103))], fill="#5F8FCB", width=width(11))
    d.rounded_rectangle(box((85, 120, 121, 162)), radius=width(8), fill="#9AB6D8")
    d.rounded_rectangle(box((132, 120, 171, 134)), radius=width(7), fill="#5F8FCB")
    d.rounded_rectangle(box((132, 146, 160, 156)), radius=width(5), fill="#9AB6D8")
    d.ellipse(box((154, 154, 194, 194)), fill="#69D3C8")
    d.line([box((165, 174)), box((171, 180)), box((183, 166))], fill="#1A2D43", width=width(5), joint="curve")
    return im

base = make_icon(256)
base.save(OUT, format="ICO", sizes=[(n, n) for n in (256, 128, 64, 48, 32, 16)])
base.save(OUT.with_suffix(".png"), format="PNG")
print("Created", OUT)
