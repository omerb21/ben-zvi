# מדריך תפעול חודשי - Mini CRM

## סדר הרצה חודשי

### 1. טעינת קבצי קופות (חובה)
```bash
# טעינת קבצי קופות מכל המקורות
python -m crm_ingestion.main --date 2025-01-01 --source YL uploads/yl.xlsx
python -m crm_ingestion.main --date 2025-01-01 --source FNX uploads/fnx.xlsx
python -m crm_ingestion.main --date 2025-01-01 --source MOR uploads/mor.xlsx
python -m crm_ingestion.main --date 2025-01-01 --source ANLST uploads/anlst.xlsx
python -m crm_ingestion.main --date 2025-01-01 --source DASH uploads/dash.xlsx
python -m crm_ingestion.main --date 2025-01-01 --source NFTY uploads/nfty.xlsx
python -m crm_ingestion.main --date 2025-01-01 --source AS uploads/as.xlsx
```

### 2. טעינת קובץ לקוחות חדש (אופציונלי)
```bash
# רק אם יש עדכונים לנתוני לקוחות
python tools/load_clients.py uploads/Clients_updates.xlsx
```

### 3. סגירת קופות שלא הופיעו חודשיים (חובה)
```bash
# סימון קופות כלא פעילות אם לא הופיעו במשך חודשיים
python tools/mark_closed_funds.py
```

### 4. בדיקות איכות (מומלץ)
```bash
# הרצת בדיקות אוטומטיות
pytest tests/ -v

# בדיקה מהירה של מצב המערכת
python -c "
import sqlite3
con = sqlite3.connect('crm.db')
print('Total clients:', con.execute('SELECT COUNT(*) FROM client').fetchone()[0])
print('Active funds:', con.execute('SELECT COUNT(DISTINCT client_id||fund_number||source) FROM snapshot WHERE is_active=1').fetchone()[0])
print('Inactive funds:', con.execute('SELECT COUNT(DISTINCT client_id||fund_number||source) FROM snapshot WHERE is_active=0').fetchone()[0])
con.close()
"
```

### 5. הרצת האפליקציה
```bash
# הפעלת השרת
python app.py
```

## לוח זמנים מומלץ

### תחילת חודש (1-5 בחודש)
1. ✅ קבלת קבצי נתונים מכל המקורות
2. ✅ טעינת קבצי הקופות למערכת
3. ✅ הרצת סקריפט סגירת קופות
4. ✅ בדיקות איכות ואימות נתונים

### אמצע חודש (15 בחודש)
1. ✅ בדיקת תקינות המערכת
2. ✅ גיבוי בסיס הנתונים
3. ✅ עדכון נתוני לקוחות (אם נדרש)

### סוף חודש (25-30 בחודש)
1. ✅ הכנה לחודש הבא
2. ✅ ארכוב קבצים ישנים
3. ✅ דוחות חודשיים

## בדיקות איכות

### בדיקות אוטומטיות
```bash
# בדיקת כל הפונקציונליות
pytest tests/ -v --cov=. --cov-report=html

# בדיקות ספציפיות לסגירת קופות
pytest tests/test_close_funds.py -v

# בדיקות טעינת לקוחות
pytest tests/test_client_details_api.py -v
```

### בדיקות ידניות
1. **בדיקת ממשק משתמש**:
   - פתיחת דף לקוחות וודא שמוצגים רק קופות פעילות
   - בדיקת דף פרטי לקוח - ודא שכל השדות מוצגים
   - בדיקת דשבורד - ודא שהסכומים נכונים

2. **בדיקת נתונים**:
   - ודא שמספר הלקוחות עלה/נשאר יציב
   - ודא שקופות ישנות סומנו כלא פעילות
   - ודא שקופות חדשות מוצגות כפעילות

## פתרון בעיות נפוצות

### שגיאות טעינה
```bash
# אם יש שגיאה בטעינת קובץ, בדוק את המבנה:
python -c "
import pandas as pd
df = pd.read_excel('uploads/problematic_file.xlsx')
print('Columns:', list(df.columns))
print('Shape:', df.shape)
print('First row:', df.iloc[0].to_dict())
"
```

### בעיות ביצועים
```bash
# אם המערכת איטית, בדוק את גודל בסיס הנתונים:
sqlite3 crm.db "
SELECT 
    'clients' as table_name, COUNT(*) as count FROM client
UNION ALL
SELECT 
    'snapshots', COUNT(*) FROM snapshot
UNION ALL
SELECT 
    'active_snapshots', COUNT(*) FROM snapshot WHERE is_active = 1;
"
```

### גיבוי ושחזור
```bash
# גיבוי יומי
cp crm.db backups/crm_$(date +%Y%m%d).db

# שחזור מגיבוי
cp backups/crm_20250128.db crm.db
```

## קבצי לוג

המערכת יוצרת לוגים בקבצים הבאים:
- `logs/ingestion.log` - לוגי טעינת נתונים
- `logs/app.log` - לוגי האפליקציה
- `logs/fund_closure.log` - לוגי סגירת קופות

## אנשי קשר ותמיכה

- **מפתח המערכת**: [פרטי קשר]
- **מנהל נתונים**: [פרטי קשר]
- **תמיכה טכנית**: [פרטי קשר]

## עדכונים ושינויים

תיעוד השינויים נמצא ב-`CHANGELOG.md`
