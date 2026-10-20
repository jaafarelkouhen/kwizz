import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quizz.database import connexion  # noqa: E402


@pytest.fixture
def con():
    """Base SQLite en mémoire, neuve pour chaque test."""
    c = connexion(":memory:")
    yield c
    c.close()
