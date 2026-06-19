import unittest
from server.utils import kdf


class TestKDF(unittest.TestCase):
    def test_ok(self):
        password = "crazyturtoise"
        hash = kdf.hash(password)
        self.assertTrue(kdf.verify(password, hash))

    def test_nok(self):
        hash = kdf.hash("amazingflower")
        self.assertFalse(kdf.verify("bluemarble", hash))


if __name__ == "__main__":
    unittest.main()
