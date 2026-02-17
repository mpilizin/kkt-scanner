import os
import json
import requests
from datetime import datetime
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import TwoLineListItem
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.clock import Clock

# --- ИМПОРТ НАТИВНОГО СКАНЕРА (ТОЛЬКО ДЛЯ ANDROID) ---
if platform == 'android':
    from jnius import autoclass, cast
    from android import activity
    from android.permissions import request_permissions, Permission
    
    # Классы Android
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')

# --- НАСТРОЙКИ ---
API_URL = "https://proverkacheka.nalog.ru/api/v1/inns/*/kkts/*/fss/*/tickets/*"

KV = '''
ScreenManager:
    ConsentScreen:
    HomeScreen:
    ResultScreen:
    HistoryScreen:

# --- 1. ЭКРАН СОГЛАСИЯ ---
<ConsentScreen>:
    name: 'consent'
    MDBoxLayout:
        orientation: 'vertical'
        padding: "30dp"
        spacing: "20dp"

        MDIcon:
            icon: "security"
            halign: "center"
            font_size: "80sp"
            theme_text_color: "Custom"
            text_color: 0.2, 0.4, 0.8, 1

        MDLabel:
            text: "Правовая информация"
            halign: "center"
            font_style: "H5"
            bold: True

        MDLabel:
            text: "Для работы приложения требуется доступ к камере (для сканирования QR) и интернету. Нажимая кнопку, вы соглашаетесь с условиями."
            halign: "center"
            theme_text_color: "Secondary"

        MDRaisedButton:
            text: "ПРИНЯТЬ И НАЧАТЬ"
            size_hint_x: 1
            height: "50dp"
            md_bg_color: 0, 0.6, 0, 1
            on_release: root.accept_terms()

# --- 2. ГЛАВНЫЙ ЭКРАН ---
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
                spacing: "20dp"

                # КНОПКА СКАНЕРА
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: "140dp"
                    radius: [15]
                    padding: "15dp"
                    md_bg_color: 0.9, 0.95, 1, 1
                    elevation: 2
                    on_release: root.start_native_scan()
                    ripple_behavior: True

                    MDIcon:
                        icon: "qrcode-scan"
                        halign: "center"
                        font_size: "50sp"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.4, 0.8, 1
                    
                    MDLabel:
                        text: "СКАНИРОВАТЬ QR-КОД"
                        halign: "center"
                        bold: True
                        font_style: "Subtitle1"

                MDLabel:
                    text: "— или введите вручную —"
                    halign: "center"
                    theme_text_color: "Hint"

                MDTextField:
                    id: sum_field
                    hint_text: "Сумма (1200.00)"
                    input_filter: 'float'
                    mode: "fill"

                MDTextField:
                    id: fn_field
                    hint_text: "ФН (Накопитель)"
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
                        on_release: root.show_date_picker()

                    MDRaisedButton:
                        id: time_btn
                        text: "ВРЕМЯ"
                        size_hint_x: 0.5
                        on_release: root.show_time_picker()

                MDRaisedButton:
                    text: "ПРОВЕРИТЬ ЧЕК"
                    size_hint_x: 1
                    height: "50dp"
                    on_release: root.check_receipt()

# --- 3. РЕЗУЛЬТАТ ---
<ResultScreen>:
    name: 'result'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.9, 0.9, 0.9, 1

        MDTopAppBar:
            title: "Чек"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]

        ScrollView:
            padding: "20dp"
            
            MDCard:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: "15dp"
                radius: [0]
                md_bg_color: 1, 1, 1, 1
                elevation: 3
                size_hint_x: 0.95
                pos_hint: {"center_x": .5}

                MDLabel:
                    id: shop_label
                    text: "МАГАЗИН"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    adaptive_height: True

                MDLabel:
                    id: address_label
                    text: "Адрес..."
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Caption"
                    adaptive_height: True
                    padding_y: "10dp"

                MDSeparator:
                    height: "2dp"

                MDBoxLayout:
                    id: items_box
                    orientation: 'vertical'
                    adaptive_height: True
                    padding: [0, 10, 0, 10]
                    spacing: "10dp"

                MDSeparator:
                    height: "2dp"

                MDBoxLayout:
                    adaptive_height: True
                    padding: [0, 10, 0, 0]
                    MDLabel:
                        text: "ИТОГ:"
                        bold: True
                        font_style: "H6"
                    MDLabel:
                        id: total_label
                        text: "0.00"
                        halign: "right"
                        bold: True
                        font_style: "H6"

                MDLabel:
                    id: payment_type_label
                    text: "Оплата: -"
                    halign: "right"
                    font_style: "Caption"
                    adaptive_height: True

# --- 4. ИСТОРИЯ ---
<HistoryScreen>:
    name: 'history'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "История запросов"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]

        ScrollView:
            MDList:
                id: history_list
'''

class ConsentScreen(Screen):
    def accept_terms(self):
        MDApp.get_running_app().store.put('user_settings', agreed=True)
        # Запрашиваем разрешения при старте
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.INTERNET])
        MDApp.get_running_app().root.current = 'home'

class HomeScreen(Screen):
    date_val = ""
    time_val = ""

    def show_date_picker(self):
        picker = MDDatePicker()
        picker.bind(on_save=self.on_date_save)
        picker.open()

    def on_date_save(self, instance, value, date_range):
        self.date_val = value.strftime("%Y-%m-%d")
        self.ids.date_btn.text = self.date_val

    def show_time_picker(self):
        picker = MDTimePicker()
        picker.bind(on_save=self.on_time_save)
        picker.open()

    def on_time_save(self, instance, time):
        self.time_val = time.strftime("%H:%M")
        self.ids.time_btn.text = self.time_val

    def open_history(self):
        self.manager.get_screen('history').load_history()
        self.manager.current = 'history'

    def start_native_scan(self):
        if platform == 'android':
            # Запускаем нативный сканер ZXing
            integrator = IntentIntegrator(PythonActivity.mActivity)
            integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
            integrator.setPrompt("Наведите камеру на QR-код чека")
            integrator.setCameraId(0)
            integrator.setBeepEnabled(False)
            integrator.setBarcodeImageEnabled(False)
            integrator.initiateScan()
        else:
            print("Сканер работает только на Android!")
            # Для теста на ПК заполним данными
            self.fill_from_qr("t=20230615T1200&s=500.00&fn=123456789&i=123&fp=987654321&n=1")

    def fill_from_qr(self, qr_text):
        try:
            params = dict(x.split('=') for x in qr_text.split('&') if '=' in x)
            if 's' in params: self.ids.sum_field.text = params['s']
            if 'fn' in params: self.ids.fn_field.text = params['fn']
            if 'i' in params: self.ids.fd_field.text = params['i']
            if 'fp' in params: self.ids.fp_field.text = params['fp']
            
            # Парсим дату t=20230615T1200
            if 't' in params:
                raw_date = params['t']
                # Простейшая обработка
                if len(raw_date) >= 8:
                    d = raw_date[:8] # 20230615
                    self.date_val = f"{d[:4]}-{d[4:6]}-{d[6:]}"
                    self.ids.date_btn.text = self.date_val
                if 'T' in raw_date:
                    t = raw_date.split('T')[1]
                    if len(t) >= 4:
                        self.time_val = f"{t[:2]}:{t[2:4]}"
                        self.ids.time_btn.text = self.time_val
            
            # Сразу запускаем проверку
            self.check_receipt()
            
        except Exception as e:
            print(f"Ошибка парсинга QR: {e}")

    def check_receipt(self):
        sum_text = self.ids.sum_field.text.replace(',', '.')
        fn = self.ids.fn_field.text
        fd = self.ids.fd_field.text
        fp = self.ids.fp_field.text

        if not (sum_text and fn and fd and fp):
            return 

        req_data = {"fn": fn, "fd": fd, "fp": fp, "sum": sum_text, "date": self.date_val, "time": self.time_val}

        try:
            # ТЕСТОВЫЙ ОТВЕТ (ЗАГЛУШКА)
            json_str = """
            {"code":3,"user":"ПАО 'СБЕРМАРКЕТ'","items":[{"nds":20,"sum":15000,"name":"Доставка продуктов","price":15000,"quantity":1.0},{"nds":10,"sum":85000,"name":"Молоко 3.2%","price":85000,"quantity":1.0}],"retailPlaceAddress":"г. Москва, ул. Вавилова 19","totalSum":100000,"ecashTotalSum":100000,"cashTotalSum":0}
            """
            result_data = json.loads(json_str)
            MDApp.get_running_app().add_history(req_data, result_data)
            self.manager.get_screen('result').render_receipt(result_data)
            self.manager.current = 'result'
        except Exception as e:
            print(e)

class ResultScreen(Screen):
    def go_home(self):
        self.manager.current = 'home'

    def render_receipt(self, data):
        self.ids.shop_label.text = data.get('user', 'Магазин')
        self.ids.address_label.text = data.get('retailPlaceAddress', '')
        box = self.ids.items_box
        box.clear_widgets()
        for item in data.get('items', []):
            name = item.get('name', 'Товар')
            price = item.get('price', 0) / 100
            qty = item.get('quantity', 1)
            total = item.get('sum', 0) / 100
            
            box.add_widget(MDLabel(text=name, adaptive_height=True, theme_text_color="Primary"))
            row = MDBoxLayout(adaptive_height=True)
            row.add_widget(MDLabel(text=f"{qty} x {price:.2f}", theme_text_color="Secondary", font_style="Caption"))
            row.add_widget(MDLabel(text=f"={total:.2f}", halign="right", bold=True))
            box.add_widget(row)
            box.add_widget(MDLabel(text="- "*20, theme_text_color="Hint", font_style="Caption", halign="center"))

        total_sum = data.get('totalSum', 0) / 100
        self.ids.total_label.text = f"{total_sum:.2f} ₽"
        pay = "Наличными"
        if data.get('ecashTotalSum', 0) > 0: pay = "Карта / Безнал"
        self.ids.payment_type_label.text = f"Оплата: {pay}"

class HistoryScreen(Screen):
    def go_home(self):
        self.manager.current = 'home'

    def load_history(self):
        lst = self.ids.history_list
        lst.clear_widgets()
        store = MDApp.get_running_app().store
        for key in sorted(store.keys(), reverse=True):
            entry = store.get(key)
            req, res = entry['request'], entry['result']
            item = TwoLineListItem(
                text=f"{res.get('user', 'Магазин')} ({req['sum']}р)",
                secondary_text=f"{req['date']}",
                on_release=lambda x, r=res: self.show_details(r)
            )
            lst.add_widget(item)

    def show_details(self, res):
        app = MDApp.get_running_app()
        app.root.get_screen('result').render_receipt(res)
        app.root.current = 'result'

class CheckApp(MDApp):
    store = None

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        self.store = JsonStore(os.path.join(self.user_data_dir, "history.json"))
        # Привязываем обработчик результата сканирования (только для Android)
        if platform == 'android':
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)
        return Builder.load_string(KV)

    def on_start(self):
        if self.store.exists('user_settings') and self.store.get('user_settings')['agreed']:
            self.root.current = 'home'
        else:
            self.root.current = 'consent'

    def add_history(self, req, res):
        key = datetime.now().strftime("%Y%m%d%H%M%S")
        self.store.put(key, request=req, result=res)

    # ОБРАБОТКА РЕЗУЛЬТАТА ОТ SCANNER-А (ANDROID)
    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 49374: # Код ZXing
            from jnius import autoclass
            IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')
            result = IntentIntegrator.parseActivityResult(request_code, result_code, intent)
            if result:
                contents = result.getContents()
                if contents:
                    # Успех! Передаем строку QR кода в обработчик
                    Clock.schedule_once(lambda dt: self.root.get_screen('home').fill_from_qr(contents), 0)

if __name__ == '__main__':
    CheckApp().run()
