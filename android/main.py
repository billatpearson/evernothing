# Main Python file for the Evernothing Android app using Kivy.

# --- App Structure ---
# 1. Login Screen: The initial screen for user authentication.
# 2. Main Screen: After login, this screen will display the user's folders and recent notes.
# 3. Folder Screen: Displays the contents of a selected folder (notes and subfolders).
# 4. Note Screen: Displays the content of a selected note, with options to edit or delete.
# 5. Add/Edit Note Screen: A screen for creating or editing a note.
# 6. Admin Screen: For user management.

# --- Kivy Implementation Plan ---
# - Use Kivy's ScreenManager to manage the different screens of the app.
# - Use Kivy's networking capabilities to communicate with the existing Flask backend.
# - Replicate the UI style (black background, gold text) as much as possible.

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text='Username'))
        self.username = TextInput(multiline=False)
        layout.add_widget(self.username)
        layout.add_widget(Label(text='Password'))
        self.password = TextInput(password=True, multiline=False)
        layout.add_widget(self.password)
        layout.add_widget(Button(text='Login'))
        layout.add_widget(Button(text='Register'))
        self.add_widget(layout)

class EvernothingApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        return sm

if __name__ == '__main__':
    EvernothingApp().run()
