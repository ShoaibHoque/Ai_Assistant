import re

class NLUProcessor:
    def __init__(self, model_name="xlm-roberta-base"):
        from transformers import pipeline
        self.entity_recognizer = pipeline("ner", model=model_name)

    def parse_intent_and_entities(self, text, lang="en"):
        # Define intents
        intents = {
            "en": {"request_money": "request money"},
            "ar": {"request_money": "طلب الأموال"}
        }
        intent = "unknown_intent"
        for key, phrase in intents[lang].items():
            if phrase in text.lower():
                intent = key
                break

        # Entity extraction
        entities = self.entity_recognizer(text)
        extracted_info = {entity["entity"]: entity["word"] for entity in entities}

        # Pattern matching for fallback
        project_name = re.search(r"project (named|name|called)?\s*(\w[\w\s]*)", text, re.IGNORECASE)
        amount = re.search(r"\b\d+(\.\d{1,2})?\b", text)  # Matches amounts like 500, 500.50
        reason = re.search(r"to buy (\w[\w\s]*)", text, re.IGNORECASE)

        # Normalize fields
        normalized_entities = {
            "PROJECT_NAME": extracted_info.get("PROJECT_NAME", project_name.group(2).strip() if project_name else ""),
            "AMOUNT": extracted_info.get("AMOUNT", amount.group(0).strip() if amount else ""),
            "REASON": extracted_info.get("REASON", reason.group(1).strip() if reason else ""),
        }

        return {"intent": intent, "entities": normalized_entities}
