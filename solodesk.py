import csv,os,shutil,sqlite3,sys,webbrowser,json,threading,urllib.request
from pathlib import Path
from datetime import date
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import customtkinter as ctk

APP_VERSION="V1.3"
ROOT=Path(os.environ.get("LOCALAPPDATA",Path.home()))/("SoloDesk" if sys.platform=="win32" else ".solodesk")
ROOT.mkdir(parents=True,exist_ok=True);DB=ROOT/"solodesk.db"
SYMBOLS={"GBP":"£","USD":"$","EUR":"€","CAD":"C$","AUD":"A$","INR":"₹","JPY":"¥","CHF":"Fr"}
FONTS=["Segoe UI","Arial","Verdana","Trebuchet MS","Georgia"]
THEMES={
"Dollar":("#B8E4C7","#6EB88A"),"Euro":("#B8D5F5","#6E9FD9"),
"Pound":("#D3C2F2","#9678D0"),"Yen":("#F2C1CC","#D77F96"),"Franc":("#B4E7E0","#58B5AA")}
YOUTUBE="https://www.youtube.com/@Adrianvaleitl";TIKTOK="https://www.tiktok.com/@adrianvaleitl";KOFI="https://ko-fi.com/marketinsight"
REPO="https://github.com/adrianvaleitl-debug/SoloDesk";RELEASES=REPO+"/releases/latest"

class SoloDesk(ctk.CTk):
 def __init__(self):
  self.db=sqlite3.connect(DB);self.db.row_factory=sqlite3.Row
  self.db.executescript("""CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT);
  CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT,company TEXT,email TEXT,phone TEXT,notes TEXT);
  CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY,number TEXT UNIQUE,customer_id INTEGER,description TEXT,amount REAL,issued TEXT,due TEXT,status TEXT);
  CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,category TEXT,description TEXT,amount REAL,date TEXT,supplier TEXT);
  CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT,due TEXT,priority TEXT,done INTEGER DEFAULT 0);
  CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,title TEXT,category TEXT,path TEXT,added TEXT);""")
  defaults={"business":"My Business","currency":"GBP","appearance":"Dark","colour_theme":"Dollar","font_family":"Segoe UI","bold_text":"1","tutorial_completed":"0","startup":"0","auto_updates":"1"}
  for k,v in defaults.items():self.db.execute("INSERT OR IGNORE INTO settings VALUES(?,?)",(k,v))
  self.db.commit();self.cfg={r["k"]:r["v"] for r in self.db.execute("SELECT * FROM settings")}
  self.font_family=self.cfg["font_family"];self.bold=self.cfg["bold_text"]=="1";self.theme=self.cfg["colour_theme"]
  ctk.set_appearance_mode(self.cfg["appearance"])
  super().__init__();self.title("SoloDesk "+APP_VERSION);self.geometry("1480x920");self.minsize(1150,740)
  self.protocol("WM_DELETE_WINDOW",self.close);self.pages={};self.nav={};self.tables={}
  self.build_shell();self.show("Overview");self.refresh()
  if self.cfg["tutorial_completed"]!="1":self.after(650,self.tutorial)
  if self.cfg.get("auto_updates","1")=="1":self.after(1800,self.check_updates)

 def get(self,k,d=""):return self.cfg.get(k,d)
 def set(self,k,v):
  self.cfg[k]=str(v);self.db.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",(k,str(v)));self.db.commit()
 def accent(self):return THEMES.get(self.theme,THEMES["Dollar"])[0]
 def accent2(self):return THEMES.get(self.theme,THEMES["Dollar"])[1]
 def col(self,k):
  dark=ctk.get_appearance_mode()=="Dark"
  return {"bg":"#101612" if dark else "#F1F5F1","side":"#121B16" if dark else "#E7EEE8",
  "panel":"#17211B" if dark else "#FFFFFF","panel2":"#1D2922" if dark else "#E8F0E9",
  "line":"#2A3A30" if dark else "#D8E3DA","text":"#EDF5EF" if dark else "#24352A",
  "muted":"#A1B1A6" if dark else "#718278","input":"#1D2922" if dark else "#F8FAF8",
  "hover":"#293B2F" if dark else "#DCE8DE","danger":"#D77F7F" }[k]
 def font(self,n=12):return ctk.CTkFont(family=self.font_family,size=n,weight="bold" if self.bold else "normal")
 def panel(self,p):return ctk.CTkFrame(p,fg_color=self.col("panel"),corner_radius=18,border_width=1,border_color=self.col("line"))
 def label(self,p,t,size=12,color="text",**kw):return ctk.CTkLabel(p,text=t,font=self.font(size),text_color=self.col(color),**kw)
 def button(self,p,t,fn,primary=False,width=None):
  return ctk.CTkButton(p,text=t,command=fn,width=width or 120,height=37,corner_radius=11,
   fg_color=self.accent() if primary else self.col("panel2"),hover_color=self.accent2(),
   text_color="#15251B" if primary else self.col("text"),font=self.font(11))
 def build_shell(self):
  self.configure(fg_color=self.col("bg"))
  self.side=ctk.CTkFrame(self,width=240,corner_radius=0,fg_color=self.col("side"));self.side.pack(side="left",fill="y");self.side.pack_propagate(False)
  b=ctk.CTkFrame(self.side,fg_color="transparent");b.pack(fill="x",padx=20,pady=(25,25))
  self.label(b,"◈",27,"accent").pack(side="left",padx=(0,8));self.label(b,"SoloDesk",22).pack(side="left")
  self.label(self.side,"YOUR BUSINESS, IN ONE PLACE",9,"muted").pack(anchor="w",padx=22,pady=(0,15))
  for name,ico in [("Overview","⌂"),("Customers","♙"),("Invoices","▤"),("Expenses","↗"),("Tasks","✓"),("Documents","▧"),("Analytics","▥"),("What's New","✦"),("Settings","⚙")]:
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
  self.body=ctk.CTkFrame(self.work,fg_color="transparent");self.body.pack(fill="both",expand=True,padx=23,pady=20)
  for n in ["Overview","Customers","Invoices","Expenses","Tasks","Documents","Analytics","What's New","Settings"]:self.pages[n]=ctk.CTkFrame(self.body,fg_color="transparent")
 def show(self,n):
  for p in self.pages.values():p.pack_forget()
  self.pages[n].pack(fill="both",expand=True);self.titlelabel.configure(text=n)
  for k,b in self.nav.items():b.configure(fg_color=self.col("panel2") if k==n else "transparent",text_color=self.accent() if k==n else self.col("muted"))
  if n=="Overview":self.overview()
  elif n in self.tables or n in ("Customers","Invoices","Expenses","Tasks","Documents"):self.table_page(n)
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
  if n=="Tasks":return (r["id"],r["title"],r["due"],r["priority"],"Complete" if r["done"] else "Open")
  return (r["id"],r["title"],r["category"],r["path"],r["added"])
 def table_page(self,n):
  p=self.pages[n]
  for w in p.winfo_children():w.destroy()
  self.heading(p,n,{"Customers":"Customer directory and contact records.","Invoices":"Create, edit and track invoice payments.","Expenses":"Record business spending and suppliers.","Tasks":"Prioritise the next things to do.","Documents":"Keep business files linked in one place."}[n])
  bar=ctk.CTkFrame(p,fg_color="transparent");bar.pack(fill="x",pady=(0,12))
  self.search=tk.StringVar();e=ctk.CTkEntry(bar,textvariable=self.search,placeholder_text="Search records…",width=260,height=36,corner_radius=10,font=self.font(11));e.pack(side="left",padx=(0,10));e.bind("<KeyRelease>",lambda ev:self.refresh_table(n))
  acts={"Customers":[("＋ Add",self.add_customer),("Edit",self.edit_customer),("Delete",lambda:self.delete(n,"customers")),("CSV",lambda:self.export("customers"))],
  "Invoices":[("＋ New invoice",self.add_invoice),("Edit",self.edit_invoice),("Mark paid",self.mark_paid),("Delete",lambda:self.delete(n,"invoices")),("CSV",lambda:self.export("invoices"))],
  "Expenses":[("＋ Add",self.add_expense),("Edit",self.edit_expense),("Delete",lambda:self.delete(n,"expenses")),("CSV",lambda:self.export("expenses"))],
  "Tasks":[("＋ Add",self.add_task),("Complete / reopen",self.toggle_task),("Delete",lambda:self.delete(n,"tasks")),("CSV",lambda:self.export("tasks"))],
  "Documents":[("＋ Add document",self.add_document),("Open",self.open_document),("Delete",lambda:self.delete(n,"documents")),("CSV",lambda:self.export("documents"))]}
  for i,(t,fn) in enumerate(acts[n]):self.button(bar,t,fn,i==0,105 if i else 125).pack(side="left",padx=3)
  box=self.panel(p);box.pack(fill="both",expand=True)
  cols={"Customers":("id","name","company","email","phone"),"Invoices":("id","number","customer","description","amount","issued","due","status"),"Expenses":("id","date","category","description","supplier","amount"),"Tasks":("id","title","due","priority","status"),"Documents":("id","title","category","path","added")}[n]
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
   widget=ctk.CTkComboBox(row,values=opts,variable=v,width=300,height=34,corner_radius=9,font=self.font(11)) if opts else ctk.CTkEntry(row,textvariable=v,width=300,height=34,corner_radius=9,font=self.font(11))
   widget.pack(side="right")
  out={}
  def save():out.update({k:v.get().strip() for k,v in vars.items()});w.destroy()
  self.button(w,"Save",save,True,120).pack(anchor="e",padx=22,pady=15);w.wait_window();return out or None
 def customer_options(self):
  rows=self.db.execute("SELECT id,name FROM customers ORDER BY name").fetchall();return {f"{r['id']} - {r['name']}":r["id"] for r in rows}
 def add_customer(self):
  d=self.form("Add customer",[(k,k.title(),None) for k in ("name","company","email","phone","notes")])
  if d and d["name"]:self.db.execute("INSERT INTO customers(name,company,email,phone,notes) VALUES(?,?,?,?,?)",tuple(d.values()));self.db.commit();self.refresh()
 def edit_customer(self):
  i=self.chosen("Customers")
  if i is None:return
  r=self.db.execute("SELECT * FROM customers WHERE id=?",(i,)).fetchone();d=self.form("Edit customer",[(k,k.title(),None) for k in ("name","company","email","phone","notes")],dict(r))
  if d and d["name"]:self.db.execute("UPDATE customers SET name=?,company=?,email=?,phone=?,notes=? WHERE id=?",(d["name"],d["company"],d["email"],d["phone"],d["notes"],i));self.db.commit();self.refresh()
 def add_invoice(self):
  opts=self.customer_options()
  if not opts:return messagebox.showinfo("Add a customer first","Create a customer before an invoice.")
  d=self.form("New invoice",[("customer","Customer",list(opts)),("description","Description",None),("amount","Amount",None),("issued","Issue date YYYY-MM-DD",None),("due","Due date YYYY-MM-DD",None),("status","Status",["Draft","Sent","Paid"])],{"issued":date.today().isoformat(),"due":date.today().isoformat(),"status":"Draft"})
  if not d:return
  try:
   a=float(d["amount"]);date.fromisoformat(d["issued"]);date.fromisoformat(d["due"])
   if a<0:raise ValueError()
   num=f"SD-{date.today():%y%m%d}-{self.db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]+1:04d}"
   self.db.execute("INSERT INTO invoices(number,customer_id,description,amount,issued,due,status) VALUES(?,?,?,?,?,?,?)",(num,opts[d["customer"]],d["description"],a,d["issued"],d["due"],d["status"]));self.db.commit();self.refresh()
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
  d=self.form("Add task",[("title","Task",None),("due","Due date (optional)",None),("priority","Priority",["Low","Normal","High"])],{"priority":"Normal"})
  if d and d["title"]:self.db.execute("INSERT INTO tasks(title,due,priority) VALUES(?,?,?)",tuple(d.values()));self.db.commit();self.refresh()
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
  if i:self.db.execute("UPDATE invoices SET status='Paid' WHERE id=?",(i,));self.db.commit();self.refresh()
 def toggle_task(self):
  i=self.chosen("Tasks")
  if i:self.db.execute("UPDATE tasks SET done=1-done WHERE id=?",(i,));self.db.commit();self.refresh()
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
  notes=[("V1.3","Market Insight design system",["Dark-first interface, rounded cards and consistent controls.","Five colour themes, five fonts, global bold text and dark/light/system modes.","Analytics, searchable records, document links, quick-start guide and creator links."]),("V1.2","Business workspace refresh",["Overview dashboard, customers, invoices, expenses and tasks.","Invoice and expense editing, CSV exports, local database backups.","Responsive website and Windows packaging."])]
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
  v=tk.StringVar(value=self.get(key,opts[0]));ctk.CTkComboBox(r,values=opts,variable=v,width=230,height=34,corner_radius=10,font=self.font(11),command=lambda x,k=key:self.apply_setting(k,x)).pack(side="right")
 def setting_select_var(self,p,label,var,opts):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");ctk.CTkComboBox(r,values=opts,variable=var,width=230,height=34,corner_radius=10,font=self.font(11)).pack(side="right")
 def setting_entry(self,p,label,var):
  r=ctk.CTkFrame(p,fg_color="transparent");r.pack(fill="x",padx=18,pady=5);self.label(r,label,11,"muted").pack(side="left");ctk.CTkEntry(r,textvariable=var,width=230,height=34,corner_radius=10,font=self.font(11)).pack(side="right")
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
   command="$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut('"+q(shortcut)+"'); $s.TargetPath='"+q(target)+"'; $s.Arguments='"+q(args)+"'; $s.WorkingDirectory='"+q(str(Path(target).parent))+"'; $s.Description='SoloDesk business workspace'; $s.Save()"
   import subprocess
   subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",command],check=True,capture_output=True,text=True)
   messagebox.showinfo("Shortcut","SoloDesk desktop shortcut created.")
  except Exception as e:messagebox.showerror("Shortcut error",str(e))
 def check_updates(self,manual=False):
  def worker():
   try:
    req=urllib.request.Request("https://api.github.com/repos/adrianvaleitl-debug/SoloDesk/releases/latest",headers={"User-Agent":"SoloDesk"})
    with urllib.request.urlopen(req,timeout=8) as response:data=json.loads(response.read().decode("utf-8"))
    latest=data.get("tag_name","V1.0")
    def parts(v):
     try:return tuple(int(x) for x in v.lstrip("vV").split("."))
     except:return (0,)
    if parts(latest)>parts(APP_VERSION):
     self.after(0,lambda:self.offer_update(latest))
    elif manual:self.after(0,lambda:messagebox.showinfo("SoloDesk is up to date",f"You are using {APP_VERSION}, the latest available release."))
   except Exception as e:
    if manual:self.after(0,lambda err=str(e):messagebox.showwarning("Update check unavailable",f"Could not check GitHub Releases right now.\\n\\n{err}"))
  threading.Thread(target=worker,daemon=True).start()
 def offer_update(self,version):
  if messagebox.askyesno("Update available",f"SoloDesk {version} is available.\\n\\nWould you like to open the download page?"):webbrowser.open(RELEASES)
 def backup(self):
  path=filedialog.asksaveasfilename(defaultextension=".db",initialfile="solodesk-backup.db")
  if path:self.db.commit();shutil.copy2(DB,path);messagebox.showinfo("Backup","Database backup saved.")
 def tutorial(self):
  w=ctk.CTkToplevel(self);w.title("Welcome to SoloDesk");w.geometry("620x500");w.transient(self);w.grab_set();w.configure(fg_color=self.col("bg"))
  self.label(w,"Welcome to SoloDesk",24).pack(anchor="w",padx=25,pady=(25,5));self.label(w,"Your business, in one place.",13,"accent").pack(anchor="w",padx=25,pady=(0,15))
  for title,desc in [("01  Set up your workspace","Add your business name and preferred display currency."),("02  Add customers","Save contact details, then create invoices for your customers."),("03  Track your money","Record invoices and expenses to understand paid and outstanding amounts."),("04  Stay organised","Use tasks and document links to keep your work together. Back up your local database from Settings.")]:
   card=self.panel(w);card.pack(fill="x",padx=22,pady=6);self.label(card,title,13).pack(anchor="w",padx=14,pady=(10,2));self.label(card,desc,10,"muted",wraplength=520,justify="left").pack(anchor="w",padx=14,pady=(0,10))
  def done():self.set("tutorial_completed","1");w.destroy()
  self.button(w,"Get started",done,True,140).pack(anchor="e",padx=25,pady=15)
 def close(self):
  self.db.commit();self.db.close();self.destroy()

if __name__=="__main__":SoloDesk().mainloop()
