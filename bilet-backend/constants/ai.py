FILTER_KEYS = ["city", "category", "start_date", "end_date"]
SLOT_KEYS = ["category", "city", "date"]
SLOT_STATUSES = ["unknown", "filled", "any"]
AI_CHAT_INTENTS = ["search_events", "update_filters", "reset_filters", "smalltalk", "help"]
INVALID_AI_VALUES = ["null", "", "yok", "belirtilmemiş", "belirtilmemis", "none"]

AI_FILTER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "city": {
            "type": ["string", "null"]
        },
        "category": {
            "type": ["string", "null"],
            "enum": ["Konser", "Tiyatro", "Festival", "Stand-up", "Spor", None]
        },
        "start_date": {
            "type": ["string", "null"]
        },
        "end_date": {
            "type": ["string", "null"]
        }
    },
    "required": ["city", "category", "start_date", "end_date"]
}

AI_CHAT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": AI_CHAT_INTENTS
        },
        "filters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": ["string", "null"]
                },
                "category": {
                    "type": ["string", "null"],
                    "enum": ["Konser", "Tiyatro", "Festival", "Stand-up", "Spor", None]
                },
                "start_date": {
                    "type": ["string", "null"]
                },
                "end_date": {
                    "type": ["string", "null"]
                }
            },
            "required": ["city", "category", "start_date", "end_date"]
        },
        "should_search": {
            "type": "boolean"
        },
        "needs_clarification": {
            "type": "boolean"
        },
        "assistant_reply": {
            "type": "string"
        }
    },
    "required": [
        "intent",
        "filters",
        "should_search",
        "needs_clarification",
        "assistant_reply"
    ]
}
