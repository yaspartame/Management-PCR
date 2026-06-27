# System Updates & Enhancements Summary

This document summarizes all the recent updates and modifications implemented across the IPCR (Individual Performance Commitment and Review) management system.

---

## 1. Documentation & Visual Flows
* **Mermaid Flowchart Added:**
  * Updated [flow.md](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/flow.md) with a comprehensive `Mermaid` flowchart showing the database lifecycle and table transitions from the initial workload distribution to draft submissions, chair reviews, decisions, and locking.

---

## 2. Regular Faculty Dashboard
* **Removed Redundant Alerts:**
  * Removed the duplicate `"IPCR is Locked (View-Only Mode)"` warning banner at the top of [faculty_dashboard.html](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/templates/faculty_dashboard.html). The more descriptive black banner remains active.
* **Separated Instructions & Support Functions:**
  * Removed **Research** and **Extension** targets from the core left-hand column list (to avoid redundancy, as they are already managed in the dedicated checklist menus on the right).
  * Split the core workloads card into two distinct cards:
    * **A. Instructions** (blue styled card)
    * **B. Support Functions** (orange/warning styled card)
* **Jinja2 Namespace Scoping Fix:**
  * Resolved a bug where the `"No strategic workloads assigned."` empty-state row was shown even when workloads were present. Loop variables were updated to use Jinja2 `namespace` check objects (`ns_inst.has_core` / `ns_supp.has_core`) to persist scope outside the iteration loops.
* **Submission Status Labeling:**
  * Renamed status badges and messages for first-time submissions:
    * Top right status badge updated from `"Pending Chair Approval"` to `"Waiting for Review"`.
    * Bottom right alert text updated from `"Your IPCR is currently locked pending approval."` to `"Your IPCR is currently waiting for review."`.

---

## 3. Program Chair Dashboard & Backend Database logic
* **Header Label Standardization:**
  * Renamed target allocation headers in Phase 1 of [prog_chair_dashboard.html](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/templates/prog_chair_dashboard.html) from "Instructions" and "Support Functions" to **"A. Instructions"** and **"B. Support Functions"** to align labels with the regular faculty dashboard.
* **Approved & Locked IPCRs List:**
  * Created database query function [get_locked_faculty_ipcrs](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/models/prog_chair.py#L152-L187) in the chair models.
  * Added controller integration in [prog_chair.py](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/routes/prog_chair.py#L14-L66) to query and pass `locked_drafts` to the template.
  * Added a new **"Approved & Locked IPCRs"** table in [prog_chair_dashboard.html](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/templates/prog_chair_dashboard.html) to display all faculty members who have locked their final evaluation targets for the active term.
* **Dedicated Read-Only Modal:**
  * Designed and added a new modal (`#viewLockedIpcrModal`) for viewing final locked targets.
  * Removed all inputs, remarks, textareas, return buttons, and approval buttons. It displays only final targets, original/reviewed quantities, and chair remarks in a clean static grid.
  * Configured dynamic JavaScript loaders (`.open-view-locked-modal` handler) to populate this modal via AJAX.
