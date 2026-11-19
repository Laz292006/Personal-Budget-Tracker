"""Automated tests for the Personal Budget Tracker."""
import tempfile
import unittest
from pathlib import Path
from budget_tracker import BudgetTracker, parse_money, valid_date, valid_month


class BudgetTrackerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'test_data.json'
        self.tracker = BudgetTracker(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_money_validation(self):
        self.assertEqual(parse_money('12.50'), 1250)
        self.assertEqual(parse_money('$1,000.01'), 100001)
        for invalid in ('-3', '0', 'abc', '1.999', 'NaN'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_money(invalid)

    def test_dates(self):
        self.assertEqual(valid_date('2026-11-16'), '2026-11-16')
        self.assertEqual(valid_month('2026-11'), '2026-11')
        with self.assertRaises(ValueError):
            valid_date('2026-02-30')

    def test_add_and_totals(self):
        self.tracker.add('income', '1000', 'Income', 'Paycheck', '2026-11-16')
        self.tracker.add('expense', '42.50', 'Food', 'Groceries', '2026-11-16')
        self.assertEqual(self.tracker.totals(), (100000, 4250, 95750))
        self.assertEqual(self.tracker.by_category('2026-11')['Food'], 4250)

    def test_edit_search_and_delete(self):
        item = self.tracker.add('expense', '5', 'Food', 'Coffee', '2026-11-16')
        self.assertEqual(len(self.tracker.filtered(keyword='cof')), 1)
        self.assertTrue(self.tracker.edit(item.id, '7.25', 'Tea'))
        self.assertEqual(self.tracker.find(item.id).cents, 725)
        self.assertTrue(self.tracker.delete(item.id))
        self.assertFalse(self.tracker.delete(item.id))
        self.assertEqual(len(self.tracker.filtered()), 0)

    def test_budget_and_reload(self):
        self.tracker.set_budget('2026-11', 'Food', '50')
        self.tracker.add('expense', '60', 'Food', 'Dinner', '2026-11-16')
        self.assertEqual(self.tracker.budget_status('2026-11')[0][3], -1000)
        restored = BudgetTracker(self.path)
        self.assertEqual(restored.totals(), (0, 6000, -6000))
        self.assertEqual(restored.next_id, 2)

    def test_csv_export(self):
        self.tracker.add('income', '25', 'Income', 'Gift', '2026-11-16')
        output = Path(self.directory.name) / 'export.csv'
        self.tracker.export_csv(output)
        self.assertIn('Gift', output.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
