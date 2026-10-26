class VernacularTranslator:
    def __init__(self):
        # Dictionary of key disaster terminology mappings for reliable emergency template rendering
        self.glossary = {
            "Minor Damage Building": "சிறிய சேதமடைந்த கட்டிடம்",
            "Major Damage Building": "கடுமையாக சேதமடைந்த கட்டிடம்",
            "Destroyed Building": "முழுமையாக இடிந்த கட்டிடம்",
            "Blocked Road (Debris)": "சாலை அடைப்பு (இடிபாடுகள்)",
            "Flooded Road": "வெள்ளத்தில் மூழ்கிய சாலை",
            "Bridge Collapse": "பாலம் சரிவு"
        }

    def translate_sitrep_tamil(self, sitrep_english: str) -> str:
        """
        Applies offline template translation for emergency SMS formatting.
        Can be integrated with offline IndicTrans2 / Bhashini models for full-text translation.
        """
        translated_text = sitrep_english
        for en_term, ta_term in self.glossary.items():
            translated_text = translated_text.replace(en_term, f"{ta_term} ({en_term})")
            
        header = "🚨 [அவசர எச்சரிக்கை - DISASTERLENS SITREP] 🚨\n"
        return header + translated_text