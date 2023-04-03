# для работы кода нужно, чтобы на диске пользователя была папка, которая расшарена адресу service-account@active-dictionary-db.iam.gserviceaccount.com
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaIoBaseDownload
import io
import json

import googleapiclient.discovery as discovery
from httplib2 import Http


def parse_folder(user_folder: str) -> list:
    files = []
    scope = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "active-dictionary-db-72b7b0756fc6.json", scope)  # json с ключом
    service = build("drive", "v3", credentials=credentials)
    DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'
    http = credentials.authorize(Http())
    docs_service = discovery.build(
        'docs', 'v1', http=http, discoveryServiceUrl=DISCOVERY_DOC)
    results = service.files().list(pageSize=10,
                                   fields="nextPageToken, files(id, name, mimeType, parents, createdTime, modifiedTime)").execute()  # метаданные: id, название, дата создания, дата изменения
    for f in results['files']:  # находим папку по названию, мб по ссылке сделать?
        # print(f)
        if f['name'] == user_folder:
            target_id = f['id']
            print("Match found!", f['name'])
    for f in results['files']:  # скрипт для получения содержимого файлов папки
        if f['mimeType'][-8:] == 'document' and f['parents'][0] == target_id:  # парсит все, кроме docx
            file_id = f['id']
            file_name = f['name']
            try:
                doc = docs_service.documents().get(documentId=file_id).execute()
                doc_content = doc.get('body').get(
                    'content')  # содержимое файла
                # метаданные + содержимое дока в кортеже
                files.append((f, doc_content))
            except HttpError as e:
                print(e)
    return files


def check_changes(folder_name: str) -> None:
    """
    Итерируется по файлам в указанной папке проверяя дату изменения (изменился ли файл с прошлой проверки)
    В случае несовпадения времени последнего изменения последнее время перезаписывается, а данные в бд обновляются
    через функцию update (пока не работает)
    """
    with open("text_last_dates.json", 'r', encoding="utf-8") as f:
        dates = json.loads(f.read())
    
    for word in parse_folder(folder_name):
        if word[0]['name'] in dates and word[0]['modifiedTime'] != dates[word[0]['name']]:
            dates[word[0]['name']] = word[0]['modifiedTime']
            update(word[0]['name'])

    with open("text_last_dates.json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(dates, ensure_ascii=False, indent=2))


def update(word: str) -> None:
    pass


if __name__ == "__main__":
    updates = {}
    with open("text_last_dates.json", 'w', encoding="utf-8") as f:
        for i in parse_folder("том 6"):
            updates[i[0]['name']] = i[0]['modifiedTime']
            print(i[0]['name'], i[0]['modifiedTime'], '\n', i[1],
                  end="\n------------------------------------\n")
            print(i)

        f.write(json.dumps(updates, ensure_ascii=False, indent=2))
