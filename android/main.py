"""
EverNothing Android App (Kivy)

Installation (Termux on Android):
  pkg install python
  pip install kivy requests

Installation (desktop testing):
  pip install kivy requests

Run:
  python android/main.py

Configuration:
  Set EVERNOTHING_SERVER env var to your Flask server IP/port
  e.g. export EVERNOTHING_SERVER=http://192.168.1.100:5000
  Default: http://127.0.0.1:5000
"""

try:
    from kivy.app import App
except ModuleNotFoundError as e:
    raise SystemExit(f"Kivy not found: {e}\nInstall with: pip install kivy") from e

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
import requests
import os

SERVER_URL = os.environ.get('EVERNOTHING_SERVER', 'http://127.0.0.1:5000')

# Theme colors
GOLD = (1, 0.84, 0, 1)
GOLD_DIM = (0.72, 0.59, 0.05, 1)
RED = (0.8, 0.13, 0, 1)
BG = (0.04, 0.04, 0.04, 1)
BG2 = (0.07, 0.07, 0.07, 1)
WHITE = (1, 1, 1, 1)

Window.clearcolor = BG


# --- Helpers ---

def gold_label(text, size=16, bold=False, **kwargs):
    return Label(text=text, color=GOLD, font_size=dp(size), bold=bold,
                 size_hint_y=None, height=dp(size + 14), **kwargs)

def gold_input(password=False, **kwargs):
    return TextInput(
        password=password, multiline=False,
        background_color=BG2, foreground_color=GOLD,
        cursor_color=GOLD, hint_text_color=GOLD_DIM,
        size_hint_y=None, height=dp(40),
        **kwargs
    )

def gold_button(text, on_press=None, danger=False, **kwargs):
    btn = Button(
        text=text,
        background_color=RED if danger else (0.15, 0.15, 0.15, 1),
        color=GOLD,
        size_hint_y=None, height=dp(44),
        font_size=dp(15),
        **kwargs
    )
    if on_press:
        btn.bind(on_press=on_press)
    return btn

def show_popup(title, message):
    content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
    content.add_widget(Label(text=message, color=GOLD, font_size=dp(14)))
    btn = Button(text='OK', size_hint_y=None, height=dp(40),
                 background_color=RED, color=GOLD)
    content.add_widget(btn)
    popup = Popup(title=title, content=content, size_hint=(0.85, 0.4),
                  background_color=BG2, title_color=GOLD)
    btn.bind(on_press=popup.dismiss)
    popup.open()


# --- API Client ---

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.base = SERVER_URL

    def _post(self, path, data):
        try:
            return self.session.post(f'{self.base}{path}', json=data, timeout=10)
        except Exception as e:
            return None

    def _get(self, path, params=None):
        try:
            return self.session.get(f'{self.base}{path}', params=params, timeout=10)
        except Exception as e:
            return None

    def _delete(self, path):
        try:
            return self.session.delete(f'{self.base}{path}', timeout=10)
        except Exception as e:
            return None

    def _put(self, path, data):
        try:
            return self.session.put(f'{self.base}{path}', json=data, timeout=10)
        except Exception as e:
            return None

    def login(self, username, password):
        r = self._post('/api/login', {'username': username, 'password': password})
        if r and r.status_code == 200:
            return True, r.json().get('username')
        msg = r.json().get('error', 'Login failed') if r else 'Cannot reach server'
        return False, msg

    def logout(self):
        self._post('/api/logout', {})

    def get_folders(self):
        r = self._get('/api/folders')
        return r.json() if r and r.status_code == 200 else []

    def create_folder(self, name, parent_id=None):
        r = self._post('/api/folders', {'name': name, 'parent_id': parent_id})
        return r and r.status_code == 200

    def delete_folder(self, fid):
        r = self._delete(f'/api/folders/{fid}')
        return r and r.status_code == 200

    def get_folder_notes(self, fid):
        r = self._get(f'/api/folders/{fid}/notes')
        return r.json() if r and r.status_code == 200 else []

    def get_note(self, nid):
        r = self._get(f'/api/notes/{nid}')
        return r.json() if r and r.status_code == 200 else None

    def create_note(self, folder_id, key, value, description=''):
        r = self._post('/api/notes', {'key': key, 'value': value, 'folder_id': folder_id, 'description': description})
        if r and r.status_code == 200:
            return True, None
        msg = r.json().get('error', 'Failed') if r else 'Cannot reach server'
        return False, msg

    def update_note(self, nid, key, value, folder_id, description=''):
        r = self._put(f'/api/notes/{nid}', {'key': key, 'value': value, 'folder_id': folder_id, 'description': description})
        return r and r.status_code == 200

    def delete_note(self, nid):
        r = self._delete(f'/api/notes/{nid}')
        return r and r.status_code == 200

    def search(self, q):
        r = self._get('/api/search', {'q': q})
        return r.json() if r and r.status_code == 200 else []


# --- Screens ---

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(12))
        layout.add_widget(Label(text='◆ EverNothing', font_size=dp(28), color=GOLD,
                                bold=True, size_hint_y=None, height=dp(50)))
        layout.add_widget(Label(text='Sign in to your notes', font_size=dp(13),
                                color=GOLD_DIM, size_hint_y=None, height=dp(24)))
        layout.add_widget(gold_label('Username'))
        self.username = gold_input(hint_text='Username')
        layout.add_widget(self.username)
        layout.add_widget(gold_label('Password'))
        self.password = gold_input(password=True, hint_text='Password')
        layout.add_widget(self.password)
        self.error = Label(text='', color=RED, font_size=dp(13),
                           size_hint_y=None, height=dp(24))
        layout.add_widget(self.error)
        layout.add_widget(gold_button('Login', on_press=self.do_login))
        layout.add_widget(Label())  # spacer
        self.add_widget(layout)

    def do_login(self, _):
        app = App.get_running_app()
        ok, result = app.api.login(self.username.text.strip(), self.password.text)
        if ok:
            self.error.text = ''
            self.password.text = ''
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'folders'
            self.manager.get_screen('folders').load()
        else:
            self.error.text = result


class FoldersScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical')

        # Nav bar
        nav = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(6), spacing=dp(6))
        nav.add_widget(Label(text='◆ EverNothing', color=GOLD, bold=True, font_size=dp(16)))
        nav.add_widget(gold_button('Search', on_press=lambda _: self._go('search'), size_hint_x=0.25))
        nav.add_widget(gold_button('Logout', on_press=self.do_logout, danger=True, size_hint_x=0.25))
        root.add_widget(nav)

        # Folder list
        self.scroll = ScrollView()
        self.list = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(8))
        self.list.bind(minimum_height=self.list.setter('height'))
        self.scroll.add_widget(self.list)
        root.add_widget(self.scroll)

        # Add folder button
        root.add_widget(gold_button('+ Create Folder', on_press=self._add_folder,
                                    size_hint_y=None, height=dp(48)))
        self.add_widget(root)

    def load(self):
        app = App.get_running_app()
        folders = app.api.get_folders()
        # Only top-level folders
        top = [f for f in folders if f['parent_id'] is None]
        self.list.clear_widgets()
        if not top:
            self.list.add_widget(gold_label('No folders. Create one below.', size=14))
            return
        for f in sorted(top, key=lambda x: x['name'].lower()):
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
            btn = Button(text=f"📁 {f['name']}", background_color=BG2, color=GOLD,
                         font_size=dp(15), size_hint_x=0.75)
            fid = f['id']
            btn.bind(on_press=lambda _, fid=fid, name=f['name']: self._open(fid, name))
            del_btn = gold_button('✕', danger=True, size_hint_x=0.25)
            del_btn.bind(on_press=lambda _, fid=fid, name=f['name']: self._confirm_delete(fid, name))
            row.add_widget(btn)
            row.add_widget(del_btn)
            self.list.add_widget(row)

    def _open(self, fid, name):
        s = self.manager.get_screen('folder')
        s.folder_id = fid
        s.folder_name = name
        s.load()
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'folder'

    def _add_folder(self, _):
        self.manager.get_screen('add_folder').parent_id = None
        self.manager.get_screen('add_folder').back_screen = 'folders'
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'add_folder'

    def _confirm_delete(self, fid, name):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=f'Delete "{name}" and all its contents?', color=GOLD))
        btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(44))
        yes = gold_button('Yes, Delete', danger=True)
        no = gold_button('Cancel')
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        popup = Popup(title='Confirm Delete', content=content,
                      size_hint=(0.85, 0.4), background_color=BG2, title_color=GOLD)
        yes.bind(on_press=lambda _: self._do_delete(fid, popup))
        no.bind(on_press=popup.dismiss)
        popup.open()

    def _do_delete(self, fid, popup):
        popup.dismiss()
        App.get_running_app().api.delete_folder(fid)
        self.load()

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = screen

    def do_logout(self, _):
        App.get_running_app().api.logout()
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'login'


class FolderScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.folder_id = None
        self.folder_name = ''
        self.root_layout = BoxLayout(orientation='vertical')

        nav = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(6), spacing=dp(6))
        self.back_btn = gold_button('← Back', on_press=self._back, size_hint_x=0.3)
        self.title_lbl = Label(text='', color=GOLD, bold=True, font_size=dp(16))
        nav.add_widget(self.back_btn)
        nav.add_widget(self.title_lbl)
        self.root_layout.add_widget(nav)

        self.scroll = ScrollView()
        self.list = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(8))
        self.list.bind(minimum_height=self.list.setter('height'))
        self.scroll.add_widget(self.list)
        self.root_layout.add_widget(self.scroll)

        add_btn = gold_button('+ Add Note', on_press=self._add_note,
                              size_hint_y=None, height=dp(48))
        self.root_layout.add_widget(add_btn)
        self.add_widget(self.root_layout)

    def load(self):
        self.title_lbl.text = f'📁 {self.folder_name}'
        app = App.get_running_app()
        notes = app.api.get_folder_notes(self.folder_id)
        self.list.clear_widgets()
        if not notes:
            self.list.add_widget(gold_label('No notes. Add one below.', size=14))
            return
        for n in notes:
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
            btn = Button(text=n['key'], background_color=BG2, color=GOLD,
                         font_size=dp(14), size_hint_x=0.75, halign='left',
                         text_size=(None, None))
            nid = n['id']
            btn.bind(on_press=lambda _, nid=nid: self._open_note(nid))
            del_btn = gold_button('✕', danger=True, size_hint_x=0.25)
            del_btn.bind(on_press=lambda _, nid=nid, name=n['key']: self._confirm_delete(nid, name))
            row.add_widget(btn)
            row.add_widget(del_btn)
            self.list.add_widget(row)

    def _open_note(self, nid):
        s = self.manager.get_screen('edit_note')
        s.folder_id = self.folder_id
        s.load(nid)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'edit_note'

    def _add_note(self, _):
        s = self.manager.get_screen('add_note')
        s.folder_id = self.folder_id
        s.clear()
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'add_note'

    def _confirm_delete(self, nid, name):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=f'Delete "{name}"?', color=GOLD))
        btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(44))
        yes = gold_button('Yes, Delete', danger=True)
        no = gold_button('Cancel')
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        popup = Popup(title='Confirm Delete', content=content,
                      size_hint=(0.85, 0.35), background_color=BG2, title_color=GOLD)
        yes.bind(on_press=lambda _: self._do_delete(nid, popup))
        no.bind(on_press=popup.dismiss)
        popup.open()

    def _do_delete(self, nid, popup):
        popup.dismiss()
        App.get_running_app().api.delete_note(nid)
        self.load()

    def _back(self, _):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'folders'
        self.manager.get_screen('folders').load()


class AddFolderScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parent_id = None
        self.back_screen = 'folders'
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
        layout.add_widget(gold_label('Create Folder', size=20, bold=True))
        layout.add_widget(gold_label('Folder Name'))
        self.name = gold_input(hint_text='Enter folder name')
        layout.add_widget(self.name)
        self.error = Label(text='', color=RED, size_hint_y=None, height=dp(24))
        layout.add_widget(self.error)
        layout.add_widget(gold_button('Create', on_press=self.do_create))
        layout.add_widget(gold_button('Cancel', on_press=self._cancel))
        layout.add_widget(Label())
        self.add_widget(layout)

    def do_create(self, _):
        name = self.name.text.strip()
        if not name:
            self.error.text = 'Name required'
            return
        ok = App.get_running_app().api.create_folder(name, self.parent_id)
        if ok:
            self.name.text = ''
            self.error.text = ''
            self._cancel(None)
        else:
            self.error.text = 'Failed to create folder'

    def _cancel(self, _):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = self.back_screen
        self.manager.get_screen(self.back_screen).load()


class AddNoteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.folder_id = None
        layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        nav = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        nav.add_widget(gold_button('← Back', on_press=self._cancel, size_hint_x=0.3))
        nav.add_widget(Label(text='Add Note', color=GOLD, bold=True, font_size=dp(16)))
        layout.add_widget(nav)

        layout.add_widget(gold_label('Title'))
        self.key = gold_input(hint_text='Note title')
        layout.add_widget(self.key)

        layout.add_widget(gold_label('Description (optional)'))
        self.desc = gold_input(hint_text='Short description')
        layout.add_widget(self.desc)

        layout.add_widget(gold_label('Contents'))
        self.value = TextInput(
            multiline=True, background_color=BG2, foreground_color=GOLD,
            cursor_color=GOLD, font_size=dp(13), size_hint_y=1
        )
        layout.add_widget(self.value)

        self.error = Label(text='', color=RED, size_hint_y=None, height=dp(24))
        layout.add_widget(self.error)
        layout.add_widget(gold_button('Add Note', on_press=self.do_add,
                                      size_hint_y=None, height=dp(48)))
        self.add_widget(layout)

    def clear(self):
        self.key.text = ''
        self.desc.text = ''
        self.value.text = ''
        self.error.text = ''

    def do_add(self, _):
        key = self.key.text.strip()
        value = self.value.text.strip()
        if not key or not value:
            self.error.text = 'Title and contents required'
            return
        ok, err = App.get_running_app().api.create_note(self.folder_id, key, value, self.desc.text[:255])
        if ok:
            self.clear()
            self._cancel(None)
        else:
            self.error.text = err or 'Failed to create note'

    def _cancel(self, _):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'folder'
        self.manager.get_screen('folder').load()


class EditNoteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.note_id = None
        self.folder_id = None
        layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        nav = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        nav.add_widget(gold_button('← Back', on_press=self._back, size_hint_x=0.3))
        nav.add_widget(Label(text='Edit Note', color=GOLD, bold=True, font_size=dp(16)))
        nav.add_widget(gold_button('Delete', on_press=self._confirm_delete,
                                   danger=True, size_hint_x=0.25))
        layout.add_widget(nav)

        layout.add_widget(gold_label('Title'))
        self.key = gold_input()
        layout.add_widget(self.key)

        layout.add_widget(gold_label('Description (optional)'))
        self.desc = gold_input()
        layout.add_widget(self.desc)

        layout.add_widget(gold_label('Contents'))
        self.value = TextInput(
            multiline=True, background_color=BG2, foreground_color=GOLD,
            cursor_color=GOLD, font_size=dp(13), size_hint_y=1
        )
        layout.add_widget(self.value)

        self.error = Label(text='', color=RED, size_hint_y=None, height=dp(24))
        layout.add_widget(self.error)
        layout.add_widget(gold_button('Save', on_press=self.do_save,
                                      size_hint_y=None, height=dp(48)))
        self.add_widget(layout)

    def load(self, nid):
        self.note_id = nid
        note = App.get_running_app().api.get_note(nid)
        if note:
            self.key.text = note['key']
            self.desc.text = note.get('description', '')
            self.value.text = note['value']
            self.folder_id = note['folder_id']
            self.error.text = ''
        else:
            self.error.text = 'Failed to load note'

    def do_save(self, _):
        key = self.key.text.strip()
        value = self.value.text.strip()
        if not key or not value:
            self.error.text = 'Title and contents required'
            return
        ok = App.get_running_app().api.update_note(
            self.note_id, key, value, self.folder_id, self.desc.text[:255])
        if ok:
            self._back(None)
        else:
            self.error.text = 'Failed to save'

    def _confirm_delete(self, _):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=f'Delete "{self.key.text}"?', color=GOLD))
        btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(44))
        yes = gold_button('Yes, Delete', danger=True)
        no = gold_button('Cancel')
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        popup = Popup(title='Confirm Delete', content=content,
                      size_hint=(0.85, 0.35), background_color=BG2, title_color=GOLD)
        yes.bind(on_press=lambda _: self._do_delete(popup))
        no.bind(on_press=popup.dismiss)
        popup.open()

    def _do_delete(self, popup):
        popup.dismiss()
        App.get_running_app().api.delete_note(self.note_id)
        self._back(None)

    def _back(self, _):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'folder'
        self.manager.get_screen('folder').load()


class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        nav = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        nav.add_widget(gold_button('← Back', on_press=self._back, size_hint_x=0.3))
        nav.add_widget(Label(text='Search', color=GOLD, bold=True, font_size=dp(16)))
        layout.add_widget(nav)

        search_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.query = gold_input(hint_text='Search notes...')
        search_row.add_widget(self.query)
        search_row.add_widget(gold_button('Go', on_press=self.do_search, size_hint_x=0.25))
        layout.add_widget(search_row)

        self.scroll = ScrollView()
        self.results = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(4))
        self.results.bind(minimum_height=self.results.setter('height'))
        self.scroll.add_widget(self.results)
        layout.add_widget(self.scroll)
        self.add_widget(layout)

    def do_search(self, _):
        q = self.query.text.strip()
        if not q:
            return
        notes = App.get_running_app().api.search(q)
        self.results.clear_widgets()
        if not notes:
            self.results.add_widget(gold_label('No matches.', size=14))
            return
        for n in notes:
            btn = Button(text=f"{n['key']}  ({n['updated_at']})",
                         background_color=BG2, color=GOLD,
                         font_size=dp(13), size_hint_y=None, height=dp(48))
            nid = n['id']
            btn.bind(on_press=lambda _, nid=nid: self._open(nid))
            self.results.add_widget(btn)

    def _open(self, nid):
        s = self.manager.get_screen('edit_note')
        s.load(nid)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'edit_note'

    def _back(self, _):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'folders'


# --- App ---

class EvernothingApp(App):
    def build(self):
        self.api = APIClient()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(FoldersScreen(name='folders'))
        sm.add_widget(FolderScreen(name='folder'))
        sm.add_widget(AddFolderScreen(name='add_folder'))
        sm.add_widget(AddNoteScreen(name='add_note'))
        sm.add_widget(EditNoteScreen(name='edit_note'))
        sm.add_widget(SearchScreen(name='search'))
        return sm

    def get_application_name(self):
        return 'EverNothing'


if __name__ == '__main__':
    EvernothingApp().run()
