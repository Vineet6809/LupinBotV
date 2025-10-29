import json
import logging
import os

from google import genai
from google.genai import types
from pydantic import BaseModel


logger = logging.getLogger('LupinBot.gemini')

# Lazy initialization - only create client when needed
_client = None

def get_client():
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return None
        try:
            _client = genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to create Gemini client: {e}")
            return None
    return _client

class CodeDetectionResult(BaseModel):
    contains_code: bool
    confidence: float


def detect_code_in_image(image_bytes: bytes, mime_type: str = "image/png") -> bool:
    try:
        client = get_client()
        if client is None:
            logger.warning("Gemini client not available, accepting image as fallback")
            return True
        
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
            logger.warning("Empty response from Gemini, accepting image as fallback")
            return True

    except Exception as e:
        logger.error(f"Failed to analyze image with Gemini (quota/error), accepting image as fallback: {e}")
        return True


def generate_challenge_from_history(history_samples: list[str], guild_name: str, channel_name: str) -> str:
    """Generate a weekly coding challenge based on last 7 days' history using Gemini.
    Falls back to a generic challenge when API unavailable.
    """
    try:
        client = get_client()
        if client is None:
            # Fallback simple challenge
            return (
                "Build a small project inspired by your recent work: implement a CLI tool that parses input, "
                "applies a transformation (e.g., sorting/filtering), and outputs results with tests."
            )
        
        context_snippets = "\n\n".join(history_samples[:30]) or "No specific code available."
        system_instruction = (
            "You are a senior coding mentor crafting a single, clear weekly coding challenge for a Discord coding community. "
            "Use the provided recent history snippets (messages or code fragments) as inspiration to make the challenge relevant. "
            "Constraints: The challenge should be unique to this community, self-contained, doable within a week, and flexible across languages. "
            "Output only the challenge text (2-5 sentences) without additional commentary, markdown headings, or code blocks."
        )
        user_prompt = (
            f"Guild: {guild_name}\nChannel: {channel_name}\n\n"
            f"Recent history (last 7 days, snippets):\n{context_snippets}\n\n"
            "Now produce one compelling weekly challenge based on recurring themes or skills from the context."
        )

        resp = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.8,
            ),
        )
        text = (resp.text or "").strip()
        if not text:
            return "Design and implement a small application covering I/O, data structures, and error handling, with unit tests."
        # Trim overly long outputs
        return text[:1000]
    except Exception as e:
        logger.error(f"Gemini challenge generation failed: {e}")
        return (
            "Create a small app inspired by your recent work: ingest data, perform meaningful transformations, and expose a simple interface."
        )
