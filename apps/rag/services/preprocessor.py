import re

from models.interfaces import BasePreprocessor

# Hebrew combining diacritics (nikud, cantillation marks)
_NIKUD = re.compile(r"[֑-ׇ]")
# Unicode RTL/LTR control marks and zero-width characters
_CONTROL = re.compile(r"[​‎‏‪-‮⁦-⁩﻿]")
# Maqaf (Hebrew hyphen) → space
_MAQAF = re.compile(r"־")
# Collapse multiple whitespace to single space
_WHITESPACE = re.compile(r"\s+")


class HebrewPreprocessor(BasePreprocessor):
    def clean(self, texts: list[str]) -> list[str]:
        cleaned = []
        for text in texts:
            text = _NIKUD.sub("", text)
            text = _CONTROL.sub("", text)
            text = _MAQAF.sub(" ", text)
            text = _WHITESPACE.sub(" ", text).strip()
            if text:
                cleaned.append(text)
        return cleaned
