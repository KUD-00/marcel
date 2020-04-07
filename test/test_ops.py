import os
import pathlib

import marcel.main
import marcel.object.host
from marcel.util import *

import test_base

Error = marcel.object.error.Error
start_dir = os.getcwd()
MAIN = marcel.main.Main()
TEST = test_base.Test(MAIN)


def test_no_such_op():
    TEST.run('gen 5 | abc', expected_err='Unknown op abc')


def test_gen():
    # Explicit out
    TEST.run('gen 5 | out',
             expected_out=[0, 1, 2, 3, 4])
    # Implicit out
    TEST.run('gen 5',
             expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 10 | out',
             expected_out=[10, 11, 12, 13, 14])
    TEST.run('gen 5 10 123 | out',
             expected_err='unrecognized arguments: 123')
    TEST.run('gen 5 -5 | out',
             expected_out=[-5, -4, -3, -2, -1])
    TEST.run('gen 3 -p 2 | out',
             expected_out=['00', '01', '02'])
    TEST.run('gen 3 --pad 2 | out',
             expected_out=['00', '01', '02'])
    TEST.run('gen 3 99 -p 3 | out',
             expected_out=['099', '100', '101'])
    TEST.run('gen 3 99 -p 2 | out',
             expected_err='Padding too small')
    TEST.run('gen 3 -p 3 99 | out',
             expected_err='unrecognized arguments: 99')
    TEST.run('gen 3 -10 -p 4 | out',
             expected_err='Padding incompatible with START < 0')
    # Error along with output
    TEST.run('gen 3 -1 | map (x: 5 / x)',
             expected_out=[-5.0, Error('division by zero'), 5.0])


def test_out():
    output_filename = '/tmp/out.txt'
    TEST.run('gen 3 | out {}',
             expected_out=[0, 1, 2])
    TEST.run('gen 3',
             expected_out=[0, 1, 2])
    TEST.run('gen 3 | out -c',
             expected_out=[0, 1, 2])
    TEST.run('gen 3 | out --csv',
             expected_out=[0, 1, 2])
    TEST.run('gen 3 | out -c {}',
             expected_err='-c/--csv and FORMAT specifications are incompatible')
    TEST.run(f'gen 3 | out -f {output_filename}',
             expected_out=[0, 1, 2], file=output_filename)
    TEST.run(f'gen 3 | out --file {output_filename}',
             expected_out=[0, 1, 2], file=output_filename)
    TEST.delete_file(output_filename)
    TEST.run(f'gen 3 | out -a {output_filename}',
             expected_out=[0, 1, 2],
             file=output_filename)
    TEST.run(f'gen 3 | out --append {output_filename}',
             expected_out=[0, 1, 2, 0, 1, 2],
             file=output_filename)
    TEST.run(f'gen 3 | out -a {output_filename} -f {output_filename}',
             expected_err='argument -f/--file: not allowed with argument -a/--append')
    TEST.delete_file(output_filename)


def test_sort():
    TEST.run('gen 5 | sort', expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 | sort (lambda x: -x)', expected_out=[4, 3, 2, 1, 0])
    TEST.run('gen 5 | map (x: (-x, x)) | sort', expected_out=[(-4, 4), (-3, 3), (-2, 2), (-1, 1), (0, 0)])


def test_map():
    TEST.run('gen 5 | map (x: -x)',
             expected_out=[0, -1, -2, -3, -4])
    TEST.run('gen 5 | map (lambda x: -x)',
             expected_out=[0, -1, -2, -3, -4])
    TEST.run('map (3)',
             expected_out=[3])
    TEST.run('map (: 3)',
             expected_out=[3])
    TEST.run('map (lambda: 3)',
             expected_out=[3])


def test_select():
    TEST.run('gen 5 | select (x: True)',
             expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 | select (x: False)',
             expected_out=[])
    TEST.run('gen 5 | select (x: x % 2 == 1)',
             expected_out=[1, 3])


def test_red():
    # Test function symbols
    TEST.run('gen 5 1 | red +',
             expected_out=[15])
    TEST.run('gen 5 1 | red *',
             expected_out=[120])
    TEST.run('gen 5 1 | red ^',
             expected_out=[1])
    TEST.run('gen 20 1 | select (x: x in (3, 7, 15)) | red &',
             expected_out=[3])
    TEST.run('gen 75 | select (x: x in (18, 36, 73)) | red \|',
             expected_out=[127])
    TEST.run('gen 3 | map (x: x == 1) | red and',
             expected_out=[False])
    TEST.run('gen 3 | map (x: x == 1) | red or',
             expected_out=[True])
    TEST.run('gen 5 | red max',
             expected_out=[4])
    TEST.run('gen 5 | red min',
             expected_out=[0])
    # Test incremental reduction
    TEST.run('gen 5 1 | red -i +',
             expected_out=[(1, 1), (2, 3), (3, 6), (4, 10), (5, 15)])
    # Test incremental reduction
    TEST.run('gen 5 1 | red --incremental +',
             expected_out=[(1, 1), (2, 3), (3, 6), (4, 10), (5, 15)])
    # Test lambdas
    TEST.run('gen 5 1 | map (x: (x, x)) | red (x, y: x + y) (x, y: x * y)',
             expected_out=[(15, 120)])
    # Test multiple reduction
    TEST.run('gen 5 1 | map (x: (x, x)) | red + *',
             expected_out=[(15, 120)])
    # Test multiple incremental reduction
    TEST.run('gen 5 1 | map (x: (x, x)) | red -i + *',
             expected_out=[(1, 1, 1, 1),
                           (2, 2, 3, 2),
                           (3, 3, 6, 6),
                           (4, 4, 10, 24),
                           (5, 5, 15, 120)])
    # Test grouping
    TEST.run('gen 9 1 | map (x: (x, x // 2, x * 100, x // 2)) | red + . + .',
             expected_out=[(1, 0, 100, 0),
                           (5, 1, 500, 1),
                           (9, 2, 900, 2),
                           (13, 3, 1300, 3),
                           (17, 4, 1700, 4)])
    # Test incremental grouping
    TEST.run('gen 9 1 | map (x: (x, x // 2, x * 100, x // 2)) | red -i + . + .',
             expected_out=[(1, 0, 100, 0, 1, 100),
                           (2, 1, 200, 1, 2, 200),
                           (3, 1, 300, 1, 5, 500),
                           (4, 2, 400, 2, 4, 400),
                           (5, 2, 500, 2, 9, 900),
                           (6, 3, 600, 3, 6, 600),
                           (7, 3, 700, 3, 13, 1300),
                           (8, 4, 800, 4, 8, 800),
                           (9, 4, 900, 4, 17, 1700)])


def test_expand():
    # Test singletons
    TEST.run('gen 5 | expand',
             expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 | map (x: ([x, x],)) | expand',
             expected_out=[0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
    TEST.run('gen 5 | map (x: ((x, x),)) | expand',
             expected_out=[0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
    TEST.run('gen 5 | expand 0',
             expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 | map (x: ([x, x],)) | expand 0',
             expected_out=[0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
    TEST.run('gen 5 | map (x: ((x, x),)) | expand 0',
             expected_out=[0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
    # Test non-singletons
    TEST.run('gen 5 | map (x: (x, -x)) | expand',
             expected_out=[0, 0, 1, -1, 2, -2, 3, -3, 4, -4])
    TEST.run('gen 5 | map (x: (x, -x)) | expand 0',
             expected_out=[(0, 0), (1, -1), (2, -2), (3, -3), (4, -4)])
    TEST.run('gen 5 | map (x: (x, -x)) | expand 1',
             expected_out=[(0, 0), (1, -1), (2, -2), (3, -3), (4, -4)])
    TEST.run('gen 5 | map (x: (x, -x)) | expand 2',
             expected_out=[(0, 0), (1, -1), (2, -2), (3, -3), (4, -4)])
    # Expand list
    TEST.run('gen 5 | map (x: ([100, 200], x, -x)) | expand 0',
             expected_out=[(100, 0, 0),
                           (200, 0, 0),
                           (100, 1, -1),
                           (200, 1, -1),
                           (100, 2, -2),
                           (200, 2, -2),
                           (100, 3, -3),
                           (200, 3, -3),
                           (100, 4, -4),
                           (200, 4, -4)])
    TEST.run('gen 5 | map (x: (x, [100, 200], -x)) | expand 1',
             expected_out=[(0, 100, 0),
                           (0, 200, 0),
                           (1, 100, -1),
                           (1, 200, -1),
                           (2, 100, -2),
                           (2, 200, -2),
                           (3, 100, -3),
                           (3, 200, -3),
                           (4, 100, -4),
                           (4, 200, -4)])
    TEST.run('gen 5 | map (x: (x, -x, [100, 200])) | expand 2',
             expected_out=[(0, 0, 100),
                           (0, 0, 200),
                           (1, -1, 100),
                           (1, -1, 200),
                           (2, -2, 100),
                           (2, -2, 200),
                           (3, -3, 100),
                           (3, -3, 200),
                           (4, -4, 100),
                           (4, -4, 200)])
    TEST.run('gen 5 | map (x: (x, -x, [100, 200])) | expand 3',
             expected_out=[(0, 0, [100, 200]),
                           (1, -1, [100, 200]),
                           (2, -2, [100, 200]),
                           (3, -3, [100, 200]),
                           (4, -4, [100, 200])])
    # Expand tuple
    TEST.run('gen 5 | map (x: ((100, 200), x, -x)) | expand 0',
             expected_out=[(100, 0, 0),
                           (200, 0, 0),
                           (100, 1, -1),
                           (200, 1, -1),
                           (100, 2, -2),
                           (200, 2, -2),
                           (100, 3, -3),
                           (200, 3, -3),
                           (100, 4, -4),
                           (200, 4, -4)])
    # Expand file
    with open('/tmp/test_expand_1', 'w') as file:
        file.writelines(['abc\n', 'def\n'])  # lf at end of file
    with open('/tmp/test_expand_2', 'w') as file:
        file.writelines(['ghi\n', 'jkl'])  # No lf at end of file
    TEST.run('ls /tmp/test_expand_? | expand',
             expected_out=['abc', 'def', 'ghi', 'jkl'])
    TEST.run('ls /tmp/test_expand_? | map (f: (str(f), f)) | expand 1',
             expected_out=[('/tmp/test_expand_1', 'abc'),
                           ('/tmp/test_expand_1', 'def'),
                           ('/tmp/test_expand_2', 'ghi'),
                           ('/tmp/test_expand_2', 'jkl')])
    os.remove('/tmp/test_expand_1')
    os.remove('/tmp/test_expand_2')


def test_head():
    TEST.run('gen 100 | head 0',
             expected_out=[])
    TEST.run('gen 100 | head 1',
             expected_out=[0])
    TEST.run('gen 100 | head 2',
             expected_out=[0, 1])
    TEST.run('gen 100 | head 3',
             expected_out=[0, 1, 2])
    TEST.run('gen 3 | head 3',
             expected_out=[0, 1, 2])
    TEST.run('gen 3 | head 4',
             expected_out=[0, 1, 2])


def test_tail():
    TEST.run('gen 100 | tail 0',
             expected_out=[])
    TEST.run('gen 100 | tail 1',
             expected_out=[99])
    TEST.run('gen 100 | tail 2',
             expected_out=[98, 99])
    TEST.run('gen 100 | tail 3',
             expected_out=[97, 98, 99])
    TEST.run('gen 3 | tail 3',
             expected_out=[0, 1, 2])
    TEST.run('gen 3 | tail 4',
             expected_out=[0, 1, 2])


def test_reverse():
    TEST.run('gen 5 | select (x: False) | reverse',
             expected_out=[])
    TEST.run('gen 5 | reverse',
             expected_out=[4, 3, 2, 1, 0])


def test_squish():
    TEST.run('gen 5 | squish',
             expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 | squish +',
             expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 | map (x: (x, -x)) | squish',
             expected_out=[0, 0, 0, 0, 0])
    TEST.run('gen 5 | map (x: (x, -x)) | squish +',
             expected_out=[0, 0, 0, 0, 0])
    TEST.run('gen 5 | map (x: (x, -x)) | squish min',
             expected_out=[0, -1, -2, -3, -4])
    TEST.run('gen 5 | map (x: (x, -x)) | squish max',
             expected_out=[0, 1, 2, 3, 4])
    TEST.run('gen 5 | map (x: ([-x, x], [-x, x])) | squish +',
             expected_out=[(0, 0, 0, 0),
                           (-1, 1, -1, 1),
                           (-2, 2, -2, 2),
                           (-3, 3, -3, 3),
                           (-4, 4, -4, 4)])


def test_unique():
    TEST.run('gen 10 | unique',
             expected_out=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    TEST.run('gen 10 | select (x: False) | unique',
             expected_out=[])
    TEST.run('gen 10 | unique -c',
             expected_out=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    TEST.run('gen 10 | select (x: False) | unique -c',
             expected_out=[])
    TEST.run('gen 10 | map (x: x // 3) | unique',
             expected_out=[0, 1, 2, 3])
    TEST.run('gen 10 | map (x: x // 3) | unique -c',
             expected_out=[0, 1, 2, 3])
    TEST.run('gen 10 | map (x: x // 3) | unique --consecutive',
             expected_out=[0, 1, 2, 3])
    TEST.run('gen 10 | map (x: x % 3) | unique',
             expected_out=[0, 1, 2])


def test_window():
    TEST.run('gen 10 | window (x: False)',
             expected_out=[((0,), (1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,))])
    TEST.run('gen 10 | window (x: True)',
             expected_out=[(0,), (1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,)])
    TEST.run('gen 10 | window -o 1',
             expected_out=[(0,), (1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,)])
    TEST.run('gen 10 | window -o 3',
             expected_out=[((0,), (1,), (2,)),
                           ((1,), (2,), (3,)),
                           ((2,), (3,), (4,)),
                           ((3,), (4,), (5,)),
                           ((4,), (5,), (6,)),
                           ((5,), (6,), (7,)),
                           ((6,), (7,), (8,)),
                           ((7,), (8,), (9,)),
                           ((8,), (9,), (None,)),
                           ((9,), (None,), (None,))])
    TEST.run('gen 10 | window -d 1',
             expected_out=[(0,), (1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,)])
    TEST.run('gen 10 | window -d 3',
             expected_out=[((0,), (1,), (2,)),
                           ((3,), (4,), (5,)),
                           ((6,), (7,), (8,)),
                           ((9,), (None,), (None,))])
    # Negative-test args
    TEST.run('gen 10 | window -d 33 -o 22',
             expected_err='argument -o/--overlap: not allowed with argument -d/--disjoint')
    TEST.run('gen 10 | window',
             expected_err='Incorrect arguments given for window')
    TEST.run('gen 10 | window -o 3 (x: True)',
             expected_err='Incorrect arguments given for window')


def test_bash():
    TEST.run('bash echo hello  world',
             expected_out=['hello world'])
    # TODO: This doesn't work. quoted string has two spaces, but output has one.
    # TEST.run('bash echo "hello  world"',
    #          expected_out=['hello  world\n'])


def test_fork():
    TEST.run('@1 [ gen 3 100 ]',
             expected_out=[(0, 100), (0, 101), (0, 102)])
    TEST.run('@3 [ gen 3 100 ] | sort',
             expected_out=[(0, 100), (0, 101), (0, 102),
                           (1, 100), (1, 101), (1, 102),
                           (2, 100), (2, 101), (2, 102)])


def test_namespace():
    config_file = '/tmp/.marcel.py'
    config_path = pathlib.Path(config_file)
    # Default namespace has just __builtins__ and initial set of env vars.
    config_path.touch()
    config_path.unlink()
    config_path.touch()
    TEST.reset_environment(config_file)
    TEST.run('map (globals().keys())',
             expected_out=["dict_keys(['USER', 'HOME', 'HOST', 'PWD', '__builtins__'])"])
    # Try to use an undefined symbol
    TEST.run('map (pi)',
             expected_out=[Error("name 'pi' is not defined")])
    # Try a namespace importing symbols in the math module
    config_path.unlink()
    with open(config_file, 'w') as file:
        file.writelines('from math import *')
    TEST.reset_environment(config_file)
    TEST.run('map (pi)',
             expected_out=['3.141592653589793'])
    # Reset environment
    TEST.reset_environment()


def test_remote():
    localhost = marcel.object.host.Host('localhost', None)
    # TEST.run('@jao [ gen 3 ]',
    #          expected_out=[(localhost, 0), (localhost, 1), (localhost, 2)])
    # Handling of remote errors
    TEST.run('@jao [ gen 3 -1 | map (x: 5 / x) ]',
             expected_out=[(localhost, -5.0), Error('division by zero'), (localhost, 5.0)])
    # Bug 4
    TEST.run('@jao [ gen 3 ] | red . +',
             expected_out=[(localhost, 3)])
    TEST.run('@jao [ gen 10 | map (x: (x%2, x)) | red . + ]',
             expected_out=[(localhost, 0, 20), (localhost, 1, 25)])


def main_stable():
    test_gen()
    test_out()
    test_sort()
    test_map()
    test_select()
    test_red()
    test_expand()
    test_head()
    test_tail()
    test_reverse()
    test_squish()
    test_unique()
    test_window()
    test_bash()
    test_fork()
    test_namespace()
    test_remote()
    test_no_such_op()


def main_dev():
    pass
    # TODO: test_ps()  How?
    # TODO: test cd: absolute, relative, target does not exist


def main():
    TEST.reset_environment()
    main_stable()
    main_dev()
    print(f'Test failures: {TEST.failures}')


main()