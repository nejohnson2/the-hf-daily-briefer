import logging
import random
import tempfile

from huggingface_hub import HfApi, hf_hub_download

logger = logging.getLogger(__name__)

MAX_README_LENGTH = 20000


def fetch_trending_item(token=None, used_names=None):
    """Fetch trending models & datasets, pick an unused one at random.

    Args:
        token: Optional HuggingFace API token.
        used_names: Set of item_name strings already reported on.

    Returns:
        A metadata dict for the selected item.

    Raises:
        RuntimeError: If no unused trending items can be found.
    """
    if used_names is None:
        used_names = set()

    api = HfApi(token=token)

    # Try with 20 first, expand to 50 if all are used
    for limit in (20, 50):
        models = list(
            api.list_models(sort="trending_score", direction=-1, limit=limit)
        )
        datasets = list(
            api.list_datasets(sort="trending_score", direction=-1, limit=limit)
        )

        pool = [(m, "model") for m in models] + [(d, "dataset") for d in datasets]

        # Filter out previously used items
        available = [(item, t) for item, t in pool if item.id not in used_names]

        if available:
            item, item_type = random.choice(available)
            return _extract_metadata(item, item_type)

    raise RuntimeError(
        "All trending items have already been reported on. "
        "Try again later when new items are trending."
    )


def _extract_metadata(item, item_type):
    """Pull relevant fields from a ModelInfo or DatasetInfo object."""
    meta = {
        "id": item.id,
        "type": item_type,
        "author": item.author,
        "downloads": item.downloads,
        "likes": item.likes,
        "trending_score": getattr(item, "trending_score", None),
        "tags": item.tags or [],
        "created_at": str(item.created_at) if item.created_at else None,
        "last_modified": str(item.last_modified) if item.last_modified else None,
    }

    if item_type == "model":
        meta["pipeline_tag"] = getattr(item, "pipeline_tag", None)
        meta["library_name"] = getattr(item, "library_name", None)

    if hasattr(item, "card_data") and item.card_data:
        meta["card_data_summary"] = str(item.card_data)[:2000]

    return meta


def fetch_readme(repo_id, item_type, token=None):
    """Download the README.md for a specific HuggingFace repo.

    Args:
        repo_id: The exact repo ID (e.g. "meta-llama/Llama-3-8B").
        item_type: "model" or "dataset" — determines the repo_type.
        token: Optional HuggingFace API token.

    Returns:
        The README content as a string, or None if unavailable.
    """
    repo_type = "dataset" if item_type == "dataset" else "model"

    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename="README.md",
            repo_type=repo_type,
            token=token,
            cache_dir=tempfile.mkdtemp(),
        )
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) > MAX_README_LENGTH:
            logger.info(
                "README for %s is %d chars, truncating to %d",
                repo_id, len(content), MAX_README_LENGTH,
            )
            content = content[:MAX_README_LENGTH] + "\n\n[... truncated ...]"

        logger.info("Fetched README for %s (%d chars)", repo_id, len(content))
        return content

    except Exception as e:
        logger.warning("Could not fetch README for %s: %s", repo_id, e)
        return None
