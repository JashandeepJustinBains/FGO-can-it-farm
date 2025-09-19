import os
import re
from typing import Tuple, List, Dict, Any


def read_file(path: str) -> str:
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def summarize_execution(logs: str, output_md: str) -> Tuple[str, int, int, List[Dict[str, Any]]]:
    """
    Simple summarizer that extracts counts of successes/failures from logs and attempts to parse result blocks from the output_md.
    This is intentionally lightweight and mirrors the high-level behavior expected by the Flask app.
    """
    success_count = len(re.findall(r"SUCCESS", logs))
    failure_count = len(re.findall(r"FAILURE|ERROR", logs))

    # Try to find JSON-like result blocks in output_md (very tolerant)
    results = []
    # naive pattern for result entries starting with 'Result:' or code blocks
    result_blocks = re.split(r"\n-{3,}\n", output_md)
    for block in result_blocks:
        block = block.strip()
        if not block:
            continue
        if len(block) < 20:
            continue
        results.append({'snippet': block[:100]})

    summary = f"{success_count} successful runs, {failure_count} failures"
    return summary, success_count, failure_count, results
