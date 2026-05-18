from __future__ import annotations

import json
import os
import subprocess
import sys
from json import JSONDecoder

from common import output_path, require_env, write_output


def extract_last_json_blob(text: str) -> dict:
    decoder = JSONDecoder()
    last_obj = None
    for idx, char in enumerate(text):
        if char != "{":
            continue
        try:
            obj, _end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            last_obj = obj
    if last_obj is None:
        raise RuntimeError("OpenClaw output did not contain a valid JSON object")
    return last_obj


def parse_json_candidate(text: str) -> dict | None:
    candidate = text.strip()
    if not candidate:
        return None
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3:
            candidate = "\n".join(lines[1:-1]).strip()
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def extract_agent_payload(text: str) -> dict:
    envelope = parse_json_candidate(text)
    if envelope:
        meta = envelope.get("result", {})
        candidates: list[str] = []
        final_text = meta.get("meta", {}).get("finalAssistantRawText")
        if isinstance(final_text, str) and final_text.strip():
            candidates.append(final_text)
        for payload in meta.get("payloads", []) or []:
            payload_text = payload.get("text") if isinstance(payload, dict) else None
            if isinstance(payload_text, str) and payload_text.strip():
                candidates.append(payload_text)
        for candidate in candidates:
            parsed = parse_json_candidate(candidate)
            if parsed:
                return parsed
            try:
                return extract_last_json_blob(candidate)
            except RuntimeError:
                continue
        if envelope.get("status") == "ok":
            raise RuntimeError("OpenClaw JSON envelope did not contain a valid assistant JSON payload")
    return extract_last_json_blob(text)




def load_env_file(path_str: str) -> dict[str, str]:
    path = os.path.expanduser(path_str)
    if not os.path.exists(path):
        return {}
    loaded: dict[str, str] = {}
    for raw_line in open(path, 'r', encoding='utf-8'):
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            loaded[key] = value
    return loaded

def default_exec_command() -> str:
    return 'openclaw agent --agent "$LLM_WIKI_OPENCLAW_AGENT_ID" --message "$LLM_WIKI_OPENCLAW_PROMPT" --json'


def main() -> int:
    agent_id = require_env("LLM_WIKI_OPENCLAW_AGENT_ID")
    prompt = require_env("LLM_WIKI_OPENCLAW_PROMPT")
    timeout_seconds = int(os.getenv("OPENCLAW_AGENT_TIMEOUT_SECONDS", "180"))
    command = os.getenv("OPENCLAW_EXEC_COMMAND", "").strip() or default_exec_command()

    env = os.environ.copy()
    env.update(load_env_file('~/.openclaw/.env'))
    env["LLM_WIKI_OPENCLAW_AGENT_ID"] = agent_id
    env["LLM_WIKI_OPENCLAW_PROMPT"] = prompt

    try:
        result = subprocess.run(
            command,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"OpenClaw command timed out after {timeout_seconds} seconds") from exc

    merged = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    if result.returncode != 0 and not merged:
        raise RuntimeError(f"OpenClaw command failed with exit code {result.returncode}")

    payload = extract_agent_payload(merged)
    write_output(payload)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
