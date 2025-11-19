import logging
import os
from typing import Any


def replace_env_vars(obj: Any) -> Any:
    """
    Recursively replace environment variable placeholders in strings.
    Placeholders should be in the format ${VAR_NAME}.
    """
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    elif isinstance(obj, dict):
        return {k: replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_env_vars(item) for item in obj]
    return obj


def get_header(header_name: str, json_data: dict[str, Any]) -> str | None:
    header = json_data.get("webhook_header", {})
    return header.get(header_name)


def get_required_header(
    header_name: str, json_data: dict[str, Any], log_context: str = ""
) -> tuple[str | None, tuple[str, int] | None]:
    """
    Gets a required header. If missing, logs an error and returns an error tuple.
    """
    header_value = get_header(header_name, json_data)
    if header_value is None:
        error_message = f"The {header_name.replace('_', ' ')} is required."
        log_message = f"The '{header_name}' is required but was not provided in header."
        if log_context:
            log_message += f" ({log_context})"
        logging.error(log_message)
        return None, (error_message, 400)
    return header_value, None
