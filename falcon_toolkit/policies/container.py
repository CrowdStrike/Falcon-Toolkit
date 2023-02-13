"""Falcon Toolkit: Policy Management.

This file contains a data model to hold a poilicy object, along with the associated Falcon
Toolkit-specific metadata required to ensure that an import will succeed.
"""
import json

from typing import Dict, List, Type

from caracara.common.policy_wrapper import Policy

from falcon_toolkit.policies.constants import POLICY_TYPES


class PolicyContainer:
    """Container for a policy that is either about to be imported or has just been exported."""

    def __init__(
        self,
        policy: Policy,
        policy_type: str,
        format_version: int = 1,
    ):
        """Create a new Policy Container object."""
        self.policy = policy
        self.policy_type = policy_type
        self.format_version = format_version

    def dumps(self) -> str:
        """Dump the Policy Container to a JSON object."""
        policy_data = self.policy.dump()

        # Mandatory fields
        export_data = {
            "format_version": self.format_version,
            "enabled": self.policy.enabled,
            "name": self.policy.name,
            "platform_name": self.policy.platform_name,
            "policy_type": self.policy_type,
            "settings_key_name": self.policy.settings_key_name,
            "settings_groups": policy_data[self.policy.settings_key_name],
        }

        # Optional fields
        if self.policy.description:
            export_data["description"] = self.policy.description

        return json.dumps(export_data, sort_keys=True, indent=2)

    @classmethod
    def loads(cls: Type["PolicyContainer"], policy_container_dump: str) -> "PolicyContainer":
        """Load a JSON string representing a policy and return a new PolicyContainer object."""
        import_data: Dict = json.loads(policy_container_dump)
        format_version = int(import_data.get("format_version", "0"))
        if format_version != 1:
            raise ValueError(
                "Policy export format version either does not exist or is not supported."
            )

        try:
            enabled: bool = import_data['enabled']
            name: str = import_data['name']
            platform_name: str = import_data['platform_name']
            policy_type: str = import_data['policy_type']
            settings_key_name: str = import_data['settings_key_name']
            settings_groups: List[Dict] = import_data['settings_groups']
        except KeyError as exc:
            raise KeyError("Policy export does not contain all the required fields.") from exc

        if policy_type not in POLICY_TYPES:
            raise ValueError(
                "Policy is not of a supported type. This version of Falcon Toolkit "
                "only supports these policy types: " +
                str(POLICY_TYPES)
            )

        description: str = import_data.get("description", "Imported by Falcon Toolkit")

        policy_dict = {
            "description": description,
            "enabled": enabled,
            "name": name,
            "platform_name": platform_name,
            settings_key_name: settings_groups,
        }
        policy = Policy(data_dict=policy_dict, style=policy_type)

        policy_container: Type["PolicyContainer"] = cls(
            policy,
            policy_type,
            format_version,
        )
        return policy_container
