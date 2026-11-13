import csv,os,shutil,sqlite3,sys,webbrowser,json,threading,urllib.request,subprocess,tempfile,ctypes,traceback,ssl,certifi
from pathlib import Path
from datetime import date, timedelta, datetime
import calendar
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageTk

GLASS_KEY = "#010101"

def apply_windows_glass_backdrop(window, transparency=8, light=False):
    """Expose a Windows acrylic backdrop through transparent Tk root pixels."""
    if sys.platform != "win32":
        return False
    key = GLASS_KEY
    try:
        # Tk's colour-key transparency lets DWM draw acrylic behind the client
        # area without fading child text, icons or controls.
        window.wm_attributes("-transparentcolor", key)
        window.configure(fg_color=key)
    except Exception:
        # Keep the app usable if colour-key transparency is unavailable.
        try:
            window.configure(fg_color=palette_color("#EDEDED") if light else palette_color("#101012"))
        except Exception:
            pass
    try:
        window.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = ctypes.c_void_p(window.winfo_id())
        try:
            user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            user32.GetAncestor.restype = ctypes.c_void_p
            hwnd = ctypes.c_void_p(user32.GetAncestor(hwnd, 2) or hwnd.value)
        except Exception:
            pass

        # Windows 11 system backdrop (transient acrylic).
        backdrop_ok = False
        try:
            backdrop = ctypes.c_int(3)
            dwm_set = ctypes.windll.dwmapi.DwmSetWindowAttribute
            dwm_set.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
            dwm_set.restype = ctypes.c_long
            result = dwm_set(hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
            backdrop_ok = (result == 0)
        except Exception:
            pass

        # Acrylic fallback also supplies a user-adjustable tint on Windows 10.
        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                        ("GradientColor", ctypes.c_int), ("AnimationId", ctypes.c_int)]
        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                        ("SizeOfData", ctypes.c_size_t)]
        amount = max(0, min(35, int(transparency)))
        alpha = 0xE8 - round((0xE8 - 0x70) * amount / 35)
        colour = 0x00F0F0F0 if light else 0x0017171B
        policy = ACCENT_POLICY(4, 2, (alpha << 24) | colour, 0)
        data = WINDOWCOMPOSITIONATTRIBDATA(19, ctypes.addressof(policy), ctypes.sizeof(policy))
        apply_attribute = user32.SetWindowCompositionAttribute
        apply_attribute.argtypes = [ctypes.c_void_p, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
        apply_attribute.restype = ctypes.c_bool
        accent_ok = bool(apply_attribute(hwnd, ctypes.byref(data)))
        try:
            user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                            ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            user32.SetWindowPos.restype = ctypes.c_bool
            user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                                0x0001 | 0x0002 | 0x0004 | 0x0020)
        except Exception:
            pass
        return backdrop_ok or accent_ok
    except Exception:
        return False



def install_accent_spotlight(window, accent, background="#101012"):
    """Render a soft multi-layer nebula glow behind the app's glass surfaces."""
    try:
        if not isinstance(accent, str) or len(accent) != 7 or not accent.startswith("#"):
            return
        window.update_idletasks()
        width = max(900, int(window.winfo_width()))
        height = max(620, int(window.winfo_height()))
        rgb = tuple(int(accent[index:index + 2], 16) for index in (1, 3, 5))
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow)
        blobs = [(0.76,0.10,0.48,0.48,68),(0.92,0.42,0.34,0.38,46),
                 (0.18,0.88,0.42,0.38,32),(0.46,0.52,0.34,0.30,22)]
        for cx,cy,rx,ry,alpha in blobs:
            draw.ellipse((int((cx-rx)*width),int((cy-ry)*height),
                          int((cx+rx)*width),int((cy+ry)*height)),fill=(*rgb,alpha))
        glow=glow.filter(ImageFilter.GaussianBlur(max(90,int(min(width,height)*0.19))))
        photo=ImageTk.PhotoImage(glow)
        previous=getattr(window,"_accent_spotlight_canvas",None)
        if previous is not None and previous.winfo_exists():previous.destroy()
        canvas=tk.Canvas(window,width=width,height=height,highlightthickness=0,borderwidth=0,bg=background)
        canvas.place(x=0,y=0,relwidth=1,relheight=1)
        canvas.create_image(0,0,anchor="nw",image=photo)
        canvas.lower()
        window._accent_spotlight_canvas=canvas
        window._accent_spotlight_photo=photo
        window._active_spotlight_colour=accent
        # Keep the pre-rendered accent haze stable during interactive resizing.
        # Recreating and blurring a full-window bitmap on every Configure event
        # made dragging the window edge unnecessarily expensive.
    except Exception:
        pass

APP_VERSION="V3.4"
ROOT=Path(os.environ.get("LOCALAPPDATA",Path.home()))/("SoloDesk" if sys.platform=="win32" else ".solodesk")
ROOT.mkdir(parents=True,exist_ok=True);DB=ROOT/"solodesk.db"
SYMBOLS={"GBP":"£","USD":"$","EUR":"€","CAD":"C$","AUD":"A$","INR":"₹","JPY":"¥","CHF":"Fr"}
FONTS=["Segoe UI","Arial","Verdana","Trebuchet MS","Georgia"]
THEMES={"Classy":("#DCE5F0","#AAB9CC"),"Royal":("#FFC34D","#DFA52F")}
LEGACY_THEMES={"Black":"Classy","Amber":"Royal","Azure":"Classy","Lavender":"Classy","Rose":"Classy","Teal":"Classy","Dollar":"Classy","Euro":"Classy","Pound":"Classy","Yen":"Classy","Franc":"Classy","Ocean":"Classy","Sage":"Classy","Violet":"Classy","Coral":"Classy"}
ACTIVE_THEME="Classy"
def palette_color(value):
 royal={"#101012":"#24160E","#19191D":"#362316","#202024":"#432C1B","#29292E":"#52351F","#38383E":"#75512D","#404040":"#75512D","#36363D":"#694523","#1B1B20":"#2C1C11","#F2F2F2":"#F1D9A8","#A9A9A9":"#C5A978","#AFAFAF":"#C5A978","#EDEDED":"#24160E","#FBFBFB":"#432C1B","#F9F9F9":"#2C1C11","#E9E9E9":"#52351F","#E4E4E4":"#694523","#DBDBDB":"#75512D","#7E7E7E":"#C5A978","#333333":"#F1D9A8","#1E1E1E":"#24160E","#282828":"#52351F","#1F1F1F":"#432C1B","#7F7F7F":"#A98753","#D6D6D6":"#75512D","#CBCBCB":"#694523","#585858":"#75512D","#343434":"#52351F","#B9B9B9":"#F1D9A8","#A0A0A0":"#D7B979"}
 classy={"#101012":"#000412","#19191D":"#0B1020","#202024":"#111B2B","#29292E":"#18243A","#38383E":"#29364A","#404040":"#29364A","#36363D":"#24334A","#1B1B20":"#0B1424","#F2F2F2":"#EBEEF2","#A9A9A9":"#AAB4C2","#AFAFAF":"#AAB4C2","#EDEDED":"#000412","#FBFBFB":"#111B2B","#F9F9F9":"#0B1424","#E9E9E9":"#18243A","#E4E4E4":"#24334A","#DBDBDB":"#29364A","#7E7E7E":"#AAB4C2","#333333":"#EBEEF2","#1E1E1E":"#000412","#282828":"#18243A","#1F1F1F":"#111B2B","#7F7F7F":"#AAB4C2","#D6D6D6":"#29364A","#CBCBCB":"#24334A","#585858":"#29364A","#343434":"#18243A","#B9B9B9":"#DCE5F0","#A0A0A0":"#AAB9CC"}
 palette = royal if ACTIVE_THEME=="Royal" else classy
 if value in palette:return palette[value]
 if value in ("#202020","#1A1A1A","#1F1F1F","#363636"):return "#24160E" if ACTIVE_THEME=="Royal" else "#000412"
 if len(value)==7 and value.startswith("#"):
  try:
   rgb=tuple(int(value[i:i+2],16) for i in (1,3,5))
   if max(rgb)-min(rgb)<=2:
    level=sum(rgb)//3
    if level<=35:return "#24160E" if ACTIVE_THEME=="Royal" else "#000412"
    if level<=65:return "#75512D" if ACTIVE_THEME=="Royal" else "#29364A"
    if level<=125:return "#C5A978" if ACTIVE_THEME=="Royal" else "#AAB4C2"
    if level<=185:return "#75512D" if ACTIVE_THEME=="Royal" else "#29364A"
    if level<=225:return "#52351F" if ACTIVE_THEME=="Royal" else "#18243A"
    return "#F1D9A8" if ACTIVE_THEME=="Royal" else "#EBEEF2"
  except ValueError:pass
 return value
YOUTUBE="https://www.youtube.com/@Adrianvaleitl";TIKTOK="https://www.tiktok.com/@adrianvaleitl";KOFI="https://ko-fi.com/marketinsight";PERSONAL_SITE="https://adrianvaleitl-debug.github.io/"
REPO="https://github.com/adrianvaleitl-debug/SoloDesk";RELEASES=REPO+"/releases/latest"
GITHUB_SSL_CONTEXT=ssl.create_default_context(cafile=certifi.where())
_SINGLE_INSTANCE_MUTEX=None

def acquire_single_instance():
 global _SINGLE_INSTANCE_MUTEX
 if sys.platform!="win32":return True
 try:
  kernel32=ctypes.windll.kernel32
  kernel32.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
  kernel32.CreateMutexW.restype=ctypes.c_void_p
  handle=kernel32.CreateMutexW(None,False,"Local\\AdrianVale.SoloDesk.Singleton")
  if not handle:return True
  if kernel32.GetLastError()==183:
   kernel32.CloseHandle(handle)
   ctypes.windll.user32.MessageBoxW(None,"SoloDesk is already running.\n\nCheck your taskbar for the open window.","SoloDesk",0x40)
   return False
  _SINGLE_INSTANCE_MUTEX=handle
  return True
 except Exception:return True

class SoloDesk(ctk.CTk):
 def __init__(self):
  if sys.platform=="win32":
   try:ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AdrianVale.SoloDesk")
   except Exception:pass
  self.db=sqlite3.connect(DB);self.db.row_factory=sqlite3.Row
  self.db.executescript("""CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT);
  CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT,company TEXT,email TEXT,phone TEXT,notes TEXT);
  CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY,number TEXT UNIQUE,customer_id INTEGER,description TEXT,amount REAL,issued TEXT,due TEXT,status TEXT);
  CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,category TEXT,description TEXT,amount REAL,date TEXT,supplier TEXT);
  CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT,due TEXT,priority TEXT,done INTEGER DEFAULT 0,recurrence TEXT DEFAULT 'None');
  CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,title TEXT,category TEXT,path TEXT,added TEXT);
  CREATE TABLE IF NOT EXISTS customer_activity(id INTEGER PRIMARY KEY,customer_id INTEGER,activity TEXT,created TEXT);""")
  task_columns={row["name"] for row in self.db.execute("PRAGMA table_info(tasks)")}
  if "recurrence" not in task_columns:self.db.execute("ALTER TABLE tasks ADD COLUMN recurrence TEXT DEFAULT 'None'")
  self.db.execute("CREATE INDEX IF NOT EXISTS idx_customer_activity_customer ON customer_activity(customer_id, id DESC)")
  defaults={"business":"My Business","currency":"GBP","appearance":"Dark","colour_theme":"Classy","font_family":"Segoe UI","bold_text":"1","tutorial_completed":"0","startup":"0","auto_updates":"1","transparency":"8"}
  for k,v in defaults.items():self.db.execute("INSERT OR IGNORE INTO settings VALUES(?,?)",(k,v))
  self.db.commit();self.cfg={r["k"]:r["v"] for r in self.db.execute("SELECT * FROM settings")}
  self.font_family=self.cfg["font_family"];self.bold=self.cfg["bold_text"]=="1"
  self.theme=LEGACY_THEMES.get(self.cfg["colour_theme"],self.cfg["colour_theme"])
  if self.theme not in THEMES:self.theme="Classy"
  global ACTIVE_THEME
  ACTIVE_THEME=self.theme
  self.set("colour_theme",self.theme)
  self.set("appearance","Dark")
  ctk.set_default_color_theme("blue")
  theme=ctk.ThemeManager.theme
  for widget,radius in (("CTkFrame",22),("CTkButton",15),("CTkEntry",15),("CTkComboBox",15),("CTkOptionMenu",15)):
   if widget in theme:theme[widget]["corner_radius"]=radius
  control_colors={"fg_color":[self.accent(),self.accent()],"hover_color":[self.accent2(),self.accent2()],"text_color":[palette_color("#202020"),palette_color("#202020")]}
  if "CTkButton" in theme:theme["CTkButton"].update({**control_colors,"corner_radius":13})
  if "CTkCheckBox" in theme:theme["CTkCheckBox"].update({"fg_color":[self.accent(),self.accent()],"hover_color":[self.accent2(),self.accent2()],"border_color":[palette_color("#7F7F7F"),palette_color("#7F7F7F")],"checkmark_color":[palette_color("#202020"),palette_color("#202020")]})
  if "CTkSwitch" in theme:theme["CTkSwitch"].update({"progress_color":[self.accent(),self.accent()]})
  if "CTkSlider" in theme:theme["CTkSlider"].update({"progress_color":[self.accent(),self.accent()],"button_color":[self.accent(),self.accent()],"button_hover_color":[self.accent2(),self.accent2()]})
  if "CTkComboBox" in theme:
   theme["CTkComboBox"].update({"fg_color":[palette_color("#1A1A1A"),palette_color("#1A1A1A")],"border_color":[palette_color("#404040"),palette_color("#404040")],"button_color":[self.accent(),self.accent()],"button_hover_color":[self.accent2(),self.accent2()],"text_color":[palette_color("#F2F2F2"),palette_color("#F2F2F2")],"dropdown_fg_color":[palette_color("#1F1F1F"),palette_color("#1F1F1F")],"dropdown_hover_color":[palette_color("#363636"),palette_color("#363636")],"dropdown_text_color":[palette_color("#F2F2F2"),palette_color("#F2F2F2")]})
  if "CTkOptionMenu" in theme:
   theme["CTkOptionMenu"].update({"fg_color":[palette_color("#282828"),palette_color("#282828")],"button_color":[self.accent(),self.accent()],"button_hover_color":[self.accent2(),self.accent2()],"text_color":[palette_color("#F2F2F2"),palette_color("#F2F2F2")],"dropdown_fg_color":[palette_color("#1F1F1F"),palette_color("#1F1F1F")],"dropdown_hover_color":[palette_color("#363636"),palette_color("#363636")],"dropdown_text_color":[palette_color("#F2F2F2"),palette_color("#F2F2F2")]})
  ctk.set_appearance_mode("Dark")
  super().__init__();self.title("SoloDesk "+APP_VERSION);screen_w=self.winfo_screenwidth();screen_h=self.winfo_screenheight();self.geometry(f"{min(1480,max(900,screen_w-80))}x{min(920,max(640,screen_h-100))}");self.minsize(min(1150,max(900,screen_w-80)),min(740,max(620,screen_h-100)))
  self.set_app_icon()
  self.apply_glass_effect()

  if sys.platform=="win32":self.after(120,lambda:self.state("zoomed"))
  self.protocol("WM_DELETE_WINDOW",self.close);self.pages={};self.nav={};self.tables={}
  self.calendar_month=date.today().replace(day=1)
  self.build_shell();self.show("Overview");self.refresh()
  self.after(350,self.apply_glass_effect)
  self.after(650,self.show_legal_notice)

 def apply_glass_effect(self):
  try:
   if not sys.platform.startswith("win"):return
   apply_windows_glass_backdrop(self,int(self.get("transparency","8")),ctk.get_appearance_mode()=="Light")
  except Exception:pass

 def set_app_icon(self):
  try:
   base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))
   icon=base/"solodesk.ico"
   if not icon.exists():icon=base/"assets"/"solodesk.ico"
   if icon.exists():self.iconbitmap(default=str(icon))
   logo=base/"solodesk.png"
   if not logo.exists():logo=base/"assets"/"solodesk.png"
   self.brand_image=ctk.CTkImage(light_image=Image.open(logo),dark_image=Image.open(logo),size=(32,32)) if logo.exists() else None
   if logo.exists():
    self._taskbar_icon_photo=tk.PhotoImage(file=str(logo))
    self.iconphoto(True,self._taskbar_icon_photo)
  except Exception:self.brand_image=None
 def get(self,k,d=""):return self.cfg.get(k,d)
 def set(self,k,v):
  self.cfg[k]=str(v);self.db.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",(k,str(v)));self.db.commit()
 def accent(self):return THEMES.get(self.theme,THEMES["Classy"])[0]
 def accent2(self):return THEMES.get(self.theme,THEMES["Classy"])[1]
 def col(self,k):
  dark=ctk.get_appearance_mode()=="Dark"
  bases={"bg":palette_color(palette_color("#101012")),"side":palette_color(palette_color("#19191D")),
   "panel":palette_color(palette_color("#202024")),"panel2":palette_color(palette_color("#29292E")),
   "line":palette_color(palette_color("#38383E")),"text":palette_color(palette_color("#F2F2F2")),
   "muted":palette_color(palette_color("#A9A9A9")),"input":palette_color(palette_color("#1B1B20")),
   "hover":palette_color(palette_color("#36363D")),"accent":self.accent(),"danger":palette_color("#9B9B9B")}
  return bases[k]
 def font(self,n=12):return ctk.CTkFont(family=self.font_family,size=n,weight="bold" if self.bold else "normal")
 def panel(self,p):return ctk.CTkFrame(p,fg_color=self.col("panel"),corner_radius=22,border_width=1,border_color=self.col("line"))
 def label(self,p,t,size=12,color="text",**kw):return ctk.CTkLabel(p,text=t,font=self.font(size),text_color=self.col(color),**kw)
 def button(self,p,t,fn,primary=False,width=None):
  return ctk.CTkButton(p,text=t,command=fn,width=width or 120,height=37,corner_radius=11,
   fg_color=self.accent() if primary else self.col("panel2"),hover_color=self.accent2(),
   text_color=palette_color("#1E1E1E") if primary else self.col("text"),font=self.font(11))
 def build_shell(self):
  self.configure(fg_color=GLASS_KEY if sys.platform=="win32" else self.col("bg"))
  install_accent_spotlight(self,self.accent(),GLASS_KEY if sys.platform=="win32" else (palette_color("#EDEDED") if ctk.get_appearance_mode()=="Light" else palette_color("#101012")))
  self.work=ctk.CTkFrame(self,fg_color="transparent",corner_radius=18);self.work.pack(fill="both",expand=True)
  self.work.grid_columnconfigure(1,weight=1);self.work.grid_rowconfigure(1,weight=1)
  self.sidebar=ctk.CTkFrame(self.work,width=224,fg_color=self.col("side"),corner_radius=26,border_width=1,border_color=self.col("line"))
  self.sidebar.grid(row=0,column=0,rowspan=2,sticky="nsew",padx=(14,8),pady=14);self.sidebar.grid_propagate(False)
  brand=ctk.CTkFrame(self.sidebar,fg_color="transparent");brand.pack(fill="x",padx=20,pady=(24,26))
  if self.brand_image:ctk.CTkLabel(brand,text="",image=self.brand_image).pack(side="left",padx=(0,9))
  else:self.label(brand,"▦",27,"accent").pack(side="left",padx=(0,9))
  brand_text=ctk.CTkFrame(brand,fg_color="transparent");brand_text.pack(side="left")
  self.label(brand_text,"SoloDesk",20).pack(anchor="w")
  self.label(brand_text,"BUSINESS WORKSPACE",8,"muted").pack(anchor="w",pady=(1,0))
  nav_area=ctk.CTkScrollableFrame(self.sidebar,fg_color="transparent",corner_radius=18)
  nav_area.pack(fill="both",expand=True,padx=12,pady=(0,8))
  groups=[
   ("WORKSPACE",[("Overview","⌂"),("Customers","♙"),("Customer Activity","◷")]),
   ("MONEY",[("Invoices","▤"),("Expenses","↗"),("Analytics","▥")]),
   ("ORGANISE",[("Tasks","✓"),("Task Calendar","▦"),("Documents","▧")]),
   ("PREFERENCES",[("What's New","✦"),("Settings","⚙")])]
  self.nav={}
  for group,items in groups:
   self.label(nav_area,group,9,"muted").pack(anchor="w",padx=12,pady=(15,7))
   for name,ico in items:
    x=self.button(nav_area,ico+"   "+name,lambda n=name:self.show(n),width=190)
    x.configure(anchor="w",height=42,corner_radius=12,fg_color="transparent",text_color=self.col("muted"),hover_color=self.col("hover"),font=self.font(11))
    x.pack(fill="x",padx=2,pady=2);self.nav[name]=x
  foot=self.panel(self.sidebar);foot.pack(fill="x",padx=14,pady=14)
  self.label(foot,"LOCAL-FIRST",8,"accent").pack(anchor="w",padx=12,pady=(10,3))
  self.label(foot,"Your business records stay on this computer.",9,"muted",wraplength=180,justify="left").pack(anchor="w",padx=12,pady=(0,8))
  self.button(foot,"My website ↗",lambda:webbrowser.open(PERSONAL_SITE),width=180).pack(fill="x",padx=10,pady=3)
  self.button(foot,"Optional support · Ko-fi ↗",lambda:webbrowser.open(KOFI),True,180).pack(fill="x",padx=10,pady=(2,10))
  self.top=ctk.CTkFrame(self.work,height=68,fg_color=self.col("panel"),corner_radius=24,border_width=1,border_color=self.col("line"))
  self.top.grid(row=0,column=1,sticky="ew",padx=(8,14),pady=(14,8));self.top.grid_propagate(False)
  self.titlelabel=self.label(self.top,"Overview",16);self.titlelabel.pack(side="left",padx=25)
  self.search_open=False
  self.global_search_entry=ctk.CTkEntry(self.top,placeholder_text="Search records…",width=190,height=32,corner_radius=10,font=self.font(10),fg_color=self.col("input"),border_width=0,text_color=self.col("text"))
  self.global_search_entry.bind("<Return>",lambda _event:self.global_search())
  self.global_search_entry.bind("<Escape>",lambda _event:self.toggle_global_search(False))
  self.search_button=ctk.CTkButton(self.top,text="⌕",command=self.toggle_global_search,width=32,height=30,corner_radius=9,fg_color=self.col("panel2"),hover_color=self.col("hover"),text_color=self.col("text"),font=self.font(17),border_width=0)
  self.search_button.pack(side="right",padx=(4,12),pady=8)
  self.biz=self.label(self.top,self.get("business"),10,"accent",fg_color=self.col("panel2"),corner_radius=12,padx=13,pady=8)
  self.biz.pack(side="right",padx=12)
  self.top.bind("<Configure>",lambda _event:self.global_search_entry.configure(width=145 if self.top.winfo_width()<1050 else 165 if self.top.winfo_width()<1250 else 190),add="+")
  self.body=ctk.CTkFrame(self.work,fg_color="transparent")
  self.body.grid(row=1,column=1,sticky="nsew",padx=(16,14),pady=(10,14))
  for n in ["Overview","Customers","Invoices","Expenses","Tasks","Task Calendar","Customer Activity","Documents","Analytics","What's New","Settings"]:
   self.pages[n]=ctk.CTkFrame(self.body,fg_color="transparent")
 def show(self,n):
  for p in self.pages.values():p.pack_forget()
  self.pages[n].pack(fill="both",expand=True);self.titlelabel.configure(text=n)
  for k,b in self.nav.items():b.configure(fg_color=self.col("panel2") if k==n else "transparent",text_color=self.accent() if k==n else self.col("muted"))
  if n=="Overview":self.overview()
  elif n in self.tables or n in ("Customers","Invoices","Expenses","Tasks","Documents"):self.table_page(n)
  elif n=="Task Calendar":self.task_calendar()
  elif n=="Customer Activity":self.customer_activity_page()
  elif n=="Analytics":self.analytics()
  elif n=="What's New":self.whats_new()
  else:self.settings_page()
 def heading(self,p,t,sub):
  self.label(p,t,24).pack(anchor="w",pady=(3,2));self.label(p,sub,11,"muted").pack(anchor="w",pady=(0,15))
 def metric(self,p,title,value,sub):
  f=self.panel(p);f.pack(side="left",fill="both",expand=True,padx=5)
  self.label(f,title.upper(),9,"muted").pack(anchor="w",padx=16,pady=(15,4));self.label(f,value,23).pack(anchor="w",padx=16)
  self.label(f,sub,10,"accent").pack(anchor="w",padx=16,pady=(3,14))
 def money(self,x):return f"{SYMBOLS.get(self.get('currency','GBP'),'£')}{float(x or 0):,.2f}"
 def tree_style(self):
  s=ttk.Style(self)
  try:s.theme_use("clam")
  except:pass
  s.configure("Treeview",rowheight=39,font=(self.font_family,10,"bold" if self.bold else "normal"),background=self.col("panel"),fieldbackground=self.col("panel"),foreground=self.col("text"),borderwidth=0)
  s.configure("Treeview.Heading",font=(self.font_family,9,"bold" if self.bold else "normal"),background=self.col("panel2"),foreground=self.col("muted"),padding=(11,12),relief="flat")
  s.map("Treeview",background=[("selected",self.col("hover"))],foreground=[("selected",self.col("text"))])
 def overview(self):
  p=self.pages["Overview"]
  for w in p.winfo_children():w.destroy()
  self.heading(p,"Business overview","A clear view of what is happening across your business.")
  row=ctk.CTkFrame(p,fg_color="transparent");row.pack(fill="x",pady=10)
  overdue_tasks=self.db.execute("SELECT COUNT(*) FROM tasks WHERE done=0 AND due<>'' AND due<?",(date.today().isoformat(),)).fetchone()[0]
  overdue_invoices=self.db.execute("SELECT COUNT(*) FROM invoices WHERE status<>'Paid' AND due<>'' AND due<?",(date.today().isoformat(),)).fetchone()[0]
  if overdue_tasks or overdue_invoices:
   alert=self.panel(p);alert.pack(fill="x",pady=(3,8))
   self.label(alert,f"Overdue reminders  ·  {overdue_tasks} tasks  ·  {overdue_invoices} unpaid invoices",12,"danger").pack(anchor="w",padx=16,pady=12)
  paid=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Paid'").fetchone()[0]
  due=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status IN ('Draft','Sent')").fetchone()[0]
  spent=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
  count=self.db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
  self.metric(row,"Paid income",self.money(paid),"Invoices marked paid");self.metric(row,"Outstanding",self.money(due),"Draft and sent invoices")
  self.metric(row,"Expenses",self.money(spent),"Recorded spending");self.metric(row,"Customers",str(count),"People and businesses")
  lower=ctk.CTkFrame(p,fg_color="transparent");lower.pack(fill="both",expand=True,pady=10)
  left=self.panel(lower);left.pack(side="left",fill="both",expand=True,padx=(0,8))
  right=self.panel(lower);right.pack(side="left",fill="y",padx=(8,0))
  self.label(left,"Recent invoices",16).pack(anchor="w",padx=16,pady=14)
  self.recent=ttk.Treeview(left,columns=("number","customer","amount","due","status"),show="headings",height=8);self.tree_style()
  for c in ("number","customer","amount","due","status"):self.recent.heading(c,text=c.title());self.recent.column(c,width=120)
  self.recent.pack(fill="both",expand=True,padx=10,pady=(0,12));self.refresh_recent()
  self.label(right,"Quick actions",16).pack(anchor="w",padx=16,pady=(14,10))
  for t,fn in [("＋ New invoice",self.add_invoice),("＋ Add customer",self.add_customer),("＋ Add expense",self.add_expense),("＋ Add task",self.add_task)]:
   self.button(right,t,fn).pack(fill="x",padx=12,pady=5)
  self.label(right,"LOCAL-FIRST STORAGE",9,"muted").pack(anchor="w",padx=16,pady=(20,3))
  self.label(right,"Your records stay on this computer.",10,"muted").pack(anchor="w",padx=16,pady=(0,16))
 def data(self,n):
  if n=="Customers":return self.db.execute("SELECT id,name,company,email,phone FROM customers ORDER BY name").fetchall()
  if n=="Invoices":return self.db.execute("SELECT i.*,COALESCE(c.name,'—') customer FROM invoices i LEFT JOIN customers c ON c.id=i.customer_id ORDER BY i.id DESC").fetchall()
  if n=="Expenses":return self.db.execute("SELECT * FROM expenses ORDER BY date DESC,id DESC").fetchall()
  if n=="Tasks":return self.db.execute("SELECT * FROM tasks ORDER BY done,due,id DESC").fetchall()
  return self.db.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
 def values(self,n,r):
  if n=="Customers":return (r["id"],r["name"],r["company"],r["email"],r["phone"])
  if n=="Invoices":return (r["id"],r["number"],r["customer"],r["description"],self.money(r["amount"]),r["issued"],r["due"],r["status"])
  if n=="Expenses":return (r["id"],r["date"],r["category"],r["description"],r["supplier"],self.money(r["amount"]))
  if n=="Tasks":return (r["id"],r["title"],r["due"],r["priority"],r["recurrence"] or "None","Complete" if r["done"] else "Open")
  return (r["id"],r["title"],r["category"],r["path"],r["added"])
 def table_page(self,n):
  p=self.pages[n]
  for w in p.winfo_children():w.destroy()
  self.heading(p,n,{"Customers":"Customer directory and contact records.","Invoices":"Create, edit and track invoice payments.","Expenses":"Record business spending and suppliers.","Tasks":"Prioritise the next things to do.","Documents":"Keep business files linked in one place."}[n])
  if n=="Tasks":
   overdue_tasks=self.db.execute("SELECT COUNT(*) FROM tasks WHERE done=0 AND due<>'' AND due<?",(date.today().isoformat(),)).fetchone()[0]
   overdue_invoices=self.db.execute("SELECT COUNT(*) FROM invoices WHERE status<>'Paid' AND due<>'' AND due<?",(date.today().isoformat(),)).fetchone()[0]
   self.label(p,f"Overdue reminders: {overdue_tasks} tasks · {overdue_invoices} unpaid invoices",11,"danger").pack(anchor="w",pady=(0,10))
  bar=ctk.CTkFrame(p,fg_color="transparent");bar.pack(fill="x",pady=(0,12))
  self.search=tk.StringVar();e=ctk.CTkEntry(bar,textvariable=self.search,placeholder_text="Search records…",width=260,height=36,corner_radius=10,font=self.font(11));e.pack(side="left",padx=(0,10));e.bind("<KeyRelease>",lambda ev:self.refresh_table(n))
  acts={"Customers":[("＋ Add",self.add_customer),("Edit",self.edit_customer),("Delete",lambda:self.delete(n,"customers")),("CSV",lambda:self.export("customers"))],
  "Invoices":[("＋ New invoice",self.add_invoice),("Edit",self.edit_invoice),("Mark paid",self.mark_paid),("Delete",lambda:self.delete(n,"invoices")),("CSV",lambda:self.export("invoices"))],
  "Expenses":[("＋ Add",self.add_expense),("Edit",self.edit_expense),("Delete",lambda:self.delete(n,"expenses")),("CSV",lambda:self.export("expenses"))],
  "Tasks":[("＋ Add",self.add_task),("Complete / reopen",self.toggle_task),("Delete",lambda:self.delete(n,"tasks")),("CSV",lambda:self.export("tasks"))],
  "Documents":[("＋ Add document",self.add_document),("Open",self.open_document),("Delete",lambda:self.delete(n,"documents")),("CSV",lambda:self.export("documents"))]}
  for i,(t,fn) in enumerate(acts[n]):self.button(bar,t,fn,i==0,105 if i else 125).pack(side="left",padx=3)
  box=self.panel(p);box.pack(fill="both",expand=True)
  cols={"Customers":("id","name","company","email","phone"),"Invoices":("id","number","customer","description","amount","issued","due","status"),"Expenses":("id","date","category","description","supplier","amount"),"Tasks":("id","title","due","priority","recurrence","status"),"Documents":("id","title","category","path","added")}[n]
  self.tree=ttk.Treeview(box,columns=cols,show="headings");self.tree_style()
  for c in cols:self.tree.heading(c,text=c.replace("_"," ").title());self.tree.column(c,width=125)
  self.tree.pack(fill="both",expand=True,padx=10,pady=10);self.tables[n]=self.tree;self.refresh_table(n)
 def refresh_table(self,n):
  tree=self.tables.get(n)
  if not tree:return
  for x in tree.get_children():tree.delete(x)
  q=self.search.get().lower() if hasattr(self,"search") else ""
  for r in self.data(n):
   v=self.values(n,r)
   if not q or q in " ".join(map(str,v)).lower():tree.insert("","end",values=v)
 def refresh_recent(self):
  if not hasattr(self,"recent"):return
  try:
   if not self.recent.winfo_exists():return
   for x in self.recent.get_children():self.recent.delete(x)
  except tk.TclError:return
  for r in self.data("Invoices")[:8]:self.recent.insert("","end",values=(r["number"],r["customer"],self.money(r["amount"]),r["due"],r["status"]))
 def refresh(self):
  for n in list(self.tables):self.refresh_table(n)
  self.refresh_recent()
  if hasattr(self,"pages") and self.pages["Overview"].winfo_children():self.overview()
 def toggle_global_search(self,force=None):
  opening=(not self.search_open) if force is None else bool(force)
  if opening==self.search_open:return
  self.search_open=opening
  if opening:
   self.global_search_entry.pack(side="right",before=self.search_button,padx=(6,2),pady=8)
   self.global_search_entry.focus_set()
   self.search_button.configure(text="×")
  else:
   self.global_search_entry.pack_forget()
   self.global_search_entry.delete(0,"end")
   self.search_button.configure(text="⌕")
 def global_search(self):
  query=self.global_search_entry.get().strip()
  if not query:return
  like="%"+query+"%"
  searches=[
   ("Customers","SELECT id,name || ' · ' || COALESCE(company,'') FROM customers WHERE name LIKE ? OR company LIKE ? OR email LIKE ? OR phone LIKE ? OR notes LIKE ?",(like,like,like,like,like)),
   ("Invoices","SELECT id,number || ' · ' || description FROM invoices WHERE number LIKE ? OR description LIKE ?",(like,like)),
   ("Expenses","SELECT id,category || ' · ' || description FROM expenses WHERE category LIKE ? OR description LIKE ? OR supplier LIKE ?",(like,like,like)),
   ("Tasks","SELECT id,title || ' · ' || due FROM tasks WHERE title LIKE ? OR due LIKE ?",(like,like)),
   ("Documents","SELECT id,title || ' · ' || path FROM documents WHERE title LIKE ? OR category LIKE ? OR path LIKE ?",(like,like,like)),
  ]
  found=[]
  for category,sql,args in searches:
   for row in self.db.execute(sql,args).fetchall():found.append((category,row[0],row[1]))
  win=ctk.CTkToplevel(self);win.title("Search results");win.geometry("760x500");win.transient(self)
  self.label(win,f"Search results for: {query}",18).pack(anchor="w",padx=20,pady=(18,8))
  tree=ttk.Treeview(win,columns=("type","id","record"),show="headings");self.tree_style()
  for col,title,width in [("type","Type",130),("id","ID",65),("record","Matching record",500)]:
   tree.heading(col,text=title);tree.column(col,width=width)
  tree.pack(fill="both",expand=True,padx=18,pady=12)
  for item in found:tree.insert("","end",values=item)
  def open_result(_event=None):
   selected=tree.selection()
   if not selected:return
   category,record_id,_=tree.item(selected[0],"values");win.destroy();self.show(category)
   def select_record():
    target=self.tables.get(category)
    if target:
     for iid in target.get_children():
      if str(target.item(iid,"values")[0])==str(record_id):
       target.selection_set(iid);target.focus(iid);target.see(iid);break
   self.after(180,select_record)
  tree.bind("<Double-1>",open_result)
  if not found:self.label(win,"No matching records found.",12,"muted").pack(anchor="w",padx=22,pady=5)
  else:self.label(win,f"{len(found)} matching records · double-click a result to open it",10,"muted").pack(anchor="w",padx=20,pady=(0,12))

 def next_recurrence_date(self,current,recurrence):
  if recurrence=="Daily":return current+timedelta(days=1)
  if recurrence=="Weekly":return current+timedelta(days=7)
  if recurrence=="Monthly":
   year=current.year+(1 if current.month==12 else 0);month=1 if current.month==12 else current.month+1
   return date(year,month,min(current.day,calendar.monthrange(year,month)[1]))
  return current

 def task_calendar(self):
  p=self.pages["Task Calendar"]
  for w in p.winfo_children():w.destroy()
  month=self.calendar_month
  self.heading(p,"Task calendar","A monthly view of dated tasks, with a list of everything scheduled this month.")
  bar=ctk.CTkFrame(p,fg_color="transparent");bar.pack(fill="x",pady=(0,12))
  self.button(bar,"← Previous",lambda:self.change_calendar_month(-1)).pack(side="left",padx=4)
  self.label(bar,month.strftime("%B %Y"),16,"accent").pack(side="left",padx=18)
  self.button(bar,"Next →",lambda:self.change_calendar_month(1)).pack(side="left",padx=4)
  grid=ctk.CTkFrame(p,fg_color="transparent");grid.pack(fill="x",pady=5)
  for col,day_name in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
   self.label(grid,day_name,10,"muted").grid(row=0,column=col,sticky="nsew",padx=3,pady=4);grid.grid_columnconfigure(col,weight=1)
  month_tasks=self.db.execute("SELECT * FROM tasks WHERE due>=? AND due<=? ORDER BY due,done",(month.isoformat(),date(month.year,month.month,calendar.monthrange(month.year,month.month)[1]).isoformat())).fetchall()
  counts={}
  for task in month_tasks:counts[task["due"]]=counts.get(task["due"],0)+1
  weeks=calendar.monthcalendar(month.year,month.month)
  for row_index,week in enumerate(weeks,1):
   for col,day_num in enumerate(week):
    cell=ctk.CTkFrame(grid,fg_color=self.col("panel"),corner_radius=9,border_width=0,border_color=self.col("line"),height=62)
    cell.grid(row=row_index,column=col,sticky="nsew",padx=3,pady=3);cell.grid_propagate(False)
    if day_num:
     key=date(month.year,month.month,day_num).isoformat()
     self.label(cell,str(day_num),12).pack(anchor="nw",padx=8,pady=(5,0))
     if counts.get(key):self.label(cell,f"{counts[key]} task(s)",9,"accent").pack(anchor="nw",padx=8)
  listing=self.panel(p);listing.pack(fill="x",pady=12)
  self.label(listing,"Tasks this month",14).pack(anchor="w",padx=16,pady=(12,5))
  if not month_tasks:self.label(listing,"No dated tasks for this month yet.",11,"muted").pack(anchor="w",padx=16,pady=(0,12))
  for task in month_tasks:
   status="Complete" if task["done"] else "Open"
   self.label(listing,f"{task['due']}  ·  {task['title']}  ·  {task['priority']}  ·  {status}",10,"muted").pack(anchor="w",padx=16,pady=3)

 def change_calendar_month(self,offset):
  year=self.calendar_month.year+(self.calendar_month.month-1+offset)//12
  month=(self.calendar_month.month-1+offset)%12+1
  self.calendar_month=date(year,month,1);self.task_calendar()

 def record_customer_activity(self,customer_id,activity):
  self.db.execute("INSERT INTO customer_activity(customer_id,activity,created) VALUES(?,?,?)",(customer_id,activity,datetime.now().strftime("%Y-%m-%d %H:%M")))
  self.db.commit()

 def customer_activity_page(self):
  p=self.pages["Customer Activity"]
  for w in p.winfo_children():w.destroy()
  self.heading(p,"Customer activity history","Keep a timeline of conversations, follow-ups and important customer updates.")
  options=self.customer_options()
  if not options:
   self.label(p,"Add a customer first to start an activity history.",12,"muted").pack(anchor="w",pady=12);return
  row=ctk.CTkFrame(p,fg_color="transparent");row.pack(fill="x",pady=8)
  self.activity_customer_var=tk.StringVar(value=next(iter(options)))
  ctk.CTkComboBox(row,values=list(options),variable=self.activity_customer_var,width=320,font=self.font(11),command=lambda _value:self.refresh_customer_activity()).pack(side="left",padx=4)
  self.activity_note=ctk.CTkTextbox(p,height=100,corner_radius=12);self.activity_note.pack(fill="x",pady=8)
  self.button(p,"＋ Add activity",self.add_customer_activity,True,150).pack(anchor="e",pady=5)
  self.activity_timeline=ctk.CTkScrollableFrame(p,fg_color="transparent");self.activity_timeline.pack(fill="both",expand=True,pady=10)
  self.refresh_customer_activity()

 def selected_activity_customer(self):
  label=self.activity_customer_var.get()
  try:return int(label.split(" - ",1)[0])
  except Exception:return None

 def add_customer_activity(self):
  customer_id=self.selected_activity_customer()
  note=self.activity_note.get("1.0","end").strip()
  if not customer_id or not note:return messagebox.showinfo("Add an activity","Choose a customer and write a short note first.")
  self.record_customer_activity(customer_id,note)
  self.activity_note.delete("1.0","end");self.refresh_customer_activity()

 def refresh_customer_activity(self):
  if not hasattr(self,"activity_timeline") or not self.activity_timeline.winfo_exists():return
  for w in self.activity_timeline.winfo_children():w.destroy()
  customer_id=self.selected_activity_customer()
  if not customer_id:return
  rows=self.db.execute("SELECT activity,created FROM customer_activity WHERE customer_id=? ORDER BY id DESC",(customer_id,)).fetchall()
  if not rows:self.label(self.activity_timeline,"No activity recorded for this customer yet.",11,"muted").pack(anchor="w",pady=8)
  for item in rows:
   card=self.panel(self.activity_timeline);card.pack(fill="x",pady=5)
   self.label(card,item["created"],9,"accent").pack(anchor="w",padx=14,pady=(9,2))
   self.label(card,item["activity"],11,"text",wraplength=850,justify="left").pack(anchor="w",padx=14,pady=(0,9))

 def chosen(self,n):
  tree=self.tables.get(n)
  if not tree or not tree.selection():messagebox.showinfo("Select a record","Select a record first.");return None
  return int(tree.item(tree.selection()[0],"values")[0])
 def form(self,title,fields,initial=None):
  w=ctk.CTkToplevel(self);w.title(title);w.geometry(f"520x{max(260,120+len(fields)*54)}");w.transient(self);w.grab_set();w.configure(fg_color=self.col("bg"));vars={}
  self.label(w,title,20).pack(anchor="w",padx=22,pady=(18,8))
  for k,l,opts in fields:
   row=ctk.CTkFrame(w,fg_color="transparent");row.pack(fill="x",padx=20,pady=4);self.label(row,l,11,"muted",width=145,anchor="w").pack(side="left")
   v=tk.StringVar(value=(initial or {}).get(k,""));vars[k]=v
   widget=ctk.CTkComboBox(row,values=opts,variable=v,width=300,height=34,corner_radius=9,font=self.font(11),button_color=self.accent2(),button_hover_color=self.accent(),fg_color=self.col("input"),border_color=self.col("line"),text_color=self.col("text"),dropdown_fg_color=self.col("panel"),dropdown_text_color=self.col("text")) if opts else ctk.CTkEntry(row,textvariable=v,width=300,height=34,corner_radius=9,font=self.font(11),fg_color=self.col("input"),border_color=self.col("line"),text_color=self.col("text"))
   widget.pack(side="right")
  out={}
  def save():out.update({k:v.get().strip() for k,v in vars.items()});w.destroy()
  self.button(w,"Save",save,True,120).pack(anchor="e",padx=22,pady=15);w.wait_window();return out or None
 def customer_options(self):
  rows=self.db.execute("SELECT id,name FROM customers ORDER BY name").fetchall();return {f"{r['id']} - {r['name']}":r["id"] for r in rows}
 def add_customer(self):
  d=self.form("Add customer",[(k,k.title(),None) for k in ("name","company","email","phone","notes")])
  if d and d["name"]:
   self.db.execute("INSERT INTO customers(name,company,email,phone,notes) VALUES(?,?,?,?,?)",tuple(d.values()));self.db.commit()
   customer_id=self.db.execute("SELECT last_insert_rowid()").fetchone()[0];self.record_customer_activity(customer_id,"Customer record created")
   self.refresh()
 def edit_customer(self):
  i=self.chosen("Customers")
  if i is None:return
  r=self.db.execute("SELECT * FROM customers WHERE id=?",(i,)).fetchone();d=self.form("Edit customer",[(k,k.title(),None) for k in ("name","company","email","phone","notes")],dict(r))
  if d and d["name"]:
   self.db.execute("UPDATE customers SET name=?,company=?,email=?,phone=?,notes=? WHERE id=?",(d["name"],d["company"],d["email"],d["phone"],d["notes"],i));self.db.commit()
   self.record_customer_activity(i,"Customer details updated");self.refresh()
 def add_invoice(self):
  opts=self.customer_options()
  if not opts:return messagebox.showinfo("Add a customer first","Create a customer before an invoice.")
  d=self.form("New invoice",[("customer","Customer",list(opts)),("description","Description",None),("amount","Amount",None),("issued","Issue date YYYY-MM-DD",None),("due","Due date YYYY-MM-DD",None),("status","Status",["Draft","Sent","Paid"])],{"issued":date.today().isoformat(),"due":date.today().isoformat(),"status":"Draft"})
  if not d:return
  try:
   a=float(d["amount"]);date.fromisoformat(d["issued"]);date.fromisoformat(d["due"])
   if a<0:raise ValueError()
   num=f"SD-{date.today():%y%m%d}-{self.db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]+1:04d}"
   customer_id=opts[d["customer"]]
   self.db.execute("INSERT INTO invoices(number,customer_id,description,amount,issued,due,status) VALUES(?,?,?,?,?,?,?)",(num,customer_id,d["description"],a,d["issued"],d["due"],d["status"]));self.db.commit()
   self.record_customer_activity(customer_id,f"Invoice {num} created · {self.money(a)}");self.refresh()
  except Exception:messagebox.showerror("Invalid invoice","Check invoice amount and dates.")
 def edit_invoice(self):
  i=self.chosen("Invoices")
  if i is None:return
  r=self.db.execute("SELECT * FROM invoices WHERE id=?",(i,)).fetchone();opts=self.customer_options()
  if not opts:return
  selected=next((k for k,v in opts.items() if v==r["customer_id"]),list(opts)[0])
  d=self.form("Edit invoice",[("customer","Customer",list(opts)),("description","Description",None),("amount","Amount",None),("issued","Issue date YYYY-MM-DD",None),("due","Due date YYYY-MM-DD",None),("status","Status",["Draft","Sent","Paid"])],{"customer":selected,"description":r["description"],"amount":str(r["amount"]),"issued":r["issued"],"due":r["due"],"status":r["status"]})
  if not d:return
  try:
   a=float(d["amount"]);date.fromisoformat(d["issued"]);date.fromisoformat(d["due"])
   if a<0:raise ValueError()
   self.db.execute("UPDATE invoices SET customer_id=?,description=?,amount=?,issued=?,due=?,status=? WHERE id=?",(opts[d["customer"]],d["description"],a,d["issued"],d["due"],d["status"],i));self.db.commit();self.refresh()
  except Exception:messagebox.showerror("Invalid invoice","Check invoice fields.")
 def add_expense(self):
  d=self.form("Add expense",[("date","Date YYYY-MM-DD",None),("category","Category",["Travel","Software","Equipment","Office","Marketing","Other"]),("description","Description",None),("supplier","Supplier",None),("amount","Amount",None)],{"date":date.today().isoformat()})
  if not d:return
  try:
   date.fromisoformat(d["date"]);a=float(d["amount"])
   if a<0:raise ValueError()
   self.db.execute("INSERT INTO expenses(category,description,amount,date,supplier) VALUES(?,?,?,?,?)",(d["category"],d["description"],a,d["date"],d["supplier"]));self.db.commit();self.refresh()
  except Exception:messagebox.showerror("Invalid expense","Check expense date and amount.")
 def edit_expense(self):
  i=self.chosen("Expenses")
  if i is None:return
  r=self.db.execute("SELECT * FROM expenses WHERE id=?",(i,)).fetchone()
  d=self.form("Edit expense",[("date","Date YYYY-MM-DD",None),("category","Category",["Travel","Software","Equipment","Office","Marketing","Other"]),("description","Description",None),("supplier","Supplier",None),("amount","Amount",None)],{"date":r["date"],"category":r["category"],"description":r["description"],"supplier":r["supplier"],"amount":str(r["amount"])})
  if not d:return
  try:
   date.fromisoformat(d["date"]);a=float(d["amount"])
   if a<0:raise ValueError()
   self.db.execute("UPDATE expenses SET date=?,category=?,description=?,supplier=?,amount=? WHERE id=?",(d["date"],d["category"],d["description"],d["supplier"],a,i));self.db.commit();self.refresh()
  except Exception:messagebox.showerror("Invalid expense","Check expense date and amount.")
 def add_task(self):
  d=self.form("Add task",[("title","Task",None),("due","Due date (YYYY-MM-DD)",None),("priority","Priority",["Low","Normal","High"]),("recurrence","Repeat",["None","Daily","Weekly","Monthly"])],{"priority":"Normal","recurrence":"None"})
  if d and d["title"]:
   try:
    if d["due"]:date.fromisoformat(d["due"])
    if d["recurrence"]!="None" and not d["due"]:raise ValueError("A repeating task needs a due date.")
    self.db.execute("INSERT INTO tasks(title,due,priority,recurrence) VALUES(?,?,?,?)",(d["title"],d["due"],d["priority"],d["recurrence"]));self.db.commit();self.refresh()
   except ValueError:messagebox.showerror("Invalid due date","Use YYYY-MM-DD for the task due date. Repeating tasks must have a due date.")
 def add_document(self):
  path=filedialog.askopenfilename()
  if path:
   d=self.form("Add document",[("title","Document name",None),("category","Category",["Contract","Receipt","Proposal","Reference","Other"])],{"title":Path(path).name,"category":"Other"})
   if d and d["title"]:self.db.execute("INSERT INTO documents(title,category,path,added) VALUES(?,?,?,?)",(d["title"],d["category"],path,date.today().isoformat()));self.db.commit();self.refresh()
 def open_document(self):
  i=self.chosen("Documents")
  if i:
   path=self.db.execute("SELECT path FROM documents WHERE id=?",(i,)).fetchone()[0]
   if Path(path).exists():os.startfile(path) if sys.platform=="win32" else webbrowser.open(Path(path).as_uri())
   else:messagebox.showwarning("Missing file","The original file could not be found.")
 def mark_paid(self):
  i=self.chosen("Invoices")
  if i:
   row=self.db.execute("SELECT customer_id,number,amount FROM invoices WHERE id=?",(i,)).fetchone()
   self.db.execute("UPDATE invoices SET status='Paid' WHERE id=?",(i,));self.db.commit()
   if row:self.record_customer_activity(row["customer_id"],f"Invoice {row['number']} marked paid · {self.money(row['amount'])}")
   self.refresh()
 def toggle_task(self):
  i=self.chosen("Tasks")
  if i:
   row=self.db.execute("SELECT * FROM tasks WHERE id=?",(i,)).fetchone()
   if row and not row["done"] and row["recurrence"] not in (None,"","None") and row["due"]:
    try:
     next_due=self.next_recurrence_date(date.fromisoformat(row["due"]),row["recurrence"])
     while next_due<=date.today():next_due=self.next_recurrence_date(next_due,row["recurrence"])
     self.db.execute("UPDATE tasks SET due=?,done=0 WHERE id=?",(next_due.isoformat(),i))
    except ValueError:self.db.execute("UPDATE tasks SET done=1 WHERE id=?",(i,))
   else:self.db.execute("UPDATE tasks SET done=1-done WHERE id=?",(i,))
   self.db.commit();self.refresh()
 def delete(self,n,table):
  i=self.chosen(n)
  if i and messagebox.askyesno("Delete","Permanently delete this record?"):self.db.execute(f"DELETE FROM {table} WHERE id=?",(i,));self.db.commit();self.refresh()
 def export(self,table):
  path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
  if path:
   cur=self.db.execute(f"SELECT * FROM {table}")
   with open(path,"w",newline="",encoding="utf-8-sig") as f:w=csv.writer(f);w.writerow([x[0] for x in cur.description]);w.writerows(cur.fetchall())
   messagebox.showinfo("Export","CSV export saved.")
 def refresh(self):
  for n in list(self.tables):self.refresh_table(n)
  self.refresh_recent()
  if self.pages["Overview"].winfo_children():self.overview()
 def analytics(self):
  p=self.pages["Analytics"]
  for w in p.winfo_children():w.destroy()
  self.heading(p,"Business analytics","A clearer picture of cash flow, payment timing and spending patterns.")
  now=date.today()
  paid=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Paid'").fetchone()[0]
  outstanding=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status IN ('Draft','Sent')").fetchone()[0]
  spent=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
  metrics=ctk.CTkFrame(p,fg_color="transparent");metrics.pack(fill="x",pady=7)
  for title,value,sub in [("Paid income",self.money(paid),"All-time recorded"),("Outstanding",self.money(outstanding),"Draft and sent invoices"),("Recorded expenses",self.money(spent),"All-time recorded")]:
   card=self.panel(metrics);card.pack(side="left",fill="both",expand=True,padx=5)
   self.label(card,title.upper(),9,"muted").pack(anchor="w",padx=15,pady=(13,3));self.label(card,value,21,"accent").pack(anchor="w",padx=15);self.label(card,sub,9,"muted").pack(anchor="w",padx=15,pady=(2,13))
  trend=self.panel(p);trend.pack(fill="x",pady=8)
  self.label(trend,"Six-month cashflow pulse",15).pack(anchor="w",padx=16,pady=(14,4))
  self.label(trend,"Paid invoices compared with recorded expenses by month.",10,"muted").pack(anchor="w",padx=16,pady=(0,8))
  for offset in range(5,-1,-1):
   month=(now.replace(day=1)-timedelta(days=offset*31)).replace(day=1)
   next_month=(month.replace(day=28)+timedelta(days=4)).replace(day=1)
   income=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Paid' AND issued>=? AND issued<?",(month.isoformat(),next_month.isoformat())).fetchone()[0]
   costs=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date>=? AND date<?",(month.isoformat(),next_month.isoformat())).fetchone()[0]
   row=ctk.CTkFrame(trend,fg_color="transparent");row.pack(fill="x",padx=16,pady=5)
   self.label(row,month.strftime("%b %Y"),10,"muted",width=90,anchor="w").pack(side="left")
   self.label(row,"In  "+self.money(income),10,"accent",width=180,anchor="w").pack(side="left",padx=8)
   self.label(row,"Out  "+self.money(costs),10,"text",anchor="w").pack(side="left",padx=8)
  ageing=self.panel(p);ageing.pack(fill="x",pady=8)
  self.label(ageing,"Invoice ageing",15).pack(anchor="w",padx=16,pady=(14,8))
  buckets=[("Not overdue", "due>=?",(now.isoformat(),)),("1–7 days overdue","due<? AND due>=?",(now.isoformat(),(now-timedelta(days=7)).isoformat())),("8–30 days overdue","due<? AND due>=?",((now-timedelta(days=7)).isoformat(),(now-timedelta(days=30)).isoformat())),("Over 30 days overdue","due<?",( (now-timedelta(days=30)).isoformat(),))]
  for title,condition,args in buckets:
   amount=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status<>'Paid' AND due<>'' AND "+condition,args).fetchone()[0]
   self.label(ageing,f"{title}   ·   {self.money(amount)}",11,"danger" if "overdue" in title.lower() else "text").pack(anchor="w",padx=18,pady=4)
  categories=self.panel(p);categories.pack(fill="x",pady=8)
  self.label(categories,"Spending by category",15).pack(anchor="w",padx=16,pady=(14,8))
  rows=self.db.execute("SELECT COALESCE(NULLIF(category,''),'Uncategorised') category,COALESCE(SUM(amount),0) total FROM expenses GROUP BY category ORDER BY total DESC LIMIT 8").fetchall()
  max_total=max([float(x["total"] or 0) for x in rows] or [1]) or 1
  for item in rows:
   line=ctk.CTkFrame(categories,fg_color="transparent");line.pack(fill="x",padx=16,pady=5)
   self.label(line,item["category"],10,"text",width=150,anchor="w").pack(side="left")
   bar=ctk.CTkProgressBar(line,height=10,progress_color=self.accent());bar.pack(side="left",fill="x",expand=True,padx=10);bar.set(float(item["total"] or 0)/max_total)
   self.label(line,self.money(item["total"]),10,"muted",width=120,anchor="e").pack(side="right")
  if not rows:self.label(categories,"Expense categories will appear here once you add spending.",10,"muted").pack(anchor="w",padx=18,pady=(0,14))
  self.label(p,"These insights use records stored in this local database. Currency is a display preference only; this is not accounting or tax advice.",10,"muted",wraplength=900,justify="left").pack(anchor="w",pady=10)
 def whats_new(self):
  p=self.pages["What's New"]
  for w in p.winfo_children():w.destroy()
  self.heading(p,"Release notes","A clearer record of what has changed in SoloDesk.")
  sc=ctk.CTkScrollableFrame(p,fg_color="transparent");sc.pack(fill="both",expand=True)
  latest=self.panel(sc);latest.pack(fill="x",pady=(4,14))
  top=ctk.CTkFrame(latest,fg_color="transparent");top.pack(fill="x",padx=22,pady=(20,8))
  self.label(top,"V3.4",25,"accent").pack(side="left")
  self.label(top,"LATEST RELEASE",10,"muted").pack(side="right")
  self.label(latest,"Two complete Classy and Royal themes",19).pack(anchor="w",padx=22,pady=(0,5))
  self.label(latest,"13 November 2026  ·  Windows desktop",10,"muted").pack(anchor="w",padx=22)
  self.label(latest,"This release replaces the old accent-colour collection with two complete themes: Classy in midnight navy and ice white, and Royal in dark chocolate brown and pale metallic gold. Theme changes update the full workspace and preserve your saved records.",11,"muted",wraplength=900,justify="left").pack(anchor="w",padx=22,pady=(12,15))
  self.label(latest,"IN THIS RELEASE",10,"muted").pack(anchor="w",padx=22,pady=(0,7))
  for item in ["A risk and liability notice appears before first use and must be acknowledged.","The full notice can be reopened from Settings at any time.","The notice explains local data storage, backup responsibilities and the limits of business-record outputs.","Existing customers, invoices, expenses, tasks, documents and settings are preserved."]:
   self.label(latest,"✓   "+item,11,"text",wraplength=900,justify="left").pack(anchor="w",padx=24,pady=3)
  self.label(sc,"PREVIOUS RELEASES",10,"muted").pack(anchor="w",padx=4,pady=(8,7))
  history=[("V2.9","Accent spotlight groundwork","Introduced the multi-layer accent glow and initial Windows backdrop integration. The backdrop handling is refined in V3.0."),("V2.8","Creator shortcuts","Added persistent website and Ko-fi links in the sidebar and Settings."),("V2.7","Settings reliability","Improved saved accent compatibility and safe fallback handling."),("V2.6","Workspace refinements","Refined search, spacing and optional accent colours."),("V1.8","Financial overview","Added cashflow, invoice ageing and spending breakdown insights."),("V1.7","Workspace reliability","Refined startup and update handoff behaviour."),("V1.6","Workspace redesign","Introduced the top navigation, page ribbon and improved business workspace layout."),("V1.5","Everyday workflow tools","Added recurring tasks, reminders, global search, calendar and customer activity history."),("V1.4","Personalisation and updates","Added themes, fonts, appearance modes, automatic updates and Windows branding."),("V1.3","Business workspace","Added searchable records, analytics, local backups and customisation."),("V1.2","Core organiser","Added dashboard, customers, invoices, expenses, tasks and database backups.") ]
  for version,title,detail in history:
   card=self.panel(sc);card.pack(fill="x",pady=5)
   row=ctk.CTkFrame(card,fg_color="transparent");row.pack(fill="x",padx=17,pady=(13,3))
   self.label(row,version,14,"accent").pack(side="left")
   self.label(row,title,12,"text").pack(side="left",padx=12)
   self.label(card,detail,10,"muted",wraplength=900,justify="left").pack(anchor="w",padx=18,pady=(2,13))

 def show_legal_notice(self,force=False):
  version="2026-11-13"
  if not force and self.get("legal_notice_version","") == version:
   self.continue_after_legal_notice()
   return
  w=ctk.CTkToplevel(self);w.title("SoloDesk · Important information");w.geometry("720x650");w.minsize(600,520);w.transient(self);w.grab_set();w.configure(fg_color=self.col("bg"))
  def dismiss():
   if force:w.grab_release();w.destroy()
   else:self.close()
  w.protocol("WM_DELETE_WINDOW",dismiss)
  self.label(w,"Before you use SoloDesk",24).pack(anchor="w",padx=24,pady=(22,5))
  self.label(w,"Please read and acknowledge this business software risk notice.",12,"muted").pack(anchor="w",padx=24,pady=(0,12))
  body=ctk.CTkScrollableFrame(w,fg_color=self.col("panel"));body.pack(fill="both",expand=True,padx=20,pady=(0,14))
  notice=("GENERAL ORGANISATION SOFTWARE ONLY\n\n"
   "SoloDesk is a local business organiser for recording customers, invoices, expenses, tasks and links to documents. It is not accounting, bookkeeping, tax, legal or financial advice software. It does not process payments, submit tax or VAT returns, verify invoice compliance, or convert currencies. Currency selection changes the display symbol only.\n\n"
   "CHECK YOUR RECORDS\n\n"
   "You are responsible for checking customer details, amounts, invoice numbers, dates, tax treatment, payment status, expenses, task details and exported records before using or sharing them. Calculations, summaries, exports and displayed information may contain errors or omissions and should not replace your own checks or professional advice.\n\n"
   "CUSTOMER DATA AND PRIVACY\n\n"
   "Only enter customer details you are authorised to keep and only the information needed for your purpose. Keep records accurate, protect access to your device and delete personal data when you no longer need it. SoloDesk stores records locally and does not send customer records to Adrian Vale.\n\n"
   "LOCAL DATA AND BACKUPS\n\n"
   "Business records are stored locally on this device. Device failure, accidental deletion, corrupted files, operating-system problems or user actions may cause data loss. Use the backup and export features regularly and keep copies somewhere safe. Document entries link to files at their current local paths; SoloDesk does not guarantee those files will remain available. Use Delete all SoloDesk data in Settings to remove the local database and preferences; this does not delete external documents or backups you created.\n\n"
   "AVAILABILITY AND THIRD-PARTY SERVICES\n\n"
   "The app is provided as an organisational aid. Features may change, become unavailable or contain defects. Update checks and downloads rely on third-party services, including GitHub, which are outside the developer's control.\n\n"
   "LIMITATION OF LIABILITY\n\n"
   "To the fullest extent permitted by applicable law, Adrian Vale and the people involved in creating or maintaining SoloDesk exclude responsibility for losses, damage or costs arising from use of, inability to use, or reliance on the app, including data loss, business interruption, incorrect records, missed tasks or decisions made using its outputs. This does not exclude or limit any liability or consumer right that cannot lawfully be excluded or limited.\n\n"
   "Using SoloDesk does not create an accounting, tax, legal, financial or other professional relationship with Adrian Vale. If you do not agree with this notice, do not continue using the app.")
  self.label(body,notice,11,"text",wraplength=620,justify="left").pack(fill="both",expand=True,padx=16,pady=16)
  actions=ctk.CTkFrame(w,fg_color="transparent");actions.pack(fill="x",padx=20,pady=(0,18))
  self.button(actions,"Exit SoloDesk",dismiss).pack(side="left")
  def accept():
   self.set("legal_notice_version",version)
   w.grab_release();w.destroy()
   if not force:self.continue_after_legal_notice()
  self.button(actions,"I understand — continue",accept,True,190).pack(side="right")
 def continue_after_legal_notice(self):
  if self.cfg.get("tutorial_completed","0")!="1":self.after(250,self.tutorial)
  else:self.after(250,self.first_run_shortcut_prompt)
  if self.cfg.get("auto_updates","1")=="1":self.after(1800,self.check_updates)
 def show_legal_from_settings(self):
  self.show_legal_notice(force=True)
 def settings_page(self):
  p=self.pages["Settings"]
  for w in p.winfo_children():w.destroy()
  self.heading(p,"Settings","Personalise your workspace and manage your data.")
  sc=ctk.CTkScrollableFrame(p,fg_color="transparent");sc.pack(fill="both",expand=True)
  a=self.panel(sc);a.pack(fill="x",pady=6);self.label(a,"Choose one complete colour palette for the whole app.",16).pack(anchor="w",padx=18,pady=(14,8))
  self.setting_select(a,"Colour theme","colour_theme",["Classy","Royal"]);self.setting_transparency(a);self.setting_select(a,"Font family","font_family",FONTS);self.setting_switch(a,"Bold text","bold_text")
  b=self.panel(sc);b.pack(fill="x",pady=6);self.label(b,"Business preferences",16).pack(anchor="w",padx=18,pady=(14,8))
  self.bizvar=tk.StringVar(value=self.get("business"));self.curvar=tk.StringVar(value=self.get("currency","GBP"))
  self.setting_entry(b,"Business name",self.bizvar);self.setting_select_var(b,"Display currency",self.curvar,list(SYMBOLS))
  self.button(b,"Save business settings",self.save_business,True,170).pack(anchor="e",padx=18,pady=14)
  d=self.panel(sc);d.pack(fill="x",pady=6);self.label(d,"App and data",16).pack(anchor="w",padx=18,pady=(14,8));self.setting_switch(d,"Launch when Windows starts","startup");self.setting_switch(d,"Check for updates automatically","auto_updates")
  row=ctk.CTkFrame(d,fg_color="transparent");row.pack(anchor="w",padx=12,pady=10)
  for t,fn in [("Back up database",self.backup),("Create desktop shortcut",self.create_shortcut),("Remove desktop shortcut",lambda:self.create_shortcut(True)),("Replay quick-start guide",self.tutorial),("Check for updates",lambda:self.check_updates(True)),("Open GitHub",lambda:webbrowser.open(REPO))]:self.button(row,t,fn).pack(side="left",padx=4)
  self.label(d,"Records are stored locally. Currency selection changes the displayed symbol only; no FX conversion or tax calculations are performed.",10,"muted",wraplength=900,justify="left").pack(anchor="w",padx=18,pady=(0,8))
  self.button(d,"Privacy & legal information",lambda:webbrowser.open("https://adrianvaleitl-debug.github.io/SoloDesk/legal.html")).pack(anchor="w",padx=18,pady=(0,8))
  self.button(d,"Delete all SoloDesk data…",self.delete_all_data).pack(anchor="w",padx=18,pady=(0,14))
  legal=self.panel(sc);legal.pack(fill="x",pady=6);self.label(legal,"Legal & important information",16).pack(anchor="w",padx=18,pady=(14,5))
  self.label(legal,"SoloDesk is an organiser, not accounting or tax software. Review the full risk, data and liability notice before relying on records.",10,"muted",wraplength=900,justify="left").pack(anchor="w",padx=18,pady=(0,8))
  self.button(legal,"Read legal & liability notice",self.show_legal_from_settings).pack(anchor="w",padx=18,pady=(0,14))
  cr=self.panel(sc);cr.pack(fill="x",pady=6);self.label(cr,"Created by Adrian Vale",16).pack(anchor="w",padx=18,pady=(14,3));self.label(cr,"Follow the project and support development.",11,"muted").pack(anchor="w",padx=18)
  row=ctk.CTkFrame(cr,fg_color="transparent");row.pack(anchor="w",padx=12,pady=12)
  for t,u in [("My website ↗",PERSONAL_SITE),("YouTube @Adrianvaleitl",YOUTUBE),("TikTok @adrianvaleitl",TIKTOK),("Optional support · Ko-fi",KOFI)]:self.button(row,t,lambda url=u:webbrowser.open(url)).pack(side="left",padx=4)
 def setting_transparency(self,p):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=7)
  self.label(r,"Window transparency",11,"muted").pack(side="left")
  value=int(self.get("transparency","8"));display=self.label(r,f"{value}%",11,"text",width=52)
  display.pack(side="right",padx=(8,0))
  slider=ctk.CTkSlider(r,from_=0,to=35,number_of_steps=35,width=230,command=lambda v:(self.set("transparency",round(v)),display.configure(text=f"{round(v)}%"),self.after_idle(self.apply_glass_effect)))
  slider.set(value);slider.pack(side="right",padx=8)
 def setting_select(self,p,label,key,opts):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left")
  v=tk.StringVar(value=self.get(key,opts[0]))
  ctk.CTkComboBox(r,values=opts,variable=v,width=230,height=38,corner_radius=15,font=self.font(11),button_color=self.accent2(),button_hover_color=self.accent(),fg_color=self.col("input"),border_width=0,text_color=self.col("text"),dropdown_fg_color=self.col("panel"),dropdown_hover_color=self.col("hover"),dropdown_text_color=self.col("text"),command=lambda x,k=key:self.apply_setting(k,x)).pack(side="right")
 def setting_select_var(self,p,label,var,opts):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");ctk.CTkComboBox(r,values=opts,variable=var,width=230,height=34,corner_radius=10,font=self.font(11),button_color=self.accent2(),button_hover_color=self.accent()).pack(side="right")
 def setting_entry(self,p,label,var):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");ctk.CTkEntry(r,textvariable=var,width=230,height=34,corner_radius=10,font=self.font(11),fg_color=self.col("input"),border_color=self.col("line"),text_color=self.col("text")).pack(side="right")
 def setting_switch(self,p,label,key):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");v=tk.BooleanVar(value=self.get(key,"0")=="1")
  ctk.CTkSwitch(r,text="",variable=v,progress_color=self.accent2(),command=lambda:self.apply_setting(key,"1" if v.get() else "0")).pack(side="right")
 def apply_setting(self,k,v):
  if k=="colour_theme":
   v=v if v in ("Classy","Royal") else "Classy"
  self.set(k,v)
  if k=="colour_theme":
    global ACTIVE_THEME
    self.theme=v
    ACTIVE_THEME=v
    theme=ctk.ThemeManager.theme
    if "CTkButton" in theme:theme["CTkButton"].update({"fg_color":[self.accent(),self.accent()],"hover_color":[self.accent2(),self.accent2()],"text_color":[palette_color("#202020"),palette_color("#202020")]})
    if "CTkCheckBox" in theme:theme["CTkCheckBox"].update({"fg_color":[self.accent(),self.accent()],"hover_color":[self.accent2(),self.accent2()]})
    if "CTkSwitch" in theme:theme["CTkSwitch"].update({"progress_color":[self.accent(),self.accent()]})
    if "CTkSlider" in theme:theme["CTkSlider"].update({"progress_color":[self.accent(),self.accent()],"button_color":[self.accent(),self.accent()]})
    if "CTkProgressBar" in theme:theme["CTkProgressBar"].update({"progress_color":[self.accent(),self.accent()]})
    if "CTkRadioButton" in theme:theme["CTkRadioButton"].update({"fg_color":[self.accent(),self.accent()],"hover_color":[self.accent2(),self.accent2()]})
    if "CTkOptionMenu" in theme:theme["CTkOptionMenu"].update({"button_color":[self.accent(),self.accent()],"button_hover_color":[self.accent2(),self.accent2()]})
  elif k=="font_family":self.font_family=v
  elif k=="bold_text":self.bold=v=="1"
  elif k=="startup":self.startup(v=="1")
  self.rebuild()
 def rebuild(self):
  current=self.titlelabel.cget("text")
  for w in self.winfo_children():w.destroy()
  self.pages={};self.nav={};self.tables={};self.build_shell();self.show(current if current in self.pages else "Overview")
 def save_business(self):
  if not self.bizvar.get().strip():return messagebox.showerror("Required","Enter a business name.")
  self.set("business",self.bizvar.get().strip());self.set("currency",self.curvar.get());self.biz.configure(text=self.get("business"));self.refresh()
 def startup(self,on):
  if sys.platform!="win32":return
  try:
   import winreg
   with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE) as k:
    if on:
     exe=f'"{sys.executable}"' if getattr(sys,"frozen",False) else f'"{sys.executable}" "{Path(__file__).resolve()}"'
     winreg.SetValueEx(k,"SoloDesk",0,winreg.REG_SZ,exe)
    else:
     try:winreg.DeleteValue(k,"SoloDesk")
     except FileNotFoundError:pass
  except Exception as e:messagebox.showerror("Startup setting",str(e))
 def desktop_folder(self):
  try:
   import winreg
   with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:value,_=winreg.QueryValueEx(key,"Desktop")
   return Path(os.path.expandvars(value))
  except Exception:return Path.home()/"Desktop"
 def create_shortcut(self,remove=False):
  if sys.platform!="win32":return messagebox.showinfo("Windows shortcut","Desktop shortcuts are available in the Windows app.")
  shortcut=self.desktop_folder()/"SoloDesk.lnk"
  try:
   if remove:
    if shortcut.exists():shortcut.unlink()
    return messagebox.showinfo("Shortcut","SoloDesk desktop shortcut removed.")
   target=Path(sys.executable)
   args="" if getattr(sys,"frozen",False) else '"'+str(Path(__file__).resolve())+'"'
   base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))
   icon=base/"solodesk.ico"
   shortcut.parent.mkdir(parents=True,exist_ok=True)
   ps="$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut("+repr(str(shortcut))+"); $s.TargetPath="+repr(str(target))+"; $s.Arguments="+repr(args)+"; $s.WorkingDirectory="+repr(str(target.parent))+"; $s.Description='SoloDesk business workspace'; $s.IconLocation="+repr(str(icon)+",0")+"; $s.Save()"
   encoded=__import__("base64").b64encode(ps.encode("utf-16le")).decode("ascii")
   subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-EncodedCommand",encoded],check=True,capture_output=True)
   messagebox.showinfo("Shortcut","SoloDesk desktop shortcut created.")
  except Exception as e:messagebox.showerror("Shortcut error",str(e))
 def check_updates(self,manual=False):
  if getattr(self,"_update_check_running",False):return
  self._update_check_running=True
  def worker():
   try:
    req=urllib.request.Request("https://api.github.com/repos/adrianvaleitl-debug/SoloDesk/releases/latest",headers={"User-Agent":"SoloDesk"})
    with urllib.request.urlopen(req,timeout=20,context=GITHUB_SSL_CONTEXT) as response:data=json.loads(response.read().decode("utf-8"))
    latest=data.get("tag_name","V1.0")
    def parts(v):
     out=[]
     for part in str(v).strip().lstrip("vV").split("."):
      digits="".join(ch for ch in part if ch.isdigit())
      if not digits:break
      out.append(int(digits))
     return tuple(out) if out else (0,)
    if parts(latest)>parts(APP_VERSION):
     expected="solodesk-setup-"+str(latest).lower()+".exe"
     asset=next((x for x in data.get("assets",[]) if x.get("name","").lower()==expected),None)
     self.after(0,lambda:self.offer_update(latest,asset))
    elif manual:self.after(0,lambda:messagebox.showinfo("SoloDesk is up to date",f"You are using {APP_VERSION}, the latest available release."))
   except Exception as e:
    if manual:self.after(0,lambda err=str(e):messagebox.showwarning("Update check unavailable",f"Could not check GitHub Releases right now.\n\n{err}"))
   finally:self._update_check_running=False
  threading.Thread(target=worker,daemon=True).start()
 def offer_update(self,version,asset=None):
  if not asset or not asset.get("browser_download_url"):
   if messagebox.askyesno("Update available",f"SoloDesk {version} is available.\n\nOpen the release page to download it?"):webbrowser.open(RELEASES)
   return
  if not messagebox.askyesno("Update available",f"SoloDesk {version} is available.\n\nDownload and install the update now?\nYour saved business data will be kept."):return
  if not getattr(sys,"frozen",False):
   webbrowser.open(asset["browser_download_url"]);return
  def download():
   try:
    target=Path(tempfile.gettempdir())/("SoloDesk-Setup-"+str(version)+".exe")
    req=urllib.request.Request(asset["browser_download_url"],headers={"User-Agent":"SoloDesk-Updater"})
    with urllib.request.urlopen(req,timeout=120,context=GITHUB_SSL_CONTEXT) as response,target.open("wb") as output:shutil.copyfileobj(response,output)
    if not target.exists() or target.stat().st_size<100000:raise RuntimeError("The installer download appears incomplete.")
    def launch():
     try:
      subprocess.Popen([str(target),"/SILENT","/CLOSEAPPLICATIONS","/NORESTART"],close_fds=True)
      self.after(700,self.close)
     except Exception as e:messagebox.showerror("Update failed",f"Could not launch the installer.\n\n{e}")
    self.after(0,launch)
   except Exception as e:self.after(0,lambda err=str(e):messagebox.showerror("Update download failed",f"Could not download the update.\n\n{err}"))
  threading.Thread(target=download,daemon=True).start()
 def first_run_shortcut_prompt(self):
  if self.get("shortcut_prompted","0")=="1":return
  shortcut=self.desktop_folder()/"SoloDesk.lnk"
  self.set("shortcut_prompted","1")
  if shortcut.exists():return
  if messagebox.askyesno("Create a desktop shortcut?","Would you like a SoloDesk shortcut on your Windows desktop? You can change this later in Settings."):
   self.create_shortcut()
 def delete_all_data(self):
  if not messagebox.askyesno("Delete all SoloDesk data","This permanently deletes all SoloDesk records and settings stored on this device, including customers, invoices, expenses, tasks, document links and preferences. Back up anything you want to keep first. This does not delete original documents or backup copies stored outside the SoloDesk data folder. This cannot be undone.\n\nContinue?"):
   return
  try:
   self.db.commit()
   self.db.close()
   if ROOT.exists():shutil.rmtree(ROOT)
  except Exception as exc:
   messagebox.showerror("Data deletion incomplete",f"SoloDesk could not remove all local data. Close the app and remove this folder manually:\n{ROOT}\n\nDetails: {exc}")
   self.destroy()
   return
  messagebox.showinfo("Local data deleted","SoloDesk local records and settings have been deleted from this device.")
  self.destroy()
 def backup(self):
  path=filedialog.asksaveasfilename(defaultextension=".db",initialfile="solodesk-backup.db")
  if path:self.db.commit();shutil.copy2(DB,path);messagebox.showinfo("Backup","Database backup saved.")
 def tutorial(self):
  w=ctk.CTkToplevel(self);w.title("Welcome to SoloDesk");w.geometry("700x720");w.transient(self);w.grab_set();w.configure(fg_color=self.col("bg"))
  self.label(w,"Welcome to SoloDesk",24).pack(anchor="w",padx=25,pady=(22,4));self.label(w,"Your business, in one place.  ·  Your seven-step quick start",12,"accent").pack(anchor="w",padx=25,pady=(0,10))
  scroll=ctk.CTkScrollableFrame(w,fg_color="transparent");scroll.pack(fill="both",expand=True,padx=16)
  steps=[
   ("01  Set up your workspace","Add your business name and choose the currency symbol you want to display."),
   ("02  Add your customers","Save contact details for the people and businesses you work with."),
   ("03  Create and track invoices","Create invoices for customers and track draft, sent and paid status."),
   ("04  Record your expenses","Log business spending with a date, category, description and supplier."),
   ("05  Organise your work","Use priorities and due dates for tasks, and keep useful file links in Documents."),
   ("06  Make SoloDesk yours","Choose a colour theme, font, text weight and Dark, Light or System appearance."),
   ("07  Back up and stay current","Create a database backup from Settings and use automatic or manual update checks to stay up to date."),
  ]
  for title,desc in steps:
   card=self.panel(scroll);card.pack(fill="x",padx=8,pady=5);self.label(card,title,13).pack(anchor="w",padx=14,pady=(9,2));self.label(card,desc,10,"muted",wraplength=590,justify="left").pack(anchor="w",padx=14,pady=(0,9))
  def done():
   self.set("tutorial_completed","1");w.destroy()
   self.after(350,self.first_run_shortcut_prompt)
  self.button(w,"Get started",done,True,140).pack(anchor="e",padx=25,pady=14)
 def close(self):
  self.db.commit();self.db.close();self.destroy()

def run_app():
 try:
  SoloDesk().mainloop()
 except Exception:
  details=traceback.format_exc()
  log=ROOT/"startup_error.log"
  try:
   ROOT.mkdir(parents=True,exist_ok=True)
   log.write_text(details,encoding="utf-8")
  except Exception:log=None
  message="SoloDesk could not start because something went wrong.\n\n"+details[-1800:]
  if log:message+="\n\nA diagnostic report was saved to:\n"+str(log)
  if sys.platform=="win32":
   try:ctypes.windll.user32.MessageBoxW(None,message,"SoloDesk",0x10)
   except Exception:print(message+"\n"+details)
  else:print(message+"\n"+details)

if __name__=="__main__" and acquire_single_instance():run_app()
