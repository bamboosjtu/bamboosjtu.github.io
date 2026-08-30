# tools/expandable.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from tools.base import Tool


class Expandable(ABC):
    """
    Expandable is ONLY a capability: it can yield a list of tools.
    Not tied to decorators.
    """

    @abstractmethod
    def expand(self) -> List[Tool]:
        raise NotImplementedError
