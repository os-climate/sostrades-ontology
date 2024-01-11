import unittest

class TestExample(unittest.TestCase):
    def test_addition(self):
        result = 2 + 2
        self.assertEqual(result, 4, "La somme de 2 + 2 devrait être égale à 4")

if __name__ == '__main__':
    unittest.main()
