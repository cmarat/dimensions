import codecs
import logging
import re
import pint

logging.basicConfig()

# The vocabulary contains duplicate symbols with symbols appearing later in the
# file taking preference. Reversing the file gives better results, but this
# approach is fragile and should be replaced by explicit choice of units.
vocab = codecs.open('vocabulary.txt', encoding='utf-8').readlines()[::-1]
registry = pint.UnitRegistry(vocab, on_redefinition='warn')


def value_in_brackets(header):
    value = ''
    open_brackets = 0
    for c in header[::-1]:
        value = c + value
        if c == ')':
            open_brackets += 1
        elif c == '(':
            open_brackets -= 1
        if open_brackets == 0:
            return value[1:-1]
    return ''


# Filter common sources of false positives
not_unit = re.compile('.*[0-9=]')


def parse_unit(literal):
    if not_unit.match(literal):
        return ''
    # Pint has problems with ' and "
    may_be_quantity = re.sub('[\'"]', '', literal)

    try:
        quantity = registry(may_be_quantity, case_sensitive=True)
    except:
        return None
    else:
        if not getattr(quantity, 'dimensionless', True):
            unit = quantity.units
            return unit
    # dimensionless units go here
    return ''


def parse_headers(headers):
    for i, header in enumerate(headers):
        unit = parse_unit(header) or parse_unit(value_in_brackets(header))
        if unit:
            dimensionality = registry.get_dimensionality(unit)
            yield i, str(unit), str(dimensionality), header


def main():
    headers = codecs.open('headers.txt', encoding='utf8').read().split('\n')
    with codecs.open('units.txt', 'w', encoding='utf-8') as fout:
        fout.write(u"{0:<8}{1:<60}{2:<60}{3:<}\n".format(
            "index", "unit", "dimensionality", "header"))
        for result in parse_headers(headers):
            fout.write(u"{0:<8}{1:<50}{2:<70}{3:<}\n".format(*result))


if __name__ == '__main__':
    main()
