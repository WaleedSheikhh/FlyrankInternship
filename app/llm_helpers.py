import os
import re
import time
import random
import logging
from openai import OpenAI, APITimeoutError, RateLimitError, APIStatusError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_calls")

llm_client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    timeout=30.0,
    max_retries=0,
)


def load_prompt():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "prompts", "enrich-v1.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return match.group(0)


def call_model_with_retry(messages, max_attempts=3):
    last_exception = None
    for attempt in range(max_attempts):
        start = time.time()
        try:
            response = llm_client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                temperature=0.2,
                messages=messages,
            )
            duration_ms = int((time.time() - start) * 1000)
            usage = response.usage
            logger.info(
                f"llm_call prompt_version=enrich-v1 model={os.environ['LLM_MODEL']} "
                f"input_tokens={usage.prompt_tokens} output_tokens={usage.completion_tokens} "
                f"duration_ms={duration_ms} attempt={attempt + 1}"
            )
            return response.choices[0].message.content
        except (APITimeoutError, RateLimitError) as e:
            last_exception = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"llm_call retryable_error={type(e).__name__} waiting={wait:.1f}s attempt={attempt + 1}")
            time.sleep(wait)
        except APIStatusError as e:
            if e.status_code >= 500:
                last_exception = e
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"llm_call retryable_error=5xx waiting={wait:.1f}s attempt={attempt + 1}")
                time.sleep(wait)
            else:
                logger.info(f"llm_call non_retryable_error={e.status_code}")
                raise
    raise last_exception