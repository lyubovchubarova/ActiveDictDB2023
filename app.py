import sqlite3
from flask import Flask, request, render_template, g, render_template_string, jsonify
from pymorphy2 import MorphAnalyzer

import re

con = sqlite3.connect("finalvol1.db", check_same_thread=False)
cur = con.cursor()

app = Flask(__name__, instance_relative_config=True)
morph = MorphAnalyzer()
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def hello():
    cur.execute('SELECT lexeme, lexeme_lemmas, meaning FROM dictionary ORDER BY RANDOM() LIMIT 6')
    random_words = cur.fetchall()

    random_words = [list(x) for x in random_words]
    for word in random_words:
        try:
            word[0] = word[0].replace(' ', '')
            m = re.search(r"‘(.*?)’", word[2]).group(1)
            word[2] = m
        except:
            pass
    return render_template('index.html', interesting=random_words)

@app.route('/search')
def search():
    return render_template('new_search.html')

@app.route('/process', methods=['GET'])
def process():

    header = request.args.get('articleheader')
    pos = request.args.getlist('checkbox')
    content = request.args.get('articlecontent')

    d = {'noun': 'СУЩ',
         'adv': 'НАРЕЧ',
         'adj': 'ПРИЛ',
         'verb': 'ГЛАГ',
         'part': 'ЧАСТ',
         'prep': 'ПРЕДЛ',
         'conj': 'СОЮЗ',
         'num': 'ЧИСЛ',
         'interj': 'МЕЖД'}
    pos = [d[i] for i in request.args.getlist('pos')]
    sql_query = 'SELECT lexeme, lexeme_lemmas, pos, tags, new_html, meaning FROM dictionary WHERE lexeme_lemmas LIKE ({0})'.format('"%'+header+'%"')
    if len(pos) != 0:
        sql_query += 'AND pos IN ({0})'.format(', '.join('?' for _ in pos))
        cur.execute(sql_query, pos)
    else:
        cur.execute(sql_query)
    results = cur.fetchall()
    random_words = [list(x) for x in results]
    for word in random_words:
        try:
            word[0] = word[0].replace(' ', '')
            m = re.search(r"‘(.*?)’", word[5]).group(1)
            word[5] = m
        except:
            pass

    return render_template('results.html', results=random_words)

def get_word(letter):
    sql_query = 'SELECT lexeme, lexeme_lemmas, pos, tags, new_html FROM dictionary WHERE lexeme_lemmas LIKE {letter}%'
    cur.execute(sql_query)
    #cur.execute('SELECT lexeme, lexeme_lemmas, pos, tags, new_html FROM dictionary WHERE lexeme_lemmas = "%s"' % word)
    results = cur.fetchall()
    print(results)
    # lexeme, lexeme_lemmas, pos, new_html = t[0], t[1], t[2], t[4]
    # if t[3] is not None:
    #     tags = [x for x in t[3].strip().split(' ') if x]
    # else:
    #     tags = []
    # lexeme = lexeme.replace(' ', '')
    # return {'lexeme': lexeme, 'pos': pos, 'tags': tags}

@app.route('/dictionary')
def dictionary():
    print('a')
    alphabet = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ'
    get_word('а')
    print('a')
    words = ['абрикос', 'беречь', 'абсурдный', 'абстрактный', 'беречь']
    article_list = [get_word(word) for word in words]
    return render_template('new_dictionary.html', alphabet=alphabet, article_list=article_list)

@app.route('/about')
def about():
    return render_template('about.html')


# def get_db():
#     db = getattr(g, '_database', None)
#     if db is None:
#         db = g._database = con
#     return db
# def get_words():
#     cur = get_db().cursor()
#     cur.execute("SELECT id FROM dictionary")
#     total_words = len(cur.fetchall())
#     return total_words

# @app.route('/search', methods=["GET", "POST"])
# def search():
#     cur = get_db().cursor()
#     if request.method == 'POST':
#         title = request.form.get('title', '')
#         tags = request.form.get('pos', '')
#         pomety = request.form.get('tag', '')
#         text = request.form.get('text', '')
#         where_clauses = []
#         results = []
#         if title:
#             title_condition = []
#             title_condition.append("lexeme_lemmas='%s'" % title.lower())
#             where_clauses.append('(' + '  OR '.join(title_condition) + ')')
#         if pomety:
#             pomety_condition = []
#             for p in pomety.split():
#                 p = p.strip('.')
#                 pomety_condition.append("text LIKE '%%%s.%%'" % p)
#             where_clauses.append('(' + '  OR '.join(pomety_condition) + ')')
#         if tags:
#             tags_condition = []
#             for t in tags.split(','):
#                 tags_condition.append("pos LIKE '%%%s%%'" % t)
#             where_clauses.append('(' + ' OR '.join(tags_condition) + ')')
#         if text:
#             text_condition = []
#             for t in text.split():
#                 text_condition.append("text_lemmas LIKE '%%%s%%'" % t)
#             where_clauses.append('(' + ' OR '.join(text_condition) + ')')
#
#         if not where_clauses:
#             return render_template("search.html", message="Пустой запрос!")
#
#         query = "SELECT * FROM for_search WHERE %s" % " AND ".join(where_clauses)
#         print(query)
#         cur.execute(query)
#         for i in cur.fetchall():
#             results.append(i[-1])
#         return render_template('results.html', results=results, title=title)
#     if request.method == 'GET':
#         return render_template('search.html')

# @app.route('/slovnik', defaults={'page': 1})

@app.route('/lexeme/<word>/')
def post(word):
    cur.execute('SELECT lexeme, lexeme_lemmas, pos, tags, new_html FROM dictionary WHERE lexeme_lemmas = "%s"' % word)
    t = cur.fetchone()
    lexeme, lexeme_lemmas, pos, new_html = t[0], t[1], t[2], t[4]
    if t[3] is not None:
        tags = [x for x in t[3].strip().split(' ') if x]
    else:
        tags = []
    lexeme = lexeme.replace(' ', '')
    return render_template('post.html', lexeme=lexeme, lexeme_lemmas=lexeme_lemmas, pos=pos, tags=tags,
                           new_html=new_html)

# @app.route('dictionary/<letter>')
# def get_words_starts_with_letter(letter):
#     pass

# @app.route('/content/page/<int:page>')
# def slovnik(page):
#     cur = get_db().cursor()
#     per_page = 50
#     start = page * per_page - per_page
#     cur.execute("SELECT id, lexeme FROM dictionary LIMIT %d OFFSET %d" % (per_page, start))
#     results = [{'id': l[0], 'lexeme': l[1]} for l in cur.fetchall()]
#     pagination = Pagination(page=page, per_page=per_page, total=get_words(),
#                             css_framework='bootstrap4', href='/content/page/{0}',
#                             display_msg="")
#     print(results)
#     print(pagination.info)
#     print(pagination.links)
#     return render_template('slovnik.html', results=results, pagination=pagination)

# @app.route('/content/<word_id>')
# def word_page(word_id):
#     cur = get_db().cursor()
#     cur.execute("SELECT id, html FROM dictionary WHERE id='%s'" % word_id)
#     results = [{'id': l[0], 'html': l[1]} for l in cur.fetchall()]
#     return render_template('word.html', results=results)


if __name__ == '__main__':
    app.run(threaded=True)
