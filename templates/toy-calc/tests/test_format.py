import unittest

from calc.format import format_result


class FormatTest(unittest.TestCase):
    def test_whole_number_has_no_point(self) -> None:
        self.assertEqual(format_result(5.0), "5")

    def test_fraction(self) -> None:
        self.assertEqual(format_result(1.5), "1.5")

    def test_precision(self) -> None:
        self.assertEqual(format_result(1 / 3, 2), "0.33")

    def test_precision_zero(self) -> None:
        self.assertEqual(format_result(2.6, 0), "3")
