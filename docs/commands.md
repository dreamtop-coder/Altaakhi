# Management Commands

## `map_services_to_items`

**وصف:** يقوم بفحص خدمات `Service` ومقارنتها مع الأجزاء `Part` في المخزون ويصدر تقرير CSV كـ dry-run. الهدف تمكين مراجعة يدوية قبل إجراء أي تغييرات على البيانات.

**الأمر الرئيسِي:**

```bash
venv\Scripts\python.exe manage.py map_services_to_items --output mapping.csv
```


خيارات مهمة:


أمثلة استخدام:


```bash
venv\Scripts\python.exe manage.py map_services_to_items -o mapping.csv
```


```bash
venv\Scripts\python.exe manage.py map_services_to_items --no-dry-run --create-placeholders --output mapping_applied.csv
```

مثال (مبسط) لمحتوى CSV الناتج:

```
service_id	service_name	matched_part_id	matched_part_name	match_type	confidence	note
1	Oil Change	101	Engine Oil 5L	exact	1.0	
2	Tire Swap	202	Tire 16" 	startswith	0.8	
```

توصية سير العمل الآمن:

1. شغّل الأمر بدون `--no-dry-run` (أي الافتراضي dry-run) واحفظ الـ CSV باستخدام `--output`.
2. افتح CSV في محرر/جداول بيانات وراجع مطابقة الأجزاء لكل خدمة.
3. إذا كانت المطابقة مناسبة، شغّل الأمر مع `--no-dry-run --create-placeholders` لإنشاء السجلات الناقصة.
4. نفّذ دائمًا نسخة احتياطية للبيانات أو اختبر العملية في بيئة staging قبل التشغيل على الإنتاج.

نصائح سريعة:


<!-- No-op placeholder to satisfy patch format -->
موقع الكود:

[services/management/commands/map_services_to_items.py](services/management/commands/map_services_to_items.py)
