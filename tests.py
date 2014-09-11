import unittest


class AppTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_one_equals_one(self):
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main()
