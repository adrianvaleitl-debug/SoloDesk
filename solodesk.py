import csv,os,shutil,sqlite3,sys,webbrowser,json,threading,urllib.request,subprocess,tempfile,ctypes,traceback
from pathlib import Path
from datetime import date, timedelta, datetime
import calendar
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import customtkinter as ctk
from PIL import Image

APP_VERSION="V1.5"
ROOT=Path(os.environ.get("LOCALAPPDATA",Path.home()))/("SoloDesk" if sys.platform=="win32" else ".solodesk")
ROOT.mkdir(parents=True,exist_ok=True);DB=ROOT/"solodesk.db"
SYMBOLS={"GBP":"£","USD":"$","EUR":"€","CAD":"C$","AUD":"A$","INR":"₹","JPY":"¥","CHF":"Fr"}
FONTS=["Segoe UI","Arial","Verdana","Trebuchet MS","Georgia"]
THEMES={
"Ocean":("#B8D8FF","#6F9FE0"),"Sage":("#BFE6D2","#6DBB91"),
"Violet":("#D6C8F5","#9A82D7"),"Coral":("#FFD0C2","#E58F79"),"Teal":("#B8E8E4","#62B9B1")}
LEGACY_THEMES={"Dollar":"Sage","Euro":"Ocean","Pound":"Violet","Yen":"Coral","Franc":"Teal"}
YOUTUBE="https://www.youtube.com/@Adrianvaleitl";TIKTOK="https://www.tiktok.com/@adrianvaleitl";KOFI="https://ko-fi.com/marketinsight"
REPO="https://github.com/adrianvaleitl-debug/SoloDesk";RELEASES=REPO+"/releases/latest"
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
  defaults={"business":"My Business","currency":"GBP","appearance":"Dark","colour_theme":"Dollar","font_family":"Segoe UI","bold_text":"1","tutorial_completed":"0","startup":"0","auto_updates":"1"}
  for k,v in defaults.items():self.db.execute("INSERT OR IGNORE INTO settings VALUES(?,?)",(k,v))
  self.db.commit();self.cfg={r["k"]:r["v"] for r in self.db.execute("SELECT * FROM settings")}
  self.font_family=self.cfg["font_family"];self.bold=self.cfg["bold_text"]=="1"
  self.theme=LEGACY_THEMES.get(self.cfg["colour_theme"],self.cfg["colour_theme"])
  if self.theme not in THEMES:self.theme="Ocean"
  self.set("colour_theme",self.theme)
  ctk.set_default_color_theme("blue")
  ctk.set_appearance_mode(self.cfg["appearance"])
  super().__init__();self.title("SoloDesk "+APP_VERSION);self.geometry("1480x920");self.minsize(1150,740)
  self.set_app_icon()
  if sys.platform=="win32":self.after(120,lambda:self.state("zoomed"))
  self.protocol("WM_DELETE_WINDOW",self.close);self.pages={};self.nav={};self.tables={}
  self.calendar_month=date.today().replace(day=1)
  self.build_shell();self.show("Overview");self.refresh()
  if self.cfg["tutorial_completed"]!="1":self.after(650,self.tutorial)
  else:self.after(900,self.first_run_shortcut_prompt)
  if self.cfg.get("auto_updates","1")=="1":self.after(1800,self.check_updates)

 def set_app_icon(self):
  try:
   base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))
   icon=base/"solodesk.ico"
   if not icon.exists():icon=base/"assets"/"solodesk.ico"
   if icon.exists():self.iconbitmap(default=str(icon))
   logo=base/"solodesk.png"
   if not logo.exists():logo=base/"assets"/"solodesk.png"
   self.brand_image=ctk.CTkImage(light_image=Image.open(logo),dark_image=Image.open(logo),size=(32,32)) if logo.exists() else None
  except Exception:self.brand_image=None
 def get(self,k,d=""):return self.cfg.get(k,d)
 def set(self,k,v):
  self.cfg[k]=str(v);self.db.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",(k,str(v)));self.db.commit()
 def accent(self):return THEMES.get(self.theme,THEMES["Ocean"])[0]
 def accent2(self):return THEMES.get(self.theme,THEMES["Ocean"])[1]
 def col(self,k):
  dark=ctk.get_appearance_mode()=="Dark"
  return {"bg":"#0D1420" if dark else "#F2F6FC","side":"#111D2C" if dark else "#E8EFF8",
  "panel":"#151F2D" if dark else "#FFFFFF","panel2":"#1C2A3B" if dark else "#E9F0FA",
  "line":"#2A3A50" if dark else "#D9E3F0","text":"#EFF5FF" if dark else "#26374D",
  "muted":"#9AAAC0" if dark else "#71839C","input":"#1C2A3B" if dark else "#FAFCFF",
  "hover":"#263C55" if dark else "#DCE8F6","accent":self.accent(),"danger":"#D77F7F" }[k]
 def font(self,n=12):return ctk.CTkFont(family=self.font_family,size=n,weight="bold" if self.bold else "normal")
 def panel(self,p):return ctk.CTkFrame(p,fg_color=self.col("panel"),corner_radius=18,border_width=1,border_color=self.col("line"))
 def label(self,p,t,size=12,color="text",**kw):return ctk.CTkLabel(p,text=t,font=self.font(size),text_color=self.col(color),**kw)
 def button(self,p,t,fn,primary=False,width=None):
  return ctk.CTkButton(p,text=t,command=fn,width=width or 120,height=37,corner_radius=11,
   fg_color=self.accent() if primary else self.col("panel2"),hover_color=self.accent2(),
   text_color="#122033" if primary else self.col("text"),font=self.font(11))
 def build_shell(self):
  self.configure(fg_color=self.col("bg"))
  self.side=ctk.CTkFrame(self,width=240,corner_radius=0,fg_color=self.col("side"));self.side.pack(side="left",fill="y");self.side.pack_propagate(False)
  b=ctk.CTkFrame(self.side,fg_color="transparent");b.pack(fill="x",padx=20,pady=(25,25))
  if self.brand_image:
   ctk.CTkLabel(b,text="",image=self.brand_image).pack(side="left",padx=(0,8))
  else:self.label(b,"▦",27,"accent").pack(side="left",padx=(0,8))
  self.label(b,"SoloDesk",22).pack(side="left")
  self.label(self.side,"YOUR BUSINESS, IN ONE PLACE",9,"muted").pack(anchor="w",padx=22,pady=(0,15))
  for name,ico in [("Overview","⌂"),("Customers","♙"),("Invoices","▤"),("Expenses","↗"),("Tasks","✓"),("Task Calendar","▦"),("Customer Activity","◷"),("Documents","▧"),("Analytics","▥"),("What's New","✦"),("Settings","⚙")]:
   x=self.button(self.side,ico+"   "+name,lambda n=name:self.show(n));x.configure(anchor="w",fg_color="transparent",text_color=self.col("muted"),hover_color=self.col("hover"),height=42);x.pack(fill="x",padx=12,pady=3);self.nav[name]=x
  ctk.CTkFrame(self.side,height=2,fg_color=self.col("line")).pack(fill="x",padx=18,pady=(20,12))
  self.label(self.side,"CREATED BY ADRIAN VALE",9,"muted").pack(anchor="w",padx=20,pady=(0,7))
  for t,u in [("YouTube @Adrianvaleitl",YOUTUBE),("TikTok @adrianvaleitl",TIKTOK),("Support on Ko-fi",KOFI)]:
   x=self.button(self.side,t,lambda url=u:webbrowser.open(url));x.configure(fg_color="transparent",text_color=self.accent(),anchor="w",height=29);x.pack(fill="x",padx=14,pady=1)
  self.label(self.side,APP_VERSION,10,"muted").pack(side="bottom",anchor="w",padx=22,pady=16)
  self.work=ctk.CTkFrame(self,fg_color=self.col("bg"),corner_radius=0);self.work.pack(side="left",fill="both",expand=True)
  self.top=ctk.CTkFrame(self.work,height=72,fg_color=self.col("panel"),corner_radius=0);self.top.pack(fill="x");self.top.pack_propagate(False)
  self.titlelabel=self.label(self.top,"Overview",20);self.titlelabel.pack(side="left",padx=28)
  self.biz=self.label(self.top,self.get("business"),11,"accent",fg_color=self.col("panel2"),corner_radius=10,padx=13,pady=8);self.biz.pack(side="right",padx=25)
  self.global_search_entry=ctk.CTkEntry(self.top,placeholder_text="Search customers, invoices, tasks…",width=270,height=35,corner_radius=10,font=self.font(11))
  self.global_search_entry.pack(side="right",padx=8)
  self.global_search_entry.bind("<Return>",lambda _event:self.global_search())
  self.button(self.top,"Search",self.global_search).pack(side="right",padx=4)
  self.body=ctk.CTkFrame(self.work,fg_color="transparent");self.body.pack(fill="both",expand=True,padx=23,pady=20)
  for n in ["Overview","Customers","Invoices","Expenses","Tasks","Task Calendar","Customer Activity","Documents","Analytics","What's New","Settings"]:self.pages[n]=ctk.CTkFrame(self.body,fg_color="transparent")
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
    cell=ctk.CTkFrame(grid,fg_color=self.col("panel"),corner_radius=9,border_width=1,border_color=self.col("line"),height=62)
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
    self.db.execute("INSERT INTO tasks(title,due,priority,recurrence) VALUES(?,?,?,?)",(d["title"],d["due"],d["priority"],d["recurrence"]));self.db.commit();self.refresh()
   except ValueError:messagebox.showerror("Invalid due date","Use YYYY-MM-DD for the task due date.")
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
  self.heading(p,"Business analytics","A simple summary of recorded income and spending.")
  vals=[("Paid income",self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Paid'").fetchone()[0]),("Outstanding",self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status IN ('Draft','Sent')").fetchone()[0]),("Expenses",self.db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0])]
  for title,v in vals:
   card=self.panel(p);card.pack(fill="x",pady=7);self.label(card,title,14).pack(anchor="w",padx=18,pady=(12,2));self.label(card,self.money(v),23,"accent").pack(anchor="w",padx=18,pady=(0,12))
  self.label(p,"These figures reflect records saved in this local database. Currency is a display preference only.",10,"muted").pack(anchor="w",pady=10)
 def whats_new(self):
  p=self.pages["What's New"]
  for w in p.winfo_children():w.destroy()
  self.heading(p,"What's new in SoloDesk","Release notes and product improvements.")
  notes=[("V1.5","More control over everyday work",["Recurring daily, weekly and monthly tasks with automatic next due dates.","Overdue task and unpaid invoice reminders.","Global search across all workspace records.","Monthly task calendar and customer activity history."]),("V1.4","A more personal SoloDesk",["A dedicated SoloDesk workspace icon and a fresh navy-and-blue visual identity.","Five distinct colour themes, five fonts, bold or regular text, and Dark, Light or System appearance.","Automatic updates can download and launch the latest Windows installer for you.","A direct website installer download and improved Windows app branding."]),("V1.3","A more complete business workspace",["Rounded interface, searchable records, analytics and local backups.","Five font choices, colour themes and Dark, Light or System modes.","Windows startup, desktop shortcut controls and release update checks."]),("V1.2","Business workspace refresh",["Overview dashboard, customers, invoices, expenses and tasks.","Invoice and expense editing, CSV exports and local database backups."])]
  for v,t,items in notes:
   card=self.panel(p);card.pack(fill="x",pady=7);self.label(card,v,17,"accent").pack(anchor="w",padx=18,pady=(14,2));self.label(card,t,14).pack(anchor="w",padx=18,pady=3)
   for item in items:self.label(card,"•  "+item,11,"muted",wraplength=900,justify="left").pack(anchor="w",padx=20,pady=3)
   ctk.CTkFrame(card,height=10,fg_color="transparent").pack()
 def settings_page(self):
  p=self.pages["Settings"]
  for w in p.winfo_children():w.destroy()
  self.heading(p,"Settings","Personalise your workspace and manage your data.")
  sc=ctk.CTkScrollableFrame(p,fg_color="transparent");sc.pack(fill="both",expand=True)
  a=self.panel(sc);a.pack(fill="x",pady=6);self.label(a,"Appearance and personalisation",16).pack(anchor="w",padx=18,pady=(14,8))
  self.setting_select(a,"Appearance","appearance",["Dark","Light","System"]);self.setting_select(a,"Colour theme","colour_theme",list(THEMES));self.setting_select(a,"Font family","font_family",FONTS);self.setting_switch(a,"Bold text","bold_text")
  b=self.panel(sc);b.pack(fill="x",pady=6);self.label(b,"Business preferences",16).pack(anchor="w",padx=18,pady=(14,8))
  self.bizvar=tk.StringVar(value=self.get("business"));self.curvar=tk.StringVar(value=self.get("currency","GBP"))
  self.setting_entry(b,"Business name",self.bizvar);self.setting_select_var(b,"Display currency",self.curvar,list(SYMBOLS))
  self.button(b,"Save business settings",self.save_business,True,170).pack(anchor="e",padx=18,pady=14)
  d=self.panel(sc);d.pack(fill="x",pady=6);self.label(d,"App and data",16).pack(anchor="w",padx=18,pady=(14,8));self.setting_switch(d,"Launch when Windows starts","startup");self.setting_switch(d,"Check for updates automatically","auto_updates")
  row=ctk.CTkFrame(d,fg_color="transparent");row.pack(anchor="w",padx=12,pady=10)
  for t,fn in [("Back up database",self.backup),("Create desktop shortcut",self.create_shortcut),("Remove desktop shortcut",lambda:self.create_shortcut(True)),("Replay quick-start guide",self.tutorial),("Check for updates",lambda:self.check_updates(True)),("Open GitHub",lambda:webbrowser.open(REPO))]:self.button(row,t,fn).pack(side="left",padx=4)
  self.label(d,"Records are stored locally. Currency selection changes the displayed symbol only; no FX conversion or tax calculations are performed.",10,"muted",wraplength=900,justify="left").pack(anchor="w",padx=18,pady=(0,14))
  cr=self.panel(sc);cr.pack(fill="x",pady=6);self.label(cr,"Created by Adrian Vale",16).pack(anchor="w",padx=18,pady=(14,3));self.label(cr,"Follow the project and support development.",11,"muted").pack(anchor="w",padx=18)
  row=ctk.CTkFrame(cr,fg_color="transparent");row.pack(anchor="w",padx=12,pady=12)
  for t,u in [("YouTube @Adrianvaleitl",YOUTUBE),("TikTok @adrianvaleitl",TIKTOK),("Support on Ko-fi",KOFI)]:self.button(row,t,lambda url=u:webbrowser.open(url)).pack(side="left",padx=4)
 def setting_select(self,p,label,key,opts):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left")
  v=tk.StringVar(value=self.get(key,opts[0]));ctk.CTkComboBox(r,values=opts,variable=v,width=230,height=34,corner_radius=10,font=self.font(11),button_color=self.accent2(),button_hover_color=self.accent(),command=lambda x,k=key:self.apply_setting(k,x)).pack(side="right")
 def setting_select_var(self,p,label,var,opts):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");ctk.CTkComboBox(r,values=opts,variable=var,width=230,height=34,corner_radius=10,font=self.font(11),button_color=self.accent2(),button_hover_color=self.accent()).pack(side="right")
 def setting_entry(self,p,label,var):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");ctk.CTkEntry(r,textvariable=var,width=230,height=34,corner_radius=10,font=self.font(11),fg_color=self.col("input"),border_color=self.col("line"),text_color=self.col("text")).pack(side="right")
 def setting_switch(self,p,label,key):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");v=tk.BooleanVar(value=self.get(key,"0")=="1")
  ctk.CTkSwitch(r,text="",variable=v,progress_color=self.accent2(),command=lambda:self.apply_setting(key,"1" if v.get() else "0")).pack(side="right")
 def apply_setting(self,k,v):
  self.set(k,v)
  if k=="appearance":ctk.set_appearance_mode(v)
  elif k=="colour_theme":self.theme=v
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
     exe=sys.executable if getattr(sys,"frozen",False) else f'"{sys.executable}" "{Path(__file__).resolve()}"'
     winreg.SetValueEx(k,"SoloDesk",0,winreg.REG_SZ,exe)
    else:
     try:winreg.DeleteValue(k,"SoloDesk")
     except FileNotFoundError:pass
  except Exception as e:messagebox.showerror("Startup setting",str(e))
 def create_shortcut(self,remove=False):
  if sys.platform!="win32":
   return messagebox.showinfo("Windows shortcut","Desktop shortcuts are available in the Windows app.")
  desktop=Path.home()/"Desktop";shortcut=desktop/"SoloDesk.lnk"
  try:
   if remove:
    if shortcut.exists():shortcut.unlink()
    return messagebox.showinfo("Shortcut","SoloDesk desktop shortcut removed.")
   if getattr(sys,"frozen",False):
    target=sys.executable;args=""
   else:
    target=sys.executable;args='"'+str(Path(__file__).resolve())+'"'
   q=lambda x:str(x).replace("'","''")
   icon=(Path(target).parent/"_internal"/"solodesk.ico") if getattr(sys,"frozen",False) else (Path(__file__).resolve().parent/"assets"/"solodesk.ico")
   icon_cmd="$s.IconLocation='"+q(icon)+",0'; " if icon.exists() else ""
   command="$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut('"+q(shortcut)+"'); $s.TargetPath='"+q(target)+"'; $s.Arguments='"+q(args)+"'; $s.WorkingDirectory='"+q(str(Path(target).parent))+"'; $s.Description='SoloDesk business workspace'; "+icon_cmd+"$s.Save()"
   import subprocess
   subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",command],check=True,capture_output=True,text=True)
   messagebox.showinfo("Shortcut","SoloDesk desktop shortcut created.")
  except Exception as e:messagebox.showerror("Shortcut error",str(e))
 def check_updates(self,manual=False):
  if getattr(self,"_update_check_running",False):return
  self._update_check_running=True
  def worker():
   try:
    req=urllib.request.Request("https://api.github.com/repos/adrianvaleitl-debug/SoloDesk/releases/latest",headers={"User-Agent":"SoloDesk"})
    with urllib.request.urlopen(req,timeout=12) as response:data=json.loads(response.read().decode("utf-8"))
    latest=data.get("tag_name","V1.0")
    def parts(v):
     out=[]
     for part in str(v).strip().lstrip("vV").split("."):
      digits="".join(ch for ch in part if ch.isdigit())
      if not digits:break
      out.append(int(digits))
     return tuple(out) if out else (0,)
    if parts(latest)>parts(APP_VERSION):
     asset=next((x for x in data.get("assets",[]) if "setup" in x.get("name","").lower() and x.get("name","").lower().endswith(".exe")),None)
     self.after(0,lambda:self.offer_update(latest,asset))
    elif manual:self.after(0,lambda:messagebox.showinfo("SoloDesk is up to date",f"You are using {APP_VERSION}, the latest available release."))
   except Exception as e:
    if manual:self.after(0,lambda err=str(e):messagebox.showwarning("Update check unavailable",f"Could not check GitHub Releases right now.\\n\\n{err}"))
   finally:self._update_check_running=False
  threading.Thread(target=worker,daemon=True).start()
 def offer_update(self,version,asset=None):
  if not asset or not asset.get("browser_download_url"):
   if messagebox.askyesno("Update available",f"SoloDesk {version} is available.\\n\\nOpen the release page to download it?"):webbrowser.open(RELEASES)
   return
  if not messagebox.askyesno("Update available",f"SoloDesk {version} is available.\\n\\nDownload and install the update now?\\nYour saved business data will be kept."):return
  if not getattr(sys,"frozen",False):
   webbrowser.open(asset["browser_download_url"]);return
  def download():
   try:
    target=Path(tempfile.gettempdir())/("SoloDesk-Setup-"+str(version)+".exe")
    req=urllib.request.Request(asset["browser_download_url"],headers={"User-Agent":"SoloDesk-Updater"})
    with urllib.request.urlopen(req,timeout=90) as response,target.open("wb") as output:shutil.copyfileobj(response,output)
    if not target.exists() or target.stat().st_size<100000:raise RuntimeError("The installer download appears incomplete.")
    def launch():
     try:
      subprocess.Popen([str(target),"/SILENT","/CLOSEAPPLICATIONS","/RESTARTAPPLICATIONS"],close_fds=True)
      self.after(350,self.close)
     except Exception as e:messagebox.showerror("Update failed",f"Could not launch the installer.\\n\\n{e}")
    self.after(0,launch)
   except Exception as e:self.after(0,lambda err=str(e):messagebox.showerror("Update download failed",f"Could not download the update.\\n\\n{err}"))
  threading.Thread(target=download,daemon=True).start()
 def first_run_shortcut_prompt(self):
  if self.get("shortcut_prompted","0")=="1":return
  shortcut=Path.home()/"Desktop"/"SoloDesk.lnk"
  self.set("shortcut_prompted","1")
  if shortcut.exists():return
  if messagebox.askyesno("Create a desktop shortcut?","Would you like a SoloDesk shortcut on your Windows desktop? You can change this later in Settings."):
   self.create_shortcut()
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
  message="SoloDesk could not start because something went wrong."
  if log:message+="\\n\\nA diagnostic report was saved to:\\n"+str(log)
  if sys.platform=="win32":
   try:ctypes.windll.user32.MessageBoxW(None,message,"SoloDesk",0x10)
   except Exception:print(message+"\\n"+details)
  else:print(message+"\\n"+details)

if __name__=="__main__" and acquire_single_instance():run_app()
