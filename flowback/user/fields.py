from django.db import models

class LanguageOptions(models.TextChoices):
    ENGLISH = ("en-US","English")
    HINDI = ("hi","हिंदी")
    CHINESE_SIMPLIFIED = ("zh-CN","简体中文")
    RUSSIAN = ("ru","Русский")
    SPANISH = ("es","Español")
    ITALIAN = ("it","Italiano")
    GERMAN = ("de","Deutsch")
    FRENCH = ("fr","Français")
    DUTCH = ("nl","Nederlands")
    JAPANESE = ("ja","日本語")
    ARABIC = ("ar","عربي")
    CZECH = ("cs","čeština")
    GREEK = ("el","Ελληνικά")
    HUNGARIAN = ("hu","Magyar")
    INDONESIA = ("id","Bahasa Indonesia")
    KOREAN = ("ko","한국인")
    PERSIAN = ("fa","فارسی")
    POLISH = ("pl","Polski")
    PORTUGUESE = ("pt","Português")
    THAI = ("th","แบบไทย")
    TURKISH = ("tr","Türkçe")
    VIETNAMESE = ("vi","Tiếng Việt")
    CHINESE_TRADITIONAL = ("zh-TW","繁體中文")












