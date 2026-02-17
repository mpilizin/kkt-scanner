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
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import TwoLineListItem, IconLeftWidget
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivy.graphics.texture import Texture
from kivy.utils import platform

# Попытка импорта сканера (чтобы не вылетало на Windows при тестах)
try:
    from pyzbar.pyzbar import decode
    from PIL import Image as PilImage
except ImportError:
    decode = None

# --- НАСТРОЙКИ ---
API_URL = "https://proverkacheka.nalog.ru/api/v1/inns/*/kkts/*/fss/*/tickets/*"

KV = '''
ScreenManager:
    ConsentScreen:
    HomeScreen:
    ScannerScreen:
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
            text: "Приложение отправляет данные чека в ФНС для проверки подлинности. Нажимая кнопку, вы соглашаетесь с условиями."
            halign: "center"
            theme_text_color: "Secondary"

        MDRaisedButton:
            text: "ПРИНЯТЬ И ПРОДОЛЖИТЬ"
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
                    on_release: root.open_scanner()
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
                        md_bg_color: 0.5, 0.5, 0.5, 1
                        on_release: root.show_date_picker()

                    MDRaisedButton:
                        id: time_btn
                        text: "ВРЕМЯ"
                        size_hint_x: 0.5
                        md_bg_color: 0.5, 0.5, 0.5, 1
                        on_release: root.show_time_picker()

                MDRaisedButton:
                    text: "ПРОВЕРИТЬ ЧЕК"
                    size_hint_x: 1
                    height: "50dp"
                    font_size: "18sp"
                    on_release: root.check_receipt()

# --- 3. СКАНЕР ---
<ScannerScreen>:
    name: 'scanner'
    FloatLayout:
        Camera:
            id: camera
            resolution: (640, 480)
            play: False
            keep_ratio: False
            allow_stretch: True

        MDLabel:
            text: "[   ]"
            halign: "center"
            font_size: "300sp"
            color: 0, 1, 0, 0.3
            pos_hint: {'center_x': .5, 'center_y': .5}

        MDRaisedButton:
            text: "ОТМЕНА"
            pos_hint: {'center_x': .5, 'y': 0.05}
            md_bg_color: 1, 0, 0, 1
            on_release: root.stop_scan()

# --- 4. РЕЗУЛЬТАТ (ДИЗАЙН БУМАЖНОГО ЧЕКА) ---
<ResultScreen>:
    name: 'result'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.9, 0.9, 0.9, 1  # Серый фон вокруг чека

        MDTopAppBar:
            title: "Чек"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]

        ScrollView:
            padding: "20dp"
            
            # БЕЛАЯ БУМАЖКА ЧЕКА
            MDCard:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: "15dp"
                radius: [0]
                md_bg_color: 1, 1, 1, 1
                elevation: 3
                pos_hint: {"center_x": .5}
                size_hint_x: 0.95

                # ЗАГОЛОВОК ЧЕКА
                MDLabel:
                    id: shop_label
                    text: "МАГАЗИН"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    adaptive_height: True

                MDLabel:
                    id: address_label
                    text: "Адрес магазина"
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Caption"
                    adaptive_height: True
                    padding_y: "10dp"

                MDSeparator:
                    height: "2dp"

                # СПИСОК ТОВАРОВ (Заполняется кодом)
                MDBoxLayout:
                    id: items_box
                    orientation: 'vertical'
                    adaptive_height: True
                    padding: [0, 10, 0, 10]
                    spacing: "10dp"

                MDSeparator:
                    height: "2dp"

                # ИТОГИ
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

                MDLabel:
                    text: "*** ККТ ОНЛАЙН ***"
                    halign: "center"
                    theme_text_color: "Hint"
                    font_style: "Overline"
                    padding_y: "20dp"
                    adaptive_height: True

# --- 5. ИСТОРИЯ ---
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
        app = MDApp.get_running_app()
        app.store.put('user_settings', agreed=True)
        app.root.current = 'home'

class HomeScreen(Screen):
    date_val = ""
    time_val = ""

    def show_date_picker(self):
        MDDatePicker(min_year=2020, max_year=2030).open()
        # Привязка через bind происходит внутри MDDatePicker, 
        # но в старых версиях лучше переопределить on_save
        picker = MDDatePicker()
        picker.bind(on_save=self.on_date_save)
        picker.open()

    def on_date_save(self, instance, value, date_range):
        self.date_val = value.strftime("%Y-%m-%d")
        self.ids.date_btn.text = self.date_val

    def show_time_picker(self):
        # Принудительно ставим время, но формат зависит от настроек телефона
        # Мы просто правильно отформатируем результат
        picker = MDTimePicker()
        picker.bind(on_save=self.on_time_save)
        picker.open()

    def on_time_save(self, instance, time):
        self.time_val = time.strftime("%H:%M") # Всегда 24 часа
        self.ids.time_btn.text = self.time_val

    def open_scanner(self):
        self.manager.current = 'scanner'
        self.manager.get_screen('scanner').start_scan()

    def open_history(self):
        # Загружаем историю перед показом
        self.manager.get_screen('history').load_history()
        self.manager.current = 'history'

    def check_receipt(self):
        sum_text = self.ids.sum_field.text.replace(',', '.')
        fn = self.ids.fn_field.text
        fd = self.ids.fd_field.text
        fp = self.ids.fp_field.text

        if not (sum_text and fn and fd and fp):
            return 

        # Данные запроса
        request_data = {
            "fn": fn, "fd": fd, "fp": fp, "sum": sum_text, 
            "date": self.date_val, "time": self.time_val
        }

        try:
            # ТЕСТОВЫЙ JSON (Имитация ответа ФНС)
            json_str = """
            {"code":3,"user":"ООО 'ВКУСНЫЕ ПРОДУКТЫ'","items":[{"nds":6,"sum":113700,"name":"Хлеб Бородинский нарезанный в упаковке 400г","price":113700,"quantity":1.0,"paymentType":4},{"nds":6,"sum":500,"name":"Пакет майка","price":500,"quantity":1.0,"paymentType":1}],"retailPlaceAddress":"г. Москва, ул. Ленина, д. 10","totalSum":114200,"ecashTotalSum":114200,"cashTotalSum":0}
            """
            result_data = json.loads(json_str)

            # Сохраняем в историю
            MDApp.get_running_app().add_history(request_data, result_data)

            # Показываем чек
            self.manager.get_screen('result').render_receipt(result_data)
            self.manager.current = 'result'

        except Exception as e:
            print(e)

class ScannerScreen(Screen):
    def start_scan(self):
        self.ids.camera.play = True
        # Запускаем проверку QR кода 2 раза в секунду
        Clock.schedule_interval(self.detect_qr, 0.5)

    def stop_scan(self):
        self.ids.camera.play = False
        Clock.unschedule(self.detect_qr)
        self.manager.current = 'home'

    def detect_qr(self, dt):
        if not decode: return # Если библиотека не загрузилась

        # Получаем картинку с камеры
        texture = self.ids.camera.texture
        if not texture: return
        
        # Конвертируем в формат для сканера
        pil_image = PilImage.frombytes(mode='RGBA', size=texture.size, data=texture.pixels)
        
        # Ищем коды
        barcodes = decode(pil_image)
        for barcode in barcodes:
            qr_text = barcode.data.decode('utf-8')
            # Если нашли QR с чека (там всегда есть t=...)
            if "t=" in qr_text and "s=" in qr_text:
                self.stop_scan()
                # Заполняем поля на главном экране
                self.manager.get_screen('home').fill_from_qr(qr_text)

class ResultScreen(Screen):
    def go_home(self):
        self.manager.current = 'home'

    def render_receipt(self, data):
        self.ids.shop_label.text = data.get('user', 'Магазин')
        self.ids.address_label.text = data.get('retailPlaceAddress', '')
        
        # Очистка старых товаров
        box = self.ids.items_box
        box.clear_widgets()

        # Генерация списка товаров
        for item in data.get('items', []):
            name = item.get('name', 'Товар')
            price = item.get('price', 0) / 100
            qty = item.get('quantity', 1)
            total = item.get('sum', 0) / 100
            
            # Строка товара: Название (с переносом)
            box.add_widget(MDLabel(text=name, adaptive_height=True, theme_text_color="Primary"))
            
            # Строка цены: 1 x 100.00 = 100.00
            price_row = MDBoxLayout(adaptive_height=True)
            price_row.add_widget(MDLabel(text=f"{qty} x {price:.2f}", theme_text_color="Secondary", font_style="Caption"))
            price_row.add_widget(MDLabel(text=f"={total:.2f}", halign="right", bold=True))
            box.add_widget(price_row)
            
            # Разделитель пунктиром (символический)
            box.add_widget(MDLabel(text="- " * 20, theme_text_color="Hint", font_style="Caption", halign="center"))

        # Итог
        total_sum = data.get('totalSum', 0) / 100
        self.ids.total_label.text = f"{total_sum:.2f} ₽"

        # Тип оплаты
        payment = "Наличными"
        if data.get('ecashTotalSum', 0) > 0:
            payment = "Безналичными (Карта)"
        self.ids.payment_type_label.text = f"Оплата: {payment}"

class HistoryScreen(Screen):
    def go_home(self):
        self.manager.current = 'home'

    def load_history(self):
        history_list = self.ids.history_list
        history_list.clear_widgets()
        store = MDApp.get_running_app().store
        
        # Читаем историю
        for key in sorted(store.keys(), reverse=True):
            entry = store.get(key)
            req = entry['request']
            res = entry['result']
            
            # Создаем элемент списка
            item = TwoLineListItem(
                text=f"{res.get('user', 'Магазин')} ({req['sum']} руб)",
                secondary_text=f"{req['date']} {req['time']}",
                on_release=lambda x, r=res: self.show_details(r)
            )
            history_list.add_widget(item)

    def show_details(self, result_data):
        # Открываем экран результата с сохраненными данными
        app = MDApp.get_running_app()
        app.root.get_screen('result').render_receipt(result_data)
        app.root.current = 'result'

class CheckApp(MDApp):
    store = None

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        self.store = JsonStore(os.path.join(self.user_data_dir, "history.json"))
        return Builder.load_string(KV)

    def on_start(self):
        if self.store.exists('user_settings') and self.store.get('user_settings')['agreed']:
            self.root.current = 'home'
        else:
            self.root.current = 'consent'

    def add_history(self, req, res):
        key = datetime.now().strftime("%Y%m%d%H%M%S")
        self.store.put(key, request=req, result=res)

if __name__ == '__main__':
    CheckApp().run()
