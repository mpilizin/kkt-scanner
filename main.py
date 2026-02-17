import os
import json
import requests
from datetime import datetime
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import TwoLineListItem, OneLineListItem
from kivy.storage.jsonstore import JsonStore
from kivy.properties import StringProperty

# --- НАСТРОЙКИ ---
# Сюда вставь адрес своего скрипта на сервере
API_URL = "https://твоя-ссылка.ru/api/check" 

KV = '''
ScreenManager:
    ConsentScreen:
    HomeScreen:
    ResultScreen:

# --- ЭКРАН 1: СОГЛАСИЕ (Появляется только 1 раз) ---
<ConsentScreen>:
    name: 'consent'
    MDBoxLayout:
        orientation: 'vertical'
        padding: "20dp"
        spacing: "20dp"

        MDLabel:
            text: "Согласие на обработку данных"
            halign: "center"
            font_style: "H5"
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "Для использования приложения необходимо разрешить отправку данных ФН (Фискальный Накопитель) и ФД (Фискальный Документ) на сервер для проверки чеков в ФНС."
            halign: "center"
            theme_text_color: "Secondary"

        MDBoxLayout:
            orientation: 'vertical'
            spacing: "10dp"
            adaptive_height: True

            MDRaisedButton:
                text: "Я ПРИНИМАЮ УСЛОВИЯ"
                size_hint_x: 1
                md_bg_color: 0, 0.6, 0, 1
                on_release: root.accept_terms()

# --- ЭКРАН 2: ГЛАВНЫЙ (Ввод данных) ---
<HomeScreen>:
    name: 'home'
    
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "Сканер Чеков"
            elevation: 2

        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                padding: "20dp"
                spacing: "25dp"  # Большой отступ, чтобы не наезжало

                # Поля ввода (Старый строгий стиль)
                MDTextField:
                    id: sum_field
                    hint_text: "Сумма чека (например: 1142.00)"
                    helper_text: "В рублях и копейках"
                    input_filter: 'float'
                    mode: "fill"

                MDTextField:
                    id: fn_field
                    hint_text: "ФН (Номер накопителя)"
                    input_filter: 'int'
                    mode: "fill"

                MDTextField:
                    id: fd_field
                    hint_text: "ФД (Номер документа)"
                    input_filter: 'int'
                    mode: "fill"

                MDTextField:
                    id: fp_field
                    hint_text: "ФП (Фискальный признак)"
                    input_filter: 'int'
                    mode: "fill"

                # Блок Даты и Времени
                MDBoxLayout:
                    orientation: 'horizontal'
                    spacing: "10dp"
                    adaptive_height: True

                    MDRaisedButton:
                        id: date_btn
                        text: "ДАТА"
                        size_hint_x: 0.5
                        on_release: root.show_date_picker()

                    MDRaisedButton:
                        id: time_btn
                        text: "ВРЕМЯ (24ч)"
                        size_hint_x: 0.5
                        on_release: root.show_time_picker()

                MDLabel:
                    id: date_label
                    text: "Не выбрано"
                    halign: "center"
                    theme_text_color: "Hint"

                # Кнопка проверки
                MDRaisedButton:
                    text: "ПРОВЕРИТЬ ЧЕК"
                    size_hint_x: 1
                    height: "50dp"
                    md_bg_color: 0.2, 0.4, 0.8, 1
                    on_release: root.check_receipt()

                # История (снизу, чтобы не мешала)
                MDFlatButton:
                    text: "История запросов"
                    pos_hint: {"center_x": .5}
                    on_release: pass 

# --- ЭКРАН 3: РЕЗУЛЬТАТ (Полная детализация) ---
<ResultScreen>:
    name: 'result'
    
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "Детали Чека"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]

        ScrollView:
            MDBoxLayout:
                id: result_box
                orientation: 'vertical'
                adaptive_height: True
                padding: "15dp"
                spacing: "10dp"
'''

class ConsentScreen(Screen):
    def accept_terms(self):
        # Запоминаем, что пользователь согласился
        app = MDApp.get_running_app()
        app.store.put('user_settings', agreed=True)
        app.root.current = 'home'

class HomeScreen(Screen):
    date_val = ""
    time_val = ""

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        self.date_val = value.strftime("%Y-%m-%d")
        self.update_label()

    def show_time_picker(self):
        # Пытаемся открыть часы. В KivyMD это стандартный виджет.
        time_dialog = MDTimePicker()
        time_dialog.bind(on_save=self.on_time_save)
        time_dialog.open()

    def on_time_save(self, instance, time):
        self.time_val = time.strftime("%H:%M")
        self.update_label()

    def update_label(self):
        d = self.date_val if self.date_val else "--.--.----"
        t = self.time_val if self.time_val else "--:--"
        self.ids.date_label.text = f"Дата: {d} | Время: {t}"

    def check_receipt(self):
        # 1. Собираем данные
        sum_text = self.ids.sum_field.text.replace(',', '.')
        fn = self.ids.fn_field.text
        fd = self.ids.fd_field.text
        fp = self.ids.fp_field.text

        if not (sum_text and fn and fd and fp):
            self.show_alert("Ошибка", "Заполните все поля!")
            return

        # 2. Формируем запрос
        payload = {
            "fn": fn,
            "fd": fd,
            "fp": fp,
            "sum": int(float(sum_text) * 100), # Переводим рубли в копейки
            "date": self.date_val,
            "time": self.time_val
        }

        # 3. Отправляем (Или имитируем для теста, если сервер недоступен)
        try:
            # response = requests.post(API_URL, json=payload, timeout=10)
            # data = response.json()
            
            # --- ВРЕМЕННАЯ ЗАГЛУШКА (Твой JSON для примера) ---
            # Когда настроишь сервер, удали блок ниже и раскомментируй requests
            json_str = """
            {"code":3,"user":"БАЙКОВА ИРИНА ВИКТОРОВНА","items":[{"nds":6,"sum":113700,"name":"кондитерские изделия","price":113700,"ndsSum":113700,"quantity":1.0,"paymentType":4,"productType":1,"itemsQuantityMeasure":0},{"nds":6,"sum":500,"name":"сопутствуюшие товары","price":500,"ndsSum":500,"quantity":1.0,"paymentType":4,"productType":1,"itemsQuantityMeasure":0}],"ndsNo":114200,"region":"77","userInn":"504408878360","dateTime":1771350360,"retailPlaceAddress":"124536 Москва.Зеленоград, МЖК, корп. 522, магазин продукты","totalSum":114200}
            """
            data = json.loads(json_str)
            # --------------------------------------------------

            # Переходим на экран результата и передаем данные
            self.manager.get_screen('result').display_data(data)
            self.manager.current = 'result'

        except Exception as e:
            self.show_alert("Ошибка соединения", str(e))

    def show_alert(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.parent.parent.dismiss())]).open()

class ResultScreen(Screen):
    def go_back(self):
        self.manager.current = 'home'

    def display_data(self, data):
        box = self.ids.result_box
        box.clear_widgets() # Очистить старое

        # 1. Заголовок (Магазин)
        shop_name = data.get('user', 'Неизвестный магазин')
        address = data.get('retailPlaceAddress', '')
        
        box.add_widget(OneLineListItem(text=f"{shop_name}", font_style="H6"))
        box.add_widget(TwoLineListItem(text="Адрес:", secondary_text=address))

        # 2. Список товаров (Самое важное!)
        if 'items' in data:
            box.add_widget(OneLineListItem(text="--- ТОВАРЫ ---", theme_text_color="Hint"))
            for item in data['items']:
                name = item.get('name', 'Товар')
                # Цена приходит в копейках (113700 -> 1137.00)
                price = item.get('price', 0) / 100
                qty = item.get('quantity', 1)
                final_sum = item.get('sum', 0) / 100
                
                # Добавляем в список
                item_widget = TwoLineListItem(
                    text=f"{name}",
                    secondary_text=f"{qty} шт. x {price} = {final_sum} руб."
                )
                box.add_widget(item_widget)

        # 3. Итог
        total = data.get('totalSum', 0) / 100
        box.add_widget(OneLineListItem(text="--- ИТОГО ---", theme_text_color="Hint"))
        box.add_widget(OneLineListItem(text=f"СУММА: {total} руб.", bg_color=(0.9, 0.9, 0.9, 1)))

class CheckApp(MDApp):
    store = None

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        # Создаем хранилище для настроек
        data_dir = self.user_data_dir
        self.store = JsonStore(os.path.join(data_dir, "settings.json"))
        return Builder.load_string(KV)

    def on_start(self):
        # Проверяем, согласился ли пользователь ранее
        if self.store.exists('user_settings') and self.store.get('user_settings')['agreed']:
            self.root.current = 'home'
        else:
            self.root.current = 'consent'

if __name__ == '__main__':
    CheckApp().run()
