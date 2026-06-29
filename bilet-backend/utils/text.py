def normalize_text_for_intent(text):
    return (
        text.lower()
        .replace("i̇", "i")
        .replace("\u0307", "")
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def contains_any(text, terms):
    return any(term in text for term in terms)
