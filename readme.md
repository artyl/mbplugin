# DLL шлюз для запроса баланса из программы MobileBalance без Internet Explorer.
DLL шлюз дает возможность писать собственные скрипты и уходит от ограничений IE для javascript.
Т.к. mobilebalance меньше дергает IE от меньше подвисает и падает.
Можно сохранять сессии, т.е. на каждый телефон tele2 у вас будет своя сессия с сохраненными куками.
Все собрано таким образом чтобы не оказывать никакого влияния на установленные программы, в т.ч. если установлен python другой версии.

## Установка Вариант 1 Готовый архив (простой)
Архив можно найти в [releases](https://github.com/artyl/mbplugin/releases) на github или в форуме на [4pda](https://4pda.ru/forum/index.php?showtopic=985296) посвященном MobileBalance.  
Архив распаковать в папку C:\mbplugin

## Установка Вариант 2 Из github 
Склонировать репозиторий в папку C:\mbplugin  
git clone <https://github.com/artyl/mbplugin> C:\mbplugin  
загрузить и распаковать tcc и python:  
TCC: C:\mbplugin\tcc\get_tcc.bat  
PYTHON: C:\mbplugin\python\get_python.bat  
tkinter для python, если нужен ввод капчи для python к сожалению автоматом поставить не получиться, нашел только [такой](https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter)  
Сборка всех DLL: C:\mbplugin\dllsource\compile_all_p.bat  
После этого все DLL будут находится в папке C:\mbplugin\dllplugin  
Если есть желание использовать свой питон, тогда можно поменять вызов в C:\mbplugin\plugin\mbplugin.bat

## Использование.
Пути, по крайней мере пока, жестко захардкожены и все должно лежать именно в такой структуре в папке C:\mbplugin
Подключить DLL для нужных провайдеров (Настройки\Плагины\Операторы Добавить и выбрать DLL для нужных операторов)
В настройках для соответсвующего телефона выбрать провайдера соответствующей DLL

## На данный момент реализованы плагины:
(Источником информации послужили как собственное изучение так и существующие плагины, так что пользуясь случаем хочу выразить благодарность всем авторам
leha3d Pasha comprech y-greek и другим, кто тратил свои силы и время на реверс сайтов операторов и разработку)  
test1 - Простой тест с демонстрацией всех полей (правда оказалось, что MB из DLL принимает только Balance Expired Min Internet TarifPlan BlockStatus AnyString)
test2 - Пример реализации ввода капчи  
beeline - Билайн  
cardtel - Cardtel (IP телефония)  
megafon - Мегафон  
mts - МТС  
sodexo - Получение баланса карты Sodexo (подарочные карты)  
strelka - Баланс карты стрелка  
tele2 - ТЕЛЕ2  
zadarma - Zadarma.com (IP телефония)  
usd - Курс доллара с RBC  
eur - Курс евро с RBC  
financeyahoo - Курс ценных бумаг с finance.yahoo.com  
moex - Курс ценных бумаг с moex.com  
stock - Рассчет цены портфеля ценных бумаг  
sipnet - Sipnet (IP телефония)  
avtodor-tr - Автодор транспондер  

## Как проверить вручную
запустите из C:\mbplugin\plugin:
C:\mbplugin\plugin\test_mbplugin_login_pass.bat p_test login password
Если в консоль будет выведен XML, то скорее всего у вас все работает:
```
<Response><Balance>124.45</Balance> .... </Response>
```
Таким же образом можно проверить любой плагин:
C:\mbplugin\plugin\test_mbplugin_login_pass.bat p_[имя плагина на python] [логин] [пароль]

## Как это работает
Mobilebalance вызывает DLL передавая ей логин и пароль через xml строку
DLL вызывает C:\mbplugin\plugin\mbplugin.bat передавая ему имя плагина в качестве параметра, а переданный XML через переменную окружения RequestVariable
mbplugin.bat вызывает mbplugin.py в котором вызывается соответсвующий DLL плагин.
mbplugin.bat возвращает результат через stdout.

## Почему так сделано.
Данные по параметрам вызова DLL были получены с помощью реверса существующего DLL плагина.
Я постарался сделать все так, чтобы все можно было собрать за 10 минут не устанавливая 10 гигабайтные компиляторы, минималистичная DLL весь код вынесен в скрипты.
Конечно DLL можно собрать и на vc и gpp и на Delphi и много на чем еще,
но для этого нужно много возни с установкой среды, в моем варианте все можно собрать с нуля за 10 минут скачав несколько десятков мегабайт.
DLL мог без труда любой желающий и убедится что в ней нет закладок.
Остальной код на скриптах, и его можно проверить в любой момент.
C я знаю не очень хорошо, поэтому единственный простой способ передать request я нашел через переменную окружения, а возврат осуществляется через поток вывода.
Пути прописаны абсолютными, потому что из DLL выяснить по какому пути она находится оказалось очень нетривиальной задачей, даже имя ее узнать очень непросто.
Хотел сохранить настройки путя в реестре, но из реестра прочитать оказалось тоже не просто.
В у меня получилось сделать только так, код на C получился достаточно корявый, но у меня вроде работоспособен.
Если кто в состоянии причесать сишный код, буду признателен.
Вызов bat файла а не python сделан для того чтобы если будет желание отвязаться от python
с минимумом изменений в остальном коде.

Т.к. в запросе передается только логин и пароль, то нам приходится сделать по отдельной DLL для каждого сервиса
Чтобы оставить задел на будущее я для плагинов добавил еще префиксы, для питона это p_
Таким образом мы генерируем dll по следующему принципу:
Для python плагина tele2 - файл плагина tele2.py
tele2 - имя модуля на python который получает баланс
p_tele2.dll - dll которую мы подключаем в mobilebalance

Не все поля оказывается понимает, как оказалось, например не понимает SMS,
Насколько я понял воспринимает только:
Balance Expired Min Internet TarifPlan BlockStatus AnyString
Все кроме этого будет проигнорировано

Несмотря на то что на первый взгляд это все идет не через браузер mobilebalance все равно перед стартом DLL
дергает движок IE (res://ieframe.dll/navcancl.htm и about:blank) - это видно по логу и появлению файлов
в папке кэша IE, так что не исключаю, что часть каких-то глюков может по прежнему лечиться чисткой кэша
браузера, хотя это и маловероятно.

Все это добро выложил на [github](https://github.com/artyl/mbplugin)
Там только исходники, после загрузки проекта поместить его в папку C:\mbplugin

## Как написать свой плагин
Если на python, то это файл с функцией get_balance(login, password, storename)
storename нужен для хранения сессии, формируется как имя плагина + login
Функция возвращяет результат в виде словаря.
После того как плагин будет готов запускаем C:\mbplugin\dllsource\compile_all_p.bat и будут пересобраны DLL для всех имеющихся в папке C:\mbplugin\plugin плагинов
Подключаем полученную DLL в MobileBalance и используем ее для получения баланса.
ВАЖНО. В xml который возвращает плагин поля case sensitive, так что если будет balance вместо Balance
MB будет писать что баланс равен нулю.

--- Структура request который приходит из mobilebalance через переменную окружения ----------
```
<?xml version="1.0" encoding="windows-1251" ?>
<Request>
  <ParentWindow>007F09DA</ParentWindow>
  <Login>loginlogin</Login>
  <Password>password123456</Password>
</Request>
```
---- В mobilebalance уходит xml через вывод на экран -------------
```
<Response><Balance>123</Balance></Response>
```
