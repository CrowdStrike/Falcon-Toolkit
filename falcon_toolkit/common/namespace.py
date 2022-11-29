"""Falcon Toolkit: Falcon Recursive Namespace."""


class FalconRecursiveNamespace:
    """Extensible namespace class that combines the best of classes and dictionaries.

    This class allows dictionaries to be treated as objects of attributes, which is advantageous for
    readability in decorators, function calls and f-strings.

    Inspired by the in-built SimpleNamespace, and adapted from this article:
    https://dev.to/taqkarim/extending-simplenamespace-for-nested-dictionaries-58e8
    """

    @staticmethod
    def _map_entry(entry):
        if isinstance(entry, dict):
            return FalconRecursiveNamespace(**entry)

        return entry

    def __init__(self, **kwargs):
        """Initialise a Falcon namespace, optionally with a pre-created dictionary."""
        for key, val in kwargs.items():
            if isinstance(val, dict):
                setattr(self, key, FalconRecursiveNamespace(**val))
            elif isinstance(val, list):
                setattr(self, key, list(map(self._map_entry, val)))
            else:
                setattr(self, key, val)

    def __contains__(self, key):
        """Check if an item exists in the namespace."""
        return hasattr(self, key)

    def __getitem__(self, key):
        """Obtain an item from the namespace."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Assign a key to a value in the namespace."""
        self.__init__(
            ** {key: value}
        )

    def __delitem__(self, key):
        """Delete an item from the namespace."""
        delattr(self, key)
