import json
import sqlite3
import unicodedata

from pymorphy2 import MorphAnalyzer
from pymorphy2.tokenizers import simple_word_tokenize


def strip_accents(s):
    result = ''
    prev_c = ''
    for c in unicodedata.normalize('NFD', s):
        cat = unicodedata.category(c)
        if prev_c == 'Mn' and c == ' ':
            prev_c = cat
            continue
        if cat != 'Mn':
            result += c
        prev_c =cat
    return result


m = MorphAnalyzer()

con = sqlite3.connect('example.db')

cur = con.cursor()

# Create table
cur.execute('''CREATE TABLE dictionary
               (id text, lexeme text, pos text, tags text, text text, html text)''')
cur.execute('''CREATE TABLE for_search
               (id text, lexeme text, lexeme_lemmas text, pos text, tags text, text text, text_lemmas text, html text)''')

with open('dict.json') as f:
    data = json.load(f)

for a in data:
    # Insert a row of data
    cur.execute("INSERT INTO dictionary VALUES (?,?,?,?,?,?)",
                (a['id'], a['lexema'], a['pos'], a['tags'], a['text'], a['html']))

    lemmas = m.normal_forms(strip_accents(a['lexema'].lower()))
    text_lemmas = []
    for t in simple_word_tokenize(a['text']):
        text_lemmas.append(' '.join(m.normal_forms(t)))
    cur.execute("INSERT INTO for_search VALUES (?,?,?,?,?,?,?,?)",
                (a['id'], a['lexema'], ' '.join(lemmas), a['pos'], a['tags'], a['text'], ' '.join(text_lemmas), a['html']))

    # Save (commit) the changes
    con.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
con.close()