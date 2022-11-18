# Использование mbplugin в качестве модуля

## Вводная

!!! Внимание, использование в таком варианте это пока очень ранняя beta

Можно использовать mbplugin как пакет python формат вызова:  
имя_плагина.get_balance(логин, пароль, опции) 
в качестве опций могут быть использованы параметры из секции Options, описание их можно найти в mbplugin_ini.md, 
не все опции имеют смысл. т.к. изначально создавались под работу через MobileBalance либо полноценное приложение 

## использование плагинов работающих через браузер (playwright)

Перед использованием плагинов работающих через браузер необходимо установить browser engine командой 
```sh
python -m playwright install
```

## пример кода
```py
from mbplugin.plugin import test3
result = test3.get_balance('demo@saures.ru', 'demo', show_chrome=1, logconsole=0, logging='ERROR')
print(result)
``` 
