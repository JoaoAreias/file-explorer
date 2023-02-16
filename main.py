"""Simple folder explorer GUI using kivy. From the selected folder,
it shows the files and subfolders in is as well as the size of the
files and folders.
"""
import os
import logging

from functools import cache

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@cache
def get_directory_size(path):
    total_size = 0
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)

        total_size = 0
        for item in os.listdir(path):
            total_size += get_directory_size(os.path.join(path, item))
    except Exception as e:
        logger.error('Error getting size of %s: %s' % (path, e))
    return total_size


class FileListView(FileChooserListView):
    def __init__(self, **kwargs):
        super(FileListView, self).__init__(**kwargs)
        self.bind(on_entry_added=self.update_entry)

    def format_size(self, size):
        """Formats the size of the file or folder."""
        if size < 1024:
            return str(size) + ' B'
        elif size < 1024**2:
            return f"{size/1024:.2f} KB"
        elif size < 1024**3:
            return f"{size/1024**2:.2f} MB"
        else:
            return f"{size/1024**3:.2f} GB"


    def update_entry(self, instance, entry, *args):
        """Updates the size of the file or folder."""
        if os.path.isdir(entry.path):
            # Skip if folder is protected
            if not os.access(entry.path, os.W_OK):
                return

            print(f'Computing size of folder {entry.path}')
            box_layout = entry.children[0]
            size_label = box_layout.children[0]
            size_label.text = self.format_size(get_directory_size(entry.path))

class FolderExplorer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        # Change folder menu
        self.folder_name = TextInput(text='C:\\Users\\', multiline=False)
        self.select_folder_button = Button(text='Select Folder')
        self.refresh_button = Button(text='Refresh')
        
        self.input_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.05))
        self.input_layout.add_widget(self.folder_name)
        self.input_layout.add_widget(self.select_folder_button)
        self.input_layout.add_widget(self.refresh_button)

        # File list with folder sizes
        self.file_list_view = FileListView()
        self.file_list_view.bind(path=self.update_text_input)

        # Update screen with final layout
        layout.add_widget(self.input_layout)
        layout.add_widget(self.file_list_view)

        return layout

    def on_start(self):
        self.select_folder_button.bind(on_press=self.select_folder)
        self.refresh_button.bind(on_press=self.refresh)

    def select_folder(self, instance):
        """Selects the folder and updates the file list."""
        self.file_list_view.path = self.folder_name.text
        self.file_list_view._update_files()

    def update_text_input(self, *args):
        """Updates the text input with the current folder."""
        self.folder_name.text = self.file_list_view.path

    def refresh(self, *args):
        """Invalidates the cache and refreshes the file list."""
        get_directory_size.cache_clear()
        self.file_list_view._update_files()

if __name__ == '__main__':
    FolderExplorer().run()