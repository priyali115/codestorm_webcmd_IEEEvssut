#!/usr/bin/env node
"use strict";

const args = process.argv.slice(2);
const value = (name, fallback = "") => {
  const index = args.indexOf(`--${name}`);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};
const accounts = (() => { try { return JSON.parse(value("billing-accounts", "{}")); } catch { return {}; } })();
const bills = Object.entries(accounts).filter(([, account]) => account).map(([provider, account], index) => ({
  provider, account, amount: [842, 1199, 599][index] || 499, due_date: "2026-09-05", status: "due"
}));
const action = value("action", "status");
console.log(JSON.stringify({
  module: "bills",
  status: action === "pay" ? "paid" : "success",
  action,
  bills,
  total_due: bills.reduce((total, bill) => total + bill.amount, 0),
  payment_reference: action === "pay" ? `MOCK-PAY-${Date.now()}` : null,
  note: "Mock bill extraction/payment endpoint; no real transaction was made."
}));
