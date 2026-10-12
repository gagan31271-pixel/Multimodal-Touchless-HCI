# ============================================================
# AI ENGINE
#
# Summarization -> Ollama
# Translation    -> Gemini -> Ollama fallback
#
# Gemini uses direct REST API requests with a hard timeout.
# This avoids long SDK retry delays.
# ============================================================

import os
import requests

from dotenv import load_dotenv

# ------------------------------------------------------------
# Load .env before reading the API key
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

# Hard HTTP timeout for each Gemini model request.
GEMINI_TIMEOUT_SECONDS = 12

# Maximum number of Gemini models to try.
GEMINI_MODELS = (
    GEMINI_MODEL,
    GEMINI_FALLBACK_MODEL,
)


class AIEngine:

    def __init__(self):

        # ----------------------------------------------------
        # Current project architecture:
        #
        # Summarization -> Ollama
        # Translation    -> Gemini -> Ollama
        # ----------------------------------------------------

        self.provider = (
            AI_PROVIDER
            .lower()
            .strip()
        )

        self.last_result = ""

        self.last_error = ""

    # ========================================================
    # GEMINI API KEY
    # ========================================================

    @staticmethod
    def get_gemini_api_key():

        return (
            os.getenv(
                "GEMINI_API_KEY"
            )
            or
            GEMINI_API_KEY
        )

    # ========================================================
    # CLEAN INPUT
    # ========================================================

    @staticmethod
    def clean_input(
        text
    ):

        if not text:

            return ""

        text = str(
            text
        ).strip()

        if (
            len(text)
            >
            AI_MAX_INPUT_CHARACTERS
        ):

            text = (
                text[
                    :AI_MAX_INPUT_CHARACTERS
                ]
                +
                "\n[Input truncated]"
            )

        return text

    # ========================================================
    # SUMMARY PROMPT
    # ========================================================

    def build_summary_prompt(
        self,
        text,
        output_language="English"
    ):

        return f"""
Summarize the following text in {output_language}.

Return only the concise summary.
Keep the main idea and important facts.
Do not explain your process.
Do not add information.

TEXT:
{text}
""".strip()

    # ========================================================
    # TRANSLATION PROMPT
    # ========================================================

    def build_translation_prompt(
        self,
        text,
        target_language="English"
    ):

        return f"""
Translate the following text into {target_language}.

Return only the translation.
Preserve the complete meaning.
Do not summarize.
Do not explain.
Do not add information.

TEXT:
{text}
""".strip()

    # ========================================================
    # OLLAMA GENERAL REQUEST
    # ========================================================

    def ollama_generate(
        self,
        prompt
    ):

        url = (
            OLLAMA_HOST.rstrip("/")
            +
            "/api/chat"
        )

        payload = {

            "model": OLLAMA_MODEL,

            "messages": [

                {
                    "role": "system",
                    "content": (
                        "Follow the requested task exactly. "
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

                "num_predict": (
                    AI_MAX_OUTPUT_TOKENS
                ),
            },
        }

        response = requests.post(
            url,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        result = (
            data
            .get(
                "message",
                {}
            )
            .get(
                "content",
                ""
            )
            .strip()
        )

        if not result:

            raise RuntimeError(
                "Ollama returned an empty response."
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
        is temporarily unavailable.
        """

        prompt = f"""
You are a professional translation engine.

Translate the SOURCE TEXT into {target_language}.

Important:
- Return ONLY the translated text.
- Do not explain anything.
- Do not summarize.
- Do not repeat the instructions.
- Do not translate the instructions.
- Preserve names, numbers, dates, and facts.
- Preserve the complete meaning.
- Use natural {target_language} grammar.
- Use the native script of {target_language}.

Example:
English: The weather is pleasant today.
Kannada: ಇಂದು ಹವಾಮಾನವು ಆಹ್ಲಾದಕರವಾಗಿದೆ.

SOURCE TEXT:
{text}

TRANSLATION:
""".strip()

        url = (
            OLLAMA_HOST.rstrip("/")
            +
            "/api/chat"
        )

        payload = {

            "model": OLLAMA_MODEL,

            "messages": [

                {
                    "role": "system",
                    "content": (
                        "You are a professional translation "
                        "engine. Return only the translation."
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

                "num_predict": 1600,
            },
        }

        response = requests.post(
            url,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        result = (
            data
            .get(
                "message",
                {}
            )
            .get(
                "content",
                ""
            )
            .strip()
        )

        if not result:

            raise RuntimeError(
                "Ollama translation returned "
                "an empty response."
            )

        return result

    # ========================================================
    # GEMINI REST REQUEST
    #
    # Uses direct HTTP request.
    # No hidden SDK retry loop.
    # ========================================================

    def gemini_generate(
        self,
        prompt
    ):

        api_key = (
            self.get_gemini_api_key()
        )

        if not api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        last_error = None

        # ====================================================
        # TRY GEMINI MODELS
        # ====================================================

        for model_name in GEMINI_MODELS:

            if not model_name:

                continue

            try:

                print(
                    f"Gemini model: "
                    f"{model_name}"
                )

                url = (
                    "https://generativelanguage.googleapis.com"
                    "/v1beta/models/"
                    f"{model_name}:generateContent"
                )

                headers = {
                    "Content-Type":
                        "application/json",

                    "x-goog-api-key":
                        api_key,
                }

                payload = {

                    "contents": [

                        {
                            "parts": [

                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ],

                    "generationConfig": {

                        "temperature": 0.1,

                        "maxOutputTokens": 1600,

                        "thinkingConfig": {

                            "thinkingLevel": "low"
                        },
                    },
                }

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=GEMINI_TIMEOUT_SECONDS,
                )

                # ------------------------------------------------
                # SUCCESS
                # ------------------------------------------------

                if response.ok:

                    data = response.json()

                    candidates = (
                        data.get(
                            "candidates",
                            []
                        )
                    )

                    if not candidates:

                        raise RuntimeError(
                            "Gemini returned no candidates."
                        )

                    content = (
                        candidates[0]
                        .get(
                            "content",
                            {}
                        )
                    )

                    parts = (
                        content.get(
                            "parts",
                            []
                        )
                    )

                    result_parts = []

                    for part in parts:

                        part_text = (
                            part.get(
                                "text",
                                ""
                            )
                            .strip()
                        )

                        if part_text:

                            result_parts.append(
                                part_text
                            )

                    result = "\n".join(
                        result_parts
                    ).strip()

                    if not result:

                        raise RuntimeError(
                            "Gemini returned an empty result."
                        )

                    return result

                # ------------------------------------------------
                # TEMPORARY SERVER / QUOTA ERRORS
                # ------------------------------------------------

                if response.status_code in (
                    429,
                    500,
                    502,
                    503,
                    504,
                ):

                    print(
                        f"Gemini {model_name} "
                        f"returned HTTP "
                        f"{response.status_code}."
                    )

                    last_error = (
                        f"Gemini HTTP "
                        f"{response.status_code}"
                    )

                    # Try next Gemini model.
                    continue

                # ------------------------------------------------
                # OTHER API ERROR
                # ------------------------------------------------

                try:

                    error_data = (
                        response.json()
                    )

                except Exception:

                    error_data = (
                        response.text
                    )

                raise RuntimeError(
                    f"Gemini API error "
                    f"{response.status_code}: "
                    f"{error_data}"
                )

            # ----------------------------------------------------
            # TIMEOUT
            # ----------------------------------------------------

            except requests.exceptions.Timeout:

                print(
                    f"Gemini {model_name} "
                    f"timed out after "
                    f"{GEMINI_TIMEOUT_SECONDS} seconds."
                )

                last_error = (
                    "Gemini request timed out."
                )

                continue

            # ----------------------------------------------------
            # NETWORK ERROR
            # ----------------------------------------------------

            except requests.exceptions.RequestException as error:

                print(
                    f"Gemini request error: "
                    f"{error}"
                )

                last_error = str(
                    error
                )

                continue

            # ----------------------------------------------------
            # OTHER ERROR
            # ----------------------------------------------------

            except Exception as error:

                last_error = str(
                    error
                )

                continue

        # --------------------------------------------------------
        # ALL GEMINI MODELS FAILED
        # --------------------------------------------------------

        raise RuntimeError(
            "Gemini translation is temporarily "
            "unavailable. "
            f"{last_error or ''}"
        )

    # ========================================================
    # GENERAL GENERATE
    #
    # Current configuration:
    #
    # AI_PROVIDER = "ollama"
    #
    # Therefore:
    # generate() -> Ollama
    # ========================================================

    def generate(
        self,
        prompt
    ):

        prompt = self.clean_input(
            prompt
        )

        if not prompt:

            return ""

        self.last_error = ""

        try:

            if self.provider == "ollama":

                result = (
                    self.ollama_generate(
                        prompt
                    )
                )

            elif self.provider == "gemini":

                result = (
                    self.gemini_generate(
                        prompt
                    )
                )

            else:

                raise ValueError(
                    f"Unsupported AI provider: "
                    f"{self.provider}"
                )

            self.last_result = result

            return result

        except Exception as error:

            self.last_error = (
                f"AI generation error: "
                f"{error}"
            )

            self.last_result = ""

            raise

    # ========================================================
    # SUMMARIZE
    #
    # Uses Ollama.
    # ========================================================

    def summarize(
        self,
        text,
        output_language="English"
    ):

        text = self.clean_input(
            text
        )

        if not text:

            raise ValueError(
                "No text provided for summarization."
            )

        prompt = (
            self.build_summary_prompt(
                text,
                output_language
            )
        )

        return self.generate(
            prompt
        )

    # ========================================================
    # TRANSLATE
    #
    # Primary  -> Gemini
    # Fallback -> Ollama
    # ========================================================

    def translate(
        self,
        text,
        target_language="English"
    ):

        text = self.clean_input(
            text
        )

        if not text:

            raise ValueError(
                "No text provided for translation."
            )

        prompt = (
            self.build_translation_prompt(
                text,
                target_language
            )
        )

        # ====================================================
        # PRIMARY: GEMINI
        # ====================================================

        try:

            result = (
                self.gemini_generate(
                    prompt
                )
            )

            self.last_result = result

            self.last_error = ""

            print(
                "Translation provider: Gemini"
            )

            return result

        except Exception as gemini_error:

            print(
                "Gemini unavailable."
            )

            print(
                "Using local Ollama translation fallback..."
            )

            # =================================================
            # FALLBACK: OLLAMA
            # =================================================

            try:

                result = (
                    self.ollama_translate(
                        text,
                        target_language
                    )
                )

                self.last_result = result

                self.last_error = ""

                print(
                    "Translation provider: Ollama"
                )

                return result

            except Exception as ollama_error:

                self.last_result = ""

                self.last_error = (
                    "Gemini and Ollama translation "
                    "both failed. "
                    f"Gemini: {gemini_error} | "
                    f"Ollama: {ollama_error}"
                )

                raise RuntimeError(
                    self.last_error
                )

    # ========================================================
    # PROVIDER
    # ========================================================

    def get_provider(
        self
    ):

        return self.provider

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(
        self
    ):

        return {

            "provider":
                self.provider,

            "last_result":
                self.last_result,

            "last_error":
                self.last_error,
        }