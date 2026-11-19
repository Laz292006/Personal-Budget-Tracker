"""Personal Budget Tracker | COP 1500 | Lazaro Ramirez.

Run: python budget_tracker.py
All monetary amounts are stored as integer cents to avoid rounding errors.
"""

import csv
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

DATA_FILE = Path(__file__).with_name('budget_data.json')
CATEGORIES = ('Food', 'Transportation', 'Housing', 'Utilities', 'Shopping',
              'Entertainment', 'Health', 'Education', 'Other')


def dollars(cents):
    """Format an integer number of cents as currency."""
    sign = '-' if cents < 0 else ''
    return f'{sign}${abs(cents) / 100:,.2f}'


def parse_money(value):
    """Convert positive dollar input into exact integer cents."""
    try:
        amount = Decimal(str(value).strip().replace('$', '').replace(',', ''))
        if not amount.is_finite() or amount <= 0:
            raise ValueError('Amount must be greater than zero.')
        if amount.as_tuple().exponent < -2:
            raise ValueError('Use at most two decimal places.')
        cents = int((amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        if cents > 100_000_000_000:
            raise ValueError('Amount is too large.')
        return cents
    except InvalidOperation as error:
        raise ValueError('Enter a valid number, such as 12.50.') from error


def valid_date(text):
    """Check that the date follows YYYY-MM-DD and is a real calendar date."""
    try:
        return date.fromisoformat(text.strip()).isoformat()
    except (ValueError, TypeError) as error:
        raise ValueError('Enter a real date in YYYY-MM-DD format.') from error


def valid_month(text):
    """Check a YYYY-MM month string."""
    try:
        parsed = datetime.strptime(text.strip(), '%Y-%m')
        return parsed.strftime('%Y-%m')
    except (ValueError, TypeError) as error:
        raise ValueError('Enter a month in YYYY-MM format.') from error


def safe_text(value, field='Description'):
    """Prevent empty or excessively long user-provided descriptions."""
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f'{field} cannot be blank.')
    if len(cleaned) > 100:
        raise ValueError(f'{field} must have 100 characters or fewer.')
    return cleaned


class Transaction:
    """Represent one income or expense entry."""

    def __init__(self, transaction_id, kind, cents, category, description, when):
        if type(transaction_id) is not int or transaction_id < 1:
            raise ValueError('Transaction ID must be a positive integer.')
        if kind not in ('income', 'expense'):
            raise ValueError('Type must be income or expense.')
        if type(cents) is not int or cents <= 0:
            raise ValueError('Amount must be a positive number of cents.')
        if kind == 'expense' and category not in CATEGORIES:
            raise ValueError('Invalid expense category.')
        if kind == 'income' and category != 'Income':
            raise ValueError('Income category must be Income.')
        self.id = transaction_id
        self.kind = kind
        self.cents = cents
        self.category = category
        self.description = safe_text(description)
        self.date = valid_date(when)

    def to_dict(self):
        """Convert the transaction to JSON-compatible data."""
        return {'id': self.id, 'kind': self.kind, 'cents': self.cents,
                'category': self.category, 'description': self.description,
                'date': self.date}

    @classmethod
    def from_dict(cls, data):
        """Restore a transaction from saved data."""
        return cls(data['id'], data['kind'], data['cents'], data['category'],
                   data['description'], data['date'])


class BudgetTracker:
    """Manage transactions, monthly limits, and local JSON storage."""

    def __init__(self, filename=DATA_FILE):
        self.filename = Path(filename)
        self.transactions = []
        self.budgets = {}
        self.next_id = 1
        self.load()

    def load(self):
        """Read saved data, or start empty when no file exists."""
        if not self.filename.exists():
            return
        try:
            with self.filename.open('r', encoding='utf-8') as file:
                data = json.load(file)
            loaded = [Transaction.from_dict(item)
                      for item in data.get('transactions', [])]
            ids = [item.id for item in loaded]
            if len(ids) != len(set(ids)):
                raise ValueError('Duplicate transaction IDs.')
            budgets = {}
            for month, categories in data.get('budgets', {}).items():
                month = valid_month(month)
                if not isinstance(categories, dict):
                    raise ValueError('Invalid budget information.')
                budgets[month] = {}
                for category, cents in categories.items():
                    if category not in CATEGORIES or type(cents) is not int or cents <= 0:
                        raise ValueError('Invalid budget entry.')
                    budgets[month][category] = cents
            self.transactions = loaded
            self.budgets = budgets
            self.next_id = max(ids, default=0) + 1
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            print(f'Warning: Could not load saved data: {error}')
            print('Existing data was not overwritten. Starting with an empty session.')

    def save(self):
        """Save all records to a temporary file, then replace the original."""
        data = {'transactions': [item.to_dict() for item in self.transactions],
                'budgets': self.budgets}
        temporary = self.filename.with_name(self.filename.name + '.tmp')
        try:
            with temporary.open('w', encoding='utf-8') as file:
                json.dump(data, file, indent=2)
            temporary.replace(self.filename)
            return True
        except OSError as error:
            print(f'Warning: Could not save changes: {error}')
            return False

    def add(self, kind, amount, category, description, when):
        """Create and persist a new transaction."""
        cents = parse_money(amount)
        item = Transaction(self.next_id, kind, cents, category, description, when)
        self.transactions.append(item)
        self.next_id += 1
        self.save()
        return item

    def find(self, transaction_id):
        """Find a transaction by its unique ID."""
        for item in self.transactions:
            if item.id == transaction_id:
                return item
        return None

    def delete(self, transaction_id):
        """Remove a transaction if it exists."""
        item = self.find(transaction_id)
        if item is None:
            return False
        self.transactions.remove(item)
        self.save()
        return True

    def edit(self, transaction_id, amount=None, description=None):
        """Update an existing transaction's amount or description."""
        item = self.find(transaction_id)
        if item is None:
            return False
        new_cents = item.cents if amount is None else parse_money(amount)
        new_description = (item.description if description is None
                           else safe_text(description))
        item.cents = new_cents
        item.description = new_description
        self.save()
        return True

    def filtered(self, kind=None, month=None, category=None, keyword=None):
        """Return transactions matching optional filters."""
        results = []
        for item in self.transactions:
            if kind and item.kind != kind:
                continue
            if month and not item.date.startswith(month):
                continue
            if category and item.category != category:
                continue
            if keyword and keyword.lower() not in item.description.lower():
                continue
            results.append(item)
        return sorted(results, key=lambda item: (item.date, item.id), reverse=True)

    def totals(self, month=None):
        """Calculate income, expenses, and balance in cents."""
        income = 0
        expenses = 0
        for item in self.filtered(month=month):
            if item.kind == 'income':
                income += item.cents
            else:
                expenses += item.cents
        return income, expenses, income - expenses

    def by_category(self, month=None):
        """Summarize expense amounts by category."""
        totals = {category: 0 for category in CATEGORIES}
        for item in self.filtered(kind='expense', month=month):
            totals[item.category] += item.cents
        return totals

    def set_budget(self, month, category, amount):
        """Set a monthly spending limit for a category."""
        month = valid_month(month)
        if category not in CATEGORIES:
            raise ValueError('Choose a valid category.')
        cents = parse_money(amount)
        self.budgets.setdefault(month, {})[category] = cents
        self.save()

    def budget_status(self, month):
        """Return each limit, amount spent, and remaining amount."""
        month = valid_month(month)
        spending = self.by_category(month)
        return [(category, limit, spending[category], limit - spending[category])
                for category, limit in sorted(self.budgets.get(month, {}).items())]

    def export_csv(self, filename):
        """Write transactions to a CSV spreadsheet-friendly file."""
        with Path(filename).open('w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Date', 'Type', 'Category', 'Description', 'Amount'])
            for item in self.filtered():
                writer.writerow([item.id, item.date, item.kind, item.category,
                                 item.description, f'{item.cents / 100:.2f}'])


def heading(title):
    print('\n' + '=' * 60)
    print(title.center(60))
    print('=' * 60)


def ask_choice(prompt, choices):
    """Repeat until the user selects one of the allowed choices."""
    while True:
        answer = input(prompt).strip()
        if answer in choices:
            return answer
        print('Invalid choice. Please try again.')


def ask_money(prompt):
    """Keep asking until the user provides a valid monetary amount."""
    while True:
        answer = input(prompt).strip()
        try:
            parse_money(answer)
            return answer
        except ValueError as error:
            print(f'Error: {error}')


def ask_date(prompt='Date (YYYY-MM-DD, Enter for today): '):
    """Get a real calendar date, defaulting to today."""
    while True:
        answer = input(prompt).strip() or date.today().isoformat()
        try:
            return valid_date(answer)
        except ValueError as error:
            print(f'Error: {error}')


def ask_month():
    """Get a month, defaulting to the current month."""
    while True:
        answer = input('Month (YYYY-MM, Enter for current): ').strip()
        answer = answer or date.today().strftime('%Y-%m')
        try:
            return valid_month(answer)
        except ValueError as error:
            print(f'Error: {error}')


def ask_description(prompt='Description: '):
    """Ask for a nonempty description."""
    while True:
        try:
            return safe_text(input(prompt))
        except ValueError as error:
            print(f'Error: {error}')


def ask_id():
    """Get a positive transaction ID."""
    while True:
        answer = input('Transaction ID: ').strip()
        try:
            number = int(answer)
            if number > 0:
                return number
        except ValueError:
            pass
        print('Enter a positive whole-number ID.')


def choose_category():
    """Display category options and return the selected name."""
    print('\nExpense categories:')
    for index, category in enumerate(CATEGORIES, start=1):
        print(f'  {index}. {category}')
    options = {str(number) for number in range(1, len(CATEGORIES) + 1)}
    choice = ask_choice('Choose category number: ', options)
    return CATEGORIES[int(choice) - 1]


def print_transactions(items):
    """Display a readable transaction table."""
    if not items:
        print('No transactions found.')
        return
    print(f'\n{"ID":<5} {"Date":<12} {"Type":<9} {"Category":<16} {"Amount":>12}')
    print('-' * 60)
    for item in items:
        print(f'{item.id:<5} {item.date:<12} {item.kind:<9} '
              f'{item.category:<16} {dollars(item.cents):>12}')
        print(f'      Description: {item.description}')
    print(f'\nShowing {len(items)} transaction(s).')


def add_transaction(tracker):
    heading('ADD TRANSACTION')
    print('1. Income')
    print('2. Expense')
    kind = 'income' if ask_choice('Choose type: ', {'1', '2'}) == '1' else 'expense'
    category = 'Income' if kind == 'income' else choose_category()
    amount = ask_money('Amount ($): ')
    description = ask_description()
    when = ask_date()
    item = tracker.add(kind, amount, category, description, when)
    print(f'Added transaction #{item.id}: {dollars(item.cents)} ({item.kind}).')


def view_transactions(tracker):
    heading('VIEW TRANSACTIONS')
    print('1. All transactions')
    print('2. Income only')
    print('3. Expenses only')
    print('4. Transactions for a month')
    choice = ask_choice('Choose view: ', {'1', '2', '3', '4'})
    if choice == '2':
        items = tracker.filtered(kind='income')
    elif choice == '3':
        items = tracker.filtered(kind='expense')
    elif choice == '4':
        items = tracker.filtered(month=ask_month())
    else:
        items = tracker.filtered()
    print_transactions(items)


def show_summary(tracker):
    heading('FINANCIAL SUMMARY')
    print('1. All time')
    print('2. Specific month')
    choice = ask_choice('Choose summary: ', {'1', '2'})
    month = ask_month() if choice == '2' else None
    income, expenses, balance = tracker.totals(month)
    print(f'Period: {month or "All time"}')
    print(f'Total income:   {dollars(income)}')
    print(f'Total expenses: {dollars(expenses)}')
    print(f'Net balance:    {dollars(balance)}')
    print('\nExpenses by category:')
    category_totals = tracker.by_category(month)
    for category, amount in category_totals.items():
        if amount:
            share = amount / expenses * 100 if expenses else 0
            print(f'  {category:<17} {dollars(amount):>12} ({share:.1f}%)')
    if expenses == 0:
        print('  No expenses recorded for this period.')


def manage_budgets(tracker):
    heading('MONTHLY BUDGETS')
    print('1. Set or update a spending limit')
    print('2. View budget status')
    choice = ask_choice('Choose option: ', {'1', '2'})
    month = ask_month()
    if choice == '1':
        category = choose_category()
        amount = ask_money('Monthly spending limit ($): ')
        tracker.set_budget(month, category, amount)
        print(f'Saved {dollars(parse_money(amount))} limit for {category} in {month}.')
    else:
        rows = tracker.budget_status(month)
        if not rows:
            print('No budgets set for this month.')
            return
        for category, limit, spent, remaining in rows:
            status = 'OVER BUDGET' if remaining < 0 else 'Within budget'
            print(f'\n{category}: {status}')
            print(f'  Limit: {dollars(limit)} | Spent: {dollars(spent)}')
            print(f'  Remaining: {dollars(remaining)}')


def search_transactions(tracker):
    heading('SEARCH TRANSACTIONS')
    print('1. Search by description')
    print('2. Search by expense category')
    choice = ask_choice('Choose search: ', {'1', '2'})
    if choice == '1':
        keyword = ask_description('Search keyword: ')
        items = tracker.filtered(keyword=keyword)
    else:
        category = choose_category()
        items = tracker.filtered(kind='expense', category=category)
    print_transactions(items)


def edit_transaction(tracker):
    heading('EDIT TRANSACTION')
    print_transactions(tracker.filtered())
    transaction_id = ask_id()
    item = tracker.find(transaction_id)
    if item is None:
        print('Transaction not found.')
        return
    print(f'Editing #{item.id}: {item.description}, {dollars(item.cents)}')
    print('1. Change amount')
    print('2. Change description')
    print('3. Change both')
    choice = ask_choice('Choose edit: ', {'1', '2', '3'})
    amount = ask_money('New amount ($): ') if choice in ('1', '3') else None
    description = (ask_description('New description: ')
                   if choice in ('2', '3') else None)
    tracker.edit(transaction_id, amount=amount, description=description)
    print('Transaction updated.')


def delete_transaction(tracker):
    heading('DELETE TRANSACTION')
    print_transactions(tracker.filtered())
    transaction_id = ask_id()
    item = tracker.find(transaction_id)
    if item is None:
        print('Transaction not found.')
        return
    print(f'You selected: {item.description} ({dollars(item.cents)})')
    confirmation = ask_choice('Delete this transaction? (y/n): ', {'y', 'n'})
    if confirmation == 'y':
        tracker.delete(transaction_id)
        print('Transaction deleted.')
    else:
        print('Deletion canceled.')


def export_transactions(tracker):
    heading('EXPORT TRANSACTIONS')
    filename = Path(__file__).with_name('transactions_export.csv')
    try:
        tracker.export_csv(filename)
        print(f'Exported {len(tracker.transactions)} transactions to:')
        print(filename)
    except OSError as error:
        print(f'Could not export transactions: {error}')


def show_help():
    heading('HELP AND INFORMATION')
    print('This application helps track income and expenses.')
    print('Amounts must be positive, with at most two decimal places.')
    print('Dates use YYYY-MM-DD; months use YYYY-MM.')
    print('Income adds to your balance; expenses subtract from it.')
    print('Budget limits are monthly and apply to expense categories.')
    print('Records are saved in budget_data.json beside this program.')
    print('CSV exports can be opened in Excel or another spreadsheet app.')
    print('Use the menu numbers to navigate. Choose 0 to exit.')


def show_menu():
    heading('PERSONAL BUDGET TRACKER')
    print('1. Add income or expense')
    print('2. View transactions')
    print('3. View financial summary')
    print('4. Set or view monthly budgets')
    print('5. Search transactions')
    print('6. Edit transaction')
    print('7. Delete transaction')
    print('8. Export transactions to CSV')
    print('9. Help')
    print('0. Save and exit')


def main():
    """Run the menu until the user chooses to exit."""
    tracker = BudgetTracker()
    actions = {'1': add_transaction, '2': view_transactions,
               '3': show_summary, '4': manage_budgets,
               '5': search_transactions, '6': edit_transaction,
               '7': delete_transaction, '8': export_transactions}
    print('Welcome to the Personal Budget Tracker!')
    while True:
        try:
            show_menu()
            choice = ask_choice('Enter your choice (0-9): ', set('0123456789'))
            if choice == '0':
                tracker.save()
                print('Goodbye! Your budget data has been saved.')
                break
            if choice == '9':
                show_help()
            else:
                actions[choice](tracker)
        except (KeyboardInterrupt, EOFError):
            print('\nExiting safely. Goodbye!')
            tracker.save()
            break
        except (ValueError, OSError) as error:
            print(f'Error: {error}')


if __name__ == '__main__':
    main()
