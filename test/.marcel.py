from marcel.builtin import *

jao = cluster(user='jao',
              identity='/home/jao/.ssh/id_rsa',
              host='localhost')

jdb = database(driver='psycopg2',
               dbname='jao',
               user='jao',
               password='jao')

DB_DEFAULT = jdb

RUN_ON_STARTUP = '''
ext = [e: select (f: f.suffix == '.' + e)]
grem = [pattern, files: read -l (files) | select (f, l: pattern in l) | map (f, l: f) | unique]
'''
