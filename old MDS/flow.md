# IPCR Target Lifecycle & Database Flow

This document outlines the target creation, review, rejection, approval, and locking flow, detailing where the data comes from and where it is stored in the database.

## Database Table Flow Diagram

```mermaid
flowchart TD
    %% Style definitions
    classDef config fill:#f9f5ff,stroke:#7F56D9,stroke-width:2px,color:#000;
    classDef draft fill:#eff8ff,stroke:#175CD3,stroke-width:2px,color:#000;
    classDef review fill:#fff1f3,stroke:#D11A2A,stroke-width:2px,color:#000;
    classDef final fill:#edfcf2,stroke:#039855,stroke-width:2px,color:#000;

    %% Nodes
    tbl_master_indicators["tbl_master_indicators<br/>(Master Indicators List)"]:::config
    tbl_ret_rules["tbl_ret_rules &<br/>tbl_ret_rule_indicators<br/>(RET Target Rules by Rank)"]:::config
    tbl_draft_allocation["tbl_draft_allocation<br/>(Distributed Workloads)"]:::draft
    tbl_draft_targets["tbl_draft_targets<br/>(Proposed/Draft Targets)"]:::draft
    tbl_ipcr_chair_review["tbl_ipcr_chair_review<br/>(Review Session Header)"]:::review
    tbl_ipcr_chair_review_items["tbl_ipcr_chair_review_items<br/>(Review Session Items)"]:::review
    tbl_committed_targets["tbl_committed_targets<br/>(Locked Final Targets)"]:::final

    %% Flow transitions
    tbl_master_indicators -->|1. Setup baseline workloads| tbl_draft_allocation
    
    tbl_draft_allocation -->|2. Submit Draft IPCR (Instruction/Support)| tbl_draft_targets
    tbl_master_indicators -->|2. Submit Draft IPCR (RET Selection)| tbl_draft_targets
    tbl_ret_rules -->|2. Validate RET targets based on rank| tbl_draft_targets
    
    tbl_draft_targets -->|3. Open Review Session (Copy Drafts)| tbl_ipcr_chair_review_items
    tbl_draft_targets -.->|3. Link review header| tbl_ipcr_chair_review
    
    tbl_ipcr_chair_review_items -->|4a. Chair rejects / returns| tbl_draft_targets
    tbl_ipcr_chair_review -->|4a. Set status to 'Rejected'| tbl_draft_targets
    
    tbl_ipcr_chair_review_items -->|4b. Chair approves (Sync Quantities)| tbl_draft_targets
    tbl_ipcr_chair_review -->|4b. Set status to 'Approved'| tbl_draft_targets
    
    tbl_draft_targets -->|5. Faculty locks IPCR| tbl_committed_targets
    tbl_ipcr_chair_review_items -->|5. Coalesce final quantities| tbl_committed_targets
```

---


## 1. Workload Distribution (Initial State)
- **Action**: The Program Chair distributes standard workloads (Instruction & Support Functions) to the faculty.
- **Source**: Baseline indicators are loaded from `tbl_master_indicators`.
- **Storage**: Targets are written to `tbl_draft_allocation`.
  - *Schema*: `(allocation_id, emp_id, indicator_id, assigned_quantity)`

---

## 2. Draft Submission
- **Action**: The Faculty member views their dashboard, selects Research and Extension targets, and clicks **Submit IPCR for Approval**.
- **Processing**:
  - Standard workloads are loaded from `tbl_draft_allocation`.
  - Research & Extension options are loaded from `tbl_master_indicators` based on rules in `tbl_ret_rules` and `tbl_ret_rule_indicators` matching the faculty's rank.
  - Prior reviews for this employee are deleted: `DELETE FROM tbl_ipcr_chair_review` and `DELETE FROM tbl_ipcr_chair_review_items`.
  - Relocates all pre-allocated workloads and RET selections into the staging draft table.
  - Clears `tbl_draft_allocation` for the employee.
- **Source**: `tbl_draft_allocation`, `tbl_master_indicators`, `tbl_ret_rules`.
- **Storage**: `tbl_draft_targets` with status `'Pending Review'`.
  - *Schema*: `(draft_id, emp_id, indicator_id, proposed_quantity, review_status)`

---

## 3. Review Staging & Editing
- **Action**: The Program Chair opens the faculty member's IPCR review modal.
- **Processing**:
  - Creates a review session header in `tbl_ipcr_chair_review`.
  - Pre-populates `tbl_ipcr_chair_review_items` by copying all rows from `tbl_draft_targets` that have `'Pending Review'` status.
  - If the review header already exists, a sync query copies over any missing draft targets.
  - As the Chair edits quantities or remarks, individual review items are updated.
- **Source**: `tbl_draft_targets`.
- **Storage**: 
  - `tbl_ipcr_chair_review` (status starts as `'Pending'`)
    - *Schema*: `(review_id, emp_id, term_id, chair_emp_id, overall_status, overall_remarks, reviewed_at)`
  - `tbl_ipcr_chair_review_items`
    - *Schema*: `(item_id, review_id, draft_id, indicator_id, original_quantity, reviewed_quantity, item_remarks)`

---

## 4. Rejection / Return to Faculty
- **Action**: The Program Chair rejects the IPCR and returns it to the faculty member.
- **Processing**:
  - Sets `overall_status` in `tbl_ipcr_chair_review` to `'Rejected'`.
  - Updates all rows in `tbl_draft_targets` for the employee to `'Returned'` status.
- **Faculty Dash Effect**: The Faculty dashboard shows the returned alert with remarks. The checklists and submit button are unlocked (`has_submitted` set to `False`) to allow changes.
- **Source**: Program Chair input.
- **Storage**: `tbl_ipcr_chair_review` (status updated to `'Rejected'`), `tbl_draft_targets` (status updated to `'Returned'`).

---

## 5. Re-submission
- **Action**: The Faculty member adjusts targets and submits again.
- **Processing**:
  - Triggering the submit pipeline deletes the existing `tbl_ipcr_chair_review` and `tbl_ipcr_chair_review_items` records for that employee to clear out the rejection history.
  - Draft items in `tbl_draft_targets` are reset to `'Pending Review'`.
- **Source**: Faculty checklists.
- **Storage**: `tbl_draft_targets` (reset to `'Pending Review'`), deletes `tbl_ipcr_chair_review` and `tbl_ipcr_chair_review_items`.

---

## 6. Approval
- **Action**: The Program Chair reviews the re-submitted IPCR and clicks **Approve**.
- **Processing**:
  - Sets `overall_status` in `tbl_ipcr_chair_review` to `'Approved'`.
  - Finalizes the proposed quantities in `tbl_draft_targets` to match the finalized `reviewed_quantity` from the `tbl_ipcr_chair_review_items` table.
- **Faculty Dash Effect**: The Faculty member's dashboard displays the approved alert and unlocks the **Lock My IPCR** form.
- **Source**: `tbl_ipcr_chair_review_items`.
- **Storage**: `tbl_ipcr_chair_review` (status updated to `'Approved'`), `tbl_draft_targets` (quantities synced).

---

## 7. Locking and Final Committing
- **Action**: The Faculty member clicks **Lock My IPCR**.
- **Processing**:
  - Verifies that `tbl_ipcr_chair_review` is `'Approved'`.
  - Deletes any existing rows in `tbl_committed_targets` for the employee and term.
  - Copies all targets directly from `tbl_draft_targets` into `tbl_committed_targets`.
  - Flips all rows in `tbl_draft_targets` to `'Approved'`.
- **Source**: `tbl_draft_targets`, `tbl_ipcr_chair_review`.
- **Storage**: `tbl_committed_targets` (production target table), `tbl_draft_targets` (status set to Approved).
  - *Schema*: `(target_id, emp_id, indicator_id, assigned_quantity, status)`

---

## 8. Accomplishments & Evidence Gathering
- **Action**: The Faculty member views the **Evidence Gathering** section, uploads files, and enters actual accomplished numbers.
- **Processing**:
  - The dashboard verifies locking status by checking if committed targets exist for this user in `tbl_committed_targets`.
  - If locked, the lists of targets are loaded directly from `tbl_committed_targets`.
  - Faculty inputs actual accomplishments and uploads files.
- **Source**: `tbl_committed_targets`, `tbl_master_indicators`.
- **Storage**: Accomplishments and file uploads are collected (Phase 3 submissions staging/mock store).
