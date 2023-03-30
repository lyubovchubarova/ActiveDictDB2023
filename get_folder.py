#для работы кода нужно, чтобы на диске пользователя была папка, которая расшарена адресу service-account@active-dictionary-db.iam.gserviceaccount.com
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaIoBaseDownload
import io

import googleapiclient.discovery as discovery
from httplib2 import Http

def parse_folder(user_folder):
    link = user_folder.split('/')[-1]
    files = []
    scope = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = ServiceAccountCredentials.from_json_keyfile_name("active-dictionary-db-72b7b0756fc6.json", scope) #json с ключом 
    scope_docs = ['https://www.googleapis.com/auth/documents.readonly']
    credentials_docs = ServiceAccountCredentials.from_json_keyfile_name("active-dictionary-db-72b7b0756fc6.json", scope_docs) #json с ключом 
    DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'
    http = credentials.authorize(Http())
    docs_service = discovery.build(
            'docs', 'v1', credentials=credentials_docs)
    page_token = None
    try:
        service = build("drive", "v3", credentials=credentials)
        res = []
        page_token = None
        while True:
            response = service.files().list(
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, parents, createdTime, modifiedTime)",
                pageToken=page_token).execute()
            res.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break
    except HttpError as error:
        print(f"An error occurred: {error}")
        files = None
    for f in res: 
        if f['id'] == link:
            target_id = f['id']
            print(target_id)
    
    for f in res: #скрипт для получения содержимого файлов папки
        if f['mimeType'][-8:] == 'document':
            if f['parents'][0] == target_id: #парсит все, кроме docx
                file = None
                file_id = f['id']
                file_name = f['name']
                try:
                    doc = docs_service.documents().get(documentId=file_id).execute()
                except HttpError as error:
                    print(F'An error occurred: {error}')
                doc_content = doc.get('body').get('content') #содержимое файла
                files.append((f, doc_content)) #метаданные + содержимое дока в кортеже
    return files


import pandas as pd
data = pd.DataFrame(columns = ['content', 'metadata'])

folder = parse_folder('https://drive.google.com/drive/u/0/folders/1WUoIUA95yp4DkOyxVPAk2jIGsYZk0kHh') #ввод ссылки на папку

for f in folder:
    data.loc[len(data.index)] = [f[0], f[1]]

data.to_csv('fdata.csv') #запись данных в csv-файл для дальнейшей работы с ними