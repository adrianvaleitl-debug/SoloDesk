export type AmountRow={amount?:string|number;status?:string};
export function sumAmounts(rows:AmountRow[]):number{return rows.reduce((sum,row)=>sum+(Number(row.amount)||0),0)}
export function outstandingInvoiceTotal(rows:AmountRow[]):number{return sumAmounts(rows.filter(row=>row.status!=="Paid"))}
export function netRecorded(invoices:AmountRow[],expenses:AmountRow[]):number{return sumAmounts(invoices)-sumAmounts(expenses)}
