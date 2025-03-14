import json
from pathlib import Path


class AttrGenerator:
    def __init__(self, data):
        self.__data = data

    def __getattr__(self, attr, default=None):
        result = self.__data.get(attr, default)
        if type(result) == dict:
            return self.__class__(result)
        return result

    def get(self, attr, default=None):
        return self.__getattr__(attr, default)


class Language:
    __BASE_LANGUAGE = "ru"

    def __init__(self, lang="ru"):
        path = Path(__file__).parent.absolute()

        lang_path = path / f'{lang}.json'
        base_path = path / f'{self.__BASE_LANGUAGE}.json'

        with open(lang_path, 'r', encoding='utf-8') as lang_file:
            replicas = AttrGenerator(json.load(lang_file))
        with open(base_path, 'r', encoding='utf-8') as base_file:
            base_replicas = AttrGenerator(json.load(base_file))

        self.__replicas = replicas
        self.__base_replicas = base_replicas

    def __getattr__(self, attr):
        return self.__replicas.get(attr) or self.__base_replicas.get(attr)

    def get(self, path):
        result = self
        for part in path.split("."):
            result = result.__getattr__(part)
        return result
