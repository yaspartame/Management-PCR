# Phase 0: Architecture Context & Why We Are Refactoring

**To:** Antigravity  
**Objective:** Understand the structural changes made to the database schema and the engineering reasoning behind them.

---

## 📋 The Background
During our recent capstone progress presentation, the evaluation panel flagged several "circular dependencies" or visual loops on our Entity-Relationship Diagram (ERD). 

From a strict database engineering perspective, our schema did not contain true, destructive circular deadlocks because terminal tables like `tbl_employee_profiles` and `tbl_academic_terms` do not have outgoing foreign keys[cite: 2]. Instead, what the panel saw were **convergent relationships**—visual triangles and diamonds formed when transactional tables inherit multiple keys from parent entities that are already related to one another[cite: 2]. 

To clear up the visual clutter on the ERD and satisfy the panel, we have implemented a structural database normalization cleanup across three specific areas:

### 1. Loop A (Target Context Triangle)
* **The Issue:** Previously, `tbl_committed_targets` (along with the draft and selection tables) explicitly stored both `indicator_id` and `term_id`[cite: 2]. However, every indicator inside `tbl_master_indicators` is already permanently bound to a specific academic term via its own `term_id` column[cite: 2]. Storing a local `term_id` inside the transactional target tables introduced a redundant data path[cite: 2].
* **The Database Change:** The `term_id` column and its foreign key constraints have been completely dropped from `tbl_committed_targets`, `tbl_draft_targets`, `tbl_draft_allocation`, and `tbl_addselect_targets`[cite: 2].
* **Your Mission:** Because `tbl_committed_targets` no longer possesses a local `term_id` field, any raw SQL queries executing `WHERE ct.term_id = %s` or attempting to insert a term value directly into these tables will crash with an unmapped column exception[cite: 1, 2]. You must refactor the model queries to perform an implicit or explicit SQL `JOIN` on `tbl_master_indicators` to validate or filter data by the active term frame[cite: 1, 2].

### 2. Loop B (RET Regulation Diamond)
* **The Issue:** `tbl_ret_rules` previously held an independent relationship with `tbl_academic_terms`[cite: 2]. 
* **The Database Change:** The `term_id` column has been dropped from `tbl_ret_rules`[cite: 2]. Since rules link to indicators via `tbl_ret_rule_indicators`, and indicators are already tied to a term, the rule inherits its term data transitively[cite: 2]. Our backend code (`app/models/ret_chair.py`) completely bypasses this table and manages requirements directly inside `tbl_cascaded_quotas`, meaning **zero code changes** are required on your end for Loop B.

### 3. Loop C (Co-Author Diamond)
* **The Issue:** A hard foreign key line mapped secondary contributors in `tbl_co_authors` back to `tbl_employee_profiles`, creating an ERD diamond[cite: 2].
* **The Database Change:** The formal database-level constraint line has been dropped to clear the visual line from the diagram[cite: 2]. The table safely retains a loose `emp_id` integer column, which we will now handle entirely via application-level loose binding[cite: 2]. No backend code structures are broken by this shift.

---

## 🛠️ Your Codebase Action Items
Because our web application isolates SQL commands inside dedicated model modules rather than mixing database scripts directly into route controllers, the impact of these schema changes is entirely localized to three model files. The routes and HTML view templates do not directly execute raw SQL text strings, meaning your changes will remain completely contained within the model layer[cite: 1].