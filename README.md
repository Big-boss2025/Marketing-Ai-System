# نظام التسويق الآلي الذكي
## Smart Marketing Automation System

نظام تسويق آلي شامل ومتكامل مع Odoo، يتضمن إنشاء المحتوى بالذكاء الاصطناعي، النشر على منصات التواصل الاجتماعي، نظام كريديت مرن، وإدارة كاملة للـ APIs.

## 🌟 الميزات الرئيسية

### 🤖 الذكاء الاصطناعي المتقدم
- **إنشاء المحتوى**: نصوص، صور، فيديوهات بالذكاء الاصطناعي
- **مولد الكابشن الذكي**: كابشن تسويقي بأساليب متنوعة
- **الردود التلقائية**: رد ذكي على التعليقات في جميع المنصات
- **اكتشاف التريندات**: تحليل التريندات من جميع المنصات
- **التحسين التلقائي**: تحسين الاستراتيجيات حسب الأداء

### 📱 منصات التواصل الاجتماعي
- **Facebook**: نشر وتحليل وتفاعل تلقائي
- **Instagram**: صور وستوريز وريلز
- **TikTok**: فيديوهات قصيرة وترندية
- **YouTube**: فيديوهات طويلة وشورتس
- **Twitter**: تغريدات وخيوط

### 💰 نظام الكريديت المرن
- **باقات متنوعة**: من المجاني إلى المؤسسي
- **جدولة الكريديت**: كريديت تلقائي حسب الجدولة
- **نظام الإحالة**: مكافآت للإحالات مع 5 مستويات
- **تتبع الاستخدام**: مراقبة دقيقة لاستهلاك الكريديت

### 🎯 استراتيجيات التسويق المتقدمة
- **20 استراتيجية**: من المحتوى إلى الإعلانات المدفوعة
- **توصيات ذكية**: اقتراحات مخصصة لكل عميل
- **قوالب جاهزة**: استراتيجيات لأنواع الأعمال المختلفة
- **تتبع الأداء**: قياس فعالية كل استراتيجية

### 🌍 دعم متعدد اللغات والمناطق
- **10 لغات**: عربي، إنجليزي، فرنسي، إسباني، ألماني، وأكثر
- **التوقيت الذكي**: نشر في الأوقات المثلى لكل منطقة
- **التخصيص الثقافي**: محتوى مناسب لكل ثقافة
- **كشف الموقع**: تحديد الدولة واللغة تلقائياً

### 🔗 التكامل الشامل
- **Odoo**: تكامل كامل مع CRM والفواتير
- **PayPal**: دفع آمن ومعالجة تلقائية
- **OAuth**: مصادقة آمنة مع جميع المنصات
- **Webhooks**: إشعارات فورية لجميع الأحداث

### 🤖 بوت الدعم الذكي
- **دعم 24/7**: إجابات فورية على الأسئلة
- **تصعيد ذكي**: تحويل للدعم البشري عند الحاجة
- **دعم متعدد اللغات**: عربي وإنجليزي
- **تتبع المحادثات**: حفظ تاريخ الدعم

### 📊 التحليلات والتقارير
- **لوحة تحكم شاملة**: إحصائيات مفصلة لكل منصة
- **تقارير ذكية**: تحليل الأداء والتوصيات
- **مراقبة الأداء**: تتبع النتائج في الوقت الفعلي
- **تحليل المنافسين**: مقارنة مع السوق

## 🚀 التثبيت والتشغيل

### المتطلبات
- Python 3.8+
- Flask 2.0+
- SQLite/PostgreSQL
- Redis (للتخزين المؤقت)

### خطوات التثبيت

1. **استخراج الملفات**
```bash
unzip marketing_automation_system.zip
cd marketing_automation_system
```

2. **إنشاء البيئة الافتراضية**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows
```

3. **تثبيت المتطلبات**
```bash
pip install -r requirements.txt
```

4. **إعداد متغيرات البيئة**
```bash
cp .env.example .env
# قم بتحرير ملف .env وإضافة المتغيرات المطلوبة
```

5. **إنشاء قاعدة البيانات**
```bash
python -c "from src.main import create_app; app = create_app(); app.app_context().push(); from src.models.base import db; db.create_all()"
```

6. **تشغيل النظام**
```bash
python run.py
```

النظام سيعمل على: `http://localhost:5000`

### التشغيل في الإنتاج

1. **استخدام Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

2. **استخدام Docker**
```bash
docker build -t marketing-automation .
docker run -p 5000:5000 marketing-automation
```

## 🔧 الإعدادات

### متغيرات البيئة المطلوبة (.env)

```env
# إعدادات التطبيق
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///marketing_automation.db

# إعدادات Odoo
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password

# إعدادات PayPal
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox  # أو live للإنتاج

# إعدادات البريد الإلكتروني
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourcompany.com

# إعدادات وسائل التواصل الاجتماعي
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
INSTAGRAM_CLIENT_ID=your-instagram-client-id
INSTAGRAM_CLIENT_SECRET=your-instagram-client-secret
TIKTOK_CLIENT_KEY=your-tiktok-client-key
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret

# إعدادات الذكاء الاصطناعي (مجانية)
OLLAMA_BASE_URL=http://localhost:11434
STABLE_DIFFUSION_URL=http://localhost:7860
```

## 📋 APIs المتاحة

### إدارة المستخدمين
- `POST /api/admin/users` - إنشاء مستخدم جديد
- `GET /api/admin/users` - قائمة المستخدمين
- `PUT /api/admin/users/{id}` - تحديث مستخدم
- `DELETE /api/admin/users/{id}` - حذف مستخدم

### إدارة الكريديت
- `POST /api/credit-manager/add` - إضافة كريديت
- `POST /api/credit-manager/deduct` - خصم كريديت
- `GET /api/credit-manager/balance/{user_id}` - رصيد المستخدم
- `GET /api/credit-manager/transactions/{user_id}` - تاريخ المعاملات

### جدولة الكريديت
- `POST /api/credit-schedule/create` - إنشاء جدولة جديدة
- `GET /api/credit-schedule/list` - قائمة الجدولات
- `PUT /api/credit-schedule/{id}` - تحديث جدولة
- `DELETE /api/credit-schedule/{id}` - حذف جدولة

### منصات التواصل الاجتماعي
- `POST /api/social-media/publish` - نشر محتوى
- `GET /api/social-media/analytics` - إحصائيات المنصات
- `POST /api/social-media/schedule` - جدولة منشور
- `GET /api/social-media/posts/{user_id}` - منشورات المستخدم

### الذكاء الاصطناعي
- `POST /api/ai-assistant/generate-content` - إنشاء محتوى
- `POST /api/ai-assistant/generate-image` - إنشاء صورة
- `POST /api/ai-assistant/generate-video` - إنشاء فيديو
- `POST /api/ai-assistant/analyze-performance` - تحليل الأداء

### استراتيجيات التسويق
- `GET /api/marketing-strategies/list` - قائمة الاستراتيجيات
- `GET /api/marketing-strategies/recommendations/{user_id}` - توصيات مخصصة
- `POST /api/marketing-strategies/execute` - تنفيذ استراتيجية
- `GET /api/marketing-strategies/analytics/overview` - نظرة عامة على الأداء

### نظام الإحالة
- `POST /api/referral/generate-code` - إنشاء كود إحالة
- `POST /api/referral/use-code` - استخدام كود إحالة
- `GET /api/referral/stats/{user_id}` - إحصائيات الإحالة
- `GET /api/referral/leaderboard` - لوحة المتصدرين

### الدعم الذكي
- `POST /api/support/chat` - بدء محادثة دعم
- `POST /api/support/message` - إرسال رسالة
- `GET /api/support/history/{user_id}` - تاريخ المحادثات
- `POST /api/support/escalate` - تصعيد للدعم البشري

### التقارير والتحليلات
- `GET /api/reports/dashboard/{user_id}` - لوحة تحكم المستخدم
- `GET /api/reports/performance` - تقرير الأداء
- `GET /api/reports/analytics` - تحليلات مفصلة
- `POST /api/reports/export` - تصدير التقارير

### Webhooks
- `POST /api/webhooks/paypal` - إشعارات PayPal
- `POST /api/webhooks/odoo` - إشعارات Odoo
- `POST /api/webhooks/social-media` - إشعارات المنصات
- `GET /api/webhooks/health` - فحص صحة النظام

## 🔒 الأمان والحماية

### المصادقة والتفويض
- **OAuth 2.0**: مصادقة آمنة مع جميع المنصات
- **JWT Tokens**: رموز آمنة للجلسات
- **API Keys**: مفاتيح API مشفرة
- **Rate Limiting**: حماية من الهجمات

### حماية البيانات
- **تشفير البيانات**: جميع البيانات الحساسة مشفرة
- **HTTPS**: اتصال آمن مع جميع الخدمات
- **Validation**: التحقق من صحة جميع المدخلات
- **Sanitization**: تنظيف البيانات من المحتوى الضار

### مراقبة النظام
- **Logging**: تسجيل شامل لجميع الأنشطة
- **Error Tracking**: تتبع الأخطاء والاستثناءات
- **Performance Monitoring**: مراقبة أداء النظام
- **Health Checks**: فحص دوري لصحة النظام

## 🛠️ استكشاف الأخطاء

### مشاكل شائعة وحلولها

**1. خطأ في الاتصال بقاعدة البيانات**
```bash
# تأكد من وجود ملف قاعدة البيانات
ls -la marketing_automation.db

# إعادة إنشاء قاعدة البيانات
python -c "from src.main import create_app; app = create_app(); app.app_context().push(); from src.models.base import db; db.drop_all(); db.create_all()"
```

**2. خطأ في تثبيت المتطلبات**
```bash
# تحديث pip
pip install --upgrade pip

# تثبيت المتطلبات مع تجاهل الأخطاء
pip install -r requirements.txt --ignore-installed
```

**3. خطأ في الاتصال بالخدمات الخارجية**
```bash
# فحص الاتصال بالإنترنت
ping google.com

# فحص إعدادات البروكسي
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

**4. خطأ في أذونات الملفات**
```bash
# إعطاء أذونات التنفيذ
chmod +x run.py
chmod -R 755 src/
```

### سجلات النظام
```bash
# عرض سجلات التطبيق
tail -f logs/app.log

# عرض سجلات الأخطاء
tail -f logs/error.log

# عرض سجلات قاعدة البيانات
tail -f logs/database.log
```

## 📞 الدعم والمساعدة

### التواصل
- **البريد الإلكتروني**: support@yourcompany.com
- **الهاتف**: +1-234-567-8900
- **الدردشة المباشرة**: متاحة في النظام

### الموارد
- **الوثائق**: [docs.yourcompany.com](https://docs.yourcompany.com)
- **الفيديوهات التعليمية**: [youtube.com/yourcompany](https://youtube.com/yourcompany)
- **المنتدى**: [forum.yourcompany.com](https://forum.yourcompany.com)

### التحديثات
- **الإصدارات الجديدة**: إشعارات تلقائية في النظام
- **التحديثات الأمنية**: تطبيق فوري
- **الميزات الجديدة**: إعلان في لوحة التحكم

## 📄 الترخيص

هذا النظام مطور خصيصاً لك ومحمي بحقوق الطبع والنشر. جميع الحقوق محفوظة.

## 🎉 شكر خاص

تم تطوير هذا النظام بعناية فائقة ليكون الحل الأمثل لاحتياجاتك في التسويق الآلي. نتمنى أن يحقق لك أفضل النتائج!

---

**نسخة النظام**: 1.0.0  
**تاريخ الإصدار**: 2025-01-08  
**المطور**: فريق التطوير المتخصص

