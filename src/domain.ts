export type AmountRow={ [key:string]: unknown };
export function sumAmounts(rows:AmountRow[]):number{return rows.reduce((sum,row)=>sum+(Number(row["amount"])||0),0)}
export function outstandingInvoiceTotal(rows:AmountRow[]):number{return sumAmounts(rows.filter(row=>row["status"]!=="Paid"))}
export function netRecorded(invoices:AmountRow[],expenses:AmountRow[]):number{return sumAmounts(invoices)-sumAmounts(expenses)}

export function nextRecurringDue(due:string|undefined,recurrence:string,today=new Date()):string|null{if(!["Daily","Weekly","Monthly"].includes(recurrence))return null;const parsed=due?new Date(due+"T12:00:00"):new Date(today);const base=Number.isNaN(parsed.getTime())||parsed<today?new Date(today):parsed;base.setHours(12,0,0,0);if(recurrence==="Daily")base.setDate(base.getDate()+1);else if(recurrence==="Weekly")base.setDate(base.getDate()+7);else{const day=base.getDate();base.setDate(1);base.setMonth(base.getMonth()+1);base.setDate(Math.min(day,new Date(base.getFullYear(),base.getMonth()+1,0).getDate()))}return base.toISOString().slice(0,10)}
