from __future__ import annotations

from typing import Any

from ..errors import ContractError


def role_value(roles: dict[str, Any], selector: str) -> Any:
    cursor: Any = roles
    for component in selector.split("."):
        if isinstance(cursor, dict) and component in cursor:
            cursor = cursor[component]
        else:
            raise ContractError(f"unknown semantic role: {selector}")
    return cursor


def expand_channel(roles: dict[str, Any], channel: str) -> list[tuple[str, str]]:
    try:
        role, property_name = channel.rsplit(".", 1)
    except ValueError as exc:
        raise ContractError(f"invalid semantic channel: {channel}") from exc
    wildcard = role.endswith(".*")
    if wildcard:
        role = role[:-2]
    value = role_value(roles, role)
    if wildcard:
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise ContractError(f"wildcard role is not a node list: {channel}")
        nodes = value
    else:
        if not isinstance(value, str):
            raise ContractError(f"role is not a node: {channel}")
        nodes = [value]
    return [(node, property_name) for node in nodes]


def expanded_channels(
    roles: dict[str, Any], channels: list[str]
) -> set[tuple[str, str]]:
    return {
        item
        for channel in channels
        for item in expand_channel(roles, channel)
    }
