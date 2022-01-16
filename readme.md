# Автоматический контроль баланса сотовых операторов и не только их

## Возможности программы MBplugin

На текущий момент самостоятельное приложение (Windows Linux и MacOs.), позволяющее автоматизировать получение балансов МТС, Билайн, Мегафон, Теле2, Yota(modem), Ростелеком, ОнЛайм, Zadarma, Cardtel, SipNet, Карта стрелка, Автодор транспондер, Московский паркинг, Мосэнергосбыт, курсы валют и акций, список операторов пополняется.  
Изначально была написана как надстройка для MobileBalance и такой вариант работы также возможен.  
В инструкции вариант использования без MobileBalance называется **standalone**.  
Интерфейс программы организован в виде внутреннего веб сервера.  
Умеет отправлять полученные балансы в телеграм, также через телеграм бота можно производить запросы по телефонам.  
Для работы с личными кабинетами используется где это возможно API и простые запросы. В сложных случаях (коих как показала практика большинство) используется библиотека [playwright-python](https://github.com/microsoft/playwright-python)
Все возможности standalone версии доступны и в режиме работы как плагина для MobileBalance (см соответствующий раздел в инструкции в Standalone версии)  

## Инструкцию по настройке в режиме самостоятельной программы смотрите в standalone.md 
Полное отсутствие ограничений, накладываемых лицензией mobilebalance, можно проверять любое количество телефонов.  
[Инструкция по варианту использования standalone](https://github.com/artyl/mbplugin/blob/master/standalone.md)

## Инструкцию по настройке в режиме мега-плагина для программы MobileBalance смотрите в mobilebalance.md 
[Инструкция по варианту использования mobilebalance](https://github.com/artyl/mbplugin/blob/master/mobilebalance.md)

## Дополнительная информация
[История изменения (в ней часть информации не попавшая в документацию)](https://github.com/artyl/mbplugin/blob/master/changelist.md)  
[Описание параметров mbplugin.ini (почти все параметры из секции Options из mbplugin.ini могут быть прописаны индивидуально в секцию к телефону)](https://github.com/artyl/mbplugin/blob/master/mbplugin_ini.md)

## На данный момент реализованы плагины

(Источником информации послужили как собственное изучение так и существующие плагины, так что, пользуясь случаем, хочу выразить благодарность всем авторам:
leha3d, Pasha, comprech, y-greek и другим, кто тратил свои силы и время на реверс сайтов операторов и разработку)  
mts - mts.ru МТС (сотовая связь)  
beeline - beeline.ru Билайн (сотовая связь)  
beeline_uz - beeline.uz Билайн Узбекистан (сотовая связь)  
megafon - megafon.ru Мегафон (сотовая связь)  
megafonb2b - b2blk.megafon.ru Мегафон b2b (сотовая связь)  
tele2 - tele2.ru (сотовая связь)  
yota - yota.ru (сотовая связь)  
a1by - a1.by A1(velcom) Беларусь (сотовая связь) (автор Exemok)  
rostelecom - lk.rt.ru Ростелеком (телефония и интернет)  
smile-net - smile-net.ru Infoline/smile-net/Virgin connect (Интернет провайдер)  
onlime - onlime.ru (Интернет провайдер)  
lovit - lovit.ru (Интернет провайдер)  
east - east.ru (East Telecom internet provider)  
uminet - uminet.ru (Интернет провайдер)  
zadarma - Zadarma.com (IP телефония)  
cardtel - cardtel.ru (IP телефония)  
sipnet - Sipnet.ru (IP телефония)  
strelka - strelka.ru Баланс карты стрелка  
sodexo - sodexo.com Получение баланса карты Sodexo (подарочные карты)  
currency - Курсы валют USD, EUR, с ЦБ и с MOEX, курсы акций с MOEX и yahoo finance (заменил плагины eur, usd, moex и yahoo)
stock - Расчет цены портфеля ценных бумаг  
avtodor-tr - avtodor-tr.ru Автодор транспондер  
parking_mos - parking.mos.ru оплата парковки (Вход через логин/пароль на login.mos.ru)  
mosenergosbyt - mosenergosbyt.ru Сайт мосэнергосбыт (ЖКХ) 
chailand - chailand.ru Карта парка атракционов
vscale - vscale.ru Облачные серверы для разработчиков  
beget - beget.ru (хостинг-провайдера BEGET) (автор d1mas)  
Для плагинов rostelecom и mosenergosbyt можно указывать конкретный лицевой счет если их несколько в формате ```login/лицевой_счет```  

### Тестовые плагины
test1 - Простой тест с демонстрацией всех полей (на нем хорошо видно что из DLL плагина приходят не все поля)  
test2 - Пример реализации ввода капчи через tix/tkinter  
test3 - Пример реализации проверки через браузер (playwright)  
test4 - Пример ручной реализации проверки через браузер (playwright)  

### Обратная связь.
Оптимальный способ обратной связи - [оставить issue на github](https://github.com/artyl/mbplugin/issues) (для создания issue нужно зарегистрироваться)  
Также обсуждение работы проходит в [форуме 4pda посвященном программе MobileBalance](https://4pda.to/forum/index.php?showtopic=985296)  
Или [в канале телеграмм](https://t.me/mbplugin)  
