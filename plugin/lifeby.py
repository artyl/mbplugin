# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789c75937754080a14c67f3cebf178de160d9236ca28698a4a91346c52561a08111a4856cba834282a24499194d1521ab29a48284aa5b4131a3cbcd3393acf77ce77eefdcebde7bbf7fe7135f515faf2150a7d40f2df38f43ff662c0b7422f481ff28d5ff22ff415ed8d9f783ffc24fae32f3d9000994104ca0e26445988705d5922f4e589325122d64c87784b4312ac8d4975b622c3cd9e1c6f17f2c37c284d8ea33c33898aec14aaf372a82b29a2b9a28cb6ba1a3a3bdaf9f4e913c3870f67c48811080a0a22242484b0b0302222228c1c399251a346212a2acae8d1a311131363cc9831888b8b23212181a4a424525252484b4b23232383acac2c63c78e65dcb8718c1f3f1e393939e4e5e59930610213274e64d2a4494c9e3c190505051415159932650a4a4a4a4c9d3a15656565545454505555454d4d0d75757534343498366d1a9a9a9a4c9f3e9d193366a0a5a585b6b6363a3a3acc9c39135d5d5df4f4f498356b16b367cf465f5f9f3973e6606060c0dcb973313434c4c8c8086363634c4c4c98376f1ef3e7cf67c182052c5cb890458b16b178f162962c59c2d2a54b59b66c19a6a6a62c5fbe1c333333cccdcd59b162052b57ae64d5aa55ac5ebd9a356bd6606161c1dab56bb1b4b4c4caca0a6b6b6b6c6c6c58b76e1debd7af67c3860dd8dadab271e346366ddac4e6cd9bb1b3b363cb962d6cddba157b7b7bb66ddbc6f6eddbd9b163070e0e0e383a3ae2e4e484b3b3333b77ee64d7ae5decdebd1b171717f6ecd983abab2b7bf7ee65dfbe7decdfbf9f03070e70f0e041dcdcdc707777c7c3c3034f4f4fbcbcbc3874e810870f1fe6c891231c3d7a146f6f6f7c7c7cf0f5f5e5d8b163f8f9f9e1efef4f4040008181811c3f7e9c13274e10141444707030274f9ee4d4a953848484101a1a4a585818a74f9fe6cc99339c3d7b96f0f070ce9d3b47444404e7cf9f273232920b172e101515c5c58b17898e8e262626864b972e71f9f265626363b972e50a7171715cbd7a95f8f878121212b876ed1ad7af5fe7c68d1bdcbc7993c4c444929292484e4e26252585d4d4546eddba455a5a1ae9e9e9dcbe7d9b8c8c0c323333c9caca223b3b9b3b77ee909393c3ddbb77b977ef1ef7efdfe7c183073c7cf890dcdc5cf2f2f2c8cfcfa7a0a080c2c2428a8a8a78f4e8118f1f3fe6c99327141717f3f4e9534a4a4a78f6ec19cf9f3fe7c58b17949696525656c6cb972f79f5ea15e5e5e5545454f0faf56b2a2b2ba9aaaaa2baba9a376fde505353436d6d2d6fdfbea5aeae8efafa7a1a1a1a686c6ca4a9a989e6e6665a5a5a686d6de5ddbb77b4b5b5f1fefd7b3e7cf8c0c78f1f696f6fa7a3a383cece4ebabababefee50ff0f39f7dbfd3fd057efdbee1f77f7eeacefbfdfd1b83057ee9d6030586f51e2030b45bf71a32883e027f7c6f30ecaf1fea9efd3dfd7aceebb9cfffecdbf39e6e7c06d44badca'

login_url = 'https://life.com.by/id'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]',
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['LHA_getUserBalance'], 'jsformula': "parseFloat(data.total).toFixed(2)"},
            {'name': 'UserName', 'url_tag': ['LH_Active_TP'], 'jsformula': "data.lastName+' '+data.firstName"},
            {'name': 'LicSchet', 'url_tag': ['LH_Active_TP'], 'jsformula': "data.MSISDN"},
            {'name': 'TarifPlan', 'url_tag': ['LH_Active_TP'], 'jsformula': "data.tariffName"},
            {'name': 'BlockStatus', 'url_tag': ['LH_Active_TP'], 'jsformula': "data.state_TP"},
            {'name': 'Min', 'url_tag': ['LHA_getCurrentBalances'], 'jsformula': "data.filter(el=>el.emptyIconType=='call')[0].title.replace(/\D/g,'')"},
            {'name': 'SMS', 'url_tag': ['LHA_getCurrentBalances'], 'jsformula': "data.filter(el=>el.emptyIconType=='sms')[0].title.replace(/\D/g,'')"},
            {'name': 'Internet', 'url_tag': ['LHA_getCurrentBalances'], 'jsformula': "data.filter(el=>el.emptyIconType=='traffic')[0].title.replace(/[^\d.,]/g,'').replace(',','.')"},
            #{'name': 'UslugiOn', 'url_tag': ['LHA_getUserServices'], 'jsformula': "'0/'+data.length"},
            #{'name': 'UslugiList', 'url_tag': ['LHA_getUserServices'], 'jsformula': "data.map(el=>el.title+'\t0р').join('\n')"},
            ])
            

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module life.com.by')
