# Program Chair & Specialization Updates Summary

This document outlines all the modifications and feature implementations successfully integrated into the system, specifically focusing on the Program Chair Dashboard and the Faculty Specialization data structures.

## 1. Faculty Specialization Update
* **Database Integration:** Integrated the new `specialization` column into the backend queries for `tbl_employee_profiles`.
* **Admin Dashboard (HR Roster):** 
  * Added a `Specialization` column to the "HR Roster" table view.
  * Added a Specialization dropdown menu to the "Add/Edit Faculty" modal, containing the options: WST, DST, NST, and BSDS Programs.
* **Backend Saving Logic:** Updated `save_single_profile` and `import_csv_roster` in `models.py` to ensure that specialization data is correctly saved to the database. Updated the `/admin/faculty/save` route to correctly pass the new field.

## 2. Program Chair Dashboard Logic (Filtering & Allocation)
* **Identity Recognition:** The `/authenticate` login route now fetches the Program Chair's exact `specialization` and stores it securely in the user's session.
* **Visual Specialization Badge:** Added a dynamic UI badge on the Program Chair dashboard that proudly displays their recognized specialization (e.g., `WST Program`) alongside their Middle Manager designation.
* **Vertical Masking (Category Filtering):** Database queries for the Program Chair were restricted so that they only retrieve indicators belonging to `A. Instructions` and `B. Support Functions`. A label was added to Phase 1 of the dashboard to denote this scope.
* **Horizontal Masking (Specialization Alignment):** The dashboard completely filters out "College-Wide" constraints. It exclusively fetches and renders targets from `tbl_cascaded_quotas` that perfectly align with the logged-in Program Chair's specific specialization.
* **Security Assignment Bridge:** Developed the `/prog_chair/assign_target` endpoint. When the Chair assigns a target quantity, the system automatically looks up all active faculty members who share that exact specialization and commits the target directly into their personal `tbl_committed_targets` records.

## 3. Dean Dashboard & Core System Fixes
* **Connection Bug Fix:** Resolved the `OperationalError` (`CMySQLConnection object has no attribute 'connection'`) in the Dean's `/dean/cascade_quotas` and `/dean/batch_approve` routes by properly separating the connection and cursor variables, ensuring targets successfully save.
* **Global Notifications:** Added a Flask flash messaging block into `base.html` so that green success alerts (like when cascading quotas) and red error alerts correctly pop up across all dashboards in the system.
