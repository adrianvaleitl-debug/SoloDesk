import csv,os,shutil,sqlite3,sys,webbrowser,json,threading,urllib.request,subprocess,tempfile,ctypes,traceback,ssl,certifi
from pathlib import Path
from datetime import date, timedelta, datetime
import calendar
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageTk


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
        # Broad atmospheric haze plus several softer nebula cores. Keep the
        # edges diffuse so the colour never looks like a hard spotlight.
        blobs = [
            (0.76, 0.10, 0.48, 0.48, 34),
            (0.92, 0.42, 0.34, 0.38, 22),
            (0.18, 0.88, 0.42, 0.38, 18),
            (0.46, 0.52, 0.34, 0.30, 10),
        ]
        for cx, cy, rx, ry, alpha in blobs:
            bounds = (int((cx-rx)*width), int((cy-ry)*height),
                      int((cx+rx)*width), int((cy+ry)*height))
            draw.ellipse(bounds, fill=(*rgb, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(max(90, int(min(width, height) * 0.19))))
        photo = ImageTk.PhotoImage(glow)
        previous = getattr(window, "_accent_spotlight_canvas", None)
        if previous is not None and previous.winfo_exists():
            previous.destroy()
        canvas = tk.Canvas(window, width=width, height=height, highlightthickness=0,
                           borderwidth=0, bg=background)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.lower()
        window._accent_spotlight_canvas = canvas
        window._accent_spotlight_photo = photo
        if not getattr(window, "_accent_spotlight_resize_bound", False):
            def redraw(event):
                if event.widget is window:
                    window.after_idle(lambda: install_accent_spotlight(
                        window, getattr(window, "_active_spotlight_colour", accent), background))
            window.bind("<Configure>", redraw, add="+")
            window._accent_spotlight_resize_bound = True
        window._active_spotlight_colour = accent
    except Exception:
        # A decorative layer must never interrupt app startup or navigation.
        pass

APP_VERSION="V2.9"
ROOT=Path(os.environ.get("LOCALAPPDATA",Path.home()))/("SoloDesk" if sys.platform=="win32" else ".solodesk")
ROOT.mkdir(parents=True,exist_ok=True);DB=ROOT/"solodesk.db"
SYMBOLS={"GBP":"£","USD":"$","EUR":"€","CAD":"C$","AUD":"A$","INR":"₹","JPY":"¥","CHF":"Fr"}
FONTS=["Segoe UI","Arial","Verdana","Trebuchet MS","Georgia"]
THEMES={
"Black":("#B9B9B9","#A0A0A0"),"Amber":("#D7B77F","#BFA16A"),
"Azure":("#91AFE0","#7897C8"),"Lavender":("#B5A0D8","#9B86BE"),
"Rose":("#D99EAD","#C48495"),"Teal":("#91BEC3","#76A6AB")}
LEGACY_THEMES={"Dollar":"Black","Euro":"Azure","Pound":"Lavender","Yen":"Rose","Franc":"Teal","Ocean":"Azure","Sage":"Teal","Violet":"Lavender","Coral":"Rose"}
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
   ctypes.windll.user32.MessageBoxW(None,"SoloDesk is already running.\\n\\nCheck your taskbar for the open window.","SoloDesk",0x40)
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
  defaults={"business":"My Business","currency":"GBP","appearance":"Dark","colour_theme":"Black","font_family":"Segoe UI","bold_text":"1","tutorial_completed":"0","startup":"0","auto_updates":"1","transparency":"8"}
  for k,v in defaults.items():self.db.execute("INSERT OR IGNORE INTO settings VALUES(?,?)",(k,v))
  self.db.commit();self.cfg={r["k"]:r["v"] for r in self.db.execute("SELECT * FROM settings")}
  self.font_family=self.cfg["font_family"];self.bold=self.cfg["bold_text"]=="1"
  self.theme=LEGACY_THEMES.get(self.cfg["colour_theme"],self.cfg["colour_theme"])
  if self.theme not in THEMES:self.theme="Black"
  self.set("colour_theme",self.theme)
  ctk.set_default_color_theme("blue")
  theme=ctk.ThemeManager.theme
  for widget,radius in (("CTkFrame",22),("CTkButton",15),("CTkEntry",15),("CTkComboBox",15),("CTkOptionMenu",15)):
   if widget in theme:theme[widget]["corner_radius"]=radius
  control_colors={"fg_color":[self.accent(),self.accent()],"hover_color":[self.accent2(),self.accent2()],"text_color":["#202020","#202020"]}
  if "CTkButton" in theme:theme["CTkButton"].update({**control_colors,"corner_radius":13})
  if "CTkCheckBox" in theme:theme["CTkCheckBox"].update({"fg_color":[self.accent(),self.accent()],"hover_color":[self.accent2(),self.accent2()],"border_color":["#7F7F7F","#7F7F7F"],"checkmark_color":["#202020","#202020"]})
  if "CTkSwitch" in theme:theme["CTkSwitch"].update({"progress_color":[self.accent(),self.accent()]})
  if "CTkSlider" in theme:theme["CTkSlider"].update({"progress_color":[self.accent(),self.accent()],"button_color":[self.accent(),self.accent()],"button_hover_color":[self.accent2(),self.accent2()]})
  if "CTkComboBox" in theme:
   theme["CTkComboBox"].update({"fg_color":["#1A1A1A","#1A1A1A"],"border_color":["#404040","#404040"],"button_color":[self.accent(),self.accent()],"button_hover_color":[self.accent2(),self.accent2()],"text_color":["#F2F2F2","#F2F2F2"],"dropdown_fg_color":["#1F1F1F","#1F1F1F"],"dropdown_hover_color":["#363636","#363636"],"dropdown_text_color":["#F2F2F2","#F2F2F2"]})
  if "CTkOptionMenu" in theme:
   theme["CTkOptionMenu"].update({"fg_color":["#282828","#282828"],"button_color":[self.accent(),self.accent()],"button_hover_color":[self.accent2(),self.accent2()],"text_color":["#F2F2F2","#F2F2F2"],"dropdown_fg_color":["#1F1F1F","#1F1F1F"],"dropdown_hover_color":["#363636","#363636"],"dropdown_text_color":["#F2F2F2","#F2F2F2"]})
  ctk.set_appearance_mode(self.cfg["appearance"])
  super().__init__();self.title("SoloDesk "+APP_VERSION);screen_w=self.winfo_screenwidth();screen_h=self.winfo_screenheight();self.geometry(f"{min(1480,max(900,screen_w-80))}x{min(920,max(640,screen_h-100))}");self.minsize(min(1150,max(900,screen_w-80)),min(740,max(620,screen_h-100)))
  self.set_app_icon()
  self.apply_glass_effect()

  if sys.platform=="win32":self.after(120,lambda:self.state("zoomed"))
  self.protocol("WM_DELETE_WINDOW",self.close);self.pages={};self.nav={};self.tables={}
  self.calendar_month=date.today().replace(day=1)
  self.build_shell();self.show("Overview");self.refresh()
  if self.cfg["tutorial_completed"]!="1":self.after(650,self.tutorial)
  else:self.after(900,self.first_run_shortcut_prompt)
  if self.cfg.get("auto_updates","1")=="1":self.after(1800,self.check_updates)

  def apply_glass_effect(self):
      """Enable a real Windows acrylic backdrop (blurred content behind the window)."""
      try:
          if not sys.platform.startswith("win"):
              return
          self.update_idletasks()
          hwnd = ctypes.c_void_p(self.winfo_id())
          # Windows 11 system backdrop: transient-window acrylic. This is the
          # supported DWM path; the legacy accent policy below is a fallback.
          try:
              backdrop = ctypes.c_int(3)  # DWMSBT_TRANSIENTWINDOW (acrylic)
              ctypes.windll.dwmapi.DwmSetWindowAttribute(
                  hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
          except Exception:
              pass
          class ACCENT_POLICY(ctypes.Structure):
              _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                          ("GradientColor", ctypes.c_int), ("AnimationId", ctypes.c_int)]
          class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
              _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                          ("SizeOfData", ctypes.c_size_t)]
          # Alpha controls the acrylic tint, not the opacity of all text/widgets.
          transparency = int(self.get("transparency", "8")) if hasattr(self, "data") else int(self.get("transparency", "8"))
          alpha = max(0x78, min(0xD8, 0xC8 - round(transparency * 1.1)))
          tint = (alpha << 24) | 0x0017171B
          policy = ACCENT_POLICY(4, 2, tint, 0)
          data = WINDOWCOMPOSITIONATTRIBDATA(19, ctypes.addressof(policy), ctypes.sizeof(policy))
          apply_attribute = ctypes.windll.user32.SetWindowCompositionAttribute
          apply_attribute.argtypes = [ctypes.c_void_p, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
          apply_attribute.restype = ctypes.c_bool
          apply_attribute(hwnd, ctypes.byref(data))
      except Exception:
          pass

