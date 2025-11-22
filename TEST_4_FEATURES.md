# Test 4 - Advanced SQL Features Implementation

This document describes the implementation of four new advanced SQL modules added to the Domain DDoS Monitoring application.

## Overview

Four new modules have been integrated into the Admin panel:

1. **Advanced Grouping (ROLLUP, CUBE, GROUPING SETS)**
2. **Views Manager**
3. **Materialized Views Manager**
4. **CTE (Common Table Expressions) Builder**

## 1. Advanced Grouping Dialog

**File**: `src/advanced_grouping_dialog.py`

### Features

This module provides a GUI interface for creating multidimensional aggregated reports without manually writing SQL.

#### Grouping Types Supported:
- **Simple GROUP BY**: Standard grouping by selected columns
- **ROLLUP**: Creates subtotals for hierarchical data (order matters)
- **CUBE**: Creates subtotals for all possible combinations of dimensions
- **GROUPING SETS**: Custom grouping sets defined by the user

#### Key Capabilities:
- Select table from schema
- Choose multiple columns for grouping (order preserved for ROLLUP)
- Select grouping type via radio buttons
- Add aggregate functions (COUNT, SUM, AVG, MIN, MAX)
- Support for COUNT(*) and column-specific aggregates
- For GROUPING SETS: custom configuration via text input (e.g., "col1", "col2", "col1,col2")
- Generate and preview SQL before execution
- Execute and display results in table

#### Usage Example:
1. Select a table (e.g., `app.tracked_domain`)
2. Choose grouping type (e.g., ROLLUP)
3. Select columns for grouping (e.g., user_id, current_state)
4. Add aggregate function (e.g., COUNT(*))
5. Click "Generate SQL" to preview
6. Click "Execute Query" to see results

Generated SQL example:
```sql
SELECT "user_id", "current_state", COUNT(*)
FROM app.tracked_domain
GROUP BY ROLLUP("user_id", "current_state")
ORDER BY 1
```

## 2. Views Manager

**File**: `src/views_manager_dialog.py`

### Features

Complete management interface for PostgreSQL views without manual SQL writing.

#### Capabilities:
- **Create New View**: Define view name and SELECT query via form
- **Refresh List**: Update the list of existing views
- **View Data**: Display data from selected view (up to 1000 rows)
- **View Definition**: Show the SQL definition of selected view
- **Drop View**: Delete selected view with confirmation

#### Usage Example:
1. Click "Create New View"
2. Enter view name: `domain_summary`
3. Enter SELECT query:
   ```sql
   SELECT domain, current_state, COUNT(*) as count
   FROM tracked_domain
   GROUP BY domain, current_state
   ```
4. Click "Create" - view is automatically created
5. Select view from list and click "View Data" to see results
6. Use "View Definition" to see the stored SQL

#### Features:
- Uses `CREATE OR REPLACE VIEW` for safe creation
- Reads views from `information_schema.views`
- Full CRUD operations via buttons only
- No manual SQL required

## 3. Materialized Views Manager

**File**: `src/materialized_views_dialog.py`

### Features

Management interface specifically for PostgreSQL materialized views with refresh capability.

#### Capabilities:
- **Create Materialized View**: Define name and query via form
- **Refresh List**: Update list of existing materialized views
- **REFRESH Data**: Execute `REFRESH MATERIALIZED VIEW` to update cached data
- **View Data**: Display current cached data (up to 1000 rows)
- **View Definition**: Show the SQL definition
- **Drop**: Delete materialized view with confirmation

#### Key Differences from Regular Views:
- Stores query results physically (cached)
- Requires manual refresh to update data
- Better performance for complex queries
- Uses `pg_matviews` system catalog

#### Usage Example:
1. Click "Create Materialized View"
2. Enter name: `domain_stats_snapshot`
3. Enter SELECT query:
   ```sql
   SELECT domain, current_state, COUNT(*) as total,
          MAX(submitted_at) as last_added
   FROM tracked_domain
   GROUP BY domain, current_state
   ```
4. Click "Create"
5. Later, when data changes, select the view and click "REFRESH Data"
6. Click "View Data" to see the cached results

#### Use Cases:
- Dashboard reports with complex aggregations
- Historical snapshots
- Performance optimization for expensive queries
- Analytics that don't need real-time data

## 4. CTE Builder

**File**: `src/cte_builder_dialog.py`

### Features

Visual constructor for Common Table Expressions (WITH queries) allowing complex query building without manual SQL.

#### Capabilities:
- **Define Multiple CTEs**: Create several temporary named result sets
- **Recursive CTE Support**: Checkbox to mark CTE as recursive
- **CTE Management**: Add, edit, and delete CTEs via forms
- **Main Query**: Define the final query that uses the CTEs
- **SQL Generation**: Automatically builds complete WITH clause
- **Execute**: Run the generated query and display results

#### Key Features:
- Store CTEs as named temporary tables
- Support for both regular and recursive CTEs
- Automatic WITH/WITH RECURSIVE clause generation
- Visual CTE list with edit/delete buttons
- Preview generated SQL before execution

#### Usage Example:

**Example 1: Simple CTE**
1. Enter CTE name: `active_domains`
2. Enter query:
   ```sql
   SELECT * FROM app.tracked_domain WHERE current_state = 'active'
   ```
3. Click "Add CTE"
4. Enter main query:
   ```sql
   SELECT domain, COUNT(*) FROM active_domains GROUP BY domain
   ```
5. Click "Generate Complete SQL"
6. Review generated SQL:
   ```sql
   WITH
     active_domains AS (
       SELECT * FROM app.tracked_domain WHERE current_state = 'active'
     )
   SELECT domain, COUNT(*) FROM active_domains GROUP BY domain
   ```
7. Click "Execute Query"

**Example 2: Multiple CTEs**
1. Define CTE "users_with_domains":
   ```sql
   SELECT user_id, COUNT(*) as domain_count
   FROM app.tracked_domain
   GROUP BY user_id
   ```
2. Define CTE "active_users":
   ```sql
   SELECT user_id FROM users_with_domains WHERE domain_count > 2
   ```
3. Main query:
   ```sql
   SELECT u.login, uwd.domain_count
   FROM active_users au
   JOIN users_with_domains uwd ON au.user_id = uwd.user_id
   JOIN app.app_user u ON au.user_id = u.id
   ```

**Example 3: Recursive CTE**
1. Enter CTE name: `numbers`
2. Check "Recursive" checkbox
3. Enter query:
   ```sql
   SELECT 1 as n
   UNION ALL
   SELECT n + 1 FROM numbers WHERE n < 10
   ```
4. Main query:
   ```sql
   SELECT * FROM numbers
   ```
5. Generated SQL uses WITH RECURSIVE

#### Use Cases:
- Breaking complex queries into readable parts
- Recursive queries (tree traversal, hierarchies)
- Multiple-step data transformations
- Reusing subquery results multiple times
- Improving query readability and maintenance

## Integration

All four modules are integrated into the Admin panel (`AdminWindow.py`) with dedicated buttons:

### Button Layout:
```
Row 0: [Create Schema] [Delete Schema] [ALTER TABLE] [SELECT]
Row 1: [String Funcs] [Join Master] [Advanced Grouping] [Views]
Row 2: [Materialized Views] [CTE Builder] [Main Menu]
```

### Access:
1. Login as admin user
2. Click "Admin" button in main menu
3. New buttons appear in admin panel:
   - "Продвинутая группировка" (Advanced Grouping)
   - "Представления" (Views)
   - "Материализованные" (Materialized Views)
   - "CTE конструктор" (CTE Builder)

## Technical Details

### Dependencies:
- PyQt5 (GUI framework)
- psycopg2 (PostgreSQL adapter)
- Existing `db.py` module for database operations

### Database Functions Used:
- `db.list_tables()` - Get tables from schema
- `db.list_columns()` - Get columns from table
- `db.run_select()` - Execute SELECT queries
- `db.preview()` - Execute with row limit
- `db.exec_txn()` - Execute DDL in transaction

### Styling:
All dialogs use consistent dark theme matching the application:
- Background: `rgba(16, 30, 41, 240)`
- Buttons: `rgba(2, 65, 118, 255)`
- Tables: `rgba(25, 45, 60, 200)`
- Text: White with high contrast
- Font size: 16-20px for readability

## Testing

### Test Scenarios:

#### 1. Advanced Grouping:
```sql
-- Test ROLLUP on tracked_domain
SELECT user_id, current_state, COUNT(*)
FROM app.tracked_domain
GROUP BY ROLLUP(user_id, current_state)

-- Test CUBE
SELECT user_id, current_state, COUNT(*)
FROM app.tracked_domain
GROUP BY CUBE(user_id, current_state)

-- Test GROUPING SETS
SELECT user_id, current_state, COUNT(*)
FROM app.tracked_domain
GROUP BY GROUPING SETS(user_id, current_state, (user_id, current_state))
```

#### 2. Views:
```sql
-- Create view
CREATE OR REPLACE VIEW app.domain_user_summary AS
SELECT u.login, d.domain, d.current_state
FROM app.tracked_domain d
JOIN app.app_user u ON d.user_id = u.id;

-- Query view
SELECT * FROM app.domain_user_summary;
```

#### 3. Materialized Views:
```sql
-- Create materialized view
CREATE MATERIALIZED VIEW app.hourly_stats AS
SELECT DATE_TRUNC('hour', submitted_at) as hour,
       COUNT(*) as domains_added
FROM app.tracked_domain
GROUP BY DATE_TRUNC('hour', submitted_at);

-- Refresh
REFRESH MATERIALIZED VIEW app.hourly_stats;

-- Query
SELECT * FROM app.hourly_stats;
```

#### 4. CTE:
```sql
-- Simple CTE
WITH recent_domains AS (
  SELECT * FROM app.tracked_domain
  WHERE submitted_at > NOW() - INTERVAL '7 days'
)
SELECT current_state, COUNT(*)
FROM recent_domains
GROUP BY current_state;

-- Multiple CTEs
WITH
  user_counts AS (
    SELECT user_id, COUNT(*) as cnt
    FROM app.tracked_domain
    GROUP BY user_id
  ),
  active_users AS (
    SELECT user_id FROM user_counts WHERE cnt > 1
  )
SELECT u.login, uc.cnt
FROM active_users au
JOIN user_counts uc ON au.user_id = uc.user_id
JOIN app.app_user u ON au.user_id = u.id;
```

## Error Handling

All modules include comprehensive error handling:
- User input validation
- PostgreSQL error messages captured and displayed
- Confirmation dialogs for destructive operations
- Clear error messages in user-friendly format
- Transaction rollback on errors

## Security Considerations

- All SQL is parameterized where user input is involved
- DROP operations require confirmation
- Admin-only access (requires `is_admin = TRUE`)
- Schema name fixed to `app` (not user-configurable)
- No SQL injection vulnerabilities

## Performance

- Query results limited to 1000 rows by default (using `db.preview()`)
- Materialized views provide caching for expensive queries
- CTEs optimize complex queries with subquery reuse
- All operations use prepared statements

## Future Enhancements

Possible improvements:
1. Export results to CSV/Excel
2. Save/load query templates
3. Query history and favorites
4. Visual query builder for CTE relationships
5. Performance analysis (EXPLAIN)
6. Scheduled materialized view refresh
7. View dependency graph
8. GROUPING() function support for better null handling

## Files Modified

- `src/AdminDesign.py` - Added new buttons to UI
- `src/AdminWindow.py` - Connected new dialog imports and signals

## Files Created

- `src/advanced_grouping_dialog.py` - ROLLUP/CUBE/GROUPING SETS interface
- `src/views_manager_dialog.py` - Views CRUD operations
- `src/materialized_views_dialog.py` - Materialized views with REFRESH
- `src/cte_builder_dialog.py` - WITH query constructor

## Summary

All four required modules have been successfully implemented with:
- Complete GUI interfaces (no manual SQL required)
- Buttons and dropdown menus for all operations
- Form-based input for queries and parameters
- Real-time SQL generation and preview
- Execute and display results functionality
- Comprehensive error handling
- Consistent styling with existing application
- Full integration into Admin panel

The implementation fulfills all requirements of Test 4 by providing advanced SQL capabilities through intuitive graphical interfaces.
