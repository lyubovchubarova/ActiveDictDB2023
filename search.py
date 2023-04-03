import json
import sqlite3

from pymorphy2 import MorphAnalyzer


# TODO: передавать этот результат на фронт через интеграцию в app.py
class SearchEngine():
    def __init__(self, db_path: str):
        self.morph_analyzer = MorphAnalyzer()

        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def _lemmatize(self, query):
        return [self.morph_analyzer.parse(token)[0].normal_form for token in query.split()]

    def search_lexema(self, query_word):
        """поиск по лексемам = названиям статей"""
        sql_query = f"""SELECT lexema.lexema, lexema.dictionary_form,  lexema.meaning, file.name
                        FROM  lexema 
                        JOIN article_meta  on article_meta.lexema_id = lexema.id
                        JOIN file on file.id = article_meta.file_id
                        WHERE lexema.lexema = "квалификация"
        """
        return self.cur.execute(sql_query).fetchall()

    def full_text_search(self, query, rating_thr=6):
        """поиск по всему тексту статьи с помощью FTS5"""
        sql_query = f"""SELECT lexema.lexema, lexema.dictionary_form,  lexema.meaning, file.name
                        FROM (SELECT *, rank
                            FROM meaning
                            WHERE meaning MATCH "lemmatized_meaning: человек" 
                            ORDER BY rank) query_match
                        JOIN lexema on lexema.dictionary_form = query_match.dictionary_form
                        JOIN article_meta  on article_meta.lexema_id = lexema.id
                        JOIN file on file.id = article_meta.file_id
        """
        return self.cur.execute(sql_query).fetchall()

    def search_query(self, query: str, content_search: bool=True):
        """
        поиск по всему:
            сначала запрос делится токены и лемматизируется -- с этим осуществляем поиск по названиям
            потом делаем FTS
        """

        query_words = self._lemmatize(query)

        search_result = []

        for query_word in query_words:
            lexema_search_result = self.search_lexema(query_word)
            search_result.extend(lexema_search_result)

        if content_search:
            fts_search_result = self.full_text_search(' '.join(query_words))
            for fts_res in fts_search_result:
                if fts_res in set(search_result):
                    continue
                search_result.append(fts_res)

        search_result = [
            {
                "lexeme": item[0],
                "dictionary_form": item[1],
                "meaning": item[2],
                "url": item[3],

            } for item in search_result
        ]
        return search_result

if __name__ == '__main__':
    search = SearchEngine("example.db")
    res = search.search_query("человека")
    print(res)