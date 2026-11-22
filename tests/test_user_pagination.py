import unittest
from unittest.mock import MagicMock

from sqlalchemy.dialects import sqlite

from app.schemas.user import UserFilterParams
from app.services.user import UserService


class UserPaginationTests(unittest.TestCase):
    def test_list_users_applies_offset_and_limit(self) -> None:
        params = UserFilterParams(page=2, page_size=5)
        db = MagicMock()
        db.scalar.return_value = 11
        db.scalars.return_value.all.return_value = []
        service = UserService(db=db, hasher=MagicMock())

        result = service.list_users(params)

        self.assertEqual(result.total, 11)
        statement = db.scalars.call_args.args[0]
        compiled = statement.compile(dialect=sqlite.dialect())
        sql = str(compiled)
        self.assertIn("LIMIT", sql)
        self.assertIn("OFFSET", sql)
        self.assertIn(params.offset, compiled.params.values())
        self.assertIn(params.page_size, compiled.params.values())
