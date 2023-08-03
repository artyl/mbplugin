'''
https://github.com/artyl/mbplugin/issues/36
Конвертер csv -> phones.ini 
Решил сделать более универсальный вариант.
В файле phones.csv находятся все поля которые должны попасть в phones.ini разделенные табуляцией (если хотите другой символ его можно поменять в первой строчке файла скрипта csv_to_phones_ini.py)
В архиве скрипт и пример CSV файла
csv_to_phones_ini.zip
Первая строчка phones.csv это заголовки (то что в ini будет перед равно) строчки начиная со второй - значения
кладете в одну папку файл csv_to_phones_ini.py из архива и подготовленный csv файл.
Запускаете (исправьте на путь к Вашему python)
C:\mbstandalone\mbplugin\python\python.exe csv_to_phones_ini.py 
После запуска будет создан файл phones.gen.ini проверяете, если все ок - переименовываете и кладете вместо phones.ini
Задача разовая, так что не уверен что стоит это добавлять в код mbplugin как опцию пока оставим в таком сыром виде.
Возможно потом сделаю в более удобоваримом виде.
'''

delimeter = '\t'
data = open('phones.csv', encoding='cp1251').read().strip().splitlines()
res = []
headers = data[0].split(delimeter)
for num, lines in enumerate(data[1:], 1):
    res.append(f'\n[Phone] #{num}')
    for ne, el in enumerate(lines.split(delimeter)):
        res.append(f'{headers[ne]} = {el}')
print(('\n'.join(res)).strip())
open('phones.gen.ini', 'w').write(('\n'.join(res)).strip())
        
