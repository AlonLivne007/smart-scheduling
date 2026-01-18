# הסבר מפורט: Max Consecutive Days

## 📋 סקירה כללית

האילוץ **MAX_CONSECUTIVE_DAYS** מבטיח שעובד לא יעבוד יותר מ-X ימים רצופים.
המימוש כולל שני חלקים עיקריים:

1. **אופטימיזציה (MIP Solver)** - מונע הפרות בזמן בניית הפתרון
2. **ולידציה (Constraint Service)** - בודק אם לוח זמנים קיים מפר את האילוץ

---

## 🔧 חלק 1: אופטימיזציה - Hard Constraint

### מיקום בקוד

`backend/app/services/scheduling/mip_solver.py` - שורות 439-498

### הרעיון הכללי

במקום לבדוק ישירות את משתני ההחלטה `x(i,j,r)`, הקוד יוצר **משתני עזר בינאריים** `works_on_day[i, date]` שמסמנים:

- `works_on_day[i, date] = 1` אם עובד `i` עובד **לפחות במשמרת אחת** ביום `date`
- `works_on_day[i, date] = 0` אם עובד `i` **לא עובד** ביום `date`

### שלב 1: בניית משתני `works_on_day`

```python
def _build_works_on_day_variables(...):
    works_on_day = {}

    for emp_idx in range(n_employees):
        for d in sorted_dates:
            # יוצר משתנה בינארי חדש
            var = model.add_var(var_type=mip.BINARY, name=f'works_day_emp_{emp_idx}_date_{d}')
            works_on_day[(emp_idx, d)] = var

            # מוצא את כל המשמרות ביום הזה
            shift_indices_for_date = date_to_shifts[d]
            vars_for_date = []
            for shift_idx in shift_indices_for_date:
                if (emp_idx, shift_idx) in vars_by_emp_shift:
                    vars_for_date.extend(vars_by_emp_shift[(emp_idx, shift_idx)])

            # קושר את works_on_day למשתני ההחלטה
            if vars_for_date:
                # אם עובד עובד במשמרת כלשהי ביום זה, works_on_day חייב להיות 1
                for var_for_date in vars_for_date:
                    model += works_on_day[(emp_idx, d)] >= var_for_date

                # אם עובד לא עובד ביום זה, works_on_day חייב להיות 0
                model += works_on_day[(emp_idx, d)] <= mip.xsum(vars_for_date)
```

**מה קורה כאן?**

נניח שיש לנו:

- עובד 0 (John)
- יום 2024-01-15
- משמרות ביום זה: משמרת 5, משמרת 6
- משתני החלטה: `x(0,5,1)`, `x(0,6,1)`

האילוצים שנוצרים:

1. `works_on_day[0, 2024-01-15] >= x(0,5,1)` - אם John מוקצה למשמרת 5, אז `works_on_day = 1`
2. `works_on_day[0, 2024-01-15] >= x(0,6,1)` - אם John מוקצה למשמרת 6, אז `works_on_day = 1`
3. `works_on_day[0, 2024-01-15] <= x(0,5,1) + x(0,6,1)` - אם John לא מוקצה לאף משמרת, אז `works_on_day = 0`

**תוצאה**: `works_on_day[0, 2024-01-15] = 1` אם ורק אם John עובד לפחות במשמרת אחת ביום זה.

### שלב 2: הוספת אילוצי רצף

```python
def _add_consecutive_days_constraints(...):
    # בונה את works_on_day variables
    works_on_day = self._build_works_on_day_variables(...)

    sorted_dates = sorted(date_to_shifts.keys())

    # מוצא כל רצף של (max_consecutive+1) ימים רצופים
    for start_idx in range(len(sorted_dates) - max_consecutive):
        sequence_dates = sorted_dates[start_idx:start_idx + max_consecutive + 1]

        # בודק אם הימים באמת רצופים (יום אחר יום)
        is_consecutive = True
        for i in range(len(sequence_dates) - 1):
            if (sequence_dates[i+1] - sequence_dates[i]).days != 1:
                is_consecutive = False
                break

        if not is_consecutive:
            continue  # מדלג על רצפים שלא רצופים

        # לכל עובד, מוסיף אילוץ
        for emp_idx in range(n_employees):
            day_vars = [works_on_day[(emp_idx, d)] for d in sequence_dates]
            if day_vars:
                # האילוץ: סכום הימים לא יכול להיות יותר מ-max_consecutive
                model += mip.xsum(day_vars) <= max_consecutive
```

### דוגמה מעשית

נניח:

- `MAX_CONSECUTIVE_DAYS = 3`
- ימים בשבוע: א', ב', ג', ד', ה'

**מה הקוד עושה?**

1. **בונה משתנים**: `works_on_day[0, Mon]`, `works_on_day[0, Tue]`, `works_on_day[0, Wed]`, `works_on_day[0, Thu]`, `works_on_day[0, Fri]`

2. **מוצא רצפים של 4 ימים רצופים** (max_consecutive+1 = 4):

   - רצף 1: [א', ב', ג', ד']
   - רצף 2: [ב', ג', ד', ה']

3. **מוסיף אילוצים לכל עובד**:
   ```
   עבור עובד 0:
   works_on_day[0, Mon] + works_on_day[0, Tue] + works_on_day[0, Wed] + works_on_day[0, Thu] <= 3
   works_on_day[0, Tue] + works_on_day[0, Wed] + works_on_day[0, Thu] + works_on_day[0, Fri] <= 3
   ```

**למה זה עובד?**

אם עובד עובד 4 ימים רצופים, למשל א', ב', ג', ד':

- `works_on_day[0, Mon] = 1`
- `works_on_day[0, Tue] = 1`
- `works_on_day[0, Wed] = 1`
- `works_on_day[0, Thu] = 1`

אז האילוץ הראשון: `1 + 1 + 1 + 1 = 4 <= 3` ❌ **לא אפשרי!**

אבל אם עובד עובד 3 ימים רצופים, למשל א', ב', ג':

- `works_on_day[0, Mon] = 1`
- `works_on_day[0, Tue] = 1`
- `works_on_day[0, Wed] = 1`
- `works_on_day[0, Thu] = 0`

אז האילוץ הראשון: `1 + 1 + 1 + 0 = 3 <= 3` ✅ **אפשרי!**

---

## 🔧 חלק 2: אופטימיזציה - Soft Constraint

### מיקום בקוד

`backend/app/services/scheduling/mip_solver.py` - שורות 620-653

### ההבדל מ-Hard Constraint

ב-Soft Constraint, **מותר** לעבוד יותר מ-max_consecutive ימים רצופים, אבל יש **עונש** על כל יום עודף.

### המימוש

```python
# MAX_CONSECUTIVE_DAYS (soft)
if max_consecutive_constraint and not max_consecutive_constraint[1]:  # is_soft
    max_consecutive = int(max_consecutive_constraint[0])
    works_on_day = self._build_works_on_day_variables(...)

    for start_idx in range(len(sorted_dates) - max_consecutive):
        sequence_dates = sorted_dates[start_idx:start_idx + max_consecutive + 1]

        # בודק אם רצף
        if not is_consecutive:
            continue

        for emp_idx in range(n_employees):
            day_vars = [works_on_day[(emp_idx, d)] for d in sequence_dates]
            if day_vars:
                total_days = mip.xsum(day_vars)  # כמה ימים עובד עובד ברצף

                # משתנה עזר: כמה ימים עודפים מעבר למקסימום
                excess_days = model.add_var(var_type=mip.CONTINUOUS, lb=0,
                                          name=f'max_consecutive_excess_emp_{emp_idx}_days_{start_idx}')

                # האילוץ: excess_days >= total_days - max_consecutive
                model += excess_days >= total_days - max_consecutive

                # מוסיף את העונש לפונקציית המטרה
                soft_penalty_component += excess_days
```

### דוגמה

נניח:

- `MAX_CONSECUTIVE_DAYS = 3` (soft)
- עובד עובד 5 ימים רצופים: א', ב', ג', ד', ה'

**מה קורה?**

1. **רצף 1**: [א', ב', ג', ד']

   - `total_days = 1 + 1 + 1 + 1 = 4`
   - `excess_days >= 4 - 3 = 1`
   - `excess_days = 1` (עונש על יום אחד עודף)

2. **רצף 2**: [ב', ג', ד', ה']
   - `total_days = 1 + 1 + 1 + 1 = 4`
   - `excess_days >= 4 - 3 = 1`
   - `excess_days = 1` (עונש על יום אחד עודף)

**סה"כ עונש**: `1 + 1 = 2` (שני ימים עודפים)

הסולבר ינסה למזער את העונש, אבל אם אין פתרון אחר, הוא יאפשר את ההפרה.

---

## 🔧 חלק 3: ולידציה (Constraint Service)

### מיקום בקוד

`backend/app/services/constraintService.py` - שורות 511-562

### מה זה עושה?

הפונקציה הזו בודקת אם לוח זמנים **קיים** מפר את האילוץ. זה שימושי אחרי שהסולבר כבר יצר פתרון, או כשמשתמש מקצה משמרות ידנית.

### המימוש

```python
def _check_consecutive_days(self, user_id, assignments, result):
    # מקבל את האילוץ מהגדרות המערכת
    max_consecutive_constraint = self.system_constraints.get(SystemConstraintType.MAX_CONSECUTIVE_DAYS)

    if not max_consecutive_constraint:
        return  # אין אילוץ, אין מה לבדוק

    max_consecutive = int(max_consecutive_constraint['value'])
    is_hard = max_consecutive_constraint['is_hard']

    # מוצא את כל המשמרות של העובד וממיין לפי תאריך
    shift_ids = [a['planned_shift_id'] for a in assignments]
    shifts = self.db.query(PlannedShiftModel).filter(
        PlannedShiftModel.planned_shift_id.in_(shift_ids)
    ).order_by(PlannedShiftModel.date).all()

    # מוציא רק את התאריכים הייחודיים (אם עובד עובד במספר משמרות ביום אחד)
    work_dates = sorted(set(shift.date for shift in shifts))

    if not work_dates:
        return  # אין משמרות, אין מה לבדוק

    # מוצא את הרצף הארוך ביותר של ימים רצופים
    consecutive_count = 1
    max_found = 1

    for i in range(1, len(work_dates)):
        if (work_dates[i] - work_dates[i-1]).days == 1:
            # ימים רצופים - מגדיל את המונה
            consecutive_count += 1
            max_found = max(max_found, consecutive_count)
        else:
            # לא רצופים - מתחיל לספור מחדש
            consecutive_count = 1

    # בודק אם יש הפרה
    if max_found > max_consecutive:
        severity = "HARD" if is_hard else "SOFT"
        result.add_error(ValidationError(
            "MAX_CONSECUTIVE_DAYS_EXCEEDED",
            severity,
            f"Employee {user.user_full_name} works {max_found} consecutive days (max: {max_consecutive})",
            {
                'user_id': user_id,
                'consecutive_days': max_found,
                'max_consecutive': max_consecutive
            }
        ))
```

### דוגמה

נניח:

- `MAX_CONSECUTIVE_DAYS = 3`
- עובד עובד בתאריכים: 2024-01-15, 2024-01-16, 2024-01-17, 2024-01-18, 2024-01-20

**מה הקוד עושה?**

1. **ממיין תאריכים**: [2024-01-15, 2024-01-16, 2024-01-17, 2024-01-18, 2024-01-20]

2. **בודק רצפים**:

   - `i=1`: 2024-01-16 - 2024-01-15 = 1 יום ✅ רצופים → `consecutive_count = 2`, `max_found = 2`
   - `i=2`: 2024-01-17 - 2024-01-16 = 1 יום ✅ רצופים → `consecutive_count = 3`, `max_found = 3`
   - `i=3`: 2024-01-18 - 2024-01-17 = 1 יום ✅ רצופים → `consecutive_count = 4`, `max_found = 4`
   - `i=4`: 2024-01-20 - 2024-01-18 = 2 ימים ❌ לא רצופים → `consecutive_count = 1`, `max_found = 4`

3. **תוצאה**: `max_found = 4 > 3` → **יש הפרה!**

---

## 📊 סיכום - ההבדלים בין החלקים

| מאפיין      | אופטימיזציה (Hard)       | אופטימיזציה (Soft)             | ולידציה          |
| ----------- | ------------------------ | ------------------------------ | ---------------- |
| **מתי רץ**  | בזמן בניית הפתרון        | בזמן בניית הפתרון              | אחרי שיש פתרון   |
| **מה עושה** | מונע הפרות               | מוסיף עונש על הפרות            | בודק אם יש הפרות |
| **משתנים**  | `works_on_day` + אילוצים | `works_on_day` + `excess_days` | חישוב ישיר       |
| **תוצאה**   | פתרון תמיד תקין          | פתרון עם עונש מינימלי          | דוח על הפרות     |

---

## 💡 שאלות נפוצות

### Q: למה צריך את `works_on_day`? למה לא לבדוק ישירות את `x(i,j,r)`?

**A**: כי עובד יכול לעבוד במספר משמרות ביום אחד. `works_on_day` מסכם את כל המשמרות ליום אחד.

**דוגמה**:

- עובד עובד במשמרת בוקר: `x(0,5,1) = 1`
- עובד עובד במשמרת ערב: `x(0,6,1) = 1`
- אבל זה **יום אחד** של עבודה, לא שניים!

`works_on_day[0, 2024-01-15] = 1` (יום אחד) ולא `2`.

### Q: למה בודקים רצפים של `max_consecutive+1` ימים?

**A**: כי אם נבדוק רק `max_consecutive` ימים, אפשר לעקוף את האילוץ.

**דוגמה עם `max_consecutive = 3`**:

- אם נבדוק רק 3 ימים: `works_on_day[Mon] + works_on_day[Tue] + works_on_day[Wed] <= 3`
- אפשר לעבוד: א', ב', ג', ד' (4 ימים) - כי הרצף [ב', ג', ד'] = 3 ✅
- אבל אם נבדוק 4 ימים: `works_on_day[Mon] + works_on_day[Tue] + works_on_day[Wed] + works_on_day[Thu] <= 3`
- הרצף [א', ב', ג', ד'] = 4 > 3 ❌ **תופס את ההפרה!**

### Q: מה ההבדל בין Hard ל-Soft?

**A**:

- **Hard**: הסולבר **לא יכול** ליצור פתרון שמפר את האילוץ. אם אין פתרון תקין, הוא יחזיר "לא ניתן לפתור".
- **Soft**: הסולבר **יכול** ליצור פתרון שמפר את האילוץ, אבל ינסה למזער את ההפרות (על ידי מזעור העונש).

---

## 🔗 קישורים לקוד

- **אופטימיזציה (Hard)**: `backend/app/services/scheduling/mip_solver.py:439-498`
- **אופטימיזציה (Soft)**: `backend/app/services/scheduling/mip_solver.py:620-653`
- **ולידציה**: `backend/app/services/constraintService.py:511-562`
- **בניית משתנים**: `backend/app/services/scheduling/mip_solver.py:214-259`
