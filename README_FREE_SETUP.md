# نظام التسويق الآلي المجاني - دليل الإعداد
# Free Marketing Automation System - Setup Guide

## نظرة عامة | Overview

تم تحديث هذا النظام ليعمل بالكامل باستخدام خدمات مجانية بنسبة 100%، مما يوفر عليك أكثر من $200 شهرياً في تكاليف الخدمات المدفوعة.

This system has been updated to work entirely with 100% free services, saving you over $200 monthly in paid service costs.

## الخدمات المجانية المستخدمة | Free Services Used

### 1. Google Gemini API (مجاني)
- **الاستخدام**: إنشاء النصوص والصور
- **الحد الشهري**: 50,000 طلب مجاناً
- **معدل الطلبات**: 15 طلب/دقيقة
- **التكلفة**: مجاني بالكامل

### 2. Hugging Face Inference API (مجاني)
- **الاستخدام**: نماذج الذكاء الاصطناعي المتنوعة
- **الحد الشهري**: 30,000 طلب مجاناً
- **معدل الطلبات**: 10 طلب/دقيقة
- **التكلفة**: مجاني بالكامل

### 3. Google Text-to-Speech (مجاني)
- **الاستخدام**: تحويل النص إلى صوت
- **الحد الشهري**: 1,000,000 حرف مجاناً
- **معدل الطلبات**: 100 طلب/دقيقة
- **التكلفة**: مجاني بالكامل

## متطلبات النظام | System Requirements

```bash
Python 3.8+
Flask 2.0+
```

## التثبيت | Installation

### 1. تثبيت المكتبات المطلوبة | Install Required Libraries

```bash
pip install flask flask-cors flask-jwt-extended flask-sqlalchemy python-dotenv cryptography google-generativeai requests aiohttp pillow
```

### 2. إعداد متغيرات البيئة | Environment Variables Setup

أنشئ ملف `.env` في المجلد الرئيسي:

Create a `.env` file in the root directory:

```env
# Google Gemini API (Free)
GOOGLE_GEMINI_API_KEY=your_free_gemini_api_key_here

# Hugging Face API (Free)
HUGGINGFACE_API_KEY=your_free_huggingface_api_key_here

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///marketing_automation.db

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

## الحصول على مفاتيح API المجانية | Getting Free API Keys

### 1. Google Gemini API Key (مجاني)

1. اذهب إلى: https://makersuite.google.com/app/apikey
2. سجل الدخول بحساب Google
3. انقر على "Create API Key"
4. انسخ المفتاح وضعه في متغير `GOOGLE_GEMINI_API_KEY`

### 2. Hugging Face API Key (مجاني)

1. اذهب إلى: https://huggingface.co/settings/tokens
2. سجل الدخول أو أنشئ حساب مجاني
3. انقر على "New token"
4. اختر "Read" permissions
5. انسخ المفتاح وضعه في متغير `HUGGINGFACE_API_KEY`

## تشغيل النظام | Running the System

### 1. التشغيل المحلي | Local Development

```bash
# انتقل إلى مجلد المشروع
cd marketing_automation_system

# تشغيل النظام
python3 run.py
```

### 2. التشغيل على خوادم مجانية | Free Hosting Deployment

#### Replit (مجاني)
1. ارفع المشروع إلى Replit
2. أضف متغيرات البيئة في Secrets
3. شغل الأمر: `python3 run.py`

#### Render (مجاني)
1. ارفع المشروع إلى GitHub
2. اربط المستودع مع Render
3. أضف متغيرات البيئة
4. اختر "Python" كبيئة التشغيل

#### Railway (مجاني)
1. ارفع المشروع إلى GitHub
2. اربط المستودع مع Railway
3. أضف متغيرات البيئة
4. النظام سيعمل تلقائياً

## اختبار النظام | Testing the System

### 1. اختبار الاستيرادات | Import Test

```bash
python3 test_imports.py
```

### 2. اختبار الوظائف الأساسية | Basic Functionality Test

```bash
# تشغيل النظام
python3 run.py

# في متصفح آخر، اذهب إلى:
http://localhost:5000
```

## الميزات المتاحة | Available Features

### ✅ إنشاء المحتوى النصي
- استخدام Google Gemini API
- دعم اللغة العربية والإنجليزية
- أنواع محتوى متنوعة

### ✅ إنشاء الصور
- استخدام Google Gemini و Hugging Face
- صور تسويقية احترافية
- دقة عالية

### ✅ تحويل النص إلى صوت
- استخدام Google TTS
- دعم لغات متعددة
- جودة صوت عالية

### ✅ تحليل الحملات
- تحليل ذكي للأداء
- توصيات مخصصة
- إحصائيات مفصلة

### ✅ الاستهداف الذكي
- تحليل الجمهور المستهدف
- اقتراح المنصات المناسبة
- تحسين الحملات

## حدود الخدمات المجانية | Free Service Limits

| الخدمة | الحد الشهري | معدل الطلبات | التكلفة |
|--------|-------------|-------------|---------|
| Google Gemini | 50,000 طلب | 15/دقيقة | مجاني |
| Hugging Face | 30,000 طلب | 10/دقيقة | مجاني |
| Google TTS | 1M حرف | 100/دقيقة | مجاني |

## نصائح للاستخدام الأمثل | Optimization Tips

### 1. إدارة الحدود
- راقب استخدامك الشهري
- وزع الطلبات على مدار اليوم
- استخدم التخزين المؤقت عند الإمكان

### 2. تحسين الأداء
- استخدم طلبات مجمعة عند الإمكان
- قم بضغط الصور المولدة
- احفظ النتائج محلياً

### 3. النسخ الاحتياطي
- احفظ نسخة احتياطية من قاعدة البيانات
- احفظ المحتوى المولد
- احفظ إعدادات النظام

## استكشاف الأخطاء | Troubleshooting

### مشكلة: "API Key not found"
**الحل**: تأكد من إضافة مفاتيح API في ملف `.env`

### مشكلة: "Rate limit exceeded"
**الحل**: انتظر دقيقة وحاول مرة أخرى، أو استخدم خدمة بديلة

### مشكلة: "Import Error"
**الحل**: تأكد من تثبيت جميع المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

## الدعم | Support

### الوثائق الرسمية
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [Hugging Face API Docs](https://huggingface.co/docs/api-inference)
- [Google TTS Docs](https://cloud.google.com/text-to-speech/docs)

### المجتمع
- [GitHub Issues](https://github.com/your-repo/issues)
- [Discord Community](https://discord.gg/your-server)

## التحديثات المستقبلية | Future Updates

- [ ] إضافة المزيد من الخدمات المجانية
- [ ] تحسين واجهة المستخدم
- [ ] إضافة المزيد من اللغات
- [ ] تحسين الأداء والسرعة

## الترخيص | License

هذا المشروع مرخص تحت رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ملاحظة مهمة | Important Note

🎉 **توفير 100% في التكاليف!**

بدلاً من دفع أكثر من $200 شهرياً للخدمات المدفوعة، يمكنك الآن استخدام نفس الميزات مجاناً بالكامل!

🎉 **100% Cost Savings!**

Instead of paying over $200 monthly for paid services, you can now use the same features completely free!

---

**تم التحديث**: ديسمبر 2024
**الإصدار**: 2.0.0 (Free Edition)
**الحالة**: جاهز للإنتاج

