# Шлюз для запроса баланса из программы MobileBalance без Internet Explorer.
- шлюз дает возможность писать собственные скрипты на любом языке и уходит от ограничений IE для javascript.
- Т.к. mobilebalance меньше дергает IE он меньше подвисает и падает.
- Можно сохранять сессии, т.е. на каждый телефон tele2 у вас будет своя сессия с сохраненными куками.
- Все собрано таким образом чтобы не оказывать никакого влияния на установленные программы, в т.ч. если установлен python другой версии.
- Есть два варианта использования вызов через DLL - dllplugin плагин и вызов через локальный вебсервер jsmblhplugin. 
- jsmbLh и DLL плагины это всего-лишь обертка, которая кнутри вызывает одни и те же плагины
- Т.к. у версии dllplugin обнаружился недостаток в виде того что MobileBalance принимает из dllplugin ограниченное количество параметров, то в настоящий момент приоритетной является версия с вебсервером - jsmblhplugin, хотя если вам нужен только баланс и какие-то базовые вещи, то никто не мешает использовать и dllplugin.

## Короткая инструкция по установке. 
1. Свежую версию сборки можно найти в [releases](https://github.com/artyl/mbplugin/releases) в моем репозитории на github или в форуме на 
[4pda](https://4pda.ru/forum/index.php?showtopic=985296&st=140#entry97043755) посвященном MobileBalance.  
2. 2.Распаковать свежую версию сборки в папку где установлен MobileBalance (точнее где находятся файлы Options.ini, phones.ini, BalanceHistory.mdb если в папке MobileBalance.exe есть а указанных файлов нет, то пробуйте поискать в папке например вместо C:\Program Files (x86)\Mobilebalance посмотрите в папке %localappdata%\VirtualStore\Program Files (x86)\Mobilebalance или просто поищите по диску в какой папке у вас находится phones.ini и другие файлы). В принципе можно распаковать в любую папку, в которую у скрипта при работе будет доступ на запись, базовый функционал будет работать, все остальное можно донастроить потом.  
3. Запустить из папки mbplugin setup_and_check.bat (он пересоберет плагины, поставит в автозагрузку веб сервер и проверит работу тестовым плагином)  
4. Подключить нужные плагины из папки mbplugin\jsmblhplugin
5. Можно пользоваться.  

__ВАЖНО! веб сервер__  
Веб сервер нужен для jsmbLH плагинов (запускается mbplugin\run_webserver.bat), а кроме этого если включить режим записи в БД, то через web сервер становиться доступен просмотр отчетов по телефонам, полученным через mbplugin [report](http://localhost:19777/report)  

## На данный момент реализованы плагины:
(Источником информации послужили как собственное изучение так и существующие плагины, так что пользуясь случаем хочу выразить благодарность всем авторам
leha3d Pasha comprech y-greek и другим, кто тратил свои силы и время на реверс сайтов операторов и разработку)  
test1 - Простой тест с демонстрацией всех полей  
test2 - Пример реализации ввода капчи  
mts - МТС (сотовая связь)  
beeline - Билайн (сотовая связь)  
megafon - Мегафон (сотовая связь)  
tele2 - ТЕЛЕ2 (сотовая связь)  
yota - Yota (сотовая связь)  
danycom - Danycom (сотовая связь)  
strelka - Баланс карты стрелка  
smile-net - Infoline/smile-net/Virgin connect (Интернет провайдер)  
onlime - onlime.ru (Интернет провайдер)  
zadarma - Zadarma.com (IP телефония)  
cardtel - Cardtel (IP телефония)  
sipnet - Sipnet (IP телефония)  
sodexo - Получение баланса карты Sodexo (подарочные карты)  
usd - Курс доллара с RBC  
eur - Курс евро с RBC  
financeyahoo - Курс ценных бумаг с finance.yahoo.com  
moex - Курс ценных бумаг с moex.com  
stock - Рассчет цены портфеля ценных бумаг  
avtodor-tr - Автодор транспондер  
parking_mos - parking.mos.ru оплата парковки (Вход через логин/пароль на login.mos.ru)

## Кроме простого использования есть еще
Запись в базу sqlite 
Импорт данных из mdb базы mobilebalanse в БД sqlite (необходима установка odbc драйвера для mdb) (для первоначального полного импорта используйте copy_alldata_from_mdb.bat)
В случае включения записи в базу sqlite можно в вебсервере также просматривать отчеты по балансам и генерировать html отчет  
В перспективе планирую, чтобы mbplugin работал как самостоятельное приложение  

### mbplugin.ini
Если архив был распакован в одну из папок в папке MobileBalance то при первом запуске (setup_and_check.bat) в папке, где находится mobilebalance.exe будет создан mbplugin.ini с дефолтовыми минимальными настройками (по умолдчанию все доп фишки выключены).
Если архив распакован не в папку с mobilebalance, то прижелании получить дополнительный функционал необходимо в секции [MobileBalance] path прописать путь в папку с mobilebalance  
Что можно включить:  
* __logginglevel__ - журнал работы mbplugin, по умолчанию включен режим INFO, журнал ведется в папке mbplugin\log, dllplugin пишет в mbplugin.log, jsmbLh плагин пишет в http.log в режиме DEBUG в папку log сохраняются все страницы загруженные в процессе получения баланса
* __loggingfilename__ = путь к файлу лога, относительно папки plugin, для dllplugin
* __logginghttpfilename__ = путь к файлу лога, относительно папки plugin, для web север
* __mts_usedbyme__ = 0 - спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный, 0 - показывать оставшийся трафик (NonUsed) по всем, 1 - показывать использованный трафик (usedByMe) по всем, или список тел, через запятую - показать использованный только для этих списка телефонов
* __sqlitestore__ = 1 - запись запросов в sqlite БД, ghbxtv пишуться все поля, напримет те же SMS, которые не принимает MobileBalance через DLL, sqlite БД по умолчанию находится в папк mobilebalance, но при желании это путь можно изменить в параметре dbfilename  
* __createhtmlreport__ = 1 (требуется включенный sqlitestore = 1)- после каждого вызова mbplugin создавать файл с отчетом, сходный с html страничкой, которую mobilebalance умеет отдавать в виде html. Список полей в отчете можно поменять в переменной table_format, только не трогайте на первых двух местах PhoneNumber,Operator, иначе сломается. Пока не придумал как по другому.
Местоположение отчета по умолчанию - в папке mbplugin\db\balance.html, если хотите в другое место - меняйте параметр balance_html
Если выставить sqlitestore = 1 и createhtmlreport = 1, то после каждого получения баланса будет генерироваться файл db\balance.html максимально близкий по виду к файлу который генерирует MobileBalance, но только по по тем телефонам, баланс которых мы получаем через mbplugin. Также все данные получаемые через mbplugin сохраняются в базу SQLITE схожей структуры с BalanceHistory.mdb. Данная возможность позволяет видеть те поля, которые не принимает MobileBalance из DLL плагинов, наприимер количество SMS.  
* __updatefrommdb__ = 1 - Экспериментальная фишка. Импорт данных из BalanceHistory.mdb после каждого запроса, требует установленного ODBC драйвера и включенного sqlitestore = 1,
для интеграции с базой MDB необходимо установить 32битный ODBC драйвер для MDB AccessDatabaseEngine.exe [Скачать можно отсюда](https://www.microsoft.com/en-us/download/details.aspx?id=13255)
   
* __path__ - путь к папке, где находится MobileBalance  
* Для использования этих возможностей убедитесь, что в файле mbplugin.ini в разделе [MobileBalance] параметр path указывает на папку где находится mobilebalance.exe. Если вы распаковали архив в подпапку в папке с MobileBalance то path должен настроиться автоматически.

### log журналы
В папке mbplugin\log ведется журнал работы mbplugin

## Как проверить что все работает
Запустите mbplugin\setup_and_check.bat он пересобирет плагины, настроил автозапуск web сервера для jsmbLH плагинов и проверит работу плагинов запуском обоих вариантов тестового плагина. На экран будет выведено примерно следующе 

```
Compile to p_moex.dll
Compile to p_mts.dll
Compile to p_parking_mos.dll
Compile to p_sipnet.dll
Compile to p_smile-net.dll
Compile to p_sodexo.dll
Compile to p_stock.dll
Compile to p_strelka.dll
Compile to p_tele2.dll
Compile to p_test1.dll
Compile to p_test2.dll
Compile to p_usd.dll
Compile to p_zadarma.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_avtodor-tr.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_beeline.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_cardtel.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_danycom.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_eur.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_financeyahoo.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_megafon.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_moex.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_mts.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_parking_mos.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_sipnet.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_smile-net.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_sodexo.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_stock.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_strelka.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_tele2.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_test1.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_test2.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_usd.dll
C:\new\mobil\MobileBalance\Pluguns\mbplugin\dllsource\p_zadarma.dll
Перемещено файлов:        20.
Пересобираем JSMB LH plugin
Создаем lnk на run_webserver.bat и помещаем его в автозапуск и запускаем
Скопировано файлов:         1.
Проверяем что все работает JSMB LH PLUGIN
<html><meta charset="windows-1251"><p id=response>{"Balance": 124.45, "Balance2": 22, "Balance3": 33, "LicSchet": "Лицевой счет", "UserName": "ФИО", "TarifPlan": "Тарифный план", "BlockStatus": "Статус блокировки", "AnyString": "Любая строка", "SpendBalance": 12, "KreditLimit": 23, "Currenc": "Валюта", "Average": 5, "TurnOffStr": "Ожидаемая дата отключения", "Recomend": 54, "SMS": 43, "Min": 222, "SpendMin": 32, "Expired": "Дата истечения баланса/платежа", "ObPlat": 14, "Internet": 1234, "UslugiOn": "2/8"}</p></html>
Проверяем что все работает DLL PLUGIN
INFO:
<IssaPlugin>
<Operator>DLL p_test1</Operator>
<ShortName>p_test1</ShortName>
<Author>ArtyLa</Author>
<Version>Jun 28 2020</Version>
</IssaPlugin>
EXECUTE:
<Response><Balance>124.45</Balance><Balance2>22</Balance2><Balance3>33</Balance3><LicSchet>Лицевой счет</LicSchet><UserName>ФИО</UserName><TarifPlan>Тарифный план</TarifPlan><BlockStatus>Статус блокировки</BlockStatus><AnyString>Любая строка</AnyString><SpendBalance>12</SpendBalance><KreditLimit>23</KreditLimit><Currenc>Валюта</Currenc><Average>5</Average><TurnOffStr>Ожидаемая дата отключения</TurnOffStr><Recomend>54</Recomend><SMS>43</SMS><Min>222</Min><SpendMin>32</SpendMin><Expired>Дата истечения баланса/платежа</Expired><ObPlat>14</ObPlat><Internet>1234</Internet><UslugiOn>2/8</UslugiOn></Response>
Для продолжения нажмите любую клавишу . . .
```

## Немного технических деталей
### Установка из исходников из github 
Склонировать репозиторий c github (обновления можно так же будет накатывать через git pull)
``` 
git clone <https://github.com/artyl/mbplugin>
```
загрузить и распаковать tcc и python:  
```
tcc\get_tcc.bat  
python\get_python.bat  
```
tkinter для python, если нужен ввод капчи для python к сожалению автоматом поставить не получиться, нашел только [такой способ](https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter)  
Сборка всех DLL: dllsource\compile_all_p.bat  
После этого все DLL будут находится в папке mbplugin\dllplugin  
Если есть желание использовать свой питон, тогда можно поменять вызов в mbplugin\plugin\mbplugin.bat

## Использование.
Теперь есть два варианта использования jsmblh plugin (jsmb localhost) приоритетный вариант и старый вариант dllplugin
jsmblh plugin мы подключаем из папки mbplugin\jsmblhplugin dllplugin из папки mbplugin\dllplugin
### jsmblhplugin
Для использования добавить в автозагрузку mbplugin\run_webserver.bat и  подключить нужный плагин из папки mbplugin\jsmblhplugin  
Вызов осуществляется через jsmb плагин, который передает параметры в webserver, который в свою очередь уже вызывает сам плагин. Плюсы - получаем все поля, которые могли использовать в jsmb плагинах, минусы - необходимо запускать webserver, также в этой схеме больше участия IE, и возможно глюков от замусоренного кэша IE будет больше.  
!ВАЖНО! Не забывайте, что для работы jsmblhplugin должен быть запущен web server mbplugin\run_webserver.bat (при звпущенном webserver появляется иконка в трее)
### dllplugin
Для использования в MobileBalance подключить нужный dll плагин из папки mbplugin\dllplugin
Вызов плагина осуществляется через вызов DLL, плюс - минимальное участие IE, минус MB не все поля принимает обратно  
Пути, жестко прописываются в DLL, в готовой сборке они смотрят в C:\mbplugin, если ваша папка отличается от этой, то запустите dllsource\compile_all_p.bat  
Подключить DLL для нужных провайдеров (Настройки\Плагины\Операторы Добавить и выбрать DLL для нужных операторов)
В настройках для соответсвующего телефона выбрать провайдера соответствующей DLL
!ВАЖНО! Dll plugin привязан к той папке, куда настроен, если вы хотите переместить папку mbplugin в другое место, то после перемещения ОБЯЗАТЕЛЬНО запустите mbplugin\setup_and_check.bat

## Как написать свой плагин
Если на python, то это файл с функцией get_balance(login, password, storename)
storename это строка, используемая как ключ для хранения сессии. Формируется как имя плагина + login
Функция возвращяет результат в виде словаря.
Можно посмотреть как сделаны другие плагины, также есть простые тестовые.
После того как плагин будет готов запускаем C:\mbplugin\setup_and_check.bat и будут пересобраны DLL и jsmbLH для всех имеющихся в папке C:\mbplugin\plugin плагинов.
Подключаем полученный jsmbLH или DLL плагин  в MobileBalance и используем его для получения баланса, не забывайте что для jsmbLH нужен запущенный веб сервер.

## Как работает вариант jsmbLH
На компьютере работает веб сервер (по умолчению на 19777 порту, который принимает обращения из пустышек-jsmbLH плагинов и реализует обращение к самим плагинам). Работа самих плагинов не зависит от того кто их вызвал DLLplugin или jsmbLH плагин 

## Как работает вариант DLL
ВАЖНО! DLL собраны 32 битном компиляторе, и вызываться должны из 32 битного приложения 32 битную DLL вызвать из 64 битного приложения нельзя.  
Mobilebalance вызывает DLL передавая ей логин и пароль через xml строку
В самой DLL никакого функционала нет, она служит лишь оберткой для передачи вызова в mbplugin\plugin\mbplugin.bat  
DLL вызывает mbplugin\plugin\mbplugin.bat передавая ему имя плагина в качестве параметра, а переданный XML через переменную окружения RequestVariable
mbplugin.bat вызывает mbplugin.py в котором вызывается соответсвующий python плагин.
mbplugin.bat возвращает результат через stdout.

Данные по параметрам вызова DLL были получены с помощью реверса существующего DLL плагина.
Я постарался сделать все так, чтобы все можно было собрать за 10 минут не устанавливая 10 гигабайтные компиляторы, минималистичная DLL весь код вынесен в скрипты.
Конечно DLL можно собрать и на vc и gpp и на Delphi и много на чем еще,
но для этого нужно много возни с установкой среды, в моем варианте все можно собрать с нуля за 10 минут скачав несколько десятков мегабайт.  
Количество кода для DLL минимум, чтобы любой  желающий мог без труда убедится что в нем нет закладок.

Остальной код на скриптах, и его можно проверить в любой момент.
C я знаю не очень хорошо, поэтому единственный простой способ передать request я нашел через переменную окружения, а возврат осуществляется через поток вывода.
Пути в папке mbplugin внутри DLL приходится прописывать абсолютными, потому что из DLL выяснить по какому пути она находится оказалось очень нетривиальной задачей, даже имя DLL узнать очень непросто. В принципе это проблема небольшая на tcc все пересобирается за пару секунд.
Хотел сохранить настройки для путей в реестре, но из реестра прочитать оказалось тоже не просто.
В результате у меня получилось сделать только так, код на C получился не очень хороший, но работоспособный.
Если кто в состоянии причесать сишный код, буду признателен.
Вызов bat файла а не напрямую скрипта python сделан для того чтобы если будет желание отвязаться от python, с минимумом изменений в остальном коде.

Т.к. в запросе передается только логин и пароль, то нам приходится сделать по отдельной DLL для каждого сервиса
Чтобы оставить задел на будущее я для плагинов добавил еще префиксы, для питона это p_
Таким образом мы генерируем dll по следующему принципу:
Для python плагина tele2 - файл плагина tele2.py
tele2 - имя модуля на python который получает баланс
p_tele2.dll - dll которую мы подключаем в mobilebalance

В процессе эксплуатации выяснилось, что mobilebalance оказывается все поля  принимает из результата возвраженного DLLplugin, как оказалось, например не понимает остаток SMS,
Список принимаемых полей достаточно короткий:  
- Balance
- Expired 
- Min 
- Internet 
- TarifPlan
- BlockStatus
- AnyString

Все кроме этого будет проигнорировано

Несмотря на то что на первый взгляд это все идет не через браузер mobilebalance все равно перед стартом DLL дергает движок IE (res://ieframe.dll/navcancl.htm и about:blank) - это видно по логу и появлению файлов в папке кэша IE, так что не исключаю, что часть каких-то глюков может по прежнему лечиться чисткой кэша браузера, хотя это и маловероятно.

ВАЖНО. В xml который возвращает плагин поля case sensitive, так что если будет balance вместо Balance MB будет писать что баланс равен нулю.

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
