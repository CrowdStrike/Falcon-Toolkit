"""Falcon Toolkit: Authentication Backends.

This file configures the default authentication backends.
"""
from falcon_toolkit.common.auth_backends.public_mssp import PublicCloudFlightControlParentCIDBackend
from falcon_toolkit.common.auth_backends.public_single_cid import PublicCloudSingleCIDBackend


DEFAULT_AUTH_BACKENDS = [
    PublicCloudSingleCIDBackend,  # This one should be first (default)
    PublicCloudFlightControlParentCIDBackend,
]
