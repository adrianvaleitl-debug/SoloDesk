import { useEffect, useMemo, useState } from "react";
import { Activity, ArrowUpRight, Bell, Check, ChevronDown, CircleHelp, Command, Plus, Search, Settings2, Sparkles, X, LayoutDashboard, Sun, Users, Receipt, Wallet, CheckSquare, Folder, Repeat, NotebookPen, Target, Timer, Eye, ChartNoAxesCombined, ShieldCheck, Clock } from "lucide-react";
import "./styles.css";

type Entry = { id:string; title:string; detail:string; amount?:number; done?:boolean; created:string };
const sections = ["Overview","Customers","Invoices","Expenses","Tasks","Documents"];
const storageKey = "adrianvale.SoloDesk.v1";
const IconMap:Record<string,any> = {"Overview":"LayoutDashboard","Today":"Sun","Customers":"Users","Invoices":"Receipt","Expenses":"Wallet","Tasks":"CheckSquare","Documents":"Folder","Habits":"Repeat","Notes":"NotebookPen","Goals":"Target","Focus":"Timer","Watchlist":"Eye","Research":"ChartNoAxesCombined","Risk":"ShieldCheck","Market hours":"Clock"};
const initial:Record<string,Entry[]> = {"customers":[],"invoices":[],"expenses":[],"tasks":[],"documents":[]};
const money=(n:number)=>new Intl.NumberFormat("en-GB",{style:"currency",currency:"GBP"}).format(n);
export default function App(){
 const [section,setSection]=useState(sections[0]);
 const [data,setData]=useState<Record<string,Entry[]>>(()=>{try{return {...initial,...JSON.parse(localStorage.getItem(storageKey)||"{}")}}catch{return initial}});
 const [query,setQuery]=useState("");
 const [title,setTitle]=useState("");
 const [detail,setDetail]=useState("");
 const [amount,setAmount]=useState("");
 const [showAdd,setShowAdd]=useState(false);
 const [toast,setToast]=useState("");
 const [theme,setTheme]=useState<"classy"|"royal">("classy");
 useEffect(()=>{localStorage.setItem(storageKey,JSON.stringify(data))},[data]);
 useEffect(()=>{document.documentElement.dataset.theme=theme},[theme]);
 const key = section.toLowerCase().replace(" ","");
 const dataKey = ["customers","invoices","expenses","tasks","documents"].find((k:string)=>k.replace(" ","")===key) || "customers";
 const entries=data[dataKey]||[];
 const filtered=entries.filter(e=>(e.title+" "+e.detail).toLowerCase().includes(query.toLowerCase()));
 const totals=useMemo(()=>({count:Object.values(data).flat().length,done:Object.values(data).flat().filter(e=>e.done).length,amount:Object.values(data).flat().reduce((s,e)=>s+(e.amount||0),0)}),[data]);
 function add(){if(!title.trim())return;const entry:Entry={id:crypto.randomUUID(),title:title.trim(),detail:detail.trim(),created:new Date().toISOString(),...(amount.trim()?{amount:Number(amount)}:{})};setData(p=>({...p,[dataKey]:[entry,...(p[dataKey]||[])]}));setTitle("");setDetail("");setAmount("");setShowAdd(false);setToast("Saved to your workspace");window.setTimeout(()=>setToast(""),2400)}
 function remove(id:string){setData(p=>({...p,[dataKey]:(p[dataKey]||[]).filter(e=>e.id!==id)}))}
 function toggle(id:string){setData(p=>({...p,[dataKey]:(p[dataKey]||[]).map(e=>e.id===id?{...e,done:!e.done}:e)}))}
 const pageTitle = section==="Today"?"Today":section==="Overview"?"Overview":section;
 const isTask=section==="Tasks"||section==="Today";
 const isAmount=["Invoices","Expenses"].includes(section);
 const heroMetric=money(totals.amount);
 const subMetric="Recorded across your workspace";
 return <div className="shell">
  <aside className="sidebar">
   <div className="brand"><div className="brand-mark">A</div><div><b>ADRIAN VALE</b><span>SOFTWARE COLLECTION</span></div></div>
   <div className="product"><div className="product-icon">S</div><div><strong>SoloDesk</strong><small>BUSINESS WORKSPACE</small></div><ChevronDown size={15}/></div>
   <div className="nav-label">WORKSPACE</div>
   <nav>{sections.map((s)=><button key={s} className={section===s?"active":""} onClick={()=>{setSection(s);setQuery("")}}>{(()=>{const I=IconMap[s];return I?<I size={17}/>:<Activity size={17}/>})()}<span>{s}</span>{s==="Tasks"&&data.tasks?.length?<i>{data.tasks.length}</i>:null}</button>)}</nav>
   <div className="side-bottom"><div className="side-card"><Sparkles size={16}/><b>Made by Adrian Vale</b><p>Thoughtful tools, designed to feel effortless.</p><a href="https://adrianvaleitl-debug.github.io/" target="_blank">Visit website <ArrowUpRight size={12}/></a></div><div className="side-links"><a href="https://ko-fi.com/marketinsight" target="_blank">Support the work ↗</a><span>VERSION 4.0.0</span></div></div>
  </aside>
  <main className="main">
   <header className="topbar"><div className="breadcrumbs">ADRIAN VALE <span>/</span> SOLODESK <span>/</span> {section.toUpperCase()}</div><div className="top-actions"><div className="search"><Search size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search workspace"/><kbd>⌘ K</kbd></div><button className="icon-button" aria-label="Settings" onClick={()=>setToast("Settings are being prepared for this rebuild")}><Settings2 size={17}/></button><div className="avatar">AV</div></div></header>
   <div className="content">
    <div className="welcome"><div><div className="eyebrow">YOUR SPACE, WELL SPENT</div><h1>{pageTitle}<span>.</span></h1><p>A calm workspace for the essentials of running your business.</p></div><div className="date-pill"><span className="live-dot"/>{new Intl.DateTimeFormat("en-GB",{weekday:"long",day:"numeric",month:"long"}).format(new Date())}</div></div>
    <section className="hero-panel"><div className="hero-copy"><div className="eyebrow light">BUSINESS AT A GLANCE</div><h2>Your business, in one place.</h2><p>A calm workspace for the essentials of running your business.</p><button className="primary-button" onClick={()=>setShowAdd(true)}><Plus size={16}/> Add {section==="Customers"?"customer":section==="Invoices"?"invoice":section==="Expenses"?"expense":section==="Watchlist"?"symbol":section==="Notes"?"note":"item"}</button></div><div className="hero-stat"><span>RECORDED VALUE</span><strong>{heroMetric}</strong><small>{subMetric}</small></div><div className="hero-orb"/></section>
    <div className="section-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h2>{section==="Overview"?"A clear view of everything":section==="Today"?"Your priorities":section}</h2></div><button className="secondary-button" onClick={()=>setShowAdd(true)}><Plus size={15}/> New</button></div>
    <div className="stats-grid"><div className="stat-card"><span>ALL RECORDS</span><strong>{totals.count}</strong><small>Saved on this device</small></div><div className="stat-card"><span>COMPLETED</span><strong>{totals.done}</strong><small>Progress you have made</small></div><div className="stat-card"><span>WORKSPACE VALUE</span><strong>{money(totals.amount)}</strong><small>Invoices and expenses you record</small></div></div>
    <section className="list-panel"><div className="list-head"><div><h3>{section==="Overview"?"Recent activity":section==="Today"?"Your tasks":section+" records"}</h3><p>{filtered.length} {filtered.length===1?"item":"items"} in this view</p></div><button className="text-button" onClick={()=>setShowAdd(true)}>Add new <Plus size={14}/></button></div>
    {filtered.length===0?<div className="empty"><div className="empty-icon"><Command size={21}/></div><b>Nothing here just yet</b><p>Start with one small addition. You can edit or remove it whenever you need.</p><button className="secondary-button" onClick={()=>setShowAdd(true)}><Plus size={15}/> Create your first item</button></div>:<div className="entries">{filtered.map(e=><div className="entry" key={e.id}><button className={"check "+(e.done?"checked":"")} onClick={()=>toggle(e.id)} aria-label="Toggle completion">{e.done?<Check size={13}/>:null}</button><div className="entry-copy"><b>{e.title}</b><span>{e.detail||"Added "+new Date(e.created).toLocaleDateString("en-GB")}</span></div>{e.amount!==undefined?<strong className="entry-amount">{money(e.amount)}</strong>:null}<button className="remove" onClick={()=>remove(e.id)} aria-label="Delete"><X size={15}/></button></div>)}</div>}
    </section>
    <footer>Designed with care by Adrian Vale <span>·</span> Your data stays on this device</footer>
   </div>
  </main>
  {showAdd?<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setShowAdd(false)}}><form className="modal" onSubmit={e=>{e.preventDefault();add()}}><button type="button" className="modal-close" onClick={()=>setShowAdd(false)}><X size={17}/></button><div className="eyebrow">A NEW ADDITION</div><h2>Add to {section}</h2><p>Keep it simple. You can update this later.</p><label>Name or title<input autoFocus value={title} onChange={e=>setTitle(e.target.value)} placeholder="Give it a name" required/></label><label>Details<input value={detail} onChange={e=>setDetail(e.target.value)} placeholder="A little more context"/></label>{isAmount?<label>Amount (£)<input type="number" min="0" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)} placeholder="0.00"/></label>:null}<div className="modal-actions"><button type="button" className="secondary-button" onClick={()=>setShowAdd(false)}>Cancel</button><button className="primary-button" type="submit"><Plus size={15}/> Save item</button></div></form></div>:null}
  {toast?<div className="toast"><Check size={15}/>{toast}</div>:null}
 </div>
}