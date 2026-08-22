#!/usr/bin/env node
"use strict";

const args = process.argv.slice(2);
const value = (name, fallback = "") => {
  const index = args.indexOf(`--${name}`);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};
const preferences = (() => { try { return JSON.parse(value("healthcare-preferences", "{}")); } catch { return {}; } })();
console.log(JSON.stringify({
  module: "healthcare",
  status: "success",
  action: value("action", "find_slots"),
  specialty: value("target", "general specialist"),
  location: preferences.preferred_location || value("location", "nearby"),
  insurance: preferences.insurance_provider || null,
  slots: [{ clinic: "Sample Care Clinic", date: "2026-08-28", time: "10:30", booking_url: "https://example.test/clinic" }],
  diagnosis: null,
  note: "Mock clinic search completed. Booking requires explicit user confirmation in a production adapter."
}));
