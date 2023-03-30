import sqlite3
from flask import Flask, request, render_template, g, render_template_string, jsonify
from pymorphy2 import MorphAnalyzer
import re

ALPHABET = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ'

con = sqlite3.connect("finalvol1.db", check_same_thread=False)
cur = con.cursor()

app = Flask(__name__, instance_relative_config=True)
morph = MorphAnalyzer()
app.config['TEMPLATES_AUTO_RELOAD'] = True

#стартовая
@app.route('/')
def hello():

    #Предыдущий запрос

    # cur.execute('SELECT lexeme, lexeme_lemmas, meaning FROM dictionary ORDER BY RANDOM() LIMIT 6')
    # random_words = cur.fetchall()
    #
    # random_words = [list(x) for x in random_words]
    # for word in random_words:
    #     try:
    #         word[0] = word[0].replace(' ', '')
    #         m = re.search(r"‘(.*?)’", word[2]).group(1)
    #         word[2] = m
    #     except:
    #         pass

    ### Нужен запрос с формированием списка wordlist_intresting с 6 элементами в нем

    # Столько элементов должно быть на сайте в разделе Интересное
    # wordlist_intresting -> List[Dict], каждый словарь выглядит так
    # {
    #   'lexeme': само слово,
    #   'dictionary_form': словарная форма капсом с ударением,
    #    'meaning': значение
    # }
    
    
    #Общая статистика
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

    return render_template('index.html', wordlist_interesting=wordlist_interesting, statuses=statuses, authors=authors)

#поиск
@app.route('/search')
def search():
    #нужен запрос , который на выходе дает список всех авторов из базы
    #с id или расшифровкой - опционально
    #authors -> List
    with open('names.txt', encoding='utf-8') as f:
        authors = f.read().splitlines()
    return render_template('new_search.html', authors=authors)

#результаты
@app.route('/process', methods=['GET'])
def process():
    # заголовок статьи
    header = request.args.get('articleheader') # str

    # список частей речи из запроса
    # возможные: noun, adv, adj, interj, verb, part, prep, conj, num
    pos = request.args.getlist('pos') # -> List[str]

    #содержимое статьи
    content = request.args.get('articlecontent') # -> str

    #Имена авторов (или можно выдавать id, можно переделать
    author_names = request.args.get('Authors') # -> List[str]

    #Статусы (пока есть) finished, not_finished, unknown
    status = request.args.get('status') # -> List[str]

    ### нужен запрос, который по аргументам выше возвращает спиcок с результатами results

    # results -> List[Dict], каждый словарь выглядит так
    # {
    #   'lexeme': само слово,
    #   'dictionary_form': словарная форма капсом с ударением,
    #    'meaning': значение
    # }

    #   ПРЕДЫДУЩИЙ ЗАПРОС
    # sql_query = 'SELECT lexeme, lexeme_lemmas, pos, tags, new_html, meaning\
    #              FROM dictionary\
    #              WHERE lexeme_lemmas LIKE ({0})'.format('"%'+header+'%"')
    # if len(pos) != 0:
    #     sql_query += 'AND pos IN ({0})'.format(', '.join('?' for _ in pos))
    #     cur.execute(sql_query, pos)
    # else:
    #     cur.execute(sql_query)
    #
    # results = cur.fetchall()
    # random_words = [list(x) for x in results]
    # for word in random_words:
    #     try:
    #         word[0] = word[0].replace(' ', '')
    #         m = re.search(r"‘(.*?)’", word[5]).group(1)
    #         word[5] = m
    #     except:
    #         pass
    
    # Статистика по запросу
    lexemes = tuple([result['lexeme'] for result in results])
    sql_query = 'SELECT status, COUNT(*) as cnt \
                    FROM article_meta \
                        JOIN status ON article_meta.status_id=status.id \
                        JOIN lexema ON article_meta.lexema_id=lexema.id \
                    WHERE lexema IN {0} \
                    GROUP BY article_meta.status_id \
                    ORDER BY cnt DESC'.format(lexemes)
    cur.execute(sql_query)
    res_statuses = cur.fetchall()
    statuses = [list(x) for x in res_statuses]

    sql_query = 'SELECT author, COUNT(*) as cnt \
                FROM article_meta \
                    JOIN author ON article_meta.author_id=author.id \
                    JOIN lexema ON article_meta.lexema_id=lexema.id \
                WHERE lexema IN {0} \
                GROUP BY article_meta.author_id \
                ORDER BY cnt DESC'.format(lexemes)
    cur.execute(sql_query)
    res_authors = cur.fetchall()
    authors = [list(x) for x in res_authors]

    return render_template('results.html', results=results, statuses=statuses, authors=authors)

def get_words(letter):

    sql_query = 'SELECT lexeme, lexeme_lemmas, pos, tags, new_html\
                 FROM dictionary\
                 WHERE lexeme_lemmas LIKE {0}'.format('"' + letter + '%"')
    cur.execute(sql_query)

    results = cur.fetchall()
    results = [
                {
                    'lexeme': result[0].replace(' ', ''),
                    'pos': result[2],
                    'tags': [tag for tag in result[3].strip().split(' ') if tag]
                            if result[3] is not None
                            else []
                 }
                for result in results]
    return results

@app.route('/dictionary/<start_letter>')
def dictionary(start_letter):

    # нужен запрос, который по start_letter (в верхнем регистре) возвращает список всех статей article_list на эту букву
    # кроме того, start_letter мoжет быть == all, это значит, что нужно достать все статьи
    # выше функция get_words которая делает это с текущей базой

    # article -> List[Dict], каждый словарь выглядит так
    # {
    #   'lexeme': само слово,
    #   'dictionary_form': словарная форма,
    #   'pos': часть речи,
    #    'tags': тэги в виде списка
    # }

    # if start_letter == 'all':
    #     article_list = get_words('')
    # else:
    #     article_list = get_words(start_letter.lower())

    return render_template('new_dictionary.html',
                           alphabet=ALPHABET,
                           current_letter=start_letter.lower(),
                           article_list=article_list)
#про сайт и словарь
@app.route('/about')
def about():
    return render_template('about.html')

#лексема
@app.route('/lexeme/<word>/')
def post(word):

    # Предыдущий запрос
    # cur.execute('SELECT lexeme, lexeme_lemmas, pos, tags, new_html FROM dictionary WHERE lexeme_lemmas = "%s"' % word)
    # t = cur.fetchone()
    # lexeme, lexeme_lemmas, pos, new_html = t[0], t[1], t[2], t[4]
    # if t[3] is not None:
    #     tags = [x for x in t[3].strip().split(' ') if x]
    # else:
    #     tags = []
    # lexeme = lexeme.replace(' ', '')

    #нужен запрос который будет отдавать
    # lexeme - лексему
    # pos - часть речи
    # tags - список тэгов
    # new_html - отформатированный html, старый код есть в проекте

    return render_template('post.html', lexeme=lexeme,
                                        pos=pos,
                                        tags=tags,
                                        new_html=new_html)

if __name__ == '__main__':
    app.run(threaded=True)
