import json
import sqlite3

from dict_func import process_document


def create_meta_table(cur):
    q0 = "DROP TABLE IF EXISTS article_meta"
    cur.execute(q0)
    q1 = '''CREATE TABLE "article_meta" (
            "id"    INTEGER NOT NULL UNIQUE,
            "lexema_id"    INTEGER NOT NULL,
            "author_id"    INTEGER,
            "status_id"    INTEGER,
            "format_id"    INTEGER,
            "volume"    INTEGER,
            "file_id"    INTEGER,
            "last_modified"    TEXT,
            PRIMARY KEY("id" AUTOINCREMENT)
        );'''
    cur.execute(q1)


def create_author_table(cur):
    q0 = "DROP TABLE IF EXISTS author"
    cur.execute(q0)
    q2 = '''CREATE TABLE "author" (
        "id"    INTEGER NOT NULL UNIQUE,
        "author"    TEXT NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT)
    );'''
    cur.execute(q2)


def create_file_table(cur):
    q0 = "DROP TABLE IF EXISTS file"
    cur.execute(q0)
    q3 = '''CREATE TABLE "file" (
        "id"    INTEGER NOT NULL UNIQUE,
        "name"    TEXT NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    '''
    cur.execute(q3)


def create_format_table(cur):
    q0 = "DROP TABLE IF EXISTS format"
    cur.execute(q0)
    q4 = '''CREATE TABLE "format" (
        "id"    INTEGER NOT NULL UNIQUE,
        "format"    TEXT NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT)
    );'''
    cur.execute(q4)


def create_lexema_table(cur):
    q0 = "DROP TABLE IF EXISTS lexema"
    cur.execute(q0)
    q5 = '''CREATE TABLE "lexema" (
        "id"    INTEGER NOT NULL UNIQUE,
        "lexema"    TEXT NOT NULL,
        "dictionary_form" TEXT UNIQUE,
        "meaning" TEXT,
        "lemmatized_meaning" TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
    );'''
    cur.execute(q5)


def create_meaning_fts_table(cur):
    q0 = "DROP TABLE IF EXISTS meaning"
    cur.execute(q0)
    q6 = '''CREATE VIRTUAL TABLE meaning USING FTS5 (dictionary_form, lemmatized_meaning);'''
    cur.execute(q6)


def create_status_table(cur):
    q0 = "DROP TABLE IF EXISTS status"
    cur.execute(q0)
    q7 = '''CREATE TABLE "status" (
        "id"    INTEGER NOT NULL UNIQUE,
        "status"    TEXT NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT)
    );'''
    cur.execute(q7)


def create_tables(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    _version = cur.execute("select sqlite_version();").fetchall()
    print("SSLite version:", _version)
    # Create tables
    create_meaning_fts_table(cur)
    create_meta_table(cur)
    create_file_table(cur)
    create_format_table(cur)
    create_lexema_table(cur)
    create_status_table(cur)
    create_meaning_fts_table(cur)
    con.commit()
    con.close()


def insert_file(cur, filename):
    cur.execute(
        "INSERT INTO file (name) VALUES (?) ON CONFLICT DO UPDATE SET name=EXCLUDED.name",
        (filename,)
    )
    return cur.lastrowid


def insert_meta(cur, lexema_id, file_id):
    cur.execute((
        "INSERT INTO article_meta (lexema_id, file_id) "
        "VALUES (?, ?)"
    ),
        (lexema_id, file_id)
    )


def insert_lexema(cur, lexema, dictionary_form, meaning, lemmatized_meaning):
    cur.execute((
        "INSERT INTO lexema (lexema, dictionary_form, meaning, lemmatized_meaning) "
        "VALUES (?, ?, ?, ?)"
        "ON CONFLICT(dictionary_form) DO UPDATE SET meaning = EXCLUDED.meaning, lemmatized_meaning=EXCLUDED.lemmatized_meaning"
    ),
        (lexema, dictionary_form, meaning, lemmatized_meaning)
    )

    return cur.lastrowid

def insert_meaning(cur, dictionary_form, lemmatized_meaning):
    cur.execute(
        "INSERT INTO meaning (dictionary_form, lemmatized_meaning) VALUES(?, ?)",
        (dictionary_form, lemmatized_meaning)
    )

def update_tables(db_path, data):
    if not (isinstance(data, dict) or isinstance(data, list)):
        # mock json doesn't match 'process_document' function output
        # TODO: match the keys used inside the current function to the process_document output
        with open(data) as infile:
            data = json.load(infile)
            data = process_document(data)

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    for item in data:
        file_id = insert_file(cur, item["url"])
        print(file_id)
        lexema_id = insert_lexema(
            cur,
            lexema=item["lexeme"],
            dictionary_form=item["dictionary_form"],
            meaning=item["meaning"],
            lemmatized_meaning=item["lemmatized_meaning"]
        )
        print(lexema_id)
        insert_meaning(cur, item["dictionary_form"], item["lemmatized_meaning"])
        insert_meta(cur, lexema_id, file_id)

    con.commit()
    con.close()


mock_data = [
    {
        "lexeme": "квалификация",
        "dictionary_form": "квалификация 1",
        "meaning": "Процесс оценивания свойств объекта А2 и формулировка, являющаяся результатом этого оценивания",
        "lemmatized_meaning": "процесс оценивание свойство объект формулировка являться результат этот оценивание",
        "url": "https://docs.google.com/document/d/1meJ8xJ4LPor0UHLcc5owNBI0-E_S7_5S",
    },
    {
        "lexeme": "кивнуть",
        "dictionary_form": "кивнуть 1",
        "meaning": "Человек А1 коротким движением сначала наклонил голову вниз, а затем поднял ее в исходное положение в знак согласия с собеседником А2, или в качестве утвердительного ответа на вопрос А2, или в знак приветствия А2",
        "lemmatized_meaning": "человек короткий движение сначала наклонить голова вниз затем поднять исходное положение знак согласие собеседник качество утвердительный ответ вопрос знак приветствие",
        "url": "https://docs.google.com/document/d/1meJ8xJ4LPor0UHLcc5owNBI0-E_S7_5S",
    },
]


def main():
    db_path = 'example.db'
    create_tables(db_path)
    update_tables(db_path, mock_data)


if __name__ == '__main__':
    main()
