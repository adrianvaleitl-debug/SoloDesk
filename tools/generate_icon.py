from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"solodesk.ico"
OUT.parent.mkdir(parents=True,exist_ok=True)
def make_icon(size):
    k=size/256
    im=Image.new("RGBA",(size,size),(13,22,36,255));d=ImageDraw.Draw(im)
    def box(v):return tuple(round(x*k) for x in v)
    d.rounded_rectangle(box((12,12,244,244)),radius=round(58*k),fill="#1A2D43")
    d.rounded_rectangle(box((55,61,201,190)),radius=round(23*k),fill="#EAF2FF")
    d.rounded_rectangle(box((78,88,178,103)),radius=round(7*k),fill="#5F8FCB")
    d.rounded_rectangle(box((78,119,153,132)),radius=round(6*k),fill="#9AB6D8")
    d.rounded_rectangle(box((78,148,137,161)),radius=round(6*k),fill="#9AB6D8")
    d.ellipse(box((164,143,198,177)),fill="#69D3C8")
    return im
base=make_icon(256)
base.save(OUT,format="ICO",sizes=[(n,n) for n in (256,128,64,48,32,16)])
base.save(OUT.with_suffix(".png"),format="PNG")
print("Created",OUT)
