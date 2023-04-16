import sqlite3
from flask import Flask, request, render_template, g, render_template_string, jsonify
from pymorphy2 import MorphAnalyzer
import re

ALPHABET = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ'

con = sqlite3.connect("work_db_with_some_data.db", check_same_thread=False)
cur = con.cursor()

app = Flask(__name__, instance_relative_config=True)
morph = MorphAnalyzer()
app.config['TEMPLATES_AUTO_RELOAD'] = True


#стартовая
@app.route('/')
def hello():
    # Общая статистика
    sql_query = 'SELECT status.status, COUNT(article_meta.status_id) as cnt \
                   FROM article_meta, status\
                   WHERE article_meta.status_id=status.id\
                   GROUP BY article_meta.status_id\
                   ORDER BY cnt DESC'
    cur.execute(sql_query)
    res_statuses = cur.fetchall()
    statuses = [list(x) for x in res_statuses]

    sql_query = 'SELECT author.author, COUNT(article_meta.author_id) as cnt\
                       FROM article_meta, author\
                       WHERE article_meta.author_id=author.id\
                       GROUP BY article_meta.author_id\
                       ORDER BY cnt DESC'
    cur.execute(sql_query)
    res_authors = cur.fetchall()
    authors = [list(x) for x in res_authors]

    # Список последних отредактированных
    sql_query = '''SELECT lexema.lexema, article_meta.last_modified, author.author, file.name
                    FROM article_meta
                    join lexema on lexema.id = article_meta.lexema_id
                    join author on author.id = article_meta.author_id
                    join file on file.id = article_meta.file_id
                    ORDER BY article_meta.last_modified DESC
                    LIMIT 10'''
    cur.execute(sql_query)
    res_authors = cur.fetchall()
    wordlist_interesting = [{'lexeme': x[0],
                             'date': x[1],
                             'author': x[2],
                             'link': x[3]} for x in res_authors]

    return render_template('index.html', wordlist_interesting=wordlist_interesting, statuses=statuses, authors=authors)

#поиск
@app.route('/search')
def search():
    #нужен запрос , который на выходе дает список всех авторов из базы
    #с id или расшифровкой - опционально
    #authors -> List
    sql_query = '''SELECT author.author
                    FROM author'''
    cur.execute(sql_query)
    authors = [el[0] for el in cur.fetchall()]

    sql_query = '''SELECT status.status
                        FROM status'''
    cur.execute(sql_query)
    statuses = [el[0] for el in cur.fetchall()]
    return render_template('new_search.html', authors=authors, statuses=statuses)


def process_search(lexeme, authors, statuses):
    repl = []

    if lexeme != '':
        lex_part = ' lexema.lexema = "{0}"'.format(lexeme)
        repl.append(lex_part)

    if len(authors) > 1:
        auth_part = 'author.author IN {0}'.format(tuple(authors))
        repl.append(auth_part)
    elif len(authors) == 1:
        auth_part = 'author.author = "{0}"'.format(authors[0])
        repl.append(auth_part)

    if len(statuses) > 1:
        stat_part = 'status.status IN {0}'.format(tuple(statuses))
        repl.append(stat_part)
    elif len(statuses) == 1:
        stat_part = 'status.status = "{0}"'.format(statuses[0])
        repl.append(stat_part)

    if len(repl) == 0:
        ques_part = ''
    else:
        ques_part = 'WHERE ' + ' AND '.join(repl)


    sql_query = '''SELECT lexema.lexema, article_meta.last_modified, author.author, file.name
                    FROM article_meta
                    JOIN lexema ON lexema.id = article_meta.lexema_id
                    JOIN author ON author.id = article_meta.author_id
                    JOIN status ON status.id = article_meta.status_id
                    JOIN file ON file.id = article_meta.file_id
                    {0}
                    ORDER BY article_meta.last_modified DESC'''.format(ques_part)

    cur.execute(sql_query)
    res = [{'lexeme': x[0],
             'date': x[1],
             'author': x[2],
             'link': x[3]} for x in cur.fetchall()]
    return res


def process_lexemes(res):
    lexemes = tuple([result['lexeme'] for result in res])
    if len(lexemes) > 1:
        return 'WHERE lexema IN {0}'.format(lexemes)
    elif len(lexemes) == 1:
        return 'WHERE lexema = "{0}"'.format(lexemes[0])
    else:
        return ''


def count_statistics(results):
    lexemes = process_lexemes(results)
    sql_query = 'SELECT status, COUNT(*) as cnt \
                        FROM article_meta \
                            JOIN status ON article_meta.status_id=status.id \
                            JOIN lexema ON article_meta.lexema_id=lexema.id \
                        {0} \
                        GROUP BY article_meta.status_id \
                        ORDER BY cnt DESC'.format(lexemes)
    cur.execute(sql_query)
    res_statuses = cur.fetchall()
    statuses = [list(x) for x in res_statuses]

    sql_query = 'SELECT author, COUNT(*) as cnt \
                    FROM article_meta \
                        JOIN author ON article_meta.author_id=author.id \
                        JOIN lexema ON article_meta.lexema_id=lexema.id \
                    {0} \
                    GROUP BY article_meta.author_id \
                    ORDER BY cnt DESC'.format(lexemes)
    cur.execute(sql_query)
    res_authors = cur.fetchall()
    authors = [list(x) for x in res_authors]
    return statuses, authors


# результаты
@app.route('/process', methods=['GET'])
def process():
    # заголовок статьи
    header = request.args.get('articleheader') # str

    # содержимое статьи
    # content = request.args.get('articlecontent') # -> str

    # Имена авторов (или можно выдавать id, можно переделать
    author_names = request.args.getlist('Authors')  # -> List[str]

    # Статусы
    status = request.args.getlist('status')  # -> List[str]

    # нужен запрос, который по аргументам выше возвращает спиcок с результатами results
    results = process_search(header, author_names, status)

    # Статистика по запросу
    statuses, authors = count_statistics(results)
    return render_template('results.html', results=results, statuses=statuses, authors=authors)


def get_words(letter):
    sql_query = '''SELECT lexema.lexema, article_meta.last_modified, author.author, file.name
                    FROM article_meta
                    join lexema on lexema.id = article_meta.lexema_id
                    join author on author.id = article_meta.author_id
                    join file on file.id = article_meta.file_id
                    WHERE lexema.lexema LIKE {0}'''.format('"' + letter + '%"')
    cur.execute(sql_query)
    res = [{'lexeme': x[0],
            'date': x[1],
            'author': x[2],
            'link': x[3]} for x in cur.fetchall()]
    return res


@app.route('/dictionary/<start_letter>')
def dictionary(start_letter):

    # нужен запрос, который по start_letter (в верхнем регистре) возвращает список всех статей article_list на эту букву
    # кроме того, start_letter мoжет быть == all, это значит, что нужно достать все статьи

    if start_letter == 'all':
        article_list = get_words('')
    else:
        article_list = get_words(start_letter.lower())

    return render_template('new_dictionary.html',
                           alphabet=ALPHABET,
                           current_letter=start_letter.lower(),
                           article_list=article_list)


# про сайт и словарь
@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(threaded=True)
