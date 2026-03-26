from enum import StrEnum
from functools import reduce


class Permission(StrEnum):
    ADMIN = "admin"
    QUERY_EXECUTE = "query.execute"
    PLUGIN_ENABLE = "plugin.enable"
    PLUGIN_DISABLE = "plugin.disable"
    MCP_QUERY = "mcp.query"


# Plone role → set of platform permissions. Default is empty (DENY ALL).
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "Manager": {Permission.ADMIN, Permission.QUERY_EXECUTE, Permission.PLUGIN_ENABLE, Permission.PLUGIN_DISABLE, Permission.MCP_QUERY},
    "Site Administrator": {Permission.ADMIN, Permission.QUERY_EXECUTE, Permission.PLUGIN_ENABLE, Permission.PLUGIN_DISABLE, Permission.MCP_QUERY},
    "Editor": {Permission.QUERY_EXECUTE, Permission.MCP_QUERY},
    "Reviewer": {Permission.QUERY_EXECUTE, Permission.MCP_QUERY},
    "Member": {Permission.QUERY_EXECUTE},
}


def get_permissions(plone_roles: list[str]) -> set[Permission]:
    """
    Return the union of all permissions for the given Plone roles.
    Unknown roles contribute zero permissions (default DENY).
    """
    if not plone_roles:
        return set()
    return reduce(
        lambda acc, role: acc | ROLE_PERMISSIONS.get(role, set()),
        plone_roles,
        set(),
    )
