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
    def __init__(self, size_provider=get_directory_size, **kwargs):
        super(FileListView, self).__init__(**kwargs)
        self.size_provider = size_provider
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
            size_label.text = self.format_size(self.size_provider(entry.path))

class ToolbarWidget(BoxLayout):
    def __init__(self, on_select=None, on_refresh=None, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('size_hint', (1, 0.05))
        super().__init__(**kwargs)

        self.folder_name = TextInput(text='C:\\Users\\', multiline=False)
        select_button = Button(text='Select Folder')
        refresh_button = Button(text='Refresh')

        if on_select:
            select_button.bind(on_press=lambda _: on_select(self.folder_name.text))
        if on_refresh:
            refresh_button.bind(on_press=lambda _: on_refresh())

        self.add_widget(self.folder_name)
        self.add_widget(select_button)
        self.add_widget(refresh_button)

    @property
    def path(self):
        return self.folder_name.text

    @path.setter
    def path(self, value):
        self.folder_name.text = value


class FolderExplorer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        self.toolbar = ToolbarWidget(
            on_select=self.select_folder,
            on_refresh=self.refresh,
        )
        self.file_list_view = FileListView(size_provider=get_directory_size)
        self.file_list_view.bind(path=self.update_text_input)

        layout.add_widget(self.toolbar)
        layout.add_widget(self.file_list_view)

        return layout

    def select_folder(self, path):
        """Selects the folder and updates the file list."""
        self.file_list_view.path = path
        self.file_list_view._update_files()

    def update_text_input(self, *args):
        """Updates the text input with the current folder."""
        self.toolbar.path = self.file_list_view.path

    def refresh(self):
        """Invalidates the cache and refreshes the file list."""
        get_directory_size.cache_clear()
        self.file_list_view._update_files()

if __name__ == '__main__':
    FolderExplorer().run()