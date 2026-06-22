import unittest
from server.utils.db import DB


class TestDB(unittest.TestCase):

    def setUp(self):
        self.db = DB(drop=True)
        return super().setUp()

    def test_user(self):
        u1username = "john"
        password = "secret"
        u1a = self.db.create_user(u1username, password)
        self.assertIsNotNone(u1a)
        u1b = self.db.get_user(u1username)
        self.assertIsNotNone(u1b)
        self.assertEqual(u1a, u1b)
        u2 = self.db.create_user(u1username, password)
        self.assertIsNone(u2)
        u3 = self.db.create_user("bob", password)
        self.assertIsNotNone(u3)
        self.assertNotEqual(u1a, u3)
        self.assertTrue(self.db.delete_user(u3.id))
        self.assertIsNone(self.db.get_user(u3.id))
        self.assertFalse(self.db.delete_user(100000))


if __name__ == "__main__":
    unittest.main()
