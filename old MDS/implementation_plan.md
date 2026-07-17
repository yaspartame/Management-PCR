# Program Chair Dashboard — Implementation Plan ✅ Ready for Execution

## Overview

This plan covers two major feature areas for the **Program Chair** role:

1. **Commitments Management** — Make the existing Phase 2 "Commitments" section fully functional with real DB data, per-row edit capability with a remarks textbox, and approve/reject actions.
2. **Draft IPCR Review Process** — When a Regular Faculty member submits a Draft IPCR (writes to `tbl_draft_targets` via Process 5.2/5.3), it automatically appears on the matching Program Chair's dashboard **scoped by specialization** (WST / DST / NST). The Program Chair can review, edit commitment quantities with remarks, and approve or reject the draft.

### DFD Reference (Process 5.0)
| Process | Actor | Action | Table |
|---|---|---|---|
| 5.2 / 5.3 | Regular Faculty | Adds & submits consolidated targets | `tbl_draft_targets` |
| 5.4 | Program Chair | Verifies, edits (with remarks), approves/rejects | **New tables below** |
| 5.5 | RET Chair | Commits final targets | `tbl_committed_targets` *(out of scope)* |

> The faculty's original submission in `tbl_draft_targets` is **never overwritten**. The Program Chair's review, edits, and remarks live in two separate new tables.

---

## Confirmed Design Decisions

| # | Question | Answer |
|---|---|---|
| 1 | Specialization strings | ✅ Confirmed: `WST Program`, `DST Program`, `NST Program` |
| 2 | Edit scope | ✅ Chair can only edit **quantities** — no adding/removing indicators |
| 3 | Rejection UX | ✅ Faculty stays in **"Returned"** status (draft remains locked/visible) until they manually re-submit |

> [!IMPORTANT]
> **Two New Tables Required** — Run the migration SQL in Component 1 before any code changes begin.

---

## Proposed Changes

---

### Component 1 — Database Migration

#### [NEW] Two New Tables

**`tbl_ipcr_chair_review`** — One record per faculty per term review session (the overall decision):

```sql
CREATE TABLE tbl_ipcr_chair_review (
    review_id        INT AUTO_INCREMENT PRIMARY KEY,
    emp_id           INT NOT NULL,          -- faculty being reviewed
    term_id          INT NOT NULL,
    chair_emp_id     INT NOT NULL,          -- the program chair who reviewed
    overall_status   ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    overall_remarks  TEXT NULL,             -- overall note from program chair
    reviewed_at      TIMESTAMP NULL,        -- set when decision is made
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_review (emp_id, term_id) -- one review per faculty per term
);
```

**`tbl_ipcr_chair_review_items`** — One record per target row the chair reviewed/edited:

```sql
CREATE TABLE tbl_ipcr_chair_review_items (
    item_id            INT AUTO_INCREMENT PRIMARY KEY,
    review_id          INT NOT NULL,        -- FK → tbl_ipcr_chair_review
    draft_id           INT NOT NULL,        -- FK → tbl_draft_targets (read-only reference)
    indicator_id       INT NOT NULL,
    original_quantity  INT NOT NULL,        -- copied from tbl_draft_targets at review time
    reviewed_quantity  INT NOT NULL,        -- chair's adjusted value (starts equal to original)
    item_remarks       VARCHAR(1000) NULL,  -- chair's note on this specific line edit
    FOREIGN KEY (review_id) REFERENCES tbl_ipcr_chair_review(review_id) ON DELETE CASCADE
);
```

**Flow logic:**
- When the Program Chair **opens** a faculty's IPCR for review → a `tbl_ipcr_chair_review` record is created/fetched (`overall_status = 'Pending'`), and `tbl_ipcr_chair_review_items` rows are pre-populated by copying from `tbl_draft_targets`.
- When the chair **edits a row** → only `tbl_ipcr_chair_review_items.reviewed_quantity` and `item_remarks` are updated.
- When the chair **approves or rejects** → `tbl_ipcr_chair_review.overall_status` and `overall_remarks` are updated, and `reviewed_at` is stamped.
- `tbl_draft_targets` is **never modified** by the Program Chair.

---

### Component 2 — Model Layer

#### [MODIFY] [prog_chair.py](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/models/prog_chair.py)

Add the following functions:

| Function | Purpose |
|---|---|
| `get_pending_draft_ipcrs(cursor, specialization, term_id)` | Returns all faculty members under `specialization` who have submitted draft targets (`tbl_draft_targets`) for the term, joined with their `tbl_ipcr_chair_review` status. Faculty with no review record yet are treated as "Pending". |
| `get_pending_drafts_count(cursor, specialization, term_id)` | Returns integer count of pending reviews (for the overview stats card). |
| `get_or_create_chair_review(conn, cursor, emp_id, term_id, chair_emp_id)` | Fetches existing `tbl_ipcr_chair_review` record or creates one and pre-populates `tbl_ipcr_chair_review_items` from `tbl_draft_targets`. Returns `review_id`. |
| `get_review_items(cursor, review_id)` | Returns all `tbl_ipcr_chair_review_items` for a review, joined with `tbl_master_indicators` for description and `tbl_target_categories` for category name. |
| `update_review_item(conn, cursor, item_id, reviewed_quantity, item_remarks)` | Updates a single `tbl_ipcr_chair_review_items` row's quantity and remark. |
| `decide_chair_review(conn, cursor, review_id, action, overall_remarks)` | Sets `overall_status = 'Approved'` or `'Rejected'` and stamps `reviewed_at`. If rejected, also clears `review_status` back to `'Draft'` on the linked `tbl_draft_targets` rows so faculty can re-submit. |

---

### Component 3 — Route Layer

#### [MODIFY] [prog_chair.py (routes)](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/routes/prog_chair.py)

| Route | Method | Purpose |
|---|---|---|
| `GET /prog_chair/` | GET | **Extend existing** — also load `pending_drafts` list and `pending_drafts_count` and pass to template |
| `GET /prog_chair/review_ipcr/<int:emp_id>` | GET | AJAX endpoint — calls `get_or_create_chair_review()` then `get_review_items()`, returns JSON for modal population |
| `POST /prog_chair/edit_review_item` | POST | Accepts `item_id`, `reviewed_quantity`, `item_remarks` — calls `update_review_item()` |
| `POST /prog_chair/decide_ipcr` | POST | Accepts `review_id`, `action` (approve/reject), `overall_remarks` — calls `decide_chair_review()` |

---

### Component 4 — Template (Program Chair Dashboard)

#### [MODIFY] [prog_chair_dashboard.html](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/templates/prog_chair_dashboard.html)

**A. Overview Stats Card**
- Replace hardcoded `"4"` in the "Pending Drafts" card with live `{{ pending_drafts_count }}`.

**B. Phase 2: Commitments Section — Full Replacement**

Replace the static table in `#nav-phase2` with a live table built from `pending_drafts`:

| Column | Source |
|---|---|
| Faculty Name | `tbl_employee_profiles` |
| Rank | `academic_rank` |
| Proposed Targets | Count of `tbl_draft_targets` rows for that faculty |
| Chair Review Status | Badge from `tbl_ipcr_chair_review.overall_status` — `Pending` (yellow) / `Approved` (green) / `Rejected` (red) / `Not Yet Reviewed` (grey) |
| Actions | **View / Review** button → triggers modal |

**C. New Review Modal (`#reviewIpcrModal`)**

A Bootstrap modal triggered per row, with two sections:

**Section 1 — Target Items Table**

| Column | Detail |
|---|---|
| Category | From `tbl_target_categories` |
| Indicator | From `tbl_master_indicators.indicator_description` |
| Original Qty | `original_quantity` (read-only, greyed out — chair cannot add/remove rows) |
| Reviewed Qty | `<input type="number" min="0">` — only quantity is editable |
| Item Remarks | `<textarea rows="2">` (labeled "Remarks on this change") — optional per-row note |
| Action | **Save** button per row → `POST /prog_chair/edit_review_item` |

**Section 2 — Overall Decision Panel**

- `<textarea id="overallRemarks" required>` — labeled **"Remarks / Reason"** (required for both Approve and Reject so the chair always documents their decision)
- **Approve** button (green, `bi-check-circle`) → `POST /prog_chair/decide_ipcr` with `action=approve`
- **Reject / Return to Faculty** button (red, `bi-arrow-counterclockwise`) → `POST /prog_chair/decide_ipcr` with `action=reject` — the `overall_remarks` field is especially critical here as it tells the faculty what to fix

The modal is populated via a `fetch()` call to `GET /prog_chair/review_ipcr/<emp_id>` on button click.

---

### Component 5 — Faculty Feedback Loop

#### [MODIFY] [faculty_dashboard.html](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/templates/faculty_dashboard.html)

After Program Chair rejection (`overall_status = 'Rejected'`):
- Status badge changes to **"Returned by Program Chair"** (red/danger) — remains in this state until the faculty manually clicks re-submit
- Display a prominent **alert box** showing `overall_remarks` from `tbl_ipcr_chair_review` (the rejection reason the chair entered)
- Display per-item `item_remarks` inline beside each affected target row so the faculty can see which specific quantities were flagged
- **Re-enable the Submit button** (labeled "Re-submit for Review") so the faculty can correct and re-send
- Quantities displayed to the faculty remain the **original** ones from `tbl_draft_targets` — the chair's reviewed quantity is advisory/internal until approved

#### [MODIFY] [faculty.py (routes)](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/routes/faculty.py)

- `faculty_dashboard()`: additionally query `tbl_ipcr_chair_review` for the current faculty/term to get `overall_status` and `overall_remarks` and pass to template.
- Update `has_submitted` logic: a status of `'Rejected'` should unlock the form (treat as not submitted).

#### [MODIFY] [faculty.py (models)](file:///c:/Users/Nitro%205/Documents/Capstone%20system/Management-PCR/app/models/faculty.py)

- `get_faculty_assigned_targets()`: add a LEFT JOIN on `tbl_ipcr_chair_review_items` to surface `item_remarks` alongside each target row.
- `submit_faculty_ipcr()`: on re-submission, **delete** the old `tbl_ipcr_chair_review` + cascade-delete `tbl_ipcr_chair_review_items` records for that `emp_id + term_id`, then re-write `tbl_draft_targets` rows with `review_status = 'Pending Review'` as before.

---

## Verification Plan

### Step 1 — DB
Run `DESCRIBE tbl_ipcr_chair_review` and `DESCRIBE tbl_ipcr_chair_review_items` to confirm tables created correctly.

### Step 2 — Happy Path (Approve)
1. Login as **Regular Faculty** (e.g., WST specialization) → Submit Draft IPCR.
2. Login as **WST Program Chair** → Commitments tab shows the faculty with `Pending` badge.
3. Chair clicks **View / Review** → modal opens with all target rows loaded.
4. Chair edits one row's quantity, enters an item remark → clicks **Save Edit**.
5. Confirm `tbl_ipcr_chair_review_items` row updated; `tbl_draft_targets` unchanged.
6. Chair enters overall remarks → clicks **Approve**.
7. Confirm `tbl_ipcr_chair_review.overall_status = 'Approved'`.
8. Faculty dashboard shows **"Approved by Program Chair"** status.

### Step 3 — Reject and Re-submit
1. Chair clicks **Reject / Return to Faculty** with remarks.
2. Faculty dashboard shows **"Returned by Program Chair"** + remarks visible + Submit button re-enabled.
3. Faculty re-submits → old review records deleted → Chair sees `Pending` again.

### Step 4 — Specialization Isolation
1. Login as **DST Program Chair** → verify they see **zero** records from WST faculty.
2. Login as **NST Program Chair** → same isolation check.
