import sys
import traceback

try:
    import os
    import json
    import threading
    import requests
    from datetime import datetime
    
    from kivy.lang import Builder
    from kivymd.app import MDApp
    from kivy.uix.screenmanager import ScreenManager, Screen
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.label import MDLabel
    from kivymd.uix.button import MDRaisedButton, MDIconButton
    from kivymd.uix.card import MDCard
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.list import OneLineListItem, TwoLineListItem, OneLineAvatarIconListItem, IconLeftWidget
    from kivy.storage.jsonstore import JsonStore
    from kivy.utils import platform
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.metrics import dp

    AndroidScanner = None
    if platform == 'android':
        try:
            from jnius import autoclass
            from android import activity
            from android.permissions import request_permissions, Permission
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            IntentIntegrator = autoclass('com.google.zxing.integration.android.IntentIntegrator')
            AndroidScanner = IntentIntegrator
        except Exception: pass

    # Справочники
    TAX_TYPES = {1: "ОСН", 2: "УСН", 4: "УСН д-р", 8: "ЕНВД", 16: "ЕСХН", 32: "ПСН (Патент)"}
    OP_TYPES = {1: "Приход", 2: "Возврат прихода", 3: "Расход", 4: "Возврат расхода"}

    KV = '''
ScreenManager:
    HomeScreen:
    ResultScreen:
    HistoryScreen:
    AnalyticsScreen:

# --- ГЛАВНЫЙ ЭКРАН ---
<HomeScreen>:
    name: 'home'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.98, 0.98, 0.98, 1

        MDTopAppBar:
            title: "Сканер Чеков"
            right_action_items: [["chart-bar", lambda x: root.open_analytics()], ["history", lambda x: root.open_history()]]
            elevation: 0
            md_bg_color: 0.1, 0.1, 0.1, 1
            specific_text_color: 1, 1, 1, 1

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
                    padding: "10dp"
                    md_bg_color: 0.2, 0.2, 0.2, 1
                    elevation: 6
                    on_release: root.start_scan_real()
                    ripple_behavior: True

                    MDIcon:
                        icon: "camera-iris"
                        halign: "center"
                        font_size: "60sp"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        pos_hint: {"center_x": .5}
                    
                    MDLabel:
                        text: "Сканировать QR"
                        halign: "center"
                        bold: True
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1

                    MDLabel:
                        id: status_label
                        text: "Нажмите для старта"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.8, 0.8, 0.8, 1
                        font_style: "Caption"

                MDLabel:
                    text: "— ИЛИ ВВЕДИТЕ ВРУЧНУЮ —"
                    halign: "center"
                    theme_text_color: "Hint"
                    font_style: "Overline"

                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    radius: [15]
                    padding: "20dp"
                    spacing: "15dp"
                    elevation: 2
                    md_bg_color: 1, 1, 1, 1

                    MDGridLayout:
                        cols: 2
                        spacing: "15dp"
                        adaptive_height: True
                        
                        MDTextField:
                            id: date_field
                            hint_text: "Дата"
                            text: root.get_today()
                            mode: "fill"
                        MDTextField:
                            id: time_field
                            hint_text: "Время"
                            text: root.get_now()
                            mode: "fill"
                        MDTextField:
                            id: sum_field
                            hint_text: "Сумма (руб)"
                            mode: "fill"
                            input_filter: 'float'
                        MDTextField:
                            id: fn_field
                            hint_text: "ФН"
                            mode: "fill"
                            input_filter: 'int'
                        MDTextField:
                            id: fd_field
                            hint_text: "ФД"
                            mode: "fill"
                            input_filter: 'int'
                        MDTextField:
                            id: fp_field
                            hint_text: "ФП"
                            mode: "fill"
                            input_filter: 'int'

                    MDRaisedButton:
                        text: "ПРОВЕРИТЬ ЧЕК"
                        size_hint_x: 1
                        height: "50dp"
                        md_bg_color: 0.1, 0.6, 0.1, 1
                        font_size: "16sp"
                        on_release: root.manual_check()

# --- ЭКРАН ЧЕКА ---
<ResultScreen>:
    name: 'result'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.9, 0.9, 0.9, 1 

        MDTopAppBar:
            title: "Электронный чек"
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
                radius: [6]
                md_bg_color: 1, 1, 1, 1
                elevation: 4
                pos_hint: {"center_x": .5}

                MDIcon:
                    icon: "store"
                    halign: "center"
                    font_size: "40sp"
                    theme_text_color: "Hint"
                
                MDLabel:
                    id: shop_label
                    text: "ЗАГРУЗКА..."
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    adaptive_height: True
                    padding_y: "5dp"
                
                MDLabel:
                    id: address_label
                    text: "Адрес..."
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Caption"
                    adaptive_height: True
                    text_size: self.width, None

                MDSeparator:
                    height: "1dp"
                    padding_y: "15dp"
                    color: 0, 0, 0, 0.1

                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        id: date_label
                        text: "..."
                        font_style: "Body2"
                    MDLabel:
                        id: op_label
                        text: "Приход"
                        halign: "right"
                        font_style: "Body2"
                        bold: True

                MDSeparator:
                    height: "2dp"
                    padding_y: "10dp"
                    color: 0, 0, 0, 1

                MDBoxLayout:
                    id: items_box
                    orientation: 'vertical'
                    adaptive_height: True
                    spacing: "12dp"
                    padding: [0, 10, 0, 10]

                MDSeparator:
                    height: "2dp"
                    padding_y: "10dp"
                    color: 0, 0, 0, 1

                MDBoxLayout:
                    adaptive_height: True
                    padding: [0, 10, 0, 10]
                    MDLabel:
                        text: "ИТОГ:"
                        bold: True
                        font_style: "H5"
                    MDLabel:
                        id: total_label
                        text: "0.00 ₽"
                        halign: "right"
                        bold: True
                        font_style: "H4"
                        theme_text_color: "Custom"
                        text_color: 0, 0, 0, 1
                
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "Наличными"
                        theme_text_color: "Secondary"
                        font_style: "Caption"
                    MDLabel:
                        id: cash_label
                        text: "0.00"
                        halign: "right"
                        theme_text_color: "Secondary"
                        font_style: "Caption"
                
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "Безналичными"
                        theme_text_color: "Secondary"
                        font_style: "Caption"
                    MDLabel:
                        id: card_label
                        text: "0.00"
                        halign: "right"
                        theme_text_color: "Secondary"
                        font_style: "Caption"

                MDSeparator:
                    height: "1dp"
                    padding_y: "15dp"
                    color: 0, 0, 0, 0.1

                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_height: True
                    spacing: "3dp"
                    
                    MDLabel:
                        text: "Фискальные данные"
                        font_style: "Overline"
                        halign: "center"
                        padding_y: "5dp"

                    MDLabel:
                        id: inn_label
                        text: "ИНН: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: tax_label
                        text: "СНО: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: nds_info
                        text: "НДС: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: cashier_label
                        text: "Кассир: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: shift_label
                        text: "Смена: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: kkt_label
                        text: "РН ККТ: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    # --- ВОТ СТРОКА, КОТОРУЮ Я ВЕРНУЛ ---
                    MDLabel:
                        id: serial_label
                        text: "ЗАВОД №: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: fn_label
                        text: "ФН: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: fd_label
                        text: "ФД: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: fp_label
                        text: "ФП: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                    
                    MDLabel:
                        id: ofd_label
                        text: "ОФД: ..."
                        font_style: "Overline"
                        theme_text_color: "Secondary"
                        adaptive_height: True

                MDLabel:
                    text: "СПАСИБО ЗА ПОКУПКУ!"
                    halign: "center"
                    font_style: "Caption"
                    padding_y: "20dp"
                    theme_text_color: "Hint"

<HistoryScreen>:
    name: 'history'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "История чеков"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]
            elevation: 2
            md_bg_color: 0.2, 0.2, 0.2, 1
        ScrollView:
            MDList:
                id: history_list

<AnalyticsScreen>:
    name: 'analytics'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Расходы"
            left_action_items: [["arrow-left", lambda x: root.go_home()]]
            md_bg_color: 0.2, 0.2, 0.2, 1
        ScrollView:
            MDList:
                id: shops_list
'''

    class HomeScreen(Screen):
        def get_today(self): return datetime.now().strftime("%Y-%m-%d")
        def get_now(self): return datetime.now().strftime("%H:%M")

        def start_scan_real(self):
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
                self.ids.status_label.text = "Сканер только для Android"

        def fill_from_qr(self, qr_text):
            try:
                params = dict(x.split('=') for x in qr_text.split('&') if '=' in x)
                if 't' in params:
                    raw = params['t']
                    if len(raw) >= 13:
                        self.ids.date_field.text = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                        self.ids.time_field.text = f"{raw[9:11]}:{raw[11:13]}"
                if 's' in params: self.ids.sum_field.text = params['s']
                if 'fn' in params: self.ids.fn_field.text = params['fn']
                if 'i' in params: self.ids.fd_field.text = params['i']
                if 'fp' in params: self.ids.fp_field.text = params['fp']
                self.ids.status_label.text = "Код считан..."
                self.manual_check()
            except:
                self.ids.status_label.text = "Ошибка QR"

        def manual_check(self):
            s = self.ids.sum_field.text
            fn, fd, fp = self.ids.fn_field.text, self.ids.fd_field.text, self.ids.fp_field.text
            d, t = self.ids.date_field.text, self.ids.time_field.text
            if not (s and fn and fd and fp): return
            self.ids.status_label.text = "Загрузка..."
            payload = {"sum": float(s), "fn": fn, "fd": fd, "fp": fp, "date": d, "time": t}
            threading.Thread(target=self.send_to_server, args=(payload,)).start()

        def send_to_server(self, payload):
            URL = "https://xn--j1aashl.xn--p1ai/Rss_api/proverka.php"
            try:
                response = requests.post(URL, json=payload, timeout=30, verify=False)
                res_json = response.json()
                if res_json.get("status") == "OK":
                    Clock.schedule_once(lambda dt: self.update_result(res_json["data"]), 0)
                else:
                    msg = res_json.get("message", "Ошибка")
                    Clock.schedule_once(lambda dt: self.show_error(msg), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_error(f"Сбой: {e}"), 0)

        def update_result(self, data):
            MDApp.get_running_app().add_history(data)
            self.manager.get_screen('result').render(data)
            self.manager.current = 'result'
            self.ids.status_label.text = "Готов"
        def show_error(self, msg): self.ids.status_label.text = str(msg)
        def open_history(self): self.manager.get_screen('history').load_history(); self.manager.current = 'history'
        def open_analytics(self): self.manager.get_screen('analytics').calculate_analytics(); self.manager.current = 'analytics'

    class ResultScreen(Screen):
        def go_home(self): self.manager.current = 'home'
        def render(self, data):
            self.ids.shop_label.text = data.get('shop', 'Магазин')
            self.ids.address_label.text = data.get('address', '')
            self.ids.date_label.text = data.get('date_time', '')
            self.ids.op_label.text = data.get('op_type', 'Приход')
            
            box = self.ids.items_box
            box.clear_widgets()
            items = data.get('items', [])
            
            for idx, item in enumerate(items, 1):
                name = item.get('name', 'Товар')
                price = float(item.get('price', 0))
                qty = float(item.get('quantity', 1))
                sm = float(item.get('sum', 0))
                
                box.add_widget(MDLabel(text=f"{idx}. {name}", font_style="Subtitle2", bold=True, adaptive_height=True))
                row = MDBoxLayout(adaptive_height=True)
                row.add_widget(MDLabel(text=f"{qty} x {price:,.2f}", theme_text_color="Secondary", font_style="Caption", size_hint_x=0.7))
                row.add_widget(MDLabel(text=f"= {sm:,.2f}", halign="right", bold=True, font_style="Body2", size_hint_x=0.3))
                box.add_widget(row)

            total = float(data.get('total', 0))
            cash = float(data.get('cash', 0))
            ecash = float(data.get('ecash', 0))
            self.ids.total_label.text = f"{total:,.2f} ₽"
            self.ids.cash_label.text = f"{cash:,.2f} ₽"
            self.ids.card_label.text = f"{ecash:,.2f} ₽"
            
            t_code = int(data.get('tax_type', 0))
            self.ids.tax_label.text = f"СНО: {TAX_TYPES.get(t_code, str(t_code))}"
            
            nds_str = ""
            if float(data.get('nds18', 0)) > 0: nds_str += f"20%: {data['nds18']}  "
            if float(data.get('nds10', 0)) > 0: nds_str += f"10%: {data['nds10']}  "
            if float(data.get('ndsNo', 0)) > 0: nds_str += "Без НДС"
            self.ids.nds_info.text = f"Налоги: {nds_str}"

            self.ids.inn_label.text = f"ИНН: {data.get('inn', '-')}"
            self.ids.cashier_label.text = f"Кассир: {data.get('cashier', '-')}"
            self.ids.shift_label.text = f"Смена: {data.get('shift', '-')}. Чек: {data.get('check_num', '-')}"
            self.ids.kkt_label.text = f"РН ККТ: {data.get('kkt_reg', '-')}"
            
            # --- ВОТ ЗАПОЛНЕНИЕ ВОЗВРАЩЕННОГО ПОЛЯ ---
            self.ids.serial_label.text = f"ЗАВОД №: {data.get('kkt_serial', '-')}"
            
            self.ids.fn_label.text = f"ФН: {data.get('fn', '-')}"
            self.ids.fd_label.text = f"ФД: {data.get('fd', '-')}"
            self.ids.fp_label.text = f"ФП: {data.get('fp', '-')}"
            self.ids.ofd_label.text = f"ОФД: {data.get('ofd', '-')}"

    class HistoryScreen(Screen):
        def go_home(self): self.manager.current = 'home'
        def load_history(self):
            self.ids.history_list.clear_widgets()
            store = MDApp.get_running_app().store
            for key in sorted(store.keys(), reverse=True):
                data = store.get(key)
                li = OneLineAvatarIconListItem(
                    text=f"{data.get('shop', 'Магазин')}", 
                    on_release=lambda x, d=data: self.show_details(d)
                )
                li.add_widget(IconLeftWidget(icon="receipt"))
                li.text += f"  —  {data.get('total')} ₽"
                self.ids.history_list.add_widget(li)
        def show_details(self, data):
            app = MDApp.get_running_app()
            app.root.get_screen('result').render(data)
            app.root.current = 'result'

    class AnalyticsScreen(Screen):
        def go_home(self): self.manager.current = 'home'
        def calculate_analytics(self):
            store = MDApp.get_running_app().store
            total = 0
            shops = {}
            for key in store.keys():
                d = store.get(key)
                try:
                    amt = float(d.get('total', 0))
                    total += amt
                    s = d.get('shop', 'Неизвестно')
                    shops[s] = shops.get(s, 0) + amt
                except: pass
            
            self.ids.shops_list.clear_widgets()
            header = OneLineListItem(text=f"Всего за месяц: {total:,.2f} ₽", bg_color=(0.9, 0.9, 0.9, 1))
            self.ids.shops_list.add_widget(header)
            
            for s, a in sorted(shops.items(), key=lambda x: x[1], reverse=True):
                li = OneLineAvatarIconListItem(text=f"{s}: {a:,.2f} ₽")
                li.add_widget(IconLeftWidget(icon="store"))
                self.ids.shops_list.add_widget(li)

    class CheckApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Gray"
            self.theme_cls.primary_hue = "900"
            self.store = JsonStore(os.path.join(self.user_data_dir, "history_v15.json"))
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
    error_text = traceback.format_exc()
    class CrashApp(App):
        def build(self):
            layout = ScrollView()
            label = Label(text=error_text, size_hint_y=None, color=(1,1,1,1))
            label.bind(texture_size=label.setter('size'))
            layout.add_widget(label)
            return layout
    CrashApp().run()
