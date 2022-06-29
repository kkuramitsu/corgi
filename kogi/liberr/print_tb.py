from inspect import isclass
import sys
import linecache
from traceback import print_exception


def bold(s):
    return f'\033[01m{s}\033[0m'


def glay(s):
    return f'\033[07m{s}\033[0m'


def red(s):
    return f'\033[31m{s}\033[0m'


def green(s):
    return f'\033[32m{s}\033[0m'


def yellow(s):
    return f'\033[33m{s}\033[0m'


def blue(s):
    return f'\033[34m{s}\033[0m'


def cyan(s):
    return f'\033[36m{s}\033[0m'


dots = green('...')

REPR_VALUE = {

}


def kogi_register_repr(typename, repr_func):
    REPR_VALUE[typename] = repr_func


def repr_value(value):
    typename = type(value).__name__
    if typename in REPR_VALUE:
        return REPR_VALUE[typename](value)
    if hasattr(value, '__name__'):
        return cyan(f'({typename})')+value.__name__
    if isinstance(value, list) and len(value) > 1:
        return f'[{value[0]}, {dots}]'
    if isinstance(value, str):
        return red(repr(value))
    return repr(value)


def repr_vars(vars):
    ss = []
    for key, value in vars.items():
        if key.startswith('_'):
            continue
        ss.append(f'{bold(key)}={repr_value(value)}')
    return ' '.join(ss)


def getline(filename, lines, n):
    if filename == '<string>':
        if 0 <= n-1 < len(lines):
            return lines[n-1]
        return ''
    return linecache.getline(filename, n).rstrip()


def arrow(lineno, here=False):
    s = str(lineno)
    if here:
        arrow = '-' * max(5-len(s), 0) + '> '
    else:
        arrow = ' ' * max(5-len(s), 0) + '  '
    return red(arrow) + green(f'{s}')


def filter_globals(vars, code):
    if 'get_ipython' in vars:
        newvars = {}
        for key, value in vars.items():
            if key in code:
                newvars[key] = value
        return newvars
    return vars


def print_func(filename, funcname, local_vars):
    if funcname.startswith('<ipython-input-'):
        t = funcname.split('-')
        if len(t) > 2:
            filename = f'[{t[2]}]'
    if '/ipykernel_' in filename:
        print(f'{bold(funcname)} {repr_vars(local_vars)}')
    else:
        print(f'"{glay(filename)}" {bold(funcname)} {repr_vars(local_vars)}')


def print_linecode(filename, lines, lineno):
    if lineno-2 > 0:
        print(arrow(lineno-2), getline(filename, lines, lineno-2))
    if lineno-1 > 0:
        print(arrow(lineno-1), getline(filename, lines, lineno-1))
    print(arrow(lineno, here=True), getline(filename, lines, lineno))
    print(arrow(lineno+1), getline(filename, lines, lineno+1))
    print(arrow(lineno+2), getline(filename, lines, lineno+2))


def print_header(etype):
    print(red('-'*79))
    etype = str(etype.__name__).ljust(46) + ' Traceback(most recent call last)'
    print(bold(red(etype)))


def print_syntax_error(code, exception, slots=''):
    lines = code.splitlines()
    filename = exception.filename
    slots['lineno'] = lineno = exception.lineno
    slots['line'] = text = exception.text
    slots['offset'] = exception.offset
    print_func(filename, f'[lineno: {lineno}]', {})
    if lineno-2 > 0:
        print(arrow(lineno-2), getline(filename, lines, lineno-2))
    if lineno-1 > 0:
        print(arrow(lineno-1), getline(filename, lines, lineno-1))
    print(arrow(lineno, here=True), getline(filename, lines, lineno))
    offset = max(0, offset-1)
    print(arrow(lineno), ' '*offset+bold(red('^^')))
    print(f"{bold(red(exception.__class__.__name__))}: {bold(exception.msg)}")
    return slots


def kogi_print_exc(code='', exc_info=None, exception=None):
    if exc_info is None:
        etype, evalue, tb = sys.exc_info()
    else:
        etype, evalue, tb = exc_info
    slots = dict(
        code=code,
        emsg=(f'{etype}: {evalue}').strip()
    )
    lines = code.splitlines()

    if isinstance(exception, SyntaxError):
        return print_syntax_error(lines, exception, slots)
    if exception is None and issubclass(etype, SyntaxError):
        try:
            raise
        except SyntaxError as e:
            exception = e
        return print_syntax_error(lines, exception, slots)

    print_header(etype)

    prev = None
    repeated = 0
    while tb:
        filename = tb.tb_frame.f_code.co_filename
        funcname = tb.tb_frame.f_code.co_name
        lineno = tb.tb_lineno
        local_vars = filter_globals(tb.tb_frame.f_locals, code)
        cur = (filename, funcname, lineno)
        if cur != prev:
            if repeated > 10:
                print(f'... repeated {red(str(repeated))} times ...')
            print_func(filename, funcname, local_vars)
            print_linecode(filename, lines, lineno)
            repeated = 0
        else:
            if repeated < 10:
                print_func(filename, funcname, local_vars)
            repeated += 1
        prev = cur
        tb = tb.tb_next

    print(f"{bold(red(etype.__name__))}: {bold(evalue)}")
    return slots
