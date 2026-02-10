import json
import logging
import time

from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a technical writer for a daily HuggingFace digest website.
You will receive metadata about a trending HuggingFace model or dataset.
Your job is to produce a JSON response with exactly these fields:

1. "title": A catchy, concise title for today's report (under 100 characters).
2. "summary": A 2-4 paragraph summary that meaningfully describes what this
   model/dataset is, what it can be used for, who created it, and why it is
   notable or trending. Explain the domain, task type, and any relevant
   technical details visible in the metadata (e.g., pipeline_tag tells you the
   task, library_name tells you the framework, tags describe the domain).
   Base this ONLY on the metadata provided -- do not invent capabilities or
   facts not supported by the metadata.
3. "ideas": A JSON array of exactly 5 strings. Each string is a concise
   project idea (1-2 sentences) that someone could build using this specific
   model/dataset. Each idea must be directly derived from the metadata
   (e.g., the pipeline_tag, tags, or library). Do not suggest ideas that
   require capabilities not evidenced in the metadata.

You may also receive the project's README content. When available, use it as your
primary source for understanding the project's purpose, capabilities, and usage.
The README is authoritative -- prefer it over inferences from tags or metadata.

IMPORTANT RULES:
- Output ONLY valid JSON. No markdown, no explanation outside the JSON.
- The "ideas" array must contain 5 plain strings, NOT objects or dicts.
  Example: ["Build a chatbot using...", "Create a pipeline for..."]
- Every claim in the summary must be traceable to the metadata or README.
- Every project idea must be feasible given the model/dataset's stated capabilities.
- If the metadata is sparse and no README is available, say so honestly rather than speculating.
- Do NOT hallucinate features, benchmarks, or capabilities not present in the metadata or README.
"""

USER_PROMPT_TEMPLATE = """Here is the metadata for today's trending HuggingFace {item_type}:

```json
{metadata_json}
```

Generate the report as a JSON object with keys: "title", "summary", "ideas".
Remember: "ideas" must be an array of 5 plain strings, not objects."""


def generate_report(metadata, ollama_url, api_key, model):
    """Send metadata to the LLM and parse the structured response.

    Args:
        metadata: Dict of HuggingFace item metadata.
        ollama_url: Base URL for the Ollama server.
        api_key: API key for authentication.
        model: Model name to use.

    Returns:
        Dict with keys: title, summary, ideas.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON.
    """
    logger.info("Preparing LLM request for %s (%s)", metadata["id"], metadata["type"])
    logger.info("LLM endpoint: %s, model: %s", ollama_url, model)
    has_readme = "readme" in metadata
    logger.info("README included: %s%s", has_readme,
                f" ({len(metadata['readme'])} chars)" if has_readme else "")

    client = OpenAI(
        base_url=f"{ollama_url.rstrip('/')}/v1",
        api_key=api_key,
    )

    user_content = USER_PROMPT_TEMPLATE.format(
        item_type=metadata["type"],
        metadata_json=json.dumps(metadata, indent=2, default=str),
    )

    prompt_length = len(SYSTEM_PROMPT) + len(user_content)
    logger.info("Total prompt length: %d chars", prompt_length)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    logger.info("Sending request to LLM (attempt 1)...")
    result = _call_and_parse(client, model, messages)
    if result is not None:
        logger.info("LLM returned valid report: '%s'", result["title"])
        return result

    # Retry once with a nudge
    logger.warning("First LLM attempt failed, retrying with nudge (attempt 2)...")
    messages.append(
        {
            "role": "user",
            "content": (
                "Your previous response was not valid JSON. "
                "Please output ONLY a JSON object with keys: "
                '"title", "summary", "ideas".'
            ),
        }
    )

    result = _call_and_parse(client, model, messages)
    if result is not None:
        logger.info("LLM retry succeeded: '%s'", result["title"])
        return result

    logger.error("LLM failed to produce valid JSON after 2 attempts")
    raise ValueError("LLM failed to produce valid JSON after retry.")


def _call_and_parse(client, model, messages):
    """Make an LLM call and attempt to parse the response as JSON."""
    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=2000,
    )
    elapsed = time.time() - start
    logger.info("LLM response received in %.1fs", elapsed)

    raw_text = response.choices[0].message.content.strip()
    logger.info("Response length: %d chars", len(raw_text))
    logger.info("=== LLM Raw Response ===")
    logger.info(raw_text)
    logger.info("========================")

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        raw_text = raw_text.rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON")
        return None

    logger.info("=== Parsed LLM Result ===")
    logger.info(json.dumps(result, indent=2))
    logger.info("=========================")

    # Validate expected structure
    if "title" not in result or "summary" not in result:
        return None
    if "ideas" not in result or not isinstance(result["ideas"], list):
        return None
    if len(result["ideas"]) != 5:
        return None

    # Normalize ideas: if LLM returns dicts, extract the string value
    normalized_ideas = []
    for idea in result["ideas"]:
        if isinstance(idea, dict):
            # Try common keys: name, description, idea, title
            val = (
                idea.get("description")
                or idea.get("name")
                or idea.get("idea")
                or idea.get("title")
                or str(idea)
            )
            normalized_ideas.append(val)
        else:
            normalized_ideas.append(str(idea))
    result["ideas"] = normalized_ideas

    return result
