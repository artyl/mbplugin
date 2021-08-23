# -*- coding: utf8 -*-
'Модуль для обновления версии'
import base64, collections, re, hashlib, glob, os, sys, time, typing, traceback, zipfile, shutil
from typing_extensions import runtime
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import cryptography.exceptions
import store, settings

ZipRecord = collections.namedtuple('ZipRecord', 'content mtime')

class ShaSumFile():
    'Класс для работы с файлом контрольных сумм, генерация, проверка'
    def __init__(self) -> None:
        self.raw_data = None  # данные, как они лежат в файле
        self.signature = None  # сигнатура, как она лежит в файле
        self.data = {}

    def sign_and_save(self, priv_keyname, fn_shasum, fn_shasum_sig, filelist:list):
        'Подписываем файл и сохраняем файлы с суммами и с подписью'
        for fn in filelist:
            with open(fn, 'rb') as f:
                self.data[os.path.split(fn)[-1]] = hashlib.sha256(f.read()).hexdigest()
        with open(priv_keyname, 'rb') as key_file:
            private_key = serialization.load_ssh_private_key(
                key_file.read(), password=None, backend=default_backend())
        res = []
        for k,v in self.data.items():
            res.append(f"{v}\t{k}")
        self.raw_data = '\n'.join(res).encode()
        self.signature = base64.b64encode(private_key.sign(self.raw_data))
        with open(fn_shasum, 'wb') as f:
            f.write(self.raw_data)
        with open(fn_shasum_sig, 'wb') as f:
            f.write(self.signature)

    def verify(self, filelist:list):
        'проверяем подпись и суммы, для files(имя: содержимое)'
        if self.raw_data is None or self.signature is None:
            raise RuntimeError('raw_data and signatute must not be None')
        for public_key_txt in settings.public_keys:
            public_key = serialization.load_ssh_public_key(
                public_key_txt, default_backend())
            try:
                public_key.verify(base64.b64decode(self.signature), self.raw_data)
                print(f'Signature checked by key {public_key_txt.split()[-1].decode()} OK')
                break
            except cryptography.exceptions.InvalidSignature as e:
                continue
        else:
            raise RuntimeError('ERROR: Signature files failed verification!')
        # convert raw_data sha sum files to dictionary
        for line in self.raw_data.decode().splitlines():
            if '\t' in line:
                s, fn = line.split('\t')
                self.data[fn.lower()] = s
        for fn in filelist:
            with open(fn, 'rb') as f:
                if self.data[os.path.split(fn)[-1].lower()] != hashlib.sha256(f.read()).hexdigest():
                    raise RuntimeError('The hash sum of the file {fn} did not match')
            print(f'Hash sum {fn} OK')

    def load_sum_and_sig_by_url(self, url_sum, url_sig):
        'Загружаем по url файлы с контрольными суммами и подпись'
        if url_sum is not None:
            self.raw_data = requests.get(url_sum).content
        if url_sig is not None:
            self.signature = requests.get(url_sig).content

    def load_sum_and_sig_by_file(self, fn_sum, fn_sig):
        'Загружаем по имени файла файлы с контрольными суммами и подпись'
        with open(fn_sum, 'rb') as f:
            self.raw_data = f.read()
        with open(fn_sig, 'rb') as f:
            self.signature = f.read()


class UpdaterEngine():
    '''Движок обновления через интернет и с диска с проверкой подписи файлов
    prerelease=False - не устанавливать prerelease
    draft=False - не устанавливать draft '''
    def __init__(self, prerelease=False, draft=False, version='') -> None:
        self.releases = None
        self.prerelease = prerelease
        self.draft = draft
        self.current_zipname = store.abspath_join('mbplugin', 'pack', 'current.zip')
        self.current_bak_zipname = store.abspath_join('mbplugin', 'pack', 'current.zip.bak')
        self.new_zipname = None
        self.set_version(version)

    def github_releases(self) -> list:
        'При первом обращении получаем информацию с github'
        if self.releases is None:
            url = 'https://api.github.com/repos/artyl/mbplugin1/releases'
            self.releases = requests.get(url).json()
            # print([r["tag_name"] for r in self.releases])
        return self.releases

    def exist_version(self, tag) -> bool:
        'проверяет существует ли такая версия'
        tags = [r['tag_name'] for r in self.github_releases()]
        return tag in tags

    def set_version(self, version):
        'Выставляем версию для обновления - если version это имя файла, то запоминаем его и не пытаемся дергать github'
        version_fn = store.abspath_join('mbplugin', 'pack', version)
        if os.path.exists(version_fn):
            self.new_zipname = version_fn
            return
        if version != '':
            return
        if self.exist_version(version):
            self.version = version
            self.new_zipname = store.abspath_join('mbplugin', 'pack', f'mbplugin_bare.{self.version}.zip')
        else:
            raise RuntimeError(f'Not existing version "{version}"')

    def check_update(self) -> bool:
        'проверяем наличие обновлений, prerelease=True - get prerelease, draft=True - get draft'
        release = [r for r in self.github_releases() if (not r['prerelease'] or self.prerelease) and (not r['draft'] or self.draft)][0]
        cnt = [a['download_count'] for a in release['assets'] if '_bare' in a['name']][0]
        msg = f'Latest release on github {release["tag_name"]} by {release["published_at"]}, downloaded {cnt} times with description:\n{release["body"]}'
        # print([(a['name'], a['download_count']) for a in release['assets']])
        current_ver = tuple(map(int, re.findall('\d+', store.version())))
        latest_ver = tuple(map(int, re.findall('\d+', release["tag_name"])))
        if current_ver < latest_ver: # Есть новая версия
            self.version = release["tag_name"]
            return self.version, msg
        else:
            return '', ''

    def download_version(self, version='', force=False, checksign=True) -> None:
        'Загружаем обновление, force=True независимо от наличия на диске, checksign=False - не проверять подпись'
        self.set_version(version)
        release = [r for r in self.github_releases() if r["tag_name"]==self.version][0]
        name, url = [(a['name'], a['browser_download_url']) for a in release['assets'] if '_bare' in a['name']][0]
        url_sum = [a['browser_download_url'] for a in release['assets'] if 'sha256sums.txt' == a['name']][0]
        url_sig = [a['browser_download_url'] for a in release['assets'] if 'sha256sums.txt.sig' == a['name']][0]
        local_filename = store.abspath_join('mbplugin', 'pack', name)
        # print(name)
        if checksign:
            sha_sum_verifier = ShaSumFile()
            sha_sum_verifier.load_sum_and_sig_by_url(url_sum=url_sum, url_sig=url_sig)
        if not os.path.exists(local_filename) or force:
            data = requests.get(url).content
            open(local_filename, 'wb').write(data)
        if checksign:
            sha_sum_verifier.verify(filelist=[local_filename])

    def version_check_zip(self, zipname, ignore_crlf=True, ignore_missing=True) -> list:
        'Проверяет соответствие файлов в архиве и на диске, возвращает список файлов которые отличаются'
        different = []
        for zn, zd in self.read_zip(store.abspath_join(zipname)).items():
            if os.path.isfile(zn):
                with open(zn, 'rb') as f:
                    data: bytes = f.read()
                if ignore_crlf:
                    if data.replace(b'\r\n', b'\n').strip() != zd.content.replace(b'\r\n', b'\n').strip():
                        different.append(zn)
                else:
                    if data != zd.content:
                        different.append(zn)
            elif not ignore_missing:
                different.append(zn)
        return different

    def version_update_zip(self, zipname) -> None:
        'Обновляет файлы на диске из архива'
        z_new = self.read_zip(store.abspath_join(zipname))
        for zn, zd in z_new.items():
            dir_name = os.path.split(zn)[0]
            if not os.path.isdir(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            with open(zn, 'wb') as f:
                f.write(zd.content)
            os.utime(zn, (zd.mtime, zd.mtime))  # fix file datetime by zip

    def rename_new_to_current(self, undo=False):
        ''' Rename files new.zip -> current.zip -> current.zip.bak 
            undo: current.zip <-> current.zip.bak'''
        if undo:
            if os.path.exists(self.current_zipname + '_'):
                os.remove(self.current_zipname + '_')
            if os.path.exists(self.current_zipname):
                os.rename(self.current_zipname, self.current_zipname + '_')
            if os.path.exists(self.current_bak_zipname):
                os.rename(self.current_bak_zipname, self.current_zipname)
            os.rename(self.current_zipname + '_', self.current_bak_zipname)
            return
        if os.path.exists(self.current_bak_zipname):
            os.remove(self.current_bak_zipname)
        if os.path.exists(self.current_zipname):
            os.rename(self.current_zipname, self.current_bak_zipname)
        if os.path.exists(self.new_zipname):
            shutil.copy(self.new_zipname, self.current_zipname)

    def read_zip(self, zipname) -> typing.Dict[str, ZipRecord]:
        '''Читает zip в словарь, ключи словаря - абсолютные пути на диске (где они у нас должны находится), 
        каталоги игнорируем, для них у нас в пустых папках файлы флаги созданы
        элементы - namedtuple content mtime '''
        res = {}
        with zipfile.ZipFile(store.abspath_join(zipname), 'r') as zf1:
            for zi in zf1.infolist():  # Во временную переменную прочитали
                # Первый элемент пути в зависимости от ветки может называться не так как нам нужно
                fn = store.abspath_join('mbplugin', *(store.path_split_all(zi.filename)[1:]))
                # TODO !!! Для тестов не обновляю папку plugin в релизе убрать
                if 'plugin' in store.path_split_all(zi.filename) or '.ico' in zi.filename:  # TODO !!! for debug
                    continue
                if not zi.is_dir():
                    res[fn] = ZipRecord(
                        zf1.read(zi),
                        time.mktime(zi.date_time + (0, 0, -1)))
        return res

    def install_update(self, version='', force=False, undo_update=False, by_current=False):
        'Устанавливаем обновление, undo_update - откатить, by_current - переставить текущую'
        # проверка файлов по current.zip
        # Здесь проверяем чтобы не поменять что-то что руками поменяно (отсутствующие на диске файлы не важны)
        self.set_version(version)       
        if not os.path.exists(self.current_zipname) and not force:
            # Если текущего файла нет мы не можем проверить на что обновляемся
            return False, f'Not exists {self.current_zipname} (use -f)'
        if os.path.exists(self.current_zipname):
            # Проверяем что нет файлов которые отличаются от релизных чтобы не перезатереть чужие изменения
            diff_current1 = self.version_check_zip(self.current_zipname, ignore_missing=True)
            if len(diff_current1) > 0:
                print(f'The current files are different from the release{"" if force else" (use -f)"}')
                print('\n'.join(diff_current1))
                if not force:
                    print(f'For update use option -f')
                    return False, 'The current files are different from the release'
            diff_current2 = self.version_check_zip(self.current_zipname, ignore_missing=False)
        # проверка файлов по new.zip
        # проверяем что new.zip отличается от current.zip
        # zip нельзя просто сравнивать binary из-за разного названия корневой папки можно только по содержимому
        if os.path.exists(self.new_zipname) and os.path.exists(self.current_zipname) and not force:
            if self.read_zip(self.new_zipname) == self.read_zip(self.current_zipname):
                return True, f'The file of the new version matches the current one'
        # Здесь проверяем что вдруг все файлы соответствуют новой версии (отсутствующие файлы важны)
        # и если отличаются и мы не указали пропустить установку и
        # установку надо делать из new.zip (не  by_current и не undo_update) - устанавливаем
        if os.path.exists(self.new_zipname) and not by_current and not undo_update:
            diff_new = self.version_check_zip(self.new_zipname, ignore_missing=False)
            if len(diff_new) > 0:
                # Установка new.zip
                if force or len(diff_current1) == 0:
                    print('Update:\n'+'\n'.join(diff_current2))
                    self.version_update_zip(self.new_zipname)
                    self.rename_new_to_current()
                    return True, f'Update to version {store.version()} complete'
            else:
                self.rename_new_to_current()
                return True, f'Your version is up to date with {self.new_zipname}'
        # Устанавливаем файлы из current.zip
        if by_current and os.path.exists(self.current_zipname):
            store.version_update_zip(self.current_zipname)
            return True, f'Update by current version {store.version()} complete'
        # Устанавливаем файлы из current.zip.bak
        if undo_update and os.path.exists(self.current_bak_zipname):
            self.version_update_zip(self.current_bak_zipname)
            self.rename_new_to_current(undo=True)
            return True, f'Undo to version {store.version()} complete'

def create_signature():
    'Создаем файлы контрольных сумм и подпись для дистрибутива'
    sha_sum_verifier = ShaSumFile()
    priv_keyname = os.path.join(os.path.expanduser('~'), '.ssh', 'sign.private.key')
    fn_sum = store.abspath_join('mbplugin', 'dist', 'sha256sums.txt')
    fn_sig = store.abspath_join('mbplugin', 'dist', 'sha256sums.txt.sig')
    dist_zip_mask = store.abspath_join('mbplugin', 'dist', '*.zip')
    filelist = glob.glob(dist_zip_mask)
    sha_sum_verifier.sign_and_save(priv_keyname, fn_sum, fn_sig, filelist)
    del sha_sum_verifier
    # Verify
    try:
        sha_sum_verifier2 = ShaSumFile()
        sha_sum_verifier2.load_sum_and_sig_by_file(fn_sum, fn_sig)
        sha_sum_verifier2.verify(filelist)
    except Exception:
        os.remove(fn_sum)
        os.remove(fn_sig)
        raise


if __name__ == '__main__':
    #create_signature();sys.exit()

    import pprint
    pp = pprint.PrettyPrinter(indent=4).pprint
    updater = UpdaterEngine()
    #new_version = updater.check_update()
    #print(f'{new_version=}')
    #updater.download_version(new_version)
    #updater.install_update(new_version)
    print(updater.install_update('1.00.02'))
    #print(updater.install_update('', undo_update=True))
    '''
    #releases = requests.get('https://api.github.com/repos/artyl/mbplugin1/releases').json()
    #release = [r for r in releases if not r['prerelease'] and not r['draft']][0]
    #print(f'Latest release on github {release["tag_name"]} by {release["published_at"]} with description:\n{release["body"]}')
    #pp([(a['name'], a['download_count']) for a in release['assets']])

    #print(f'{store.version()==release["tag_name"]}')  # Последний релиз уже установлен

    #name, url = [(a['name'], a['browser_download_url']) for a in release['assets'] if '_bare' in a['name']][0]
    #url_sum = [a['browser_download_url'] for a in release['assets'] if 'sha256sums.txt' == a['name']][0]
    #url_sig = [a['browser_download_url'] for a in release['assets'] if 'sha256sums.txt.sig' == a['name']][0]
    #print(url)
    #data = requests.get(url).content
    #data_sum = requests.get(url_sum).content
    #data_sig = requests.get(url_sig).content
    #sha_sum_verifier = ShaSumFile()
    #sha_sum_verifier.load_and_verify_by_url(url_sum=url_sum, url_sig=url_sig, files={name: data})
    '''