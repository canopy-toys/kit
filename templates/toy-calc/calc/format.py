"""How a result is printed."""


def format_result(value: float, precision: int | None = None) -> str:
    """Return the value as text, rounded to `precision` decimal places if given.

    A whole number prints without a decimal point: 5, not 5.0.
    """
    if precision is not None:
        value = round(value, precision)
        if precision > 0:
            return f"{value:.{precision}f}"
    if value == int(value):
        return str(int(value))
    return repr(value)
