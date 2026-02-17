import traceback
import os

# Сначала пробуем импортировать Kivy. Если даже его нет - это сразу ошибка.
try:
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.base import runTouchApp
    from kivy.lang import Builder
except Exception:
    pass # Обработаем ниже

# ГЛАВНЫЙ БЛОК ЗАПУСКА
try:
    # --- ТВОЙ ОСНОВНОЙ КОД НАЧИНАЕТСЯ ЗДЕСЬ ---
    from kivymd.app import MDApp
    from kivy.uix.screenmanager import ScreenManager, Screen
    from kivymd.uix.pickers import MDDatePicker, MDTimePicker
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.button import MDFlatButton
    from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
    from kivy.storage.jsonstore import JsonStore
    from datetime import datetime
    
    # Пытаемся импортировать requests. Если его нет в buildozer.spec - тут вылетит.
    import requests
    import json

    KV = '''
ScreenManager:
    HomeScreen:
    ResultScreen:
    HistoryScreen:

<HomeScreen>:
    name: 'home'
    MDBoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 15

        MDTopAppBar:
            title: "Проверка Чеков ФНС"
            elevation: 4
            pos_hint: {"top": 1}

        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                spacing: 15
                padding: [0, 20, 0, 0]

                MDTextField:
                    id: sum_field
                    hint_text: "Сумма чека (руб.коп)"
                    helper_text: "Например: 1500.00"
                    input_filter: 'float'
                    mode: "rectangle"

                MDTextField:
                    id: fn_field
                    hint_text: "ФН (Фискальный Накопитель)"
                    input_filter: 'int'
                    mode: "rectangle"

                MDTextField:
                    id: fd_field
                    hint_text: "ФД (Фискальный Документ)"
                    input_filter: 'int'
                    mode: "rectangle"

                MDTextField:
                    id: fp_field
                    hint_text: "ФП (Фискальный Признак)"
                    input_filter: 'int'
                    mode: "rectangle"

                MDBoxLayout:
                    orientation: 'horizontal'
                    spacing: 10
                    size_hint_y: None
                    height: "50dp"

                    MDRaisedButton:
                        id: date_btn
                        text: "Выбрать Дату"
                        on_release: root.show_date_picker()
                        size_hint_x: 0.5

                    MDRaisedButton:
                        id: time_btn
                        text: "Выбрать Время"
                        on_release: root.show_time_picker()
                        size_hint_x: 0.5

                MDLabel:
                    id: selected_datetime
                    text: "Дата и время не выбраны"
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Caption"

                MDBoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: "40dp"
                    spacing: 10

                    MDCheckbox:
                        id: consent_check
                        size_hint: None, None
                        size: "48dp", "48dp"
                        pos_hint: {'center_y': .5}
                        on_active: root.toggle_button(self.active)

                    MDLabel:
                        text: "Согласен на обработку данных и проверку в ФНС"
                        font_style: "Caption"
                        valign: "center"

                MDRaisedButton:
                    id: check_btn
                    text: "ПРОВЕРИТЬ В ИФНС"
                    size_hint_x: 1
                    disabled: True
                    md_bg_color: 0, 0.5, 0, 1
                    on_release: root.check_receipt()

                MDRaisedButton:
                    text: "История проверок"
                    size_hint_x: 1
                    md_bg_color: 0.2, 0.2, 0.2, 1
                    on_release: app.root.current = 'history'

<ResultScreen>:
    name: 'result'
    MDBoxLayout:
        orientation: 'vertical'
        padding: 20
        
        MDLabel:
            id: status_label
            text: "Статус..."
            halign: "center"
            font_style: "H5"
        
        MDLabel:
            id: details_label
            text: ""
            halign: "center"
        
        MDRaisedButton:
            text: "Назад"
            pos_hint: {"center_x": .5}
            on_release: app.root.current = 'home'

<HistoryScreen>:
    name: 'history'
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: "Моя История"
            left_action_items: [["arrow-left", lambda x: app.change_screen('home')]]
        
        ScrollView:
            MDList:
                id: history_list
'''

    class HomeScreen(Screen):
        date_str = ""
        time_str = ""

        def show_date_picker(self):
            try:
                date_dialog = MDDatePicker()
                date_dialog.bind(on_save=self.on_date_save)
                date_dialog.open()
            except Exception as e:
                self.show_dialog("Ошибка Даты", str(e))

        def on_date_save(self, instance, value, date_range):
            self.date_str = value.strftime("%Y-%m-%d")
            self.ids.date_btn.text = self.date_str
            self.update_datetime_label()

        def show_time_picker(self):
            try:
                time_dialog = MDTimePicker()
                time_dialog.bind(on_save=self.on_time_save)
                time_dialog.open()
            except Exception as e:
                self.show_dialog("Ошибка Времени", str(e))

        def on_time_save(self, instance, time):
            self.time_str = time.strftime("%H:%M")
            self.ids.time_btn.text = self.time_str
            self.update_datetime_label()

        def update_datetime_label(self):
            if self.date_str and self.time_str:
                self.ids.selected_datetime.text = f"Выбрано: {self.date_str} {self.time_str}"
            
        def toggle_button(self, is_active):
            self.ids.check_btn.disabled = not is_active

        def check_receipt(self):
            data = {
                "sum": self.ids.sum_field.text,
                "fn": self.ids.fn_field.text,
                "fd": self.ids.fd_field.text,
                "fp": self.ids.fp_field.text,
                "date": self.date_str,
                "time": self.time_str
            }
            if not all(data.values()):
                self.show_dialog("Ошибка", "Заполните все поля!")
                return

            try:
                # ЗАГЛУШКА
                result = {"status": "valid", "message": "Чек найден в базе ФНС (Тест)", "shop": "ООО Ромашка"}
                App.get_running_app().add_history(data, result)
                
                result_screen = self.manager.get_screen('result')
                result_screen.ids.status_label.text = result['message']
                result_screen.ids.details_label.text = f"Сумма: {data['sum']} руб.\nМагазин: {result.get('shop')}"
                self.manager.current = 'result'
            except Exception as e:
                self.show_dialog("Ошибка", str(e))

        def show_dialog(self, title, text):
            dialog = MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
            dialog.open()

    class ResultScreen(Screen):
        pass

    class HistoryScreen(Screen):
        pass

    class CheckApp(MDApp):
        store = None

        def build(self):
            self.theme_cls.primary_palette = "Blue"
            # Используем безопасную папку для истории
            data_dir = self.user_data_dir
            self.store = JsonStore(os.path.join(data_dir, "history.json"))
            return Builder.load_string(KV)

        def on_start(self):
            try:
                self.load_history()
            except:
                pass

        def change_screen(self, screen_name):
            self.root.current = screen_name

        def add_history(self, request_data, result_data):
            key = datetime.now().strftime("%Y%m%d%H%M%S")
            self.store.put(key, date=request_data['date'], sum=request_data['sum'], status=result_data['message'])
            self.load_history()

        def load_history(self):
            history_screen = self.root.get_screen('history')
            history_list = history_screen.ids.history_list
            history_list.clear_widgets()
            for key in sorted(self.store.keys(), reverse=True):
                item = self.store.get(key)
                list_item = TwoLineAvatarIconListItem(text=f"Сумма: {item['sum']} руб.", secondary_text=f"{item['date']}")
                list_item.add_widget(IconLeftWidget(icon="check-circle"))
                history_list.add_widget(list_item)

    if __name__ == '__main__':
        CheckApp().run()

# --- ЛОВЕЦ ОШИБОК (ЭКРАН СМЕРТИ) ---
except Exception:
    # Если наверху что-то сломалось, мы попадаем сюда
    error_text = traceback.format_exc()
    
    # Пытаемся показать ошибку на экране
    try:
        from kivy.app import App
        from kivy.uix.label import Label
        from kivy.uix.scrollview import ScrollView
        
        class CrashApp(App):
            def build(self):
                # Черный фон, белый текст, прокрутка
                return ScrollView(
                    size_hint=(1, 1),
                    child=Label(
                        text=error_text,
                        size_hint_y=None,
                        height=2000,  # Высота чтобы влез длинный текст
                        text_size=(None, None),
                        halign='left',
                        valign='top'
                    )
                )
        CrashApp().run()
    except:
        # Если даже Ловец сломался - печаль
        print("CRITICAL FAILURE")
