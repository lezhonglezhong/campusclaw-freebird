"""Guard SQLite-only material FTS helpers on a MySQL-bound session."""

from types import SimpleNamespace

from campusclaw.knowledge_indexing import refresh_keyword_index, remove_keyword_index
from campusclaw.retrieval import (
    index_material, initialize_retrieval_index, remove_material_from_index,
)


class MySQLSessionWithoutLegacyFTS:
    def get_bind(self):
        return SimpleNamespace(dialect=SimpleNamespace(name="mysql"))

    def execute(self, *_args, **_kwargs):
        raise AssertionError("SQLite FTS SQL must not run on MySQL")


def test_mysql_upload_and_seed_index_helpers_skip_legacy_fts():
    session = MySQLSessionWithoutLegacyFTS()
    material = SimpleNamespace(id=6, class_id=1)
    initialize_retrieval_index(session)
    index_material(session, material, "teacher upload or seed body")


def test_mysql_delete_helpers_skip_legacy_fts():
    session = MySQLSessionWithoutLegacyFTS()
    remove_material_from_index(session, 6)
    remove_keyword_index(session, [11])


def test_mysql_chunk_refresh_uses_relational_fulltext_index():
    session = MySQLSessionWithoutLegacyFTS()
    refresh_keyword_index(session, SimpleNamespace(chunks=[]), [11])
