# ============================================================
# AI ENGINE
#
# Summarization -> Ollama
# Translation   -> Gemini -> Ollama fallback
#
# Features:
# - Gemini REST API with timeout handling
# - Multiple Gemini model fallback
# - Ollama local AI generation
# - Improved translation prompt
# - Configurable input and output limits
# - Error handling and status reporting
# ============================================================

import os
import time
import requests
import threading
from collections import OrderedDict

from dotenv import load_dotenv

# ------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------

load_dotenv()

from config import (
    AI_PROVIDER,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_FALLBACK_MODEL,
    AI_MAX_INPUT_CHARACTERS,
    AI_MAX_OUTPUT_TOKENS,
    AI_TEMPERATURE,
)


# ============================================================
# GEMINI SETTINGS
# ============================================================

GEMINI_TIMEOUT_SECONDS = 12

GEMINI_MODELS = tuple(
    dict.fromkeys(
        model.strip()
        for model in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL)
        if model and model.strip()
    )
)

GEMINI_MAX_OUTPUT_TOKENS = 1024
TRANSLATION_CACHE_MAX_ITEMS = 64

OLLAMA_TRANSLATION_MAX_OUTPUT_TOKENS = 2048
OLLAMA_TRANSLATION_CONTEXT_TOKENS = 8192


class AIEngine:

    # Small shared cache avoids repeating identical translations when Streamlit
    # reruns or the user clicks Translate again for the same text/language.
    _translation_cache = OrderedDict()
    _translation_cache_lock = threading.Lock()

    def __init__(self):
        self.session = requests.Session()
        # Configured provider is used for general generation/summarization.
        self.provider = str(AI_PROVIDER).lower().strip()

        # Track the provider that actually handled the most recent operation.
        self.last_provider = self.provider
        self.last_result = ""
        self.last_error = ""

    # ========================================================
    # GEMINI API KEY
    # ========================================================

    @staticmethod
    def get_gemini_api_key():
        return (
            os.getenv("GEMINI_API_KEY")
            or GEMINI_API_KEY
        )

    # ========================================================
    # CLEAN INPUT
    # ========================================================

    @staticmethod
    def clean_input(text):
        if text is None:
            return ""

        text = str(text).strip()

        if len(text) > AI_MAX_INPUT_CHARACTERS:
            text = (
                text[:AI_MAX_INPUT_CHARACTERS]
                + "\n[Input truncated]"
            )

        return text

    # ========================================================
    # SUMMARY PROMPT
    # ========================================================

    def build_summary_prompt(
        self,
        text,
        output_language="English",
    ):
        return f"""
Summarize the following text in {output_language}.

Requirements:
- Preserve the main idea and important facts.
- Include the most relevant details.
- Use clear, natural language.
- Do not invent information.
- Return only the summary.

TEXT:
{text}
""".strip()

    # ========================================================
    # TRANSLATION PROMPT
    # ========================================================

    def build_translation_prompt(
        self,
        text,
        target_language="English",
    ):
        # Keep instructions short to reduce prompt processing overhead.
        return (
            f"Translate the text into natural {target_language}. "
            "Preserve meaning, names, numbers, and dates. "
            "Do not summarize, add explanations, or include anything except the translation.\n\n"
            f"TEXT:\n{text}"
        )

    # ========================================================
    # OLLAMA GENERAL REQUEST
    # ========================================================

    def ollama_generate(self, prompt):

        url = (
            OLLAMA_HOST.rstrip("/")
            + "/api/chat"
        )

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Follow the requested task accurately. "
                        "Return only the requested result."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
            "options": {
                "temperature": AI_TEMPERATURE,
                "num_predict": AI_MAX_OUTPUT_TOKENS,
            },
        }

        response = requests.post(
            url,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()
        data = response.json()

        message = data.get("message", {})
        result = str(message.get("content", "")).strip()

        if not result:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        if data.get("done_reason") == "length":
            raise RuntimeError(
                "Ollama output reached its token limit. "
                "Increase AI_MAX_OUTPUT_TOKENS."
            )

        return result

    # ========================================================
    # OLLAMA TRANSLATION FALLBACK
    # ========================================================

    def ollama_translate(
        self,
        text,
        target_language="Kannada",
    ):
        """
        Local translation fallback used when Gemini
        is unavailable.
        """

        if not str(text or "").strip():
            raise ValueError(
                "No text provided for translation."
            )

        prompt = f"""
You are a professional translation engine.

TASK:
Translate the source text into natural {target_language}.

RULES:
- Translate every sentence completely.
- Use correct {target_language} grammar and natural wording.
- Use the native script of {target_language} wherever applicable.
- Preserve the meaning of every sentence.
- Preserve names, numbers, dates, and facts.
- Do not summarize.
- Do not omit details.
- Do not invent information.
- Do not repeat the source text.
- Do not translate these instructions.
- Return only the translation.

SOURCE TEXT:
{text}

TRANSLATION:
""".strip()

        url = (
            OLLAMA_HOST.rstrip("/")
            + "/api/chat"
        )

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful translation engine. "
                        "Translate faithfully and naturally. "
                        "Return only the translated text."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": OLLAMA_TRANSLATION_MAX_OUTPUT_TOKENS,
                "num_ctx": OLLAMA_TRANSLATION_CONTEXT_TOKENS,
            },
        }

        response = self.session.post(
            url,
            json=payload,
            timeout=(3, 60),
        )

        response.raise_for_status()
        data = response.json()

        result = str(
            data.get("message", {}).get("content", "")
        ).strip()

        if not result:
            raise RuntimeError(
                "Ollama translation returned an empty response."
            )

        if data.get("done_reason") == "length":
            raise RuntimeError(
                "Ollama translation reached its output-token limit. "
                "The translation may be incomplete."
            )

        return result

    # ========================================================
    # GEMINI REST REQUEST
    # ========================================================

    def gemini_generate(self, prompt):
        """Generate text with Gemini, retrying temporary service failures."""
        api_key = self.get_gemini_api_key()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        last_error = None
        transient_statuses = {408, 429, 500, 502, 503, 504}
        max_attempts_per_model = 2
        retry_delay_seconds = 2

        for model_name in GEMINI_MODELS:
            url = (
                "https://generativelanguage.googleapis.com"
                "/v1beta/models/"
                f"{model_name}:generateContent"
            )
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            }
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS,
                    "thinkingConfig": {"thinkingLevel": "low"},
                },
            }

            for attempt in range(1, max_attempts_per_model + 1):
                print(
                    f"Gemini model: {model_name} "
                    f"(attempt {attempt}/{max_attempts_per_model})"
                )
                try:
                    response = requests.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=(10, GEMINI_TIMEOUT_SECONDS),
                    )

                    if response.ok:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            last_error = f"Gemini model {model_name} returned no candidates."
                            print(last_error)
                            break

                        candidate = candidates[0]
                        parts = candidate.get("content", {}).get("parts", [])
                        result = "\n".join(
                            str(part.get("text", "")).strip()
                            for part in parts
                            if part.get("text")
                        ).strip()

                        if candidate.get("finishReason") == "MAX_TOKENS":
                            last_error = (
                                f"Gemini model {model_name} reached its output-token limit; "
                                "the response may be incomplete."
                            )
                            print(last_error)
                            break
                        if not result:
                            last_error = f"Gemini model {model_name} returned an empty result."
                            print(last_error)
                            break
                        return result

                    if response.status_code in transient_statuses:
                        last_error = (
                            f"Gemini model {model_name} returned HTTP "
                            f"{response.status_code}."
                        )
                        print(last_error)
                        if attempt < max_attempts_per_model:
                            print(f"Retrying in {retry_delay_seconds} seconds...")
                            time.sleep(retry_delay_seconds)
                            continue
                        break

                    try:
                        error_data = response.json()
                    except ValueError:
                        error_data = response.text
                    raise RuntimeError(
                        f"Gemini API error {response.status_code}: {error_data}"
                    )

                except requests.exceptions.Timeout:
                    last_error = (
                        f"Gemini model {model_name} timed out after "
                        f"{GEMINI_TIMEOUT_SECONDS} seconds."
                    )
                    print(last_error)
                    if attempt < max_attempts_per_model:
                        print(f"Retrying in {retry_delay_seconds} seconds...")
                        time.sleep(retry_delay_seconds)
                        continue
                    break

                except requests.exceptions.RequestException as error:
                    last_error = f"Gemini network error for {model_name}: {error}"
                    print(last_error)
                    if attempt < max_attempts_per_model:
                        print(f"Retrying in {retry_delay_seconds} seconds...")
                        time.sleep(retry_delay_seconds)
                        continue
                    break

        raise RuntimeError(
            "Gemini translation/generation failed after retries. "
            f"{last_error or 'No configured Gemini model succeeded.'}"
        )

    # ========================================================
    # FAST GEMINI TRANSLATION (no long retry chain)
    # ========================================================

    def gemini_translate_generate(self, prompt):
        """Use the primary Gemini model once for low-latency translation."""
        api_key = self.get_gemini_api_key()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        if not GEMINI_MODELS:
            raise RuntimeError("No Gemini model is configured.")

        model_name = GEMINI_MODELS[0]
        url = (
            "https://generativelanguage.googleapis.com"
            "/v1beta/models/"
            f"{model_name}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingLevel": "low"},
            },
        }
        response = self.session.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            json=payload,
            timeout=(3, 12),
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini model {model_name} returned no candidates.")

        candidate = candidates[0]
        if candidate.get("finishReason") == "MAX_TOKENS":
            raise RuntimeError("Gemini translation reached its output-token limit.")
        parts = candidate.get("content", {}).get("parts", [])
        result = "\n".join(
            str(part.get("text", "")).strip()
            for part in parts
            if part.get("text")
        ).strip()
        if not result:
            raise RuntimeError(f"Gemini model {model_name} returned an empty result.")
        return result

    # ========================================================
    # GENERAL GENERATE
    # ========================================================

    def generate(self, prompt):

        prompt = self.clean_input(prompt)

        if not prompt:
            return ""

        self.last_error = ""

        try:
            if self.provider == "ollama":
                result = self.ollama_generate(prompt)

            elif self.provider == "gemini":
                result = self.gemini_generate(prompt)

            else:
                raise ValueError(
                    f"Unsupported AI provider: {self.provider}"
                )

            self.last_result = result
            self.last_provider = self.provider
            return result

        except Exception as error:
            self.last_error = f"AI generation error: {error}"
            self.last_result = ""
            raise

    # ========================================================
    # SUMMARIZE
    # ========================================================

    def summarize(
        self,
        text,
        output_language="English",
    ):

        text = self.clean_input(text)

        if not text:
            raise ValueError(
                "No text provided for summarization."
            )

        prompt = self.build_summary_prompt(
            text,
            output_language,
        )

        return self.generate(prompt)

    def _cache_translation(self, key, value):
        with self._translation_cache_lock:
            self._translation_cache[key] = value
            self._translation_cache.move_to_end(key)
            while len(self._translation_cache) > TRANSLATION_CACHE_MAX_ITEMS:
                self._translation_cache.popitem(last=False)

    # ========================================================
    # TRANSLATE
    # ========================================================

    def translate(
        self,
        text,
        target_language="English",
    ):

        text = self.clean_input(text)

        if not text:
            raise ValueError(
                "No text provided for translation."
            )

        cache_key = (text, str(target_language).strip().casefold())
        with self._translation_cache_lock:
            cached = self._translation_cache.get(cache_key)
            if cached is not None:
                self._translation_cache.move_to_end(cache_key)
                self.last_result = cached
                self.last_provider = "cache"
                self.last_error = ""
                return cached

        prompt = self.build_translation_prompt(
            text,
            target_language,
        )

        self.last_error = ""

        # --------------------------------------------
        # PRIMARY: GEMINI
        # --------------------------------------------

        try:
            result = self.gemini_translate_generate(prompt)

            self.last_result = result
            self.last_provider = "gemini"
            self.last_error = ""
            self._cache_translation(cache_key, result)

            print("Translation provider: Gemini")

            return result

        except Exception as gemini_error:
            print(f"Fast Gemini translation unavailable: {gemini_error}")
            print("Using local Ollama translation fallback...")

        # --------------------------------------------
        # FALLBACK: OLLAMA
        # --------------------------------------------

        try:
            result = self.ollama_translate(
                text,
                target_language,
            )

            self.last_result = result
            self.last_provider = "ollama"
            self.last_error = ""
            self._cache_translation(cache_key, result)

            print("Translation provider: Ollama")

            return result

        except Exception as ollama_error:
            self.last_result = ""
            self.last_provider = "unavailable"

            self.last_error = (
                "Gemini and Ollama translation both failed. "
                f"Gemini: {gemini_error} | "
                f"Ollama: {ollama_error}"
            )

            raise RuntimeError(self.last_error) from ollama_error

    # ========================================================
    # PROVIDER
    # ========================================================

    def get_provider(self):
        """Return the provider that handled the most recent successful operation."""
        return self.last_provider

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(self):
        return {
            # Actual provider used for the most recent operation.
            "provider": self.last_provider,
            # Configured provider used by general generation/summarization.
            "configured_provider": self.provider,
            "last_result": self.last_result,
            "last_error": self.last_error,
        }

