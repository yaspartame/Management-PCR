# Refactoring Technical Report: Code Realignment (REFACTOR_0617)

This document discusses the updates applied to the Management-PCR backend logic on June 17, 2026, comparing the old implementation with the newly refactored versions.

---

## 🏗️ Architectural Rationale (DFD Level 2 Realignment)
The previous database implementation overloaded production/committed evaluation tables (`tbl_committed_targets` and `tbl_cascaded_quotas`) for intermediate workflows. This violates **DFD Level 2** separation of concerns.

To normalize the database architecture:
1. **Workload Distribution (Process 3)** is redirected to `tbl_draft_allocation`.
2. **RET Menu Configuration (Process 4)** is moved from overloaded quota rows to structural templates: `tbl_ret_rules` and `tbl_ret_rule_indicators`.
3. **Faculty Submission (Process 3/4 Lifecycle)** aggregates all draft allocations and selections into `tbl_draft_targets` (Staging Store) for manager approval, leaving `tbl_committed_targets` untouched.

---

## 💻 Comparative Code Analysis

### 1. `app/models/prog_chair.py`

#### Old Version
* Direct writes to the committed targets table with a `'Draft'` status.
```python
def get_assigned_quantity(cursor, term_id, indicator_id, faculty_ids):
    # ...
    query = f"""
        SELECT ct.assigned_quantity
        FROM tbl_committed_targets ct
        JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
        WHERE mi.term_id = %s AND ct.indicator_id = %s AND ct.emp_id IN ({format_strings})
        LIMIT 1
    """
    # ...

def save_chair_allocation(conn, cursor, term_id, indicator_id, assigned_quantity, faculty_ids):
    # ...
            if existing:
                update_query = "UPDATE tbl_committed_targets SET assigned_quantity = %s WHERE target_id = %s"
            else:
                insert_query = """
                    INSERT INTO tbl_committed_targets (emp_id, indicator_id, assigned_quantity, status)
                    VALUES (%s, %s, %s, 'Draft')
                """
```

#### Refactored Version
* Isolated allocation staging in `tbl_draft_allocation`.
```python
def get_assigned_quantity(cursor, term_id, indicator_id, faculty_ids):
    # ...
    query = f"""
        SELECT da.assigned_quantity
        FROM tbl_draft_allocation da
        JOIN tbl_master_indicators mi ON da.indicator_id = mi.indicator_id
        WHERE mi.term_id = %s AND da.indicator_id = %s AND da.emp_id IN ({format_strings})
        LIMIT 1
    """
    # ...

def save_chair_allocation(conn, cursor, term_id, indicator_id, assigned_quantity, faculty_ids):
    # ...
            if existing:
                update_query = "UPDATE tbl_draft_allocation SET assigned_quantity = %s WHERE allocation_id = %s"
            else:
                insert_query = """
                    INSERT INTO tbl_draft_allocation (emp_id, indicator_id, assigned_quantity)
                    VALUES (%s, %s, %s)
                """
```

---

### 2. `app/models/ret_chair.py`

#### Old Version
* Configured rank targets by injecting rank strings into the `assigned_to_role` column of the committed `tbl_cascaded_quotas` table.
```python
def save_ret_rule(conn, cursor, term_id, academic_rank, research_selections, extension_selections, research_indicator_ids, extension_indicator_ids):
    # ...
        for ind_id in research_indicator_ids:
            cursor.execute("INSERT INTO tbl_cascaded_quotas (term_id, indicator_id, total_target_value, assigned_to_role) VALUES (%s, %s, %s, %s)",
                           (term_id, ind_id, research_selections, academic_rank))
    # ...

def get_ret_rules(cursor, term_id):
    # ...
        SELECT cq.assigned_to_role, cq.total_target_value, mi.indicator_id, mi.indicator_description, tc.category_name
        FROM tbl_cascaded_quotas cq
        # ...
```

#### Refactored Version
* Relational configuration mapping using rules templates (`tbl_ret_rules`, `tbl_ret_rule_indicators`). Handles Research and Extension independently as separate rows to maintain individual required selection counts.
```python
def save_ret_rule(conn, cursor, term_id, academic_rank, research_selections, extension_selections, research_indicator_ids, extension_indicator_ids):
    # ...
        # Save Research rule
        if research_indicator_ids and int(research_selections) > 0:
            cursor.execute("INSERT INTO tbl_ret_rules (academic_rank, required_selections) VALUES (%s, %s)", 
                           (academic_rank, int(research_selections)))
            # Link indicators in tbl_ret_rule_indicators
            
        # Save Extension rule
        if extension_indicator_ids and int(extension_selections) > 0:
            cursor.execute("INSERT INTO tbl_ret_rules (academic_rank, required_selections) VALUES (%s, %s)", 
                           (academic_rank, int(extension_selections)))
            # Link indicators in tbl_ret_rule_indicators
    # ...

def get_ret_rules(cursor, term_id):
    # ...
        SELECT r.rule_id, r.academic_rank, r.required_selections, mi.indicator_id, mi.indicator_description, tc.category_name
        FROM tbl_ret_rules r
        JOIN tbl_ret_rule_indicators rri ON r.rule_id = rri.rule_id
        # ...
```

---

### 3. `app/models/faculty.py`

#### Old Version
* Directly fetched and saved targets using `tbl_committed_targets`.
```python
def get_faculty_assigned_targets(cursor, emp_id, term_id):
    query = "SELECT * FROM tbl_committed_targets WHERE emp_id = %s ..."
    # ...

def submit_faculty_ipcr(conn, cursor, emp_id, term_id):
    # Simply changed status flag on tbl_committed_targets
    cursor.execute("UPDATE tbl_committed_targets SET status = 'Pending Approval' ...")
```

#### Refactored Version
* Implements dynamic dashboard loading (switching target tables based on submission state) and transactionally consolidates draft components on submit.
```python
def get_faculty_assigned_targets(cursor, emp_id, term_id):
    # If submitted:
    #   Load and alias proposed_quantity from tbl_draft_targets
    # Else:
    #   Load pre-assigned targets from tbl_draft_allocation
    # ...

def submit_faculty_ipcr(conn, cursor, emp_id, selected_research_targets):
    # 1. Gather workloads from tbl_draft_allocation
    # 2. Write workloads to tbl_draft_targets as 'Pending Review'
    # 3. Write selected RET indicators to tbl_draft_targets as 'Pending Review'
    # 4. Clean up tbl_draft_allocation
```

---

### 4. `app/routes/faculty.py`

#### Old Version
* Wrote selections to production tables via deprecated helpers and passed `int(term_id)` to the submission method.
```python
@faculty_bp.route('/submit_ipcr', methods=['POST'])
def faculty_submit_ipcr():
    # ...
    save_faculty_ret_selections(conn, cursor, emp_id, int(term_id), [int(x) for x in selected_indicators])
    success, msg = submit_faculty_ipcr(conn, cursor, emp_id, int(term_id))
```

#### Refactored Version
* Corrects signature compatibility. Builds the targeted research payload from checkboxes, routes them transactionally, and checks `tbl_draft_targets` to determine lock state.
```python
@faculty_bp.route('/submit_ipcr', methods=['POST'])
def faculty_submit_ipcr():
    # ...
    selected_ret_targets = [{'indicator_id': int(x), 'proposed_quantity': 1} for x in selected_indicators]
    success, msg = submit_faculty_ipcr(conn, cursor, emp_id, selected_ret_targets)
```
