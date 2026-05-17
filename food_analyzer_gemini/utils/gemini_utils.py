import json
import os
import re
from typing import Any, Dict

from google import genai
from PIL import Image


DEFAULT_MODEL = "gemini-3.1-flash-lite"


def get_client(api_key: str | None = None):
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is missing.")
    return genai.Client(api_key=key)


def build_prompt() -> str:
    return """
You are a food image analysis assistant.

Task:
Analyze the uploaded food or beverage image and return ONLY valid JSON.

Rules:
- Identify the food/drink item shown in the image.
- Detect visible ingredients and likely ingredients.
- Estimate the suitable age group.
- Mention nutrition summary in a simple way.
- Mention allergen risks.
- Mention health notes or warnings.
- If the image is unclear, say so honestly.
- Do not give dangerous medical advice.
- Keep the output compact and practical.

Return JSON with exactly these keys:

{
  "item_name": "",
  "category": "",
  "ingredients_detected": [],
  "ingredients_likely": [],
  "suitable_age_group": {
    "group": "",
    "reason": ""
  },
  "nutrition_summary": {
    "calories": "",
    "sugar": "",
    "caffeine": "",
    "fat": "",
    "salt": ""
  },
  "allergen_risks": [],
  "health_notes": [],
  "confidence": "low|medium|high",
  "short_conclusion": ""
}

Important:
- If this is a packaged item, use the label if visible.
- If not fully visible, infer carefully.
- Output only JSON. No markdown. No extra text.
""".strip()


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {
        "item_name": "Unknown",
        "category": "Unknown",
        "ingredients_detected": [],
        "ingredients_likely": [],
        "suitable_age_group": {"group": "Unknown", "reason": "Could not parse model output."},
        "nutrition_summary": {
            "calories": "Unknown",
            "sugar": "Unknown",
            "caffeine": "Unknown",
            "fat": "Unknown",
            "salt": "Unknown",
        },
        "allergen_risks": [],
        "health_notes": ["Model output could not be parsed correctly."],
        "confidence": "low",
        "short_conclusion": "Analysis unavailable.",
    }


def analyze_food_image(
    image: Image.Image,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    client = get_client(api_key)

    if image.mode != "RGB":
        image = image.convert("RGB")

    prompt = build_prompt()
    response = client.models.generate_content(
        model=model,
        contents=[prompt, image],
    )

    raw_text = getattr(response, "text", "") or ""
    return _extract_json(raw_text)