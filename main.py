from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.list import TwoLineListItem
import requests

KV = '''
MDBoxLayout:
    orientation: 'vertical'
    MDTopAppBar:
        title: "ККТ РФ Сканер"
        md_bg_color: 0, 0, 0, 1
    
    MDBottomNavigation:
        MDBottomNavigationItem:
            name: 'scan'
            text: 'Проверка'
            icon: 'qrcode-scan'
            MDBoxLayout:
                orientation: 'vertical'
                padding: "20dp"
                spacing: "10dp"
                
                MDTextField:
                    id: fn
                    hint_text: "ФН"
                    mode: "rectangle"
                MDTextField:
                    id: fd
                    hint_text: "ФД"
                    mode: "rectangle"
                MDTextField:
                    id: fp
                    hint_text: "ФП"
                    mode: "rectangle"
                MDTextField:
                    id: summ
                    hint_text: "Сумма"
                    mode: "rectangle"
                MDTextField:
                    id: date
                    hint_text: "Дата (ГГГГММДДTЧЧММ)"
                    mode: "rectangle"
                
                MDRaisedButton:
                    text: "ОТПРАВИТЬ НА САЙТ"
                    size_hint_x: 1
                    on_release: app.send_to_site()
                
                MDLabel:
                    id: status
                    text: "Ожидание..."
                    halign: "center"

        MDBottomNavigationItem:
            name: 'history'
            text: 'История'
            icon: 'history'
            on_tab_press: app.show_history()
            MDScrollView:
                MDList:
                    id: hist_list
'''

class MobileKKT(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def send_to_site(self):
        url = "https://кктрф.рф/Rss_api/proverka.php"
        payload = {
            "fn": self.root.ids.fn.text,
            "fd": self.root.ids.fd.text,
            "fp": self.root.ids.fp.text,
            "sum": self.root.ids.summ.text,
            "date": self.root.ids.date.text
        }
        
        try:
            r = requests.post(url, json=payload, timeout=20)
            res = r.json()
            if res['status'] == 'OK':
                self.root.ids.status.text = f"Успех! Сумма: {res['sum']} руб."
            else:
                self.root.ids.status.text = f"Ошибка: {res['message']}"
        except Exception as e:
            self.root.ids.status.text = "Нет связи с сайтом"

    def show_history(self):
        # Здесь можно добавить запрос к БД сайта для вывода списка
        pass

if __name__ == '__main__':
    MobileKKT().run()
