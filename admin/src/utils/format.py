def format_message(text: str, **kwargs):
    for key in kwargs:
        text = text.replace(f"{{{key.upper()}}}", str(kwargs[key] or ""))
    return text
