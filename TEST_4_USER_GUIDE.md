# Test 4 - User Quick Reference Guide

## Quick Start

### Accessing New Features

1. **Login** to the application as admin
2. Click **"Админ"** (Admin) button in main menu
3. Look for new buttons in the admin panel:
   - **Продвинутая группировка** - Advanced Grouping
   - **Представления** - Views Manager
   - **Материализованные** - Materialized Views
   - **CTE конструктор** - CTE Builder

---

## 1. Advanced Grouping (Продвинутая группировка)

### What It Does
Creates summary reports with subtotals and aggregations.

### Quick Steps
1. Select **table** from dropdown
2. Choose **grouping type**:
   - Simple GROUP BY - Basic grouping
   - ROLLUP - Hierarchical subtotals (e.g., by user, then by state)
   - CUBE - All possible combinations of subtotals
   - GROUPING SETS - Custom grouping combinations
3. **Select columns** for grouping (hold Ctrl for multiple)
4. Add **aggregate function**:
   - Choose function (COUNT, SUM, AVG, MIN, MAX)
   - Choose column (or * for COUNT)
   - Click "Add Aggregate"
5. Click **"Generate SQL"** to preview
6. Click **"Execute Query"** to see results

### Example Use Case
**Question**: "How many domains does each user have, grouped by state?"

**Steps**:
- Table: `tracked_domain`
- Grouping: ROLLUP
- Columns: `user_id`, `current_state`
- Aggregate: COUNT(*)
- Result shows: totals per user+state, totals per user, and grand total

---

## 2. Views Manager (Представления)

### What It Does
Create saved queries (views) that act like virtual tables.

### Quick Steps to Create
1. Click **"Create New View"**
2. Enter **view name** (e.g., `my_summary`)
3. Enter **SELECT query** (without CREATE VIEW):
   ```sql
   SELECT domain, current_state FROM tracked_domain
   ```
4. Click **"Create"**

### Other Operations
- **Refresh List** - Update views list
- **View Data** - See what's in the view (select view first)
- **View Definition** - See the SQL query
- **Drop View** - Delete view (with confirmation)

### Example Use Case
Create a view for frequently-used complex query:
```sql
-- View: active_domain_users
SELECT u.login, d.domain, d.submitted_at
FROM tracked_domain d
JOIN app_user u ON d.user_id = u.id
WHERE d.current_state = 'active'
```

Now query it anytime: `SELECT * FROM active_domain_users`

---

## 3. Materialized Views (Материализованные)

### What It Does
Like regular views, but stores the data physically for faster access. Must refresh manually when data changes.

### When to Use
- Complex reports that are slow to calculate
- Dashboard statistics
- Snapshots of data at specific times
- Data that doesn't change often

### Quick Steps to Create
1. Click **"Create Materialized View"**
2. Enter **name** (e.g., `daily_stats`)
3. Enter **SELECT query**:
   ```sql
   SELECT DATE(submitted_at) as day, COUNT(*) as total
   FROM tracked_domain
   GROUP BY DATE(submitted_at)
   ```
4. Click **"Create"**

### Refreshing Data
When underlying data changes:
1. Select the materialized view
2. Click **"REFRESH Data"**
3. View is updated with current data

### Other Operations
- **View Data** - See stored results
- **View Definition** - See the SQL
- **Drop** - Delete materialized view

---

## 4. CTE Builder (CTE конструктор)

### What It Does
Build complex queries by breaking them into named parts (Common Table Expressions).

### Quick Steps
1. **Define first CTE**:
   - Enter name: `step1`
   - Enter SELECT query
   - Click "Add CTE"
2. **Define more CTEs** (optional):
   - Each CTE can use previous CTEs
3. **Enter main query**:
   - Use CTE names like table names
4. Click **"Generate Complete SQL"**
5. Click **"Execute Query"**

### Example: Multi-Step Analysis

**Goal**: Find users with more than 2 domains

**Step 1 - CTE**: Count domains per user
```
CTE Name: user_counts
Query: SELECT user_id, COUNT(*) as cnt FROM tracked_domain GROUP BY user_id
```

**Step 2 - CTE**: Filter active users
```
CTE Name: active_users
Query: SELECT user_id FROM user_counts WHERE cnt > 2
```

**Step 3 - Main Query**: Get user details
```
SELECT u.login, uc.cnt
FROM active_users au
JOIN user_counts uc ON au.user_id = uc.user_id
JOIN app_user u ON au.user_id = u.id
```

### Recursive CTE
Check the **"Recursive"** checkbox for queries like:
- Hierarchies (org charts, categories)
- Number sequences
- Tree traversal

### Managing CTEs
- **Edit Selected** - Modify existing CTE
- **Delete Selected** - Remove CTE
- **Clear All** - Start over

---

## Common Workflows

### Workflow 1: Monthly Report
1. **Materialized View**: Create monthly stats view
2. **Schedule**: Refresh at start of month
3. **Dashboard**: Query materialized view instantly

### Workflow 2: Complex Analysis
1. **CTE Builder**: Break analysis into steps
2. **Test**: Run query
3. **Save**: Convert to regular view if needed

### Workflow 3: Multidimensional Report
1. **Advanced Grouping**: Use CUBE for all combinations
2. **Review**: Check subtotals at all levels
3. **Export**: Copy results from table

---

## Tips & Tricks

### Advanced Grouping
- **ROLLUP order matters**: First column creates main groups, second creates subgroups
- **CUBE** can create many rows: Use with few columns (2-3 max)
- **GROUPING SETS**: Type one column per line, or comma-separated for combinations

### Views
- **Use for security**: Hide sensitive columns
- **Use for simplicity**: Hide complex JOINs from users
- **Update anytime**: CREATE OR REPLACE overwrites existing view

### Materialized Views
- **Refresh regularly**: Set up schedule based on data change frequency
- **Index them**: Ask admin to add indexes for better performance
- **Compare**: Regular view (slow but always current) vs Materialized (fast but needs refresh)

### CTE
- **Name clearly**: Use descriptive names like `active_users` not `temp1`
- **One concept per CTE**: Break down one logical step at a time
- **Test incrementally**: Add one CTE, test main query, then add next

---

## Troubleshooting

### Error: "Table not found"
- Check schema name (should be `app`)
- Refresh table list if you just created table

### Error: "Column not found in GROUP BY"
- All non-aggregate columns must be in GROUP BY
- Or add aggregate function (COUNT, SUM, etc.)

### Materialized View not updating
- Did you click **"REFRESH Data"**?
- Data won't change until you refresh

### CTE error: "Relation does not exist"
- Make sure main query uses CTE name exactly as defined
- CTE names are case-sensitive in quotes

### Slow query
- Check number of rows (limited to 1000 by default)
- Consider creating materialized view for expensive queries
- Use EXPLAIN (ask admin) to analyze query

---

## Keyboard Shortcuts

- **Ctrl+Click** - Select multiple items in lists
- **Esc** - Close current dialog
- **Enter** - Execute in text fields

---

## Getting Help

If you encounter issues:
1. Check error message in red popup
2. Verify your SQL syntax
3. Test simpler query first
4. Ask admin for permissions check

---

## Examples Library

### Example 1: User Activity Summary (ROLLUP)
```
Table: tracked_domain
Grouping: ROLLUP
Columns: user_id, current_state
Aggregate: COUNT(*)

Shows:
- Domains per user+state
- Total per user
- Grand total
```

### Example 2: Dashboard View
```
View Name: dashboard_summary
Query:
SELECT
  DATE(submitted_at) as date,
  current_state,
  COUNT(*) as count
FROM tracked_domain
GROUP BY DATE(submitted_at), current_state
ORDER BY date DESC
```

### Example 3: Performance Snapshot (Materialized)
```
Name: performance_snapshot
Query:
SELECT
  domain,
  AVG(packets_per_s) as avg_packets,
  MAX(uniq_ips) as max_ips
FROM metric_sample
GROUP BY domain
```

### Example 4: Multi-Level Analysis (CTE)
```
CTE 1 (domain_metrics):
SELECT domain_id, AVG(packets_per_s) as avg_traffic
FROM metric_sample
GROUP BY domain_id

CTE 2 (high_traffic):
SELECT domain_id FROM domain_metrics WHERE avg_traffic > 5000

Main Query:
SELECT d.domain, dm.avg_traffic
FROM high_traffic ht
JOIN domain_metrics dm ON ht.domain_id = dm.domain_id
JOIN tracked_domain d ON ht.domain_id = d.id
```

---

## Summary

- **Advanced Grouping**: Multidimensional reports with subtotals
- **Views**: Save complex queries as virtual tables
- **Materialized Views**: Fast access to expensive queries (needs refresh)
- **CTE Builder**: Break complex queries into readable steps

All features work **without writing SQL manually** - just fill forms and click buttons!
