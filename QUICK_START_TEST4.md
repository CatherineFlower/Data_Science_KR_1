# Quick Start Guide - Test 4 Features

## Installation

### Prerequisites
```bash
# Ensure you have Python 3.12+ installed
python3 --version

# Install required packages
pip install PyQt5 psycopg2-binary python-dotenv scikit-learn numpy
```

### Database Setup
1. Ensure PostgreSQL 13+ is running
2. Configure connection in `.env` file:
   ```
   PGHOST=127.0.0.1
   PGPORT=5432
   PGDATABASE=postgres
   PGUSER=postgres
   PGPASSWORD=your_password
   ```

## Running the Application

### Start Main Application
```bash
cd src
python3 mainApp.py
```

### First Time Setup
1. **Login Screen** appears
2. Click **"Create Account"**
3. Enter username and password
4. Click **"Create Account"**

### Access Admin Panel
1. **Login** with your account
2. Click **"Admin"** button (top panel)
3. **Admin Panel** opens with new buttons

## Using Test 4 Features

### 1. Advanced Grouping

**Button**: "Продвинутая группировка"

**Quick Example**:
```
1. Click button → Dialog opens
2. Table: select "app.tracked_domain"
3. Grouping Type: Select "ROLLUP"
4. Columns: Click "user_id" and "current_state" (Ctrl+Click)
5. Aggregate:
   - Function: COUNT
   - Column: *
   - Click "Add Aggregate"
6. Click "Generate SQL" → Preview appears
7. Click "Execute Query" → Results shown
```

### 2. Views Manager

**Button**: "Представления"

**Quick Example**:
```
1. Click button → Views Manager opens
2. Click "Create New View"
3. View Name: "my_test_view"
4. Query: "SELECT domain, current_state FROM tracked_domain"
5. Click "Create" → View created
6. Select view from list
7. Click "View Data" → See results
```

### 3. Materialized Views

**Button**: "Материализованные"

**Quick Example**:
```
1. Click button → Materialized Views Manager opens
2. Click "Create Materialized View"
3. Name: "domain_stats"
4. Query: "SELECT current_state, COUNT(*) as total FROM tracked_domain GROUP BY current_state"
5. Click "Create" → Materialized view created
6. Click "View Data" → See cached results
7. Later: Click "REFRESH Data" → Update cached data
```

### 4. CTE Builder

**Button**: "CTE конструктор"

**Quick Example**:
```
1. Click button → CTE Builder opens
2. CTE Name: "active_doms"
3. Query: "SELECT * FROM app.tracked_domain WHERE current_state = 'active'"
4. Click "Add CTE"
5. Main Query: "SELECT domain, submitted_at FROM active_doms"
6. Click "Generate Complete SQL" → Preview WITH query
7. Click "Execute Query" → See results
```

## Testing Each Feature

### Test Script

```bash
# Test 1: Advanced Grouping
1. Create some test data first:
   - Add 2-3 domains via "Add Domain" in main menu

2. Open Advanced Grouping
3. Test ROLLUP on tracked_domain table
4. Should see hierarchical totals

# Test 2: Views
1. Create view "test_view"
2. Query: SELECT domain FROM tracked_domain
3. Verify view appears in list
4. View data - should show all domains

# Test 3: Materialized Views
1. Create materialized view "test_matview"
2. Query: SELECT COUNT(*) as total FROM tracked_domain
3. View data - note count
4. Add new domain in main menu
5. View matview data again - count unchanged
6. Click REFRESH
7. View data - count should increase

# Test 4: CTE
1. Define CTE "step1": SELECT user_id FROM tracked_domain
2. Main query: SELECT COUNT(*) FROM step1
3. Execute - should show user count
```

## Troubleshooting

### Issue: "Schema 'app' does not exist"
**Solution**: Click "Create Schema" button first (in admin panel)

### Issue: "No tables found"
**Solution**:
1. Create schema first
2. Click "Refresh" in dialog
3. Tables should appear

### Issue: "Permission denied"
**Solution**:
1. Ensure user is admin
2. Check database permissions
3. Verify .env configuration

### Issue: Import errors
**Solution**:
```bash
# Reinstall dependencies
pip install --upgrade PyQt5 psycopg2-binary
```

### Issue: "Module not found"
**Solution**: Make sure you're in the `src/` directory when running

## Sample Queries for Testing

### For Advanced Grouping:
```sql
-- Test CUBE
SELECT user_id, current_state, COUNT(*)
FROM app.tracked_domain
GROUP BY CUBE(user_id, current_state)
```

### For Views:
```sql
-- Create useful view
SELECT
  u.login,
  d.domain,
  d.current_state,
  d.submitted_at
FROM app.tracked_domain d
JOIN app.app_user u ON d.user_id = u.id
```

### For Materialized Views:
```sql
-- Statistics snapshot
SELECT
  current_state,
  COUNT(*) as count,
  MIN(submitted_at) as first_added,
  MAX(submitted_at) as last_added
FROM app.tracked_domain
GROUP BY current_state
```

### For CTE:
```sql
-- Multi-step analysis
-- CTE 1: Get user counts
SELECT user_id, COUNT(*) as domain_count
FROM app.tracked_domain
GROUP BY user_id

-- CTE 2: Filter power users
SELECT user_id FROM cte1 WHERE domain_count > 2

-- Main: Get details
SELECT u.login, c1.domain_count
FROM cte2 c2
JOIN cte1 c1 ON c2.user_id = c1.user_id
JOIN app.app_user u ON c2.user_id = u.id
```

## Video Walkthrough (Suggested Recording)

1. **Intro** (30 sec)
   - Show main application
   - Navigate to admin panel
   - Point out 4 new buttons

2. **Advanced Grouping** (2 min)
   - Demonstrate ROLLUP
   - Show subtotals
   - Explain use case

3. **Views Manager** (2 min)
   - Create view
   - View data
   - Show definition

4. **Materialized Views** (2 min)
   - Create matview
   - Show refresh operation
   - Explain performance benefits

5. **CTE Builder** (3 min)
   - Build multi-step query
   - Show SQL generation
   - Execute and explain

## Common Use Cases

### Use Case 1: Dashboard Reports
- Use **Materialized Views** for fast dashboard queries
- Refresh hourly or daily
- Query cached results instantly

### Use Case 2: Complex Analytics
- Use **CTE Builder** to break down analysis
- Test each step independently
- Combine for final result

### Use Case 3: Summary Reports
- Use **Advanced Grouping** with CUBE
- Get all dimensional combinations
- Export to Excel (copy from table)

### Use Case 4: Simplified Access
- Create **Views** for complex JOINs
- Hide complexity from users
- Query views like regular tables

## Performance Tips

1. **Limit Data**: Results auto-limited to 1000 rows
2. **Use Materialized Views**: For expensive aggregations
3. **Index Materialized Views**: Ask DBA to add indexes
4. **Test on Small Data**: Verify query before running on full dataset
5. **Use CTEs Wisely**: Break complex queries, but don't overdo nesting

## Next Steps

After familiarizing yourself with Test 4 features:

1. **Read Full Documentation**:
   - `TEST_4_FEATURES.md` - Technical details
   - `TEST_4_USER_GUIDE.md` - Comprehensive guide

2. **Experiment**:
   - Try different grouping combinations
   - Create useful views for your workflow
   - Build complex CTEs

3. **Integrate**:
   - Use materialized views in your dashboards
   - Create views for common queries
   - Simplify complex reports with CTEs

## Support

For issues or questions:
1. Check error messages (red popup boxes)
2. Verify database connection (.env file)
3. Ensure admin privileges
4. Review documentation files

## Quick Reference Card

```
╔════════════════════════════════════════════════════════╗
║  TEST 4 FEATURES - QUICK REFERENCE                     ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Advanced Grouping    → Multidimensional reports       ║
║    - ROLLUP           → Hierarchical subtotals         ║
║    - CUBE             → All combinations               ║
║    - GROUPING SETS    → Custom combinations            ║
║                                                        ║
║  Views Manager        → Virtual tables                 ║
║    - Create           → Save queries                   ║
║    - View Data        → See results                    ║
║    - Drop             → Remove view                    ║
║                                                        ║
║  Materialized Views   → Cached results                 ║
║    - Create           → Save + cache                   ║
║    - REFRESH          → Update cache                   ║
║    - View Data        → See cached results             ║
║                                                        ║
║  CTE Builder          → Multi-step queries             ║
║    - Add CTE          → Define named subquery          ║
║    - Main Query       → Use CTEs                       ║
║    - Execute          → Run complete query             ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

**Ready to Start?**
1. Run `python3 mainApp.py`
2. Login as admin
3. Click "Admin" button
4. Explore new features!

**Questions?** Refer to:
- `TEST_4_FEATURES.md` (technical)
- `TEST_4_USER_GUIDE.md` (user-friendly)
- `TEST_4_IMPLEMENTATION_SUMMARY.md` (overview)
