import sys
import traceback

try:
    import os
    import json
    import threading
    import requests
    from datetime import datetime
    
    # Kivy Framework
    from kivy.lang import Builder
    from kivymd.app import MDApp
    from kivy.uix.screenmanager import ScreenManager, Screen
    from kivymd.uix.pickers import MDDatePicker, MDTimePicker
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.label import MDLabel
    from kivymd.uix.button import MDRaisedButton
    from kivymd.uix.card import MDCard
    from kivymd.uix.list import OneLineListItem, TwoLineListItem, OneLineAvatarIconListItem, IconLeftWidget
    from kivy.storage.jsonstore import JsonStore
    from kivy.utils import platform
    from kivy.clock import Clock
    from kivy.core.window import Window

    # Android Libs
    AndroidScanner = None
    if platform == 'android':
        try:
            from jnius import autoclass
            from android import activity
            from android.permissions import request_permissions, Permission
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')
            AndroidScanner = IntentIntegrator
        except Exception:
            pass

    KV = '''
ScreenManager:
    HomeScreen:
    ResultScreen:
    HistoryScreen:
    AnalyticsScreen:

# --- 1. ГЛАВНЫЙ ЭКРАН ---
<HomeScreen>:
    name: 'home'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 1, 1, 1, 1

        MDTopAppBar:
            title: "Сканер Чеков"
            # Добавили кнопку АНАЛИТИКИ (иконка chart-bar)
            right_action_items: [["chart-bar", lambda x: root.open_analytics()], ["history", lambda x: root.open_history()]]
            elevation: 0
            md_bg_color: 0.2, 0.2, 0.2, 1

        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                padding: "20dp"
                spacing: "20dp"

                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: "160dp"
                    radius: [20]
                    padding: "20dp"
                    md_bg_color: 0.95, 0.95, 1, 1
                    line_color: 0.2, 0.4, 0.8, 1
                    elevation: 4
                    on_release: root.start_scan_safe()
                    ripple_behavior: True

                    MDIcon:
                        icon: "qrcode-scan"
                        halign: "center"
                        font_size: "60sp"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.4, 0.8, 1
                    
                    MDLabel:
                        text: "Сканировать Чек"
                        halign: "center"
                        bold: True
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.2, 0.2, 1

                    MDLabel:
                        id: status_label
                        text: "Нажми для старта"
                        halign: "center"
                        theme_text_color: "Hint"
                        font_style: "Caption"

                MDLabel:
                    text: "Ручной ввод:"
                    font_style: "Subtitle2"
                    theme_text_color: "Secondary"
                    padding_y: "10dp"

                MDBoxLayout:
                    spacing: "10dp"
                    adaptive_height: True
                    MDTextField:
                        id: sum_field
                        hint_text: "Сумма (руб)"
                        mode: "rectangle"
                        input_filter: 'float'
                    MDTextField:
                        id: fn_field
                        hint_text: "ФН"
                        mode: "rectangle"
                        input_filter: 'int'

                MDBoxLayout:
                    spacing: "10dp"
                    adaptive_height: True
                    MDTextField:
                        id: fd_field
                        hint_text: "ФД"
                        mode: "rectangle"
                        input_filter: 'int'
                    MDTextField:
                        id: fp_field
                        hint_text: "ФП"
                        mode: "rectangle"
                        input_filter: 'int'

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
                    text: "ПРОВЕРИТЬ"
                    size_hint_x: 1
                    height: "50dp"
                    md_bg_color: 0.2, 0.2, 0.2, 1
                    on_release: root.manual_check()

# --- 2. ЭКРАН РЕЗУЛЬТАТА ---
<ResultScreen>:
    name: 'result'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.9, 0.9, 0.9, 1
        MDTopAppBar:
            title: "Чек"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]
            elevation: 0
            md_bg_color: 0.2, 0.2, 0.2, 1
        ScrollView:
            padding: "15dp"
            MDCard:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: "20dp"
                radius: [0]
                md_bg_color: 1, 1, 1, 1
                elevation: 3
                pos_hint: {"center_x": .5}

                MDLabel:
                    id: shop_label
                    text: "ЗАГРУЗКА..."
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    adaptive_height: True

                MDLabel:
                    id: address_label
                    text: "..."
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Caption"
                    adaptive_height: True
                    text_size: self.width, None

                MDSeparator:
                    height: "2dp"
                    padding_y: "15dp"

                MDBoxLayout:
                    id: items_box
                    orientation: 'vertical'
                    adaptive_height: True
                    spacing: "15dp"

                MDSeparator:
                    height: "2dp"
                    padding_y: "15dp"
                
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "ИТОГ:"
                        bold: True
                        font_style: "H5"
                    MDLabel:
                        id: total_label
                        text: "0.00 ₽"
                        halign: "right"
                        bold: True
                        font_style: "H5"

# --- 3. ИСТОРИЯ ---
<HistoryScreen>:
    name: 'history'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Все чеки"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]
        ScrollView:
            MDList:
                id: history_list

# --- 4. АНАЛИТИКА (НОВЫЙ ЭКРАН) ---
<AnalyticsScreen>:
    name: 'analytics'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.95, 0.95, 0.95, 1
        
        MDTopAppBar:
            title: "Расходы за месяц"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]
            elevation: 2
            md_bg_color: 0.2, 0.2, 0.2, 1

        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                padding: "15dp"
                spacing: "15dp"

                # ГЛАВНАЯ ЦИФРА (ИТОГО)
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: "120dp"
                    radius: [15]
                    padding: "20dp"
                    md_bg_color: 0.2, 0.2, 0.2, 1
                    elevation: 4

                    MDLabel:
                        id: month_name_label
                        text: "Февраль 2026"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.8, 0.8, 0.8, 1
                        font_style: "Subtitle1"
                    
                    MDLabel:
                        id: total_month_label
                        text: "0 ₽"
                        halign: "center"
                        bold: True
                        font_style: "H3"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1

                MDLabel:
                    text: "Топ магазинов:"
                    font_style: "H6"
                    padding_x: "5dp"

                # СПИСОК МАГАЗИНОВ
                MDList:
                    id: shops_list
                    md_bg_color: 1, 1, 1, 1
                    radius: [10]
'''

    class HomeScreen(Screen):
        date_val = ""
        time_val = ""

        def show_date_picker(self):
            Window.release_all_keyboards()
            try:
                MDDatePicker().bind(on_save=self.on_date_save).open()
            except: pass

        def on_date_save(self, instance, value, date_range):
            self.date_val = value.strftime("%Y-%m-%d")
            self.ids.date_btn.text = self.date_val

        def show_time_picker(self):
            Window.release_all_keyboards()
            try:
                MDTimePicker().bind(on_save=self.on_time_save).open()
            except: pass

        def on_time_save(self, instance, time):
            self.time_val = time.strftime("%H:%M")
            self.ids.time_btn.text = self.time_val

        def start_scan_safe(self):
            if AndroidScanner:
                try:
                    request_permissions([Permission.CAMERA])
                    integrator = AndroidScanner(PythonActivity.mActivity)
                    integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
                    integrator.setPrompt("Наведите на QR-код")
                    integrator.setCameraId(0)
                    integrator.setBeepEnabled(True)
                    integrator.initiateScan()
                except Exception:
                    self.ids.status_label.text = "Ошибка камеры"
            else:
                self.fill_from_qr("t=20260218T1056&s=4640.70&fn=123456789&i=11111&fp=99999&n=1")

        def fill_from_qr(self, qr_text):
            try:
                params = dict(x.split('=') for x in qr_text.split('&') if '=' in x)
                if 't' in params:
                    raw = params['t']
                    if len(raw) >= 13:
                        self.date_val = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                        self.time_val = f"{raw[9:11]}:{raw[11:13]}"
                    else:
                        self.date_val = datetime.now().strftime("%Y-%m-%d")
                        self.time_val = datetime.now().strftime("%H:%M")

                if 's' in params: self.ids.sum_field.text = params['s']
                if 'fn' in params: self.ids.fn_field.text = params['fn']
                if 'i' in params: self.ids.fd_field.text = params['i']
                if 'fp' in params: self.ids.fp_field.text = params['fp']
                
                self.ids.status_label.text = "Код принят..."
                self.manual_check()
            except:
                self.ids.status_label.text = "Ошибка QR"

        def manual_check(self):
            s = self.ids.sum_field.text
            fn = self.ids.fn_field.text
            fd = self.ids.fd_field.text
            fp = self.ids.fp_field.text

            if not (s and fn and fd and fp):
                self.ids.status_label.text = "Заполните данные"
                return

            # Временный чек
            temp_data = {
                "shop": "Загрузка...",
                "address": "Связь с сервером...",
                "total": float(s),
                "date": self.date_val,
                "time": self.time_val,
                "items": [{"name": "Загрузка...", "qty": 1, "price": float(s)*100, "sum": float(s)*100}],
                "status": "loading"
            }
            MDApp.get_running_app().add_history(temp_data)
            self.manager.get_screen('result').render(temp_data)
            self.manager.current = 'result'

            # Запрос к серверу
            payload = {"sum": float(s)*100, "fn": fn, "fd": fd, "fp": fp, "date": self.date_val, "time": self.time_val}
            threading.Thread(target=self.send_to_server, args=(payload,)).start()

        def send_to_server(self, payload):
            # !!!!!!!!!!!!! URL !!!!!!!!!!!!!
            URL = "https://xn--j1aashl.xn--p1ai/Rss_api/proverka.php" 
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            try:
                response = requests.post(URL, json=payload, timeout=15)
                res_json = response.json()
                if res_json.get("status") == "OK":
                    Clock.schedule_once(lambda dt: self.update_result(res_json["data"]), 0)
                else:
                    Clock.schedule_once(lambda dt: self.show_error(res_json.get("message")), 0)
            except:
                Clock.schedule_once(lambda dt: self.show_error("Нет связи"), 0)

        def update_result(self, data):
            MDApp.get_running_app().add_history(data)
            self.manager.get_screen('result').render(data)

        def show_error(self, msg):
            s = self.manager.get_screen('result')
            s.ids.shop_label.text = "ОШИБКА"
            s.ids.address_label.text = str(msg)

        def open_history(self):
            self.manager.get_screen('history').load_history()
            self.manager.current = 'history'

        def open_analytics(self):
            self.manager.get_screen('analytics').calculate_analytics()
            self.manager.current = 'analytics'

    class ResultScreen(Screen):
        def go_home(self):
            self.manager.current = 'home'
        def render(self, data):
            total = float(data['total'])
            self.ids.shop_label.text = data.get('shop', 'Магазин')
            self.ids.address_label.text = data.get('address', '')
            self.ids.total_label.text = f"{total:,.2f} ₽"
            
            box = self.ids.items_box
            box.clear_widgets()
            items = data.get('items', [])
            if not items: return

            for item in items:
                box.add_widget(MDLabel(text=item.get('name', 'Товар'), bold=True, adaptive_height=True))
                
                qty = item.get('quantity', 1)
                price = item.get('price', 0)
                if price > 10000: price /= 100
                sum_item = item.get('sum', 0)
                if sum_item > 10000: sum_item /= 100
                
                box.add_widget(MDLabel(text=f"{qty} x {price:.2f} = {sum_item:.2f}", theme_text_color="Secondary", font_style="Caption", adaptive_height=True))
                box.add_widget(MDLabel(text="- "*30, theme_text_color="Hint", font_style="Overline", halign="center"))

    class HistoryScreen(Screen):
        def go_home(self):
            self.manager.current = 'home'
        def load_history(self):
            self.ids.history_list.clear_widgets()
            store = MDApp.get_running_app().store
            for key in sorted(store.keys(), reverse=True):
                data = store.get(key)
                li = TwoLineListItem(text=f"{data.get('shop', 'Магазин')}", 
                                     secondary_text=f"{data.get('date')} | {data.get('total')} ₽", 
                                     on_release=lambda x, d=data: self.show_details(d))
                self.ids.history_list.add_widget(li)
        def show_details(self, data):
            app = MDApp.get_running_app()
            app.root.get_screen('result').render(data)
            app.root.current = 'result'

    # --- ЛОГИКА АНАЛИТИКИ ---
    class AnalyticsScreen(Screen):
        def go_home(self):
            self.manager.current = 'home'

        def calculate_analytics(self):
            store = MDApp.get_running_app().store
            total_sum = 0
            shops = {}
            
            # Текущий месяц и год
            now = datetime.now()
            current_month_str = now.strftime("%Y-%m") # 2026-02
            
            # Считаем
            for key in store.keys():
                data = store.get(key)
                date_str = data.get('date', '') # 2026-02-18
                
                # Если дата чека совпадает с текущим месяцем
                if date_str.startswith(current_month_str):
                    try:
                        amount = float(data.get('total', 0))
                        total_sum += amount
                        
                        shop_name = data.get('shop', 'Неизвестно')
                        if shop_name in shops:
                            shops[shop_name] += amount
                        else:
                            shops[shop_name] = amount
                    except: pass

            # Обновляем UI
            months = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
            self.ids.month_name_label.text = f"{months[now.month]} {now.year}"
            self.ids.total_month_label.text = f"{total_sum:,.2f} ₽"
            
            # Топ магазинов
            self.ids.shops_list.clear_widgets()
            # Сортируем магазины по убыванию трат
            sorted_shops = sorted(shops.items(), key=lambda item: item[1], reverse=True)
            
            for shop, amount in sorted_shops:
                item = OneLineAvatarIconListItem(text=f"{shop}: {amount:,.2f} ₽")
                item.add_widget(IconLeftWidget(icon="store"))
                self.ids.shops_list.add_widget(item)

    class CheckApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "BlueGray"
            self.store = JsonStore(os.path.join(self.user_data_dir, "history_v7.json"))
            if platform == 'android':
                from android import activity
                activity.bind(on_activity_result=self.on_activity_result)
            return Builder.load_string(KV)
        def add_history(self, data):
            key = datetime.now().strftime("%Y%m%d%H%M%S")
            self.store.put(key, **data)
        def on_activity_result(self, request_code, result_code, intent):
            if request_code == 49374:
                try:
                    from jnius import autoclass
                    IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')
                    result = IntentIntegrator.parseActivityResult(request_code, result_code, intent)
                    if result and result.getContents():
                        Clock.schedule_once(lambda dt: self.root.get_screen('home').fill_from_qr(result.getContents()), 0)
                except: pass

    if __name__ == '__main__':
        CheckApp().run()
except Exception:
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.core.window import Window
    error_text = traceback.format_exc()
    class CrashApp(App):
        def build(self):
            Window.clearcolor = (0.5, 0, 0, 1)
            return ScrollView(child=Label(text=f"ERROR:\n{error_text}", size_hint_y=None, height=1000))
    CrashApp().run()
