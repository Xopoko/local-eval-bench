from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


class APIError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _maybe_set_temperature(payload: dict[str, object], temperature: float) -> None:
    if temperature and temperature > 0:
        payload["temperature"] = temperature


def _normalize_reasoning_effort(value: str) -> str | None:
    if not value:
        return None
    effort = value.strip().lower()
    if not effort:
        return None
    if effort in {"xhigh", "x-high", "extra-high", "max", "maximum"}:
        return "xhigh"
    if effort in {"low", "medium", "high"}:
        return effort
    return effort


def _maybe_set_reasoning(payload: dict[str, object], effort: str | None) -> None:
    if effort:
        payload["reasoning"] = {"effort": effort}


def _request_json(
    url: str,
    payload: dict[str, object],
    api_key: str,
    timeout: float,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8") if err.fp else ""
        raise APIError(err.code, body or err.reason) from err
    except urllib.error.URLError as err:
        raise APIError(0, str(err)) from err
    if os.getenv("OPENAI_DEBUG") == "1":
        print(body, file=sys.stderr)
    return json.loads(body)


def _extract_text_from_responses(resp: dict[str, object]) -> str:
    output_text = resp.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    texts: list[str] = []
    output = resp.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type in {"output_text", "text"}:
                text = item.get("text")
                if isinstance(text, str):
                    texts.append(text)
                continue
            if item_type != "message":
                continue
            content = item.get("content")
            if isinstance(content, str):
                texts.append(content)
                continue
            if not isinstance(content, list):
                continue
            for chunk in content:
                if not isinstance(chunk, dict):
                    continue
                chunk_type = chunk.get("type")
                if chunk_type in {"output_text", "text"}:
                    text = chunk.get("text")
                    if isinstance(text, str):
                        texts.append(text)
    if texts:
        return "".join(texts)

    return ""


def _extract_text_from_chat(resp: dict[str, object]) -> str:
    choices = resp.get("choices")
    if not isinstance(choices, list) or not choices:
        raise APIError(0, "No choices in chat response")
    first = choices[0]
    if not isinstance(first, dict):
        raise APIError(0, "Invalid chat choice payload")
    message = first.get("message")
    if not isinstance(message, dict):
        raise APIError(0, "Invalid chat message payload")
    content = message.get("content")
    if not isinstance(content, str):
        return ""
    return content


def _extract_text_from_completions(resp: dict[str, object]) -> str:
    choices = resp.get("choices")
    if not isinstance(choices, list) or not choices:
        raise APIError(0, "No choices in completions response")
    first = choices[0]
    if not isinstance(first, dict):
        raise APIError(0, "Invalid completions choice payload")
    text = first.get("text")
    if not isinstance(text, str):
        return ""
    return text


def _parse_error_message(raw: str) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(data, dict) and "error" in data:
        err = data["error"]
        if isinstance(err, dict):
            message = err.get("message")
            if isinstance(message, str):
                return message
    return raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", default="md")
    parser.add_argument("--task-id", default="unknown")
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.getenv("OPENAI_TEMPERATURE", "0")),
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "1024")),
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    )
    args = parser.parse_args()

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    api_key = openrouter_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY or OPENAI_API_KEY is not set", file=sys.stderr)
        return 1

    prompt = sys.stdin.read()
    if not prompt.strip():
        print("Empty prompt received", file=sys.stderr)
        return 1

    timeout = float(os.getenv("OPENAI_TIMEOUT", "60"))
    force_chat = os.getenv("OPENAI_FORCE_CHAT", "0") == "1"
    force_endpoint = os.getenv("OPENAI_FORCE_ENDPOINT", "").lower()
    openrouter_force_endpoint = os.getenv("OPENROUTER_FORCE_ENDPOINT", "").lower()

    api_base = args.api_base
    if openrouter_key:
        api_base = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    elif os.getenv("OPENROUTER_API_BASE"):
        api_base = os.getenv("OPENROUTER_API_BASE", api_base)

    is_openrouter = "openrouter.ai" in api_base or openrouter_key is not None
    if is_openrouter:
        force_endpoint = openrouter_force_endpoint or "chat"

    extra_headers: dict[str, str] = {}
    if is_openrouter:
        referer = (
            os.getenv("OPENROUTER_HTTP_REFERER")
            or os.getenv("OPENROUTER_SITE")
            or os.getenv("OPENROUTER_REFERER")
        )
        title = os.getenv("OPENROUTER_X_TITLE") or os.getenv("OPENROUTER_TITLE")
        if referer:
            extra_headers["HTTP-Referer"] = referer
        if title:
            extra_headers["X-Title"] = title
    reasoning_effort = _normalize_reasoning_effort(
        os.getenv("OPENAI_REASONING_EFFORT", "")
    )

    if force_endpoint == "responses":
        force_chat = False

    if not force_chat and force_endpoint != "chat":
        responses_payload = {
            "model": args.model,
            "input": prompt,
        }
        _maybe_set_temperature(responses_payload, args.temperature)
        _maybe_set_reasoning(responses_payload, reasoning_effort)
        if args.max_output_tokens > 0:
            responses_payload["max_output_tokens"] = args.max_output_tokens
        try:
            resp = _request_json(
                f"{api_base}/responses",
                responses_payload,
                api_key,
                timeout,
                extra_headers=extra_headers,
            )
            text = _extract_text_from_responses(resp)
            sys.stdout.write(text)
            return 0
        except APIError as err:
            message = _parse_error_message(err.message)
            lowered = message.lower()
            if (
                reasoning_effort == "xhigh"
                and ("unsupported value" in lowered or "supported values" in lowered)
                and "xhigh" in lowered
            ):
                responses_payload["reasoning"] = {"effort": "high"}
                try:
                    resp = _request_json(
                        f"{api_base}/responses",
                        responses_payload,
                        api_key,
                        timeout,
                        extra_headers=extra_headers,
                    )
                    text = _extract_text_from_responses(resp)
                    sys.stdout.write(text)
                    return 0
                except APIError as retry_err:
                    retry_message = _parse_error_message(retry_err.message)
                    print(
                        f"API responses error ({retry_err.status}): {retry_message}",
                        file=sys.stderr,
                    )
                    return 1
            if err.status not in (400, 404, 405):
                print(f"API responses error ({err.status}): {message}", file=sys.stderr)
                return 1
            if "not supported" in message.lower() and force_endpoint == "responses":
                print(f"API responses error ({err.status}): {message}", file=sys.stderr)
                return 1

    if force_endpoint == "completions":
        chat_payload = None
    elif force_chat:
        chat_payload = {
            "model": args.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        _maybe_set_temperature(chat_payload, args.temperature)
    else:
        chat_payload = {
            "model": args.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        _maybe_set_temperature(chat_payload, args.temperature)

    if chat_payload is not None:
        _maybe_set_reasoning(chat_payload, reasoning_effort)

    if chat_payload is not None:
        if args.max_output_tokens > 0:
            chat_payload["max_tokens"] = args.max_output_tokens
        try:
            resp = _request_json(
                f"{api_base}/chat/completions",
                chat_payload,
                api_key,
                timeout,
                extra_headers=extra_headers,
            )
            text = _extract_text_from_chat(resp)
            sys.stdout.write(text)
            return 0
        except APIError as err:
            message = _parse_error_message(err.message)
            lowered = message.lower()
            if "unsupported value" in lowered and "xhigh" in lowered:
                chat_payload["reasoning"] = {"effort": "high"}
                try:
                    resp = _request_json(
                        f"{api_base}/chat/completions",
                        chat_payload,
                        api_key,
                        timeout,
                        extra_headers=extra_headers,
                    )
                    text = _extract_text_from_chat(resp)
                    sys.stdout.write(text)
                    return 0
                except APIError as retry_err:
                    retry_message = _parse_error_message(retry_err.message)
                    print(
                        f"API chat error ({retry_err.status}): {retry_message}",
                        file=sys.stderr,
                    )
                    return 1
            if "unsupported parameter" in lowered and "reasoning" in lowered:
                chat_payload.pop("reasoning", None)
                try:
                    resp = _request_json(
                        f"{api_base}/chat/completions",
                        chat_payload,
                        api_key,
                        timeout,
                        extra_headers=extra_headers,
                    )
                    text = _extract_text_from_chat(resp)
                    sys.stdout.write(text)
                    return 0
                except APIError as retry_err:
                    retry_message = _parse_error_message(retry_err.message)
                    print(
                        f"API chat error ({retry_err.status}): {retry_message}",
                        file=sys.stderr,
                    )
                    return 1
            if "not a chat model" not in lowered and force_endpoint != "chat":
                print(f"API chat error ({err.status}): {message}", file=sys.stderr)
                return 1
            if force_endpoint == "chat":
                print(f"API chat error ({err.status}): {message}", file=sys.stderr)
                return 1

    completions_payload = {
        "model": args.model,
        "prompt": prompt,
    }
    _maybe_set_temperature(completions_payload, args.temperature)
    if args.max_output_tokens > 0:
        completions_payload["max_tokens"] = args.max_output_tokens
    try:
        resp = _request_json(
            f"{api_base}/completions",
            completions_payload,
            api_key,
            timeout,
            extra_headers=extra_headers,
        )
        text = _extract_text_from_completions(resp)
        sys.stdout.write(text)
        return 0
    except APIError as err:
        message = _parse_error_message(err.message)
        print(f"API completions error ({err.status}): {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
