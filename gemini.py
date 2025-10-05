import json
import logging
import os

from google import genai
from google.genai import types
from pydantic import BaseModel


logger = logging.getLogger('LupinBot.gemini')

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


class CodeDetectionResult(BaseModel):
    contains_code: bool
    confidence: float


def detect_code_in_image(image_bytes: bytes, mime_type: str = "image/png") -> bool:
    try:
        system_prompt = (
            "You are a programming code detection expert. "
            "Analyze the image and determine if it contains any programming code, "
            "code snippets, terminal output, IDE screenshots, or code-related content. "
            "Respond with JSON in this format: "
            "{'contains_code': boolean, 'confidence': number between 0 and 1}")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                "Does this image contain programming code, code snippets, terminal output, or code-related content?"
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=CodeDetectionResult,
            ),
        )

        raw_json = response.text
        logger.info(f"Gemini code detection response: {raw_json}")

        if raw_json:
            data = json.loads(raw_json)
            result = CodeDetectionResult(**data)
            return result.contains_code and result.confidence > 0.5
        else:
            logger.warning("Empty response from Gemini")
            return False

    except Exception as e:
        logger.error(f"Failed to analyze image with Gemini: {e}")
        return False
