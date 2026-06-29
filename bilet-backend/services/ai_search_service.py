from datetime import date

from constants.ai import AI_FILTER_JSON_SCHEMA, FILTER_KEYS
from services.ai_common import OLLAMA_MODEL, clean_ai_value, ollama_client, parse_llm_json


def normalize_ai_intent(payload):
    normalized = {
        "city": clean_ai_value(payload.get("city")),
        "category": clean_ai_value(payload.get("category")),
        "start_date": clean_ai_value(payload.get("start_date")),
        "end_date": clean_ai_value(payload.get("end_date")),
        "needs_clarification": bool(payload.get("needs_clarification", False)),
        "follow_up_question": clean_ai_value(payload.get("follow_up_question")),
    }

    has_filter = any(normalized[key] for key in FILTER_KEYS)

    if not has_filter and not normalized["needs_clarification"]:
        normalized["needs_clarification"] = True
        normalized["follow_up_question"] = "Hangi şehir, tarih veya kategoriye göre etkinlik arayayım?"

    if normalized["needs_clarification"] and not normalized["follow_up_question"]:
        normalized["follow_up_question"] = "Biraz daha detay verebilir misiniz? Şehir, tarih veya kategori söyleyebilirsiniz."

    return normalized


def event_filters_from_intent(intent):
    if "filters" in intent:
        return {key: intent["filters"].get(key) for key in FILTER_KEYS}

    return {key: intent.get(key) for key in FILTER_KEYS}


def extract_ai_search_intent(prompt):
    today = date.today().isoformat()

    system_prompt = f"""
        Sen bir etkinlik arama filtresi çıkaran API'sin.
        Bugünün tarihi: {today}.

        Kullanıcı mesajından sadece şu JSON alanlarını çıkar:
        city, category, start_date, end_date.

        Kurallar:
        - Kullanıcı bir alanı açıkça belirtmediyse o alan null olmalı.
        - Genel ifadeler kategori değildir. Örneğin "herhangi bir etkinlik", "etkinlik var mı", "ne var", "bir şey var mı" ifadelerinde category null olmalı.
        - category sadece şu değerlerden biri olabilir: Konser, Tiyatro, Festival, Stand-up, Spor.
        - Kullanıcı açıkça kategori belirtirse category bu değerlerden biri olmalı. Belirtmezse category null olmalı.
        - Kullanıcı şehir belirtirse city şehir adı olmalı. Belirtmezse city null olmalı.
        - Tarih varsa start_date ve end_date YYYY-MM-DD formatında olmalı.
        - Kullanıcı belirli bir gün verirse ("20 Temmuz", "15 Ağustos" gibi) start_date ve end_date aynı gün olmalı; bu ifadeyi ayın tamamına genişletme.
        - Kullanıcı sadece ay verirse ("Temmuz ayında" gibi) ayın başlangıç ve bitiş tarihlerini kullan.
        - Kullanıcı hafta veya aralık verirse sadece o aralığı kullan.
        - Sadece tek tarih varsa start_date ve end_date aynı gün olmalı.
        - Tarih yoksa start_date ve end_date null olmalı.
        - Türkçe ay adlarını doğru yorumla.

        Örnekler:
        Kullanıcı: "15 temmuz 15 ağustos arası herhangi bir etkinlik var mı"
        Cevap: {{"city": null, "category": null, "start_date": "2026-07-15", "end_date": "2026-08-15"}}

        Kullanıcı: "15 temmuz 15 ağustos arası istanbulda konser var mı"
        Cevap: {{"city": "İstanbul", "category": "Konser", "start_date": "2026-07-15", "end_date": "2026-08-15"}}

        Kullanıcı: "konya'da tiyatro var mı"
        Cevap: {{"city": "Konya", "category": "Tiyatro", "start_date": null, "end_date": null}}

        Sadece JSON dön. Açıklama yazma. Markdown kullanma.
        """

    response = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        stream=False,
        format=AI_FILTER_JSON_SCHEMA,
        options={
            "temperature": 0
        }
    )

    llm_output = response["message"]["content"].strip()
    return normalize_ai_intent(parse_llm_json(llm_output))
