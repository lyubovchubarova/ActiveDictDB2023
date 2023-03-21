import nltk
nltk.download('punkt')

from nltk.tokenize import word_tokenize
import re
import json
from pymorphy2 import MorphAnalyzer

morph = MorphAnalyzer()


def process_document(document, file_path=None):
    def _process_samples(texts):
        tokens = []
        if texts['textStyle'].get('italic', False):
            tokens.extend(re.sub('[^А-Яа-яЁё-]', ' ', texts['content'].lower()).strip().split())
        return tokens
    
    def _process_comm(texts):
        tokens = []
        if not texts['textStyle'].get('italic', False):
            tokens.extend(word_tokenize(re.sub('[^А-Яа-яЁё-]', ' ', texts['content'].lower()).strip()))
        return tokens

    def _process_def(texts, skip_first=False):
        tokens = []
        tokens.extend(word_tokenize(re.sub('[^А-Яа-яЁё-]', ' ', texts['content'].lower()).strip()))
        return tokens
    
    def _process_doc_comms(para):
        tokens = []
        for i in range(len(para)):
            texts = para[i]['textRun']['content']
            tokens.extend(word_tokenize(re.sub('[^А-Яа-яЁё-]', ' ', texts.lower()).strip()))
        return tokens
    
    paras = [para['paragraph']['elements'] for para in document['body']['content'] if 'paragraph' in para.keys()]
    
    cur_func = False
    
    output = {
        'author': document['title'][:2],
        'commented': False,     
        'vocab': [],
        'comms': {},
        'comm': [],
        'def': [],
        'samples': [],
        'syn': [],
        'col': [],
        'ana': [],
        'der': [],
        'gov': []
             }
    
    triggers= {"ЗНАЧЕНИЕ.": [_process_def, 'def'],
     "КОММЕНТАРИИ.": [_process_comm, 'comm'],
     "ИЛЛЮСТРАЦИИ.": [_process_samples, 'samples'],
     "ПРИМЕРЫ.": [_process_samples, 'samples'],
     "СОЧЕТАЕМОСТЬ.": [_process_samples, 'col'],
     "УПРАВЛЕНИЕ.": [_process_samples, 'gov'],
     "СИН:": [_process_samples, 'syn'],
     "АНА:": [_process_samples, 'ana'],
     "ДЕР:": [_process_samples, 'der']}
    for i in range(len(paras)):
        para = paras[i]
        for j, text in enumerate(para):
            col = text['textRun']['textStyle'].get('foregroundColor', {'color':{'rgbColor': {}}})['color']['rgbColor']
            if  not(col.get('blue', 0) == col.get('red', 0) == col.get('green', 0)):
                output['commented'] = True
                com_man = (col.get('blue', 0), col.get('red', 0), col.get('green', 0))
                output['comms'][com_man] = output['comms'].get(com_man, []) + _process_doc_comms(para)
                break
            if text['textRun']['textStyle'].get('bold', False):
                output['vocab'].append(re.sub('[,^\d.]', '', text['textRun']['content']).strip().lower())
                cur_func = False
            elif triggers.get(text['textRun']['content'].strip(), False):
                cur_func = triggers[text['textRun']['content'].strip()][0]
                cur_dest = triggers[text['textRun']['content'].strip()][1]
            elif cur_func:
                output[cur_dest].extend(cur_func(text['textRun']))
                if cur_func == _process_comm:
                    output['samples'].extend(_process_samples(text['textRun']))
    its =  list(output.items())
    for k, v in its:
        if isinstance(v, dict):
            output[k] = {k1:list(set(v1)) for k1, v1 in v.items()}
            output[k+'lemmas'] = {k1:[morph.parse(token)[0].normal_form for token in v1] for k1, v1 in output[k].items()}
        elif isinstance(v, list):
            output[k] = list(set(v))
            if k != 'vocab':
                output[k+'_lemmas'] = [morph.parse(token)[0].normal_form for token  in output[k]]
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False)
    else:
        return output
                