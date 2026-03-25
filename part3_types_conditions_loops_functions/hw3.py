#!/usr/bin/env python

from typing import TypedDict, TypeGuard

_DateTuple = tuple[int, int, int]

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

_CATEGORY_KEY = "category"
_CATEGORY_SEP = "::"

EXPENSE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
}

_DAYS_JAN_JUN = (31, 28, 31, 30, 31, 30)
_DAYS_JUL_DEC = (31, 31, 30, 31, 30, 31)
_DAYS_IN_MONTH = _DAYS_JAN_JUN + _DAYS_JUL_DEC
_LEAP_FEB_DAYS = 29
_DD_LEN = 2
_MM_LEN = 2
_YYYY_LEN = 4
_MONTH_MIN = 1
_MONTH_MAX = 12
_DAY_MIN = 1
_LEAP_CYCLE_SMALL = 4
_LEAP_CYCLE_CENTURY = 100
_LEAP_CYCLE_FULL = 400
_DATE_PARTS = 3
_CAT_PARTS = 2
_INCOME_CMD_LEN = 3
_COST_CMD_LEN = 4
_COST_CATS_CMD_LEN = 2
_STATS_CMD_LEN = 2
_LOOP_ACTIVE = True


class _Transaction(TypedDict, total=False):
    amount: float
    date: _DateTuple
    category: str


class _IncomeTransaction(TypedDict):
    amount: float
    date: _DateTuple


class _CostTransaction(TypedDict):
    amount: float
    date: _DateTuple
    category: str


financial_transactions_storage: list[_Transaction] = []


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    if year % _LEAP_CYCLE_FULL == 0:
        return True
    if year % _LEAP_CYCLE_CENTURY == 0:
        return False
    return year % _LEAP_CYCLE_SMALL == 0


def _is_date_format_valid(day_str: str, month_str: str, year_str: str) -> bool:
    lengths_ok = (
        len(day_str) == _DD_LEN
        and len(month_str) == _MM_LEN
        and len(year_str) == _YYYY_LEN
    )
    digits_ok = (
        day_str.isdigit()
        and month_str.isdigit()
        and year_str.isdigit()
    )
    return lengths_ok and digits_ok


def extract_date(maybe_dt: str) -> _DateTuple | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: tuple формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parts = maybe_dt.split("-")
    if len(parts) != _DATE_PARTS:
        return None
    if not _is_date_format_valid(parts[0], parts[1], parts[2]):
        return None
    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])
    if month < _MONTH_MIN or month > _MONTH_MAX:
        return None
    days_in_month: list[int] = list(_DAYS_IN_MONTH)
    if is_leap_year(year):
        days_in_month[1] = _LEAP_FEB_DAYS
    if day < _DAY_MIN or day > days_in_month[month - 1]:
        return None
    return day, month, year


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append(_Transaction())
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append(_Transaction())
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append(_Transaction(amount=amount, date=parsed_date))
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append(_Transaction())
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append(_Transaction())
        return INCORRECT_DATE_MSG
    cat_parts = category_name.split(_CATEGORY_SEP)
    valid_category = (
        len(cat_parts) == _CAT_PARTS
        and cat_parts[0] in EXPENSE_CATEGORIES
        and cat_parts[1] in EXPENSE_CATEGORIES[cat_parts[0]]
    )
    if not valid_category:
        financial_transactions_storage.append(_Transaction())
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append(_Transaction(
        category=category_name,
        amount=amount,
        date=parsed_date,
    ))
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(
        f"{k}{_CATEGORY_SEP}{v}"
        for k, kv in EXPENSE_CATEGORIES.items()
        for v in kv
    )


def _date_lte(date1: _DateTuple, date2: _DateTuple) -> bool:
    _, m1, y1 = date1
    _, m2, y2 = date2
    if y1 != y2:
        return y1 < y2
    if m1 != m2:
        return m1 < m2
    return date1[0] <= date2[0]


def _is_in_report_period(date: _DateTuple, as_of_date: _DateTuple) -> bool:
    same_month = date[1] == as_of_date[1]
    same_year = date[2] == as_of_date[2]
    return same_month and same_year


def _add_to_expense_details(
    expense_details: dict[str, float],
    category: str,
    amount: float,
) -> None:
    cat_key = category.split(_CATEGORY_SEP)[1]
    expense_details[cat_key] = expense_details.get(cat_key, float(0)) + amount


def _is_income(transaction: _Transaction) -> TypeGuard[_IncomeTransaction]:
    return bool(transaction) and _CATEGORY_KEY not in transaction


def _process_income(
    transaction: _IncomeTransaction,
    as_of_date: _DateTuple,
    monthly: list[float],
) -> float:
    date = transaction["date"]
    if not _date_lte(date, as_of_date):
        return float(0)
    amount = transaction["amount"]
    if _is_in_report_period(date, as_of_date):
        monthly[0] += amount
    return amount


def _accumulate_incomes(as_of_date: _DateTuple, monthly: list[float]) -> float:
    total = float(0)
    for transaction in financial_transactions_storage:
        if _is_income(transaction):
            total += _process_income(transaction, as_of_date, monthly)
    return total


def _is_cost(transaction: _Transaction) -> TypeGuard[_CostTransaction]:
    return bool(transaction) and _CATEGORY_KEY in transaction


def _process_cost(
    transaction: _CostTransaction,
    as_of_date: _DateTuple,
    monthly: list[float],
    expense_details: dict[str, float],
) -> float:
    date = transaction["date"]
    if not _date_lte(date, as_of_date):
        return float(0)
    amount = transaction["amount"]
    category = transaction["category"]
    if _is_in_report_period(date, as_of_date):
        monthly[1] += amount
        _add_to_expense_details(expense_details, category, amount)
    return amount


def _accumulate_costs(
    as_of_date: _DateTuple,
    monthly: list[float],
    expense_details: dict[str, float],
) -> float:
    total = float(0)
    for transaction in financial_transactions_storage:
        if _is_cost(transaction):
            total += _process_cost(transaction, as_of_date, monthly, expense_details)
    return total


def _process_transactions(
    as_of_date: _DateTuple,
    expense_details: dict[str, float],
) -> tuple[float, float, float]:
    monthly: list[float] = [float(0), float(0)]
    income_total = _accumulate_incomes(as_of_date, monthly)
    cost_total = _accumulate_costs(as_of_date, monthly, expense_details)
    return income_total - cost_total, monthly[0], monthly[1]


def _format_stats(
    report_date: str,
    total_capital: float,
    month_income: float,
    month_expenses: float,
    expense_details: dict[str, float],
) -> str:
    profit_loss = month_income - month_expenses
    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
    ]
    if profit_loss >= 0:
        lines.append(f"This month, the profit amounted to {profit_loss:.2f} rubles.")
    else:
        lines.append(f"This month, the loss amounted to {abs(profit_loss):.2f} rubles.")
    lines += [
        f"Income: {month_income:.2f} rubles",
        f"Expenses: {month_expenses:.2f} rubles",
        "",
        "Details (category: amount):",
    ]
    for i, (cat, amt) in enumerate(sorted(expense_details.items()), 1):
        lines.append(f"{i}. {cat}: {amt:.2f}")
    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    parsed_date = extract_date(report_date)
    if parsed_date is None:
        return INCORRECT_DATE_MSG
    expense_details: dict[str, float] = {}
    total_capital, month_income, month_expenses = _process_transactions(parsed_date, expense_details)
    return _format_stats(report_date, total_capital, month_income, month_expenses, expense_details)


def _is_valid_decimal_core(core: str) -> bool:
    integer_part, decimal_part = core.split(".", 1)
    if not (integer_part or decimal_part):
        return False
    int_ok = not integer_part or integer_part.isdigit()
    dec_ok = not decimal_part or decimal_part.isdigit()
    return int_ok and dec_ok


def _parse_amount(s: str) -> float | None:
    normalized = s.replace(",", ".")
    core = normalized.removeprefix("-")
    if not core or core.count(".") > 1:
        return None
    if "." in core and not _is_valid_decimal_core(core):
        return None
    if "." not in core and not core.isdigit():
        return None
    return float(normalized)


def _handle_income(parts: list[str]) -> None:
    if len(parts) != _INCOME_CMD_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = _parse_amount(parts[1])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(income_handler(amount, parts[2]))


def _handle_cost(parts: list[str]) -> None:
    if len(parts) == _COST_CATS_CMD_LEN and parts[1] == "categories":
        print(cost_categories_handler())
        return
    if len(parts) != _COST_CMD_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = _parse_amount(parts[2])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    result = cost_handler(parts[1], amount, parts[3])
    print(result)
    if result == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def _handle_stats(parts: list[str]) -> None:
    if len(parts) != _STATS_CMD_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(stats_handler(parts[1]))


def _process_command(parts: list[str]) -> None:
    if not parts:
        return
    handlers = {
        "income": _handle_income,
        "cost": _handle_cost,
        "stats": _handle_stats,
    }
    handler = handlers.get(parts[0])
    if handler is None:
        print(UNKNOWN_COMMAND_MSG)
    else:
        handler(parts)


def main() -> None:
    """Ваш код здесь"""
    while _LOOP_ACTIVE:
        _process_command(input().strip().split())


if __name__ == "__main__":
    main()
