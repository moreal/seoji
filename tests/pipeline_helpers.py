from datetime import date

import pytest

from seoji.lod.load import load_dump
from seoji.nlseoji.harvest import harvest_range
from tests.lod_helpers import SAMPLE_FOREIGN, SAMPLE_KR
from tests.seoji_helpers import paged_handler


@pytest.fixture
def loaded(db, make_client):
    """bronze filled from the LOD fixtures and the synthetic Seoji pages."""
    load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    load_dump(db, SAMPLE_FOREIGN, dataset="book", fmt="rdfxml", dump_date=None)
    client, _, _ = make_client(paged_handler)
    harvest_range(db, client, date(2022, 5, 9), date(2022, 5, 9), page_size=2)
    return db


@pytest.fixture
def built(loaded):
    """silver and gold rebuilt from the fixtures."""
    from seoji.silver.build import rebuild_silver

    rebuild_silver(loaded)
    return loaded
