import sys
import traceback

# --- ГЛОБАЛЬНАЯ ЗАЩИТА ОТ ВЫЛЕТОВ ---
# Если приложение попытается упасть, мы перехватим ошибку
try:
    import os
    import json
    from datetime import datetime
    
    # Kivy imports
    from kivy.lang import Builder
    from kivymd.app import MDApp
    from kivy.uix.screenmanager import ScreenManager, Screen
    from kivymd.uix.pickers import MDDatePicker, MDTimePicker
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.label import MDLabel
    from kivymd.uix.button import MDRaisedButton
    from kivymd.uix.list import TwoLineListItem
    from kivymd.uix.card import MDCard
    from kivy.storage.jsonstore import JsonStore
    from kivy.utils import platform
    from kivy.clock import Clock
    from kivy.properties import StringProperty

    # --- ПОПЫТКА ПОДКЛЮЧИТЬ ANDROID МОДУЛИ ---
    # Мы делаем это аккуратно. Если не получится - приложение будет работать без сканера.
    AndroidScanner = None
    if platform == 'android':
        try:
            from jnius import autoclass, cast
            from android import activity
            from android.permissions import request_permissions, Permission
            
            # Загружаем классы Android
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')
            AndroidScanner = IntentIntegrator
        except Exception as e:
            print(f"Ошибка загрузки сканера: {e}")
            AndroidScanner = None

    # --- РАЗМЕТКА ИНТЕРФЕЙСА (KV) ---
    KV = '''
ScreenManager:
    HomeScreen:
    ResultScreen:
    HistoryScreen:

# 1. ГЛАВНЫЙ ЭКРАН
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
                    height: "130dp"
                    radius: [15]
                    padding: "15dp"
                    md_bg_color: 0.9, 0.95, 1, 1
                    elevation: 2
                    on_release: root.start_scan_safe()
                    ripple_behavior: True

                    MDIcon:
                        icon: "qrcode-scan"
                        halign: "center"
                        font_size: "50sp"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.4, 0.8, 1
                    
                    MDLabel:
                        text: "СКАНИРОВАТЬ QR"
                        halign: "center"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.4, 0.8, 1
                        font_style: "H6"

                MDLabel:
                    id: status_label
                    text: "Готов к работе"
                    halign: "center"
                    theme_text_color: "Hint"
                    font_style: "Caption"

                # ПОЛЯ ВВОДА
                MDTextField:
                    id: sum_field
                    hint_text: "Сумма (1200.00)"
                    input_filter: 'float'
                    mode: "fill"
                MDTextField:
                    id: fn_field
                    hint_text: "ФН"
                    input_filter: 'int'
                    mode: "fill"
                MDTextField:
                    id: fd_field
                    hint_text: "ФД"
                    input_filter: 'int'
                    mode: "fill"
                MDTextField:
                    id: fp_field
                    hint_text: "ФП"
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
                    text: "ПОКАЗАТЬ ЧЕК"
                    size_hint_x: 1
                    height: "50dp"
                    on_release: root.manual_check()

# 2. ЭКРАН ЧЕКА
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
                padding: "20dp"
                radius: [0]
                md_bg_color: 1, 1, 1, 1
                elevation: 4
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
                    text_size: self.width, None

                MDSeparator:
                    height: "2dp"
                    padding_y: "10dp"

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
                        font_style: "H5"
                    MDLabel:
                        id: total_label
                        text: "0.00"
                        halign: "right"
                        bold: True
                        font_style: "H5"

# 3. ИСТОРИЯ
<HistoryScreen>:
    name: 'history'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "История"
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

        def start_scan_safe(self):
            # БЕЗОПАСНЫЙ ЗАПУСК СКАНЕРА
            if AndroidScanner:
                try:
                    request_permissions([Permission.CAMERA])
                    integrator = AndroidScanner(PythonActivity.mActivity)
                    integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
                    integrator.setPrompt("Наведите на QR-код")
                    integrator.setCameraId(0)
                    integrator.setBeepEnabled(True)
                    integrator.initiateScan()
                except Exception as e:
                    self.ids.status_label.text = f"Ошибка запуска камеры: {str(e)}"
            else:
                if platform == 'android':
                    self.ids.status_label.text = "Сканер не инициализирован (библиотека не найдена)"
                else:
                    # Тест на ПК
                    self.fill_from_qr("t=20260218T1400&s=150.00&fn=12345&i=111&fp=999")

        def fill_from_qr(self, qr_text):
            try:
                params = dict(x.split('=') for x in qr_text.split('&') if '=' in x)
                if 's' in params: self.ids.sum_field.text = params['s']
                if 'fn' in params: self.ids.fn_field.text = params['fn']
                if 'i' in params: self.ids.fd_field.text = params['i']
                if 'fp' in params: self.ids.fp_field.text = params['fp']
                
                if 't' in params:
                    raw = params['t']
                    if len(raw) >= 8:
                        self.date_val = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                        self.ids.date_btn.text = self.date_val
                    if 'T' in raw and len(raw) >= 13:
                        self.time_val = f"{raw[9:11]}:{raw[11:13]}"
                        self.ids.time_btn.text = self.time_val

                self.ids.status_label.text = "Код успешно считан!"
                self.manual_check()
            except Exception as e:
                self.ids.status_label.text = f"Ошибка чтения QR: {e}"

        def manual_check(self):
            s = self.ids.sum_field.text
            if not s: 
                self.ids.status_label.text = "Введите сумму!"
                return
            
            # Формируем данные чека
            data = {
                "shop": "МАГАЗИН (Скан)",
                "address": "Адрес не загружен (нет связи с ФНС)",
                "total": s,
                "date": self.date_val,
                "time": self.time_val,
                "items": [{"name": "Товар по чеку", "qty": 1, "price": float(s)*100, "sum": float(s)*100}]
            }
            MDApp.get_running_app().add_history(data)
            self.manager.get_screen('result').render(data)
            self.manager.current = 'result'

        def open_history(self):
            self.manager.get_screen('history').load_history()
            self.manager.current = 'history'

    class ResultScreen(Screen):
        def go_home(self):
            self.manager.current = 'home'

        def render(self, data):
            self.ids.shop_label.text = data.get('shop', 'Магазин')
            self.ids.address_label.text = data.get('address', '')
            self.ids.total_label.text = f"= {data['total']} руб"
            
            box = self.ids.items_box
            box.clear_widgets()
            for item in data.get('items', []):
                # Безопасная математика
                try:
                    price = item.get('price', 0) / 100
                    total = item.get('sum', 0) / 100
                except:
                    price = 0
                    total = 0

                name = item.get('name', 'Товар')
                box.add_widget(MDLabel(text=name, adaptive_height=True, bold=True))
                box.add_widget(MDLabel(text=f"1 x {price} = {total}", theme_text_color="Secondary", font_style="Caption"))

    class HistoryScreen(Screen):
        def go_home(self):
            self.manager.current = 'home'

        def load_history(self):
            self.ids.history_list.clear_widgets()
            store = MDApp.get_running_app().store
            for key in sorted(store.keys(), reverse=True):
                data = store.get(key)
                item = TwoLineListItem(
                    text=f"{data['total']} руб",
                    secondary_text=f"{data.get('date', '')}",
                    on_release=lambda x, d=data: self.show_details(d)
                )
                self.ids.history_list.add_widget(item)

        def show_details(self, data):
            app = MDApp.get_running_app()
            app.root.get_screen('result').render(data)
            app.root.current = 'result'

    class CheckApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Indigo"
            self.store = JsonStore(os.path.join(self.user_data_dir, "history_safe.json"))
            
            # Привязка результата Android Activity (Сканера)
            if platform == 'android':
                from android import activity
                activity.bind(on_activity_result=self.on_activity_result)
            
            return Builder.load_string(KV)

        def add_history(self, data):
            key = datetime.now().strftime("%Y%m%d%H%M%S")
            self.store.put(key, **data)

        def on_activity_result(self, request_code, result_code, intent):
            if request_code == 49374: # Код ZXing
                try:
                    from jnius import autoclass
                    IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')
                    result = IntentIntegrator.parseActivityResult(request_code, result_code, intent)
                    if result and result.getContents():
                        Clock.schedule_once(lambda dt: self.root.get_screen('home').fill_from_qr(result.getContents()), 0)
                except Exception as e:
                    print(f"Ошибка результата сканирования: {e}")

    if __name__ == '__main__':
        CheckApp().run()

# --- ЭКРАН СМЕРТИ (ЕСЛИ ВСЕ-ТАКИ УПАЛО) ---
except Exception:
    # Этот код сработает, если ошибка в самом начале (например, библиотека не найдена)
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.core.window import Window
    
    error_text = traceback.format_exc()
    
    class CrashApp(App):
        def build(self):
            Window.clearcolor = (0, 0, 0.8, 1) # Синий фон
            return ScrollView(child=Label(text=f"КРИТИЧЕСКАЯ ОШИБКА:\n\n{error_text}", 
                                          size_hint_y=None, height=1000, 
                                          text_size=(Window.width-20, None)))
    
    CrashApp().run()
