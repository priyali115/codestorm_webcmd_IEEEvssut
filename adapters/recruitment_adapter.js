#!/usr/bin/env node
"use strict";

const args = process.argv.slice(2);
const value = (name, fallback = "") => {
  const index = args.indexOf(`--${name}`);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};
const parse = (text) => { try { return JSON.parse(text); } catch { return {}; } };
const company = parse(value("recruitment-company", "{}"));
const student = parse(value("student-profile", "{}"));
console.log(JSON.stringify({
  module: "recruitment",
  status: "success",
  action: "mock_collect_and_prepare_application",
  company: company.company_name || value("target", "target company"),
  role: company.active_job || value("role", "open role"),
  candidate: student.name || "provided profile",
  credentials: { resume: (student.document_paths || [])[0] || null, skills: student.skills || [] },
  application_package: { collated: true, ready_for_review: true },
  note: "Mock DOM extraction completed; no application was submitted."
}));
