import csv, os, shutil, sqlite3, sys, webbrowser
from pathlib import Path
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home())) / ("SoloDesk" if sys.platform == "win32" else ".solodesk")
ROOT.mkdir(parents=True, exist_ok=True)
DB = ROOT / "solodesk.db"
SYMBOLS = {"GBP":"£","USD":"$","EUR":"€","CAD":"C$","AUD":"A$","INR":"₹"}

class SoloDesk(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SoloDesk V1.1"); self.geometry("1360x860"); self.minsize(1080,700)
        self.db=sqlite3.connect(DB); self.db.row_factory=sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT);
        CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT,company TEXT,email TEXT,phone TEXT,notes TEXT);
        CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY,number TEXT UNIQUE,customer_id INTEGER,description TEXT,amount REAL,issued TEXT,due TEXT,status TEXT);
        CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,category TEXT,description TEXT,amount REAL,date TEXT,supplier TEXT);
        CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT,due TEXT,priority TEXT,done INTEGER DEFAULT 0);
        """)
        self.db.execute("INSERT OR IGNORE INTO settings VALUES('business','My Business')")
        self.db.execute("INSERT OR IGNORE INTO settings VALUES('currency','GBP')"); self.db.commit()
        self.configure(bg="#F3F6FA")
        s=ttk.Style(self)
        try:s.theme_use("clam")
        except tk.TclError:pass
        s.configure(".", font=("Segoe UI", 10))
        s.configure("TFrame", background="#F3F6FA")
        s.configure("TLabel", background="#F3F6FA", foreground="#24364B", font=("Segoe UI", 10))
        s.configure("TNotebook", background="#F3F6FA", borderwidth=0, tabmargins=(4, 8, 4, 0))
        s.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(20, 13), background="#E5ECF5", foreground="#52677F")
        s.map("TNotebook.Tab", background=[("selected", "#3977D5"), ("active", "#DCE9F8")], foreground=[("selected", "#FFFFFF"), ("active", "#14243A")])
        s.configure("Treeview", rowheight=40, font=("Segoe UI", 10), background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#24364B", borderwidth=0, relief="flat")
        s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E8EFF7", foreground="#14243A", padding=(12, 13), relief="flat")
        s.map("Treeview", background=[("selected", "#DCEBFF")], foreground=[("selected", "#14243A")])
        s.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(14, 9), background="#E4ECF6", foreground="#193451", borderwidth=0)
        s.map("TButton", background=[("pressed", "#245EAD"), ("active", "#D4E4F7")], foreground=[("pressed", "#FFFFFF")])
        s.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), padding=(15, 9), background="#3977D5", foreground="#FFFFFF")
        s.map("Accent.TButton", background=[("pressed", "#245EAD"), ("active", "#2F69BE")], foreground=[("active", "#FFFFFF")])
        head=tk.Frame(self,bg="#14243A",height=82,highlightthickness=0); head.pack(fill="x"); head.pack_propagate(False)
        tk.Label(head,text="◈  SoloDesk",bg="#14243A",fg="white",font=("Segoe UI",24,"bold")).pack(side="left",padx=28)
        tk.Label(head,text="YOUR BUSINESS, IN ONE PLACE",bg="#14243A",fg="#9EC8F5",font=("Segoe UI",9,"bold")).pack(side="left")
        self.bizlabel=tk.Label(head,text=self.get("business"),bg="#1D3553",fg="#FFFFFF",font=("Segoe UI",10,"bold"),padx=16,pady=9);self.bizlabel.pack(side="right",padx=26)
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill="both",expand=True,padx=22,pady=(18,20))
        self.tables={}
        self.make_table("Customers",("id","name","company","email","phone"))
        self.make_table("Invoices",("id","number","customer","description","amount","issued","due","status"))
        self.make_table("Expenses",("id","date","category","description","supplier","amount"))
        self.make_table("Tasks",("id","title","due","priority","status"))
        self.make_overview();self.make_settings();self.refresh()

    def get(self,k):
        r=self.db.execute("SELECT v FROM settings WHERE k=?",(k,)).fetchone();return r[0] if r else ""
    def set(self,k,v):
        self.db.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",(k,v));self.db.commit()
    def money(self,n):return f"{SYMBOLS.get(self.get('currency'),'£')}{float(n):,.2f}"
    def make_table(self,name,cols):
        p=ttk.Frame(self.tabs,padding=14);self.tabs.add(p,text=name)
        tk.Label(p,text=name,bg="#F3F6FA",fg="#14243A",font=("Segoe UI",21,"bold")).pack(anchor="w",pady=(4,10))
        actions=ttk.Frame(p);actions.pack(fill="x",pady=8)
        self.tables[name]=ttk.Treeview(p,columns=cols,show="headings")
        for c in cols:self.tables[name].heading(c,text=c.replace("_"," ").title());self.tables[name].column(c,width=125)
        self.tables[name].pack(fill="both",expand=True)
        if name=="Customers":items=[("Add",self.add_customer),("Edit",self.edit_customer),("Delete",lambda:self.delete("Customers","customers")),("Export CSV",lambda:self.export("customers"))]
        elif name=="Invoices":items=[("New invoice",self.add_invoice),("Edit",self.edit_invoice),("Mark paid",self.mark_paid),("Delete",lambda:self.delete("Invoices","invoices")),("Export CSV",lambda:self.export("invoices"))]
        elif name=="Expenses":items=[("Add expense",self.add_expense),("Edit",self.edit_expense),("Delete",lambda:self.delete("Expenses","expenses")),("Export CSV",lambda:self.export("expenses"))]
        else:items=[("Add task",self.add_task),("Complete / reopen",self.toggle_task),("Delete",lambda:self.delete("Tasks","tasks"))]
        for label,fn in items:ttk.Button(actions,text=label,command=fn,style=("Accent.TButton" if label in ("Add","New invoice","Add expense","Add task") else "TButton")).pack(side="left",padx=(0,8),pady=(2,10))
    def make_overview(self):
        p=ttk.Frame(self.tabs,padding=16);self.tabs.insert(0,p,text="Overview")
        tk.Label(p,text="Business overview",bg="#F3F6FA",fg="#14243A",font=("Segoe UI",22,"bold")).pack(anchor="w",pady=(4,8))
        self.summary=tk.Label(p,text="",bg="#FFFFFF",fg="#14243A",font=("Segoe UI",13,"bold"),padx=24,pady=24,relief="flat",bd=0,justify="left");self.summary.pack(fill="x",anchor="w",pady=(18,24))
        self.recent=ttk.Treeview(p,columns=("number","customer","amount","due","status"),show="headings")
        for c in ("number","customer","amount","due","status"):self.recent.heading(c,text=c.title());self.recent.column(c,width=150)
        self.recent.pack(fill="both",expand=True)
    def make_settings(self):
        p=ttk.Frame(self.tabs,padding=16);self.tabs.add(p,text="Settings")
        tk.Label(p,text="Settings",bg="#F3F6FA",fg="#14243A",font=("Segoe UI",20,"bold")).pack(anchor="w")
        f=ttk.Frame(p);f.pack(anchor="nw",pady=20)
        ttk.Label(f,text="Business name").grid(row=0,column=0,pady=8,sticky="w")
        self.business=tk.StringVar(value=self.get("business"));ttk.Entry(f,textvariable=self.business,width=34).grid(row=0,column=1,padx=12)
        ttk.Label(f,text="Display currency").grid(row=1,column=0,pady=8,sticky="w")
        self.currency=tk.StringVar(value=self.get("currency"));ttk.Combobox(f,textvariable=self.currency,values=list(SYMBOLS),state="readonly",width=31).grid(row=1,column=1,padx=12)
        ttk.Button(f,text="Save settings",command=self.save_settings).grid(row=2,column=1,sticky="e",pady=12)
        ttk.Button(p,text="Back up database",command=self.backup).pack(anchor="w",pady=8)
        ttk.Button(p,text="Check for updates",command=lambda:webbrowser.open("https://github.com/adrianvaleitl-debug/SoloDesk/releases/latest")).pack(anchor="w",pady=8)
        ttk.Label(p,text="Currency changes the display symbol only; no currency conversion or tax calculations are performed.").pack(anchor="w",pady=8)
    def form(self,title,fields,initial=None):
        w=tk.Toplevel(self);w.title(title);w.transient(self);w.grab_set();vars={}
        for i,(key,label,options) in enumerate(fields):
            ttk.Label(w,text=label).grid(row=i,column=0,padx=10,pady=6,sticky="w")
            v=tk.StringVar(value=(initial or {}).get(key,""));vars[key]=v
            widget=ttk.Combobox(w,textvariable=v,values=options,state="readonly",width=30) if options else ttk.Entry(w,textvariable=v,width=33)
            widget.grid(row=i,column=1,padx=10,pady=6)
        out={}
        def save():out.update({k:v.get().strip() for k,v in vars.items()});w.destroy()
        ttk.Button(w,text="Save",command=save).grid(row=len(fields),column=1,pady=10,sticky="e")
        w.wait_window();return out or None
    def chosen(self,name):
        sel=self.tables[name].selection()
        if not sel:messagebox.showinfo("Select a row","Select a row first.");return None
        return int(self.tables[name].item(sel[0],"values")[0])
    def add_customer(self):
        d=self.form("Add customer",[("name","Name",None),("company","Company",None),("email","Email",None),("phone","Phone",None),("notes","Notes",None)])
        if d and d["name"]:self.db.execute("INSERT INTO customers(name,company,email,phone,notes) VALUES(?,?,?,?,?)",tuple(d.values()));self.db.commit();self.refresh()
    def edit_customer(self):
        i=self.chosen("Customers")
        if i is None:return
        r=self.db.execute("SELECT * FROM customers WHERE id=?",(i,)).fetchone()
        d=self.form("Edit customer",[(k,k.title(),None) for k in ("name","company","email","phone","notes")],dict(r))
        if d and d["name"]:self.db.execute("UPDATE customers SET name=?,company=?,email=?,phone=?,notes=? WHERE id=?",(d["name"],d["company"],d["email"],d["phone"],d["notes"],i));self.db.commit();self.refresh()
    def add_invoice(self):
        cs=self.db.execute("SELECT id,name FROM customers ORDER BY name").fetchall()
        if not cs:return messagebox.showinfo("Add a customer first","Create a customer before an invoice.")
        m={f"{r['id']} - {r['name']}":r['id'] for r in cs}
        d=self.form("New invoice",[("customer","Customer",list(m)),("description","Description",None),("amount","Amount",None),("issued","Issue date YYYY-MM-DD",None),("due","Due date YYYY-MM-DD",None),("status","Status",["Draft","Sent","Paid"])])
        if not d:return
        try:
            amount=float(d["amount"]);date.fromisoformat(d["issued"]);date.fromisoformat(d["due"])
            if amount<0:raise ValueError()
            n=self.db.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]+1
            self.db.execute("INSERT INTO invoices(number,customer_id,description,amount,issued,due,status) VALUES(?,?,?,?,?,?,?)",(f"SD-{date.today():%y%m%d}-{n:04d}",m[d["customer"]],d["description"],amount,d["issued"],d["due"],d["status"]))
            self.db.commit();self.refresh()
        except Exception:messagebox.showerror("Invalid invoice","Check all invoice fields and dates.")

    def edit_invoice(self):
        i=self.chosen("Invoices")
        if i is None:return
        r=self.db.execute("SELECT * FROM invoices WHERE id=?",(i,)).fetchone()
        cs=self.db.execute("SELECT id,name FROM customers ORDER BY name").fetchall()
        if not cs:return
        choices={f"{x['id']} - {x['name']}":x['id'] for x in cs}
        selected=next((k for k,v in choices.items() if v==r["customer_id"]),list(choices)[0])
        initial={"customer":selected,"description":r["description"],"amount":str(r["amount"]),"issued":r["issued"],"due":r["due"],"status":r["status"]}
        d=self.form("Edit invoice",[( "customer","Customer",list(choices)),("description","Description",None),("amount","Amount",None),("issued","Issue date YYYY-MM-DD",None),("due","Due date YYYY-MM-DD",None),("status","Status",["Draft","Sent","Paid"])],initial)
        if not d:return
        try:
            amount=float(d["amount"]);date.fromisoformat(d["issued"]);date.fromisoformat(d["due"])
            if amount<0:raise ValueError()
            self.db.execute("UPDATE invoices SET customer_id=?,description=?,amount=?,issued=?,due=?,status=? WHERE id=?",(choices[d["customer"]],d["description"],amount,d["issued"],d["due"],d["status"],i))
            self.db.commit();self.refresh()
        except Exception:messagebox.showerror("Invalid invoice","Check all invoice fields and dates.")

    def edit_expense(self):
        i=self.chosen("Expenses")
        if i is None:return
        r=self.db.execute("SELECT * FROM expenses WHERE id=?",(i,)).fetchone()
        initial={"date":r["date"],"category":r["category"],"description":r["description"],"supplier":r["supplier"],"amount":str(r["amount"])}
        d=self.form("Edit expense",[("date","Date YYYY-MM-DD",None),("category","Category",["Travel","Software","Equipment","Office","Marketing","Other"]),("description","Description",None),("supplier","Supplier",None),("amount","Amount",None)],initial)
        if not d:return
        try:
            date.fromisoformat(d["date"]);amount=float(d["amount"])
            if amount<0:raise ValueError()
            self.db.execute("UPDATE expenses SET date=?,category=?,description=?,supplier=?,amount=? WHERE id=?",(d["date"],d["category"],d["description"],d["supplier"],amount,i))
            self.db.commit();self.refresh()
        except Exception:messagebox.showerror("Invalid expense","Check date and amount.")

    def add_expense(self):
        d=self.form("Add expense",[("date","Date YYYY-MM-DD",None),("category","Category",["Travel","Software","Equipment","Office","Marketing","Other"]),("description","Description",None),("supplier","Supplier",None),("amount","Amount",None)])
        if not d:return
        try:
            date.fromisoformat(d["date"]);amount=float(d["amount"])
            if amount<0:raise ValueError()
            self.db.execute("INSERT INTO expenses(category,description,amount,date,supplier) VALUES(?,?,?,?,?)",(d["category"],d["description"],amount,d["date"],d["supplier"]));self.db.commit();self.refresh()
        except Exception:messagebox.showerror("Invalid expense","Check date and amount.")
    def add_task(self):
        d=self.form("Add task",[("title","Task",None),("due","Due date (optional)",None),("priority","Priority",["Low","Normal","High"])])
        if d and d["title"]:self.db.execute("INSERT INTO tasks(title,due,priority) VALUES(?,?,?)",tuple(d.values()));self.db.commit();self.refresh()
    def mark_paid(self):
        i=self.chosen("Invoices")
        if i:self.db.execute("UPDATE invoices SET status='Paid' WHERE id=?",(i,));self.db.commit();self.refresh()
    def toggle_task(self):
        i=self.chosen("Tasks")
        if i:self.db.execute("UPDATE tasks SET done=1-done WHERE id=?",(i,));self.db.commit();self.refresh()
    def delete(self,view,table):
        i=self.chosen(view)
        if i and messagebox.askyesno("Delete","Permanently delete this record?"):
            self.db.execute(f"DELETE FROM {table} WHERE id=?",(i,));self.db.commit();self.refresh()
    def export(self,table):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if not path:return
        cur=self.db.execute(f"SELECT * FROM {table}")
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f);w.writerow([x[0] for x in cur.description]);w.writerows(cur.fetchall())
        messagebox.showinfo("Exported","CSV export complete.")
    def save_settings(self):
        if not self.business.get().strip():return messagebox.showerror("Required","Enter a business name.")
        self.set("business",self.business.get().strip());self.set("currency",self.currency.get());self.bizlabel.config(text=self.get("business"));self.refresh()
    def backup(self):
        p=filedialog.asksaveasfilename(defaultextension=".db",initialfile="solodesk-backup.db")
        if p:self.db.commit();shutil.copy2(DB,p);messagebox.showinfo("Backup","Database backup saved.")
    def refresh(self):
        for tree in self.tables.values():
            for x in tree.get_children():tree.delete(x)
        for r in self.db.execute("SELECT id,name,company,email,phone FROM customers ORDER BY name"):self.tables["Customers"].insert("","end",values=tuple(r))
        inv=self.db.execute("SELECT i.*,COALESCE(c.name,'—') customer FROM invoices i LEFT JOIN customers c ON c.id=i.customer_id ORDER BY i.id DESC").fetchall()
        for r in inv:self.tables["Invoices"].insert("","end",values=(r["id"],r["number"],r["customer"],r["description"],self.money(r["amount"]),r["issued"],r["due"],r["status"]))
        for r in self.db.execute("SELECT * FROM expenses ORDER BY id DESC"):self.tables["Expenses"].insert("","end",values=(r["id"],r["date"],r["category"],r["description"],r["supplier"],self.money(r["amount"])))
        for r in self.db.execute("SELECT * FROM tasks ORDER BY done,due,id DESC"):self.tables["Tasks"].insert("","end",values=(r["id"],r["title"],r["due"],r["priority"],"Complete" if r["done"] else "Open"))
        for x in self.recent.get_children():self.recent.delete(x)
        for r in inv[:8]:self.recent.insert("","end",values=(r["number"],r["customer"],self.money(r["amount"]),r["due"],r["status"]))
        paid=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Paid'").fetchone()[0]
        due=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status IN ('Draft','Sent')").fetchone()[0]
        spent=self.db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        count=self.db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        self.summary.config(text=f"PAID INCOME     {self.money(paid)}        OUTSTANDING     {self.money(due)}\n\nEXPENSES     {self.money(spent)}        CUSTOMERS     {count}")

if __name__=="__main__":
    SoloDesk().mainloop()
