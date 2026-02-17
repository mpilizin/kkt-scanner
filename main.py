import os
import json
from datetime import datetime
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.list import TwoLineListItem
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.clock import Clock
from kivy.properties import StringProperty

# --- НАТИВНЫЙ СКАНЕР (ANDROID) ---
if platform == 'android':
    from jnius import autoclass
    from android import activity
    from android.permissions import request_permissions, Permission
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')

KV = '''
ScreenManager:
    HomeScreen:
    ResultScreen:
    HistoryScreen:

# --- 1. ГЛАВНЫЙ ЭКРАН ---
<HomeScreen>:
    name: 'home'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "Проверка Чеков"
            right_action_items: [["history", lambda x: root.open_history()]]
            elevation: 2

        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                padding: "20dp"
                spacing: "15dp"

                # КНОПКА СКАНЕРА
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: "120dp"
                    radius: [12]
                    padding: "10dp"
                    md_bg_color: 0.92, 0.95, 1, 1
                    elevation: 1
                    on_release: root.start_native_scan()
                    ripple_behavior: True

                    MDIcon:
                        icon: "qrcode-scan"
                        halign: "center"
                        font_size: "48sp"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.4, 0.8, 1
                    
                    MDLabel:
                        text: "СКАНИРОВАТЬ QR"
                        halign: "center"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.4, 0.8, 1

                MDLabel:
                    text: "Данные чека:"
                    font_style: "Subtitle2"
                    theme_text_color: "Secondary"

                MDTextField:
                    id: sum_field
                    hint_text: "Сумма (Руб.Коп)"
                    helper_text: "Пример: 45.00"
                    input_filter: 'float'
                    mode: "fill"

                MDTextField:
                    id: fn_field
                    hint_text: "ФН (Фискальный Накопитель)"
                    input_filter: 'int'
                    mode: "fill"

                MDTextField:
                    id: fd_field
                    hint_text: "ФД (Документ)"
                    input_filter: 'int'
                    mode: "fill"

                MDTextField:
                    id: fp_field
                    hint_text: "ФП (Признак)"
                    input_filter: 'int'
                    mode: "fill"

                MDBoxLayout:
                    spacing: "10dp"
                    adaptive_height: True

                    MDRaisedButton:
                        id: date_btn
                        text: "ДАТА"
                        size_hint_x: 0.5
                        md_bg_color: 0.5, 0.5, 0.5, 1
                        on_release: root.show_date_picker()

                    MDRaisedButton:
                        id: time_btn
                        text: "ВРЕМЯ"
                        size_hint_x: 0.5
                        md_bg_color: 0.5, 0.5, 0.5, 1
                        on_release: root.show_time_picker()

                MDRaisedButton:
                    text: "ПОКАЗАТЬ ЧЕК"
                    size_hint_x: 1
                    height: "50dp"
                    font_size: "18sp"
                    md_bg_color: 0, 0.6, 0, 1
                    on_release: root.process_check()

# --- 2. ЭКРАН РЕЗУЛЬТАТА (ЧЕК КАК В PDF) ---
<ResultScreen>:
    name: 'result'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.85, 0.85, 0.85, 1

        MDTopAppBar:
            title: "Электронный чек"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]

        ScrollView:
            padding: "15dp"
            
            # БЕЛАЯ БУМАГА ЧЕКА
            MDCard:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height  # Резиновая высота!
                padding: "20dp"
                radius: [0]
                md_bg_color: 1, 1, 1, 1
                elevation: 4
                pos_hint: {"center_x": .5}

                # ШАПКА
                MDLabel:
                    id: shop_label
                    text: "МАГАЗИН ПРОДУКТЫ"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    adaptive_height: True

                MDLabel:
                    id: address_label
                    text: "Загрузка адреса..."
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Caption"
                    adaptive_height: True
                    # Важно для переноса текста:
                    text_size: self.width, None 
                    padding_y: "5dp"

                MDSeparator:
                    height: "2dp"
                    color: 0, 0, 0, 1

                # ТЕЛО ЧЕКА (ДАТА И СУММА)
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_height: True
                    padding: [0, 15, 0, 15]
                    spacing: "10dp"

                    # Дата смены
                    MDBoxLayout:
                        adaptive_height: True
                        MDLabel:
                            text: "СМЕНА / ЧЕК:"
                            font_style: "Caption"
                        MDLabel:
                            id: shift_info
                            text: "№ 53 / 110"
                            halign: "right"
                            font_style: "Caption"

                    # Дата Время
                    MDBoxLayout:
                        adaptive_height: True
                        MDLabel:
                            text: "ДАТА ВРЕМЯ:"
                            font_style: "Caption"
                        MDLabel:
                            id: datetime_label
                            text: "17.02.2026 19:39"
                            halign: "right"
                            font_style: "Caption"
                            bold: True

                    MDSeparator:
                        height: "1dp"

                    # СТРОКА ИТОГА (КРУПНО)
                    MDBoxLayout:
                        adaptive_height: True
                        padding: [0, 10, 0, 0]
                        MDLabel:
                            text: "ИТОГ:"
                            bold: True
                            font_style: "H5"
                        MDLabel:
                            id: total_label
                            text: "= 45.00"
                            halign: "right"
                            bold: True
                            font_style: "H5"

                MDSeparator:
                    height: "2dp"
                    color: 0, 0, 0, 1

                # ПОДВАЛ (ФИСКАЛЬНЫЕ ДАННЫЕ)
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_height: True
                    padding: [0, 15, 0, 0]
                    spacing: "5dp"

                    MDLabel:
                        text: "ФИСКАЛЬНЫЕ ДАННЫЕ:"
                        halign: "center"
                        font_style: "Overline"
                        bold: True
                        adaptive_height: True

                    MDLabel:
                        id: fn_label
                        text: "ФН: 0000000000"
                        halign: "center"
                        font_style: "Code"
                        adaptive_height: True

                    MDLabel:
                        id: fd_label
                        text: "ФД: 0000"
                        halign: "center"
                        font_style: "Code"
                        adaptive_height: True

                    MDLabel:
                        id: fp_label
                        text: "ФП: 00000000"
                        halign: "center"
                        font_style: "Code"
                        adaptive_height: True

                MDIcon:
                    icon: "check-decagram"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0, 0, 0, 0.2
                    font_size: "40sp"
                    padding_y: "20dp"

# --- 3. ИСТОРИЯ ---
<HistoryScreen>:
    name: 'history'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "Архив чеков"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]

        ScrollView:
            MDList:
                id: history_list
'''

class HomeScreen(Screen):
    date_val = ""
    time_val = ""

    def show_date_picker(self):
        MDDatePicker().bind(on_save=self.on_date_save).open()

    def on_date_save(self, instance, value, date_range):
        self.date_val = value.strftime("%Y-%m-%d")
        self.ids.date_btn.text = self.date_val

    def show_time_picker(self):
        MDTimePicker().bind(on_save=self.on_time_save).open()

    def on_time_save(self, instance, time):
        self.time_val = time.strftime("%H:%M")
        self.ids.time_btn.text = self.time_val

    def open_history(self):
        self.manager.get_screen('history').load_history()
        self.manager.current = 'history'

    def start_native_scan(self):
        if platform == 'android':
            request_permissions([Permission.CAMERA])
            integrator = IntentIntegrator(PythonActivity.mActivity)
            integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
            integrator.setPrompt("Наведите на QR-код чека")
            integrator.setCameraId(0)
            integrator.setBeepEnabled(True)
            integrator.initiateScan()
        else:
            # ТЕСТ ДЛЯ КОМПЬЮТЕРА (эмуляция успешного скана)
            self.fill_from_qr("t=20260217T1939&s=45.00&fn=7380440902759728&i=5716&fp=61025839&n=1")

    def fill_from_qr(self, qr_text):
        try:
            # Разбираем строку: t=...&s=...
            params = dict(x.split('=') for x in qr_text.split('&') if '=' in x)
            
            if 's' in params: self.ids.sum_field.text = params['s']
            if 'fn' in params: self.ids.fn_field.text = params['fn']
            if 'i' in params: self.ids.fd_field.text = params['i']
            if 'fp' in params: self.ids.fp_field.text = params['fp']
            
            # Дата: 20260217T1939 -> 2026-02-17 19:39
            if 't' in params:
                raw = params['t'] # 20260217T1939
                if len(raw) >= 13:
                    self.date_val = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                    self.time_val = f"{raw[9:11]}:{raw[11:13]}"
                    self.ids.date_btn.text = self.date_val
                    self.ids.time_btn.text = self.time_val
            
            # Автоматически показываем чек
            self.process_check()
            
        except Exception as e:
            print(f"Ошибка QR: {e}")

    def process_check(self):
        # 1. Собираем данные с полей
        s = self.ids.sum_field.text
        fn = self.ids.fn_field.text
        fd = self.ids.fd_field.text
        fp = self.ids.fp_field.text
        
        if not (s and fn and fd and fp): return

        # 2. Создаем структуру чека (КАК В PDF)
        receipt_data = {
            "shop": "МАГАЗИН ПРОДУКТЫ", # Пока нет API, пишем заглушку
            "address": "Москва, Зеленоград, корп. 522", # Пример из твоего файла
            "total": s,
            "date": self.date_val,
            "time": self.time_val,
            "fn": fn,
            "fd": fd,
            "fp": fp
        }

        # 3. Сохраняем и показываем
        MDApp.get_running_app().add_history(receipt_data)
        self.manager.get_screen('result').render(receipt_data)
        self.manager.current = 'result'

class ResultScreen(Screen):
    def go_home(self):
        self.manager.current = 'home'

    def render(self, data):
        # Заполняем чек данными
        self.ids.shop_label.text = data.get('shop', 'Магазин')
        self.ids.address_label.text = data.get('address', '')
        self.ids.datetime_label.text = f"{data['date']} {data['time']}"
        self.ids.total_label.text = f"= {data['total']} руб"
        
        # Фискальные данные (Самое важное для проверки)
        self.ids.fn_label.text = f"ФН: {data['fn']}"
        self.ids.fd_label.text = f"ФД: {data['fd']}"
        self.ids.fp_label.text = f"ФП: {data['fp']}"

class HistoryScreen(Screen):
    def go_home(self):
        self.manager.current = 'home'

    def load_history(self):
        self.ids.history_list.clear_widgets()
        store = MDApp.get_running_app().store
        
        # Сортировка: новые сверху
        for key in sorted(store.keys(), reverse=True):
            item_data = store.get(key)
            
            # ВАЖНО: Мы создаем свой класс для кнопки, чтобы сохранить КЛЮЧ
            list_item = TwoLineListItem(
                text=f"Сумма: {item_data['total']} руб",
                secondary_text=f"{item_data['date']} {item_data['time']}",
                on_release=lambda x, k=key: self.open_receipt_by_key(k) # Передаем КЛЮЧ, а не объект
            )
            self.ids.history_list.add_widget(list_item)

    def open_receipt_by_key(self, key):
        # Безопасная загрузка по ключу
        store = MDApp.get_running_app().store
        if store.exists(key):
            data = store.get(key)
            app = MDApp.get_running_app()
            app.root.get_screen('result').render(data)
            app.root.current = 'result'

class CheckApp(MDApp):
    store = None

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        # База данных истории
        self.store = JsonStore(os.path.join(self.user_data_dir, "history_v4.json"))
        
        if platform == 'android':
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)
            
        return Builder.load_string(KV)

    def add_history(self, data):
        # Ключ = дата+время+случайное число (для уникальности)
        key = datetime.now().strftime("%Y%m%d%H%M%S")
        self.store.put(key, **data) # Сохраняем как словарь

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 49374: # ZXing
            from jnius import autoclass
            IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')
            result = IntentIntegrator.parseActivityResult(request_code, result_code, intent)
            if result:
                contents = result.getContents()
                if contents:
                    Clock.schedule_once(lambda dt: self.root.get_screen('home').fill_from_qr(contents), 0)

if __name__ == '__main__':
    CheckApp().run()
