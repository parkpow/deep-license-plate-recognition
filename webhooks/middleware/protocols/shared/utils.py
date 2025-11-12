import logging
from typing import Any, Optional

def get_header(header_name: str, json_data: dict[str, Any]) -> Optional[str]:
    header = json_data.get("webhook_header", {})
    return header.get(header_name)

def get_required_header(header_name: str, json_data: dict[str, Any], log_context: str = "") -> tuple[str | None, tuple[str, int] | None]:
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