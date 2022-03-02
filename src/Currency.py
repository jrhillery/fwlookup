
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional


def currencyFmt(value, model=None, curr="$", sep=",",
                dp=".", pos="", neg="-", trailNeg=""):
    # type: (Decimal, Optional[Decimal], str, str, str, str, str, str) -> str
    """Format currency with the number of fraction digits in 'model'"""
    if model:
        value = value.quantize(model, ROUND_HALF_EVEN)
    valueParts = value.as_tuple()
    reversedResult = []
    digits = map(str, valueParts.digits)

    if valueParts.sign:
        reversedResult.append(trailNeg)
    i = valueParts.exponent

    while i < 0:
        reversedResult.append(digits.pop() if digits else "0")
        i += 1
    reversedResult.append(dp)

    if not digits:
        reversedResult.append("0")
    i = 0

    while digits:
        reversedResult.append(digits.pop())
        i += 1

        if i == 3 and digits:
            i = 0
            reversedResult.append(sep)
    # end while
    reversedResult.append(curr)
    reversedResult.append(neg if valueParts.sign else pos)

    return "".join(reversed(reversedResult))
# end currencyFmt(Decimal, Decimal, str, str, str, str, str, str)


if __name__ == "__main__":
    num = Decimal(".0004")
    thou = Decimal("123000")
    print currencyFmt(num), currencyFmt(Decimal("-1234.56"), num), currencyFmt(thou), thou.as_tuple()
