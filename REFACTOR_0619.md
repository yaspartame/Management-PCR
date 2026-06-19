# Refactoring Technical Report: Designated Faculty Dashboard Architecture (REFACTOR_0619)

This document details the refactoring changes applied on June 19, 2026, to resolve the relational database constraint and isolation issues on the Designated Faculty Dashboard.

---

## 🏗️ Architectural Rationale (Relational Scoping Isolation)

Previously, Designated Faculty submitted custom targets directly into `tbl_individual_targets`. This structure bypassed the standard DFD Level 2 review staging table `tbl_draft_targets` and introduced data isolation issues. 

However, writing custom text rows directly into `tbl_draft_targets` was blocked by a rigid foreign key constraint: `tbl_draft_targets.indicator_id` must reference a valid row in `tbl_master_indicators`.

### The Solution: Dynamic Upstream Insertion & Scoping Isolation
1. **Dynamic Upstream Insertion**: When a custom target is submitted by a designated faculty member, the backend transactionally inserts the target description into `tbl_master_indicators` first, obtains the generated `indicator_id`, and then links it to `tbl_draft_targets`.
2. **Scoping Isolation**: To prevent individual custom targets from leaking into the global baseline lists visible to Admins and Deans, we introduced the `is_custom` boolean flag. Standard baseline queries now explicitly filter out custom targets (`is_custom = 0`), while custom targets are marked with `is_custom = 1`.
3. **Quantity Preservation**: The refactoring supports variable target quantities for both standard selectable checklist items and custom ad-hoc targets.

---

## 💻 Comparative Code Analysis

### 1. `app/models/indicator.py`

#### Old Version
* Baseline queries fetched all indicators regardless of custom status, leading to baseline list pollution.
```python
def get_master_indicators(cursor, term_id):
    query = """
        SELECT mi.*, tc.category_name 
        FROM tbl_master_indicators mi
        LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE mi.term_id = %s
        ORDER BY tc.category_name, mi.indicator_id
    """
    # ...

def import_previous_term_indicators(conn, cursor, active_term_id):
    # ...
    cursor.execute("SELECT category_id, indicator_description, efficiency_type FROM tbl_master_indicators WHERE term_id = %s", (prev_term[0],))
    # ...
```

#### Refactored Version
* Filters out custom targets during baseline fetches and prevents custom targets from copying over to new academic terms during imports.
```python
def get_master_indicators(cursor, term_id):
    query = """
        SELECT mi.*, tc.category_name 
        FROM tbl_master_indicators mi
        LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE mi.term_id = %s AND mi.is_custom = 0
        ORDER BY tc.category_name, mi.indicator_id
    """
    # ...

def import_previous_term_indicators(conn, cursor, active_term_id):
    # ...
    # Exclude custom targets from import query
    cursor.execute("SELECT category_id, indicator_description, efficiency_type FROM tbl_master_indicators WHERE term_id = %s AND is_custom = 0", (prev_term[0],))
    # ...
    for ind in prev_indicators:
        cursor.execute(
            "INSERT INTO tbl_master_indicators (category_id, indicator_description, efficiency_type, term_id, is_custom) VALUES (%s, %s, %s, %s, 0)",
            (ind[0], ind[1], ind[2], active_term_id)
        )
```

---

### 2. `app/models/designated.py`

#### Old Version
* Directly wrote custom entries into `tbl_individual_targets` and read selectable targets from dean-cascaded quotas.
```python
def get_designated_cascaded_quotas(cursor, term_id):
    # Fetched from tbl_cascaded_quotas
    # ...

def insert_custom_target(cursor, emp_id, term_id, description, quantity, category):
    query = """
        INSERT INTO tbl_individual_targets 
        (emp_id, term_id, description, target_qty, category, status) 
        VALUES (%s, %s, %s, %s, %s, 'Pending')
    """
    cursor.execute(query, (emp_id, term_id, description, quantity, category))
    # ...
```

#### Refactored Version
* Replaces legacy endpoints. Loads selectable baseline indicators directly from `tbl_master_indicators` and processes multi-target transactional submissions preserving quantities.
```python
def get_designated_selectable_indicators(cursor, term_id):
    query = """
        SELECT mi.indicator_id, mi.indicator_description, tc.category_name
        FROM tbl_master_indicators mi
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE mi.term_id = %s 
          AND mi.is_custom = 0
          AND tc.category_name IN ('A. Instructions', 'Support Functions')
        ORDER BY tc.category_name, mi.indicator_id
    """
    # ...

def submit_designated_ipcr(conn, cursor, emp_id, term_id, selected_targets, custom_targets):
    # 1. Clear unverified submissions for this emp_id from tbl_draft_targets
    cursor.execute("DELETE FROM tbl_draft_targets WHERE emp_id = %s", (emp_id,))
    
    # 2. Insert standard selectable targets with custom quantities
    for target in selected_targets:
        cursor.execute("""
            INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
            VALUES (%s, %s, %s, 'Pending Review')
        """, (emp_id, target['indicator_id'], target['proposed_quantity']))
        
    # 3. Upstream provision custom targets and map relational ID downstream to tbl_draft_targets
    for custom in custom_targets:
        # Step A: Provision category
        # ...
        # Step B: Insert into tbl_master_indicators with is_custom = 1
        cursor.execute("""
            INSERT INTO tbl_master_indicators (category_id, indicator_description, efficiency_type, term_id, is_custom)
            VALUES (%s, %s, 'Output-Based', %s, 1)
        """, (category_id, text_clean, term_id))
        new_indicator_id = cursor.lastrowid
        # Step C: Write draft target link
        cursor.execute("""
            INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
            VALUES (%s, %s, %s, 'Pending Review')
        """, (emp_id, new_indicator_id, qty))
```

---

### 3. `app/routes/designated.py`

#### Old Version
* dashboard route loaded only cascaded quotas and provided a direct `/add-target` AJAX API.
```python
@designated_bp.route('/')
def designated_dashboard():
    # ...
    dpcr_targets = get_designated_cascaded_quotas(cursor, active_term['term_id'])
    # ...

@designated_bp.route('/add-target', methods=['POST'])
def add_custom_target():
    # AJAX write to tbl_individual_targets
    # ...
```

#### Refactored Version
* Loads submitted targets from `tbl_draft_targets` if they exist (rendering dashboard in read-only mode). Provides a unified `/submit` form POST handler.
```python
@designated_bp.route('/')
def designated_dashboard():
    # Check if submitted
    cursor.execute("SELECT COUNT(*) FROM tbl_draft_targets dt ...")
    has_submitted = cursor.fetchone()[0] > 0
    
    if has_submitted:
        # Load from tbl_draft_targets
    else:
        # Load selectable baseline DPCR targets
        
    return render_template('designated_dashboard.html', ..., has_submitted=has_submitted)

@designated_bp.route('/submit', methods=['POST'])
def submit_designated_ipcr_route():
    # Parse standard target selections and custom targets with their quantities
    # Call submit_designated_ipcr() model logic
```

---

### 4. `app/templates/designated_dashboard.html`

#### Old Version
* Submitted a target using AJAX immediately from the pop-up modal, and submitted checklist selections using GET with standard inputs.
```html
<form id="dpcrForm">
    <!-- Checkboxes lack names and submit action -->
    <input type="checkbox" class="form-check-input strategic-checkbox" value="{{ target.indicator_id }}">
</form>

<script>
    addTargetBtn.addEventListener('click', function() {
        // immediate POST AJAX fetch to designated.add_custom_target
    });
</script>
```

#### Refactored Version
* Submits standard and custom targets in a single unified request. Locks fields if submission is completed. Appends custom targets dynamically on the UI instead of database-writing AJAX calls.
```html
<form id="dpcrForm" action="{{ url_for('designated.submit_designated_ipcr_route') }}" method="POST">
    <!-- Name properties configured, disabled if has_submitted is true -->
    <input type="checkbox" name="selected_indicators[]" class="form-check-input strategic-checkbox" 
           value="{{ target.indicator_id }}" {% if has_submitted %}checked disabled{% endif %}>
</form>

<script>
    addTargetBtn.addEventListener('click', function() {
        // Dynamic DOM insertion of a new row containing hidden inputs:
        // name="custom_descriptions[]" and name="custom_quantities[]"
        // Also includes a visual delete button to remove row prior to submission.
    });
</script>
```
