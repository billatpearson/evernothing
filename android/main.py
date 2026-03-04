"""
EverNothing Android Application
Kivy-based mobile interface for EverNothing note-taking app

Installation (Termux):
  pkg install python
  pip install kivy requests
  python main.py

Configuration:
  Set SERVER_URL to your Flask backend (default: http://127.0.0.1:5000)
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
import requests
import os

SERVER_URL = os.environ.get('EVERNOTHING_SERVER', 'http://127.0.0.1:5000')

# Color scheme: black background, gold text, red accents
Window.clearcolor = (0, 0, 0, 1)

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = SERVER_URL
    
    def login(self, username, password):
        try:
            r = self.session.post(f'{self.base_url}/login', 
                                 data={'username': username, 'password': password},
                                 allow_redirects=False)
            return r.status_code == 302
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def register(self, username, password, email):
        try:
            r = self.session.post(f'{self.base_url}/register',
                                 data={'username': username, 'password': password, 'email': email},
                                 allow_redirects=False)
            return r.status_code == 302
        except Exception as e:
            print(f"Register error: {e}")
            return False
    
    def get_folders(self):
        try:
            r = self.session.get(f'{self.base_url}/')
            if 'Login' in r.text:
                return None
            # Parse HTML for folders (simplified)
            folders = []
            for line in r.text.split('\n'):
                if '/folder/' in line and '<a href=' in line:
                    parts = line.split('>')
                    if len(parts) > 1:
                        name = parts[1].split('<')[0]
                        fid = line.split('/folder/')[1].split('"')[0]
                        folders.append({'id': fid, 'name': name})
            return folders
        except Exception as e:
            print(f"Get folders error: {e}")
            return None
    
    def get_folder_contents(self, fid):
        try:
            r = self.session.get(f'{self.base_url}/folder/{fid}')
            notes, subfolders = [], []
            for line in r.text.split('\n'):
                if '/edit/' in line and '<a href=' in line:
                    name = line.split('>')[1].split('<')[0]
                    nid = line.split('/edit/')[1].split('"')[0]
                    notes.append({'id': nid, 'name': name})
                elif '/folder/' in line and '<a href=' in line and f'/folder/{fid}' not in line:
                    name = line.split('>')[1].split('<')[0]
                    sfid = line.split('/folder/')[1].split('"')[0]
                    if sfid != fid:
                        subfolders.append({'id': sfid, 'name': name})
            return {'notes': notes, 'subfolders': subfolders}
        except Exception as e:
            print(f"Get folder error: {e}")
            return {'notes': [], 'subfolders': []}
    
    def create_folder(self, name, parent_id=None):
        try:
            url = f'{self.base_url}/folder/add' if not parent_id else f'{self.base_url}/folder/{parent_id}/add_folder'
            r = self.session.post(url, data={'name': name}, allow_redirects=False)
            return r.status_code == 302
        except Exception as e:
            print(f"Create folder error: {e}")
            return False
    
    def create_note(self, fid, note, content):
        try:
            r = self.session.post(f'{self.base_url}/add/{fid}',
                                 data={'note': note, 'content': content},
                                 allow_redirects=False)
            return r.status_code == 302
        except Exception as e:
            print(f"Create note error: {e}")
            return False
    
    def logout(self):
        try:
            self.session.get(f'{self.base_url}/logout')
        except:
            pass

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='EverNothing', font_size=32, color=(1, 0.84, 0, 1)))
        layout.add_widget(Label(text='Username:', color=(1, 0.84, 0, 1)))
        self.username = TextInput(multiline=False, background_color=(0.1, 0.1, 0.1, 1), 
                                  foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.username)
        
        layout.add_widget(Label(text='Password:', color=(1, 0.84, 0, 1)))
        self.password = TextInput(password=True, multiline=False, 
                                  background_color=(0.1, 0.1, 0.1, 1),
                                  foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.password)
        
        self.error = Label(text='', color=(1, 0, 0, 1))
        layout.add_widget(self.error)
        
        btn_layout = BoxLayout(spacing=10)
        login_btn = Button(text='Login', background_color=(1, 0, 0, 1), 
                          color=(1, 0.84, 0, 1))
        login_btn.bind(on_press=self.do_login)
        btn_layout.add_widget(login_btn)
        
        register_btn = Button(text='Register', background_color=(1, 0, 0, 1),
                             color=(1, 0.84, 0, 1))
        register_btn.bind(on_press=self.show_register)
        btn_layout.add_widget(register_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def do_login(self, instance):
        app = App.get_running_app()
        if app.api.login(self.username.text, self.password.text):
            app.root.current = 'folders'
            app.root.get_screen('folders').load_folders()
        else:
            self.error.text = 'Invalid username or password'
    
    def show_register(self, instance):
        self.manager.current = 'register'

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Register', font_size=24, color=(1, 0.84, 0, 1)))
        layout.add_widget(Label(text='Username:', color=(1, 0.84, 0, 1)))
        self.username = TextInput(multiline=False, background_color=(0.1, 0.1, 0.1, 1),
                                  foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.username)
        
        layout.add_widget(Label(text='Email:', color=(1, 0.84, 0, 1)))
        self.email = TextInput(multiline=False, background_color=(0.1, 0.1, 0.1, 1),
                               foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.email)
        
        layout.add_widget(Label(text='Password:', color=(1, 0.84, 0, 1)))
        self.password = TextInput(password=True, multiline=False,
                                  background_color=(0.1, 0.1, 0.1, 1),
                                  foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.password)
        
        self.error = Label(text='', color=(1, 0, 0, 1))
        layout.add_widget(self.error)
        
        btn_layout = BoxLayout(spacing=10)
        create_btn = Button(text='Create', background_color=(1, 0, 0, 1),
                           color=(1, 0.84, 0, 1))
        create_btn.bind(on_press=self.do_register)
        btn_layout.add_widget(create_btn)
        
        cancel_btn = Button(text='Cancel', background_color=(1, 0, 0, 1),
                           color=(1, 0.84, 0, 1))
        cancel_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        btn_layout.add_widget(cancel_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def do_register(self, instance):
        app = App.get_running_app()
        if app.api.register(self.username.text, self.password.text, self.email.text):
            self.manager.current = 'login'
        else:
            self.error.text = 'Username already exists'

class FoldersScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint_y=0.1, spacing=10)
        header.add_widget(Label(text='Folders', font_size=24, color=(1, 0.84, 0, 1)))
        logout_btn = Button(text='Logout', size_hint_x=0.3, background_color=(1, 0, 0, 1),
                           color=(1, 0.84, 0, 1))
        logout_btn.bind(on_press=self.do_logout)
        header.add_widget(logout_btn)
        self.layout.add_widget(header)
        
        self.scroll = ScrollView()
        self.folder_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.folder_list.bind(minimum_height=self.folder_list.setter('height'))
        self.scroll.add_widget(self.folder_list)
        self.layout.add_widget(self.scroll)
        
        add_btn = Button(text='Create Folder', size_hint_y=0.1, 
                        background_color=(1, 0, 0, 1), color=(1, 0.84, 0, 1))
        add_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'add_folder'))
        self.layout.add_widget(add_btn)
        
        self.add_widget(self.layout)
    
    def load_folders(self):
        app = App.get_running_app()
        folders = app.api.get_folders()
        self.folder_list.clear_widgets()
        
        if folders:
            for folder in folders:
                btn = Button(text=folder['name'], size_hint_y=None, height=50,
                           background_color=(0.1, 0.1, 0.1, 1), color=(1, 0.84, 0, 1))
                btn.bind(on_press=lambda x, fid=folder['id']: self.open_folder(fid))
                self.folder_list.add_widget(btn)
    
    def open_folder(self, fid):
        folder_screen = self.manager.get_screen('folder')
        folder_screen.folder_id = fid
        folder_screen.load_contents()
        self.manager.current = 'folder'
    
    def do_logout(self, instance):
        App.get_running_app().api.logout()
        self.manager.current = 'login'

class FolderScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.folder_id = None
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint_y=0.1, spacing=10)
        back_btn = Button(text='Back', size_hint_x=0.3, background_color=(1, 0, 0, 1),
                         color=(1, 0.84, 0, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'folders'))
        header.add_widget(back_btn)
        header.add_widget(Label(text='Folder', font_size=20, color=(1, 0.84, 0, 1)))
        self.layout.add_widget(header)
        
        self.scroll = ScrollView()
        self.content_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.content_list.bind(minimum_height=self.content_list.setter('height'))
        self.scroll.add_widget(self.content_list)
        self.layout.add_widget(self.scroll)
        
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        add_note_btn = Button(text='Add Note', background_color=(1, 0, 0, 1),
                             color=(1, 0.84, 0, 1))
        add_note_btn.bind(on_press=self.show_add_note)
        btn_layout.add_widget(add_note_btn)
        
        add_folder_btn = Button(text='Add Subfolder', background_color=(1, 0, 0, 1),
                               color=(1, 0.84, 0, 1))
        add_folder_btn.bind(on_press=self.show_add_subfolder)
        btn_layout.add_widget(add_folder_btn)
        self.layout.add_widget(btn_layout)
        
        self.add_widget(self.layout)
    
    def load_contents(self):
        app = App.get_running_app()
        contents = app.api.get_folder_contents(self.folder_id)
        self.content_list.clear_widgets()
        
        if contents['notes']:
            self.content_list.add_widget(Label(text='Notes:', color=(1, 0.84, 0, 1),
                                              size_hint_y=None, height=30))
            for note in contents['notes']:
                btn = Button(text=note['name'], size_hint_y=None, height=50,
                           background_color=(0.1, 0.1, 0.1, 1), color=(1, 0.84, 0, 1))
                self.content_list.add_widget(btn)
        
        if contents['subfolders']:
            self.content_list.add_widget(Label(text='Subfolders:', color=(1, 0.84, 0, 1),
                                              size_hint_y=None, height=30))
            for subfolder in contents['subfolders']:
                btn = Button(text=subfolder['name'], size_hint_y=None, height=50,
                           background_color=(0.1, 0.1, 0.1, 1), color=(1, 0.84, 0, 1))
                btn.bind(on_press=lambda x, fid=subfolder['id']: self.open_subfolder(fid))
                self.content_list.add_widget(btn)
    
    def open_subfolder(self, fid):
        self.folder_id = fid
        self.load_contents()
    
    def show_add_note(self, instance):
        add_note_screen = self.manager.get_screen('add_note')
        add_note_screen.folder_id = self.folder_id
        self.manager.current = 'add_note'
    
    def show_add_subfolder(self, instance):
        add_folder_screen = self.manager.get_screen('add_folder')
        add_folder_screen.parent_id = self.folder_id
        self.manager.current = 'add_folder'

class AddFolderScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parent_id = None
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Create Folder', font_size=24, color=(1, 0.84, 0, 1)))
        layout.add_widget(Label(text='Folder name:', color=(1, 0.84, 0, 1)))
        self.name = TextInput(multiline=False, background_color=(0.1, 0.1, 0.1, 1),
                             foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.name)
        
        btn_layout = BoxLayout(spacing=10)
        create_btn = Button(text='Create', background_color=(1, 0, 0, 1),
                           color=(1, 0.84, 0, 1))
        create_btn.bind(on_press=self.do_create)
        btn_layout.add_widget(create_btn)
        
        cancel_btn = Button(text='Cancel', background_color=(1, 0, 0, 1),
                           color=(1, 0.84, 0, 1))
        cancel_btn.bind(on_press=self.do_cancel)
        btn_layout.add_widget(cancel_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def do_create(self, instance):
        app = App.get_running_app()
        if app.api.create_folder(self.name.text, self.parent_id):
            self.name.text = ''
            if self.parent_id:
                self.manager.current = 'folder'
                self.manager.get_screen('folder').load_contents()
            else:
                self.manager.current = 'folders'
                self.manager.get_screen('folders').load_folders()
    
    def do_cancel(self, instance):
        self.name.text = ''
        self.manager.current = 'folder' if self.parent_id else 'folders'

class AddNoteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.folder_id = None
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Add Note', font_size=24, color=(1, 0.84, 0, 1)))
        layout.add_widget(Label(text='Note:', color=(1, 0.84, 0, 1)))
        self.note = TextInput(multiline=False, background_color=(0.1, 0.1, 0.1, 1),
                             foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.note)
        
        layout.add_widget(Label(text='Contents:', color=(1, 0.84, 0, 1)))
        self.content = TextInput(multiline=True, background_color=(0.1, 0.1, 0.1, 1),
                                foreground_color=(1, 0.84, 0, 1))
        layout.add_widget(self.content)
        
        self.error = Label(text='', color=(1, 0, 0, 1))
        layout.add_widget(self.error)
        
        btn_layout = BoxLayout(spacing=10, size_hint_y=0.15)
        add_btn = Button(text='Add', background_color=(1, 0, 0, 1),
                        color=(1, 0.84, 0, 1))
        add_btn.bind(on_press=self.do_add)
        btn_layout.add_widget(add_btn)
        
        cancel_btn = Button(text='Cancel', background_color=(1, 0, 0, 1),
                           color=(1, 0.84, 0, 1))
        cancel_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'folder'))
        btn_layout.add_widget(cancel_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def do_add(self, instance):
        if not self.note.text.strip() or not self.content.text.strip():
            self.error.text = 'Note and content cannot be empty'
            return
        
        app = App.get_running_app()
        if app.api.create_note(self.folder_id, self.note.text, self.content.text):
            self.note.text = ''
            self.content.text = ''
            self.error.text = ''
            self.manager.current = 'folder'
            self.manager.get_screen('folder').load_contents()
        else:
            self.error.text = 'Failed to create note'

class EvernothingApp(App):
    def build(self):
        self.api = APIClient()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(FoldersScreen(name='folders'))
        sm.add_widget(FolderScreen(name='folder'))
        sm.add_widget(AddFolderScreen(name='add_folder'))
        sm.add_widget(AddNoteScreen(name='add_note'))
        return sm

if __name__ == '__main__':
    EvernothingApp().run()
