import json
import sqlite3
import unicodedata

from pymorphy2 import MorphAnalyzer
from pymorphy2.tokenizers import simple_word_tokenize


def strip_accents(s):
    result = ''
    prev_c = ''
    prev = ''
    for c in unicodedata.normalize('NFD', s):
        cat = unicodedata.category(c)
        if prev in 'иИ' and c == '\u0306':
            result = result[:-1]
            result += 'й'
            prev_c = cat
            prev = c
            continue
        if prev_c == 'Mn' and c == ' ':
            prev_c = cat
            prev = c
            continue
        if cat != 'Mn':
            result += c
        prev_c = cat
        prev = c
    return result


m = MorphAnalyzer()

con1 = sqlite3.connect('AS_vol1_38-200.db')
cur = con1.cursor()
cur.execute("SELECT id,lexeme,pos,tags,text,html FROM dictionary")
data = cur.fetchall()

con2 = sqlite3.connect('AS_vol1_200-404.db')
cur = con2.cursor()
cur.execute("SELECT id,lexeme,pos,tags,text,html FROM dictionary")
data += cur.fetchall()

con = sqlite3.connect('AS1.db')
cur = con.cursor()
# Create table
cur.execute('''CREATE TABLE dictionary
               (id text, lexeme text, pos text, tags text, text text, html text)''')
cur.execute('''CREATE TABLE for_search
               (id text, lexeme text, lexeme_lemmas text, pos text, tags text, text text, text_lemmas text, html text)''')

for a in data:
    # Insert a row of data
    cur.execute("INSERT INTO dictionary VALUES (?,?,?,?,?,?)", a)
    # (a['id'], a['lexema'], a['pos'], a['tags'], a['text'], a['html']))

    # lemmas = m.normal_forms(strip_accents(a[1].lower()))
    lemmas = strip_accents(a[1].lower()).strip()
    text_lemmas = []
    for t in simple_word_tokenize(a[4]):
        text_lemmas.append(' '.join(m.normal_forms(t)))
    cur.execute("INSERT INTO for_search VALUES (?,?,?,?,?,?,?,?)",
                (a[0], a[1], lemmas, a[2], a[3], a[4], ' '.join(text_lemmas), a[5]))

    # Save (commit) the changes
    con.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
con.close()