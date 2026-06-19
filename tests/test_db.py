import unittest
from server.utils import db


class TestDB(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestDB, self).__init__(*args, **kwargs)
        db.init(drop=True)

    def test_user(self):
        u1username = "john"
        password = "secret"
        u1a = db.create_user(u1username, password)
        self.assertIsNotNone(u1a)
        u1b = db.get_user(u1username)
        self.assertIsNotNone(u1b)
        self.assertEqual(u1a, u1b)
        u2 = db.create_user(u1username, password)
        self.assertIsNone(u2)
        u3 = db.create_user("bob", password)
        self.assertIsNotNone(u3)
        self.assertNotEqual(u1a, u3)
        self.assertTrue(db.delete_user(u3.id))
        self.assertIsNone(db.get_user(u3.id))
        self.assertFalse(db.delete_user(100000))


if __name__ == "__main__":
    unittest.main()
