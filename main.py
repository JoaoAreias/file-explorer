"""Simple folder explorer GUI using kivy. From the selected folder,
it shows the files and subfolders in is as well as the size of the
files and folders.
"""
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import cache

from kivy.app import App
from kivy.clock import Clock
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
        workers = max(1, (os.cpu_count() or 1) - 1)
        self._executor = ThreadPoolExecutor(max_workers=workers)
        self._pending_futures = []
        self._generation = 0
        self._size_cache = {}
        self._resorting = False
        self._default_sort_func = self.sort_func
        self.bind(on_entry_added=self.update_entry)

    def _update_files(self, *args, **kwargs):
        if not self._resorting:
            self._generation += 1
            for future in self._pending_futures:
                future.cancel()
            self._pending_futures.clear()
            self._size_cache.clear()
        super()._update_files(*args, **kwargs)

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
        if not os.path.isdir(entry.path):
            return

        box_layout = entry.children[0]
        size_label = box_layout.children[0]

        if entry.path in self._size_cache:
            size_label.text = self.format_size(self._size_cache[entry.path])
            return

        size_label.text = "..."
        path = entry.path
        generation = self._generation

        def compute():
            size = self.size_provider(path)
            self._size_cache[path] = size
            formatted = self.format_size(size)
            def update(dt):
                if self._generation == generation:
                    size_label.text = formatted
            Clock.schedule_once(update)

        self._pending_futures.append(self._executor.submit(compute))

    def set_sort(self, by_size):
        if by_size:
            self.sort_func = lambda files, fs: sorted(
                files, key=lambda f: self._size_cache.get(f, 0), reverse=True
            )
        else:
            self.sort_func = self._default_sort_func
        self._resorting = True
        self._update_files()
        self._resorting = False

class ToolbarWidget(BoxLayout):
    def __init__(self, on_select=None, on_refresh=None, on_sort=None, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('size_hint', (1, 0.05))
        super().__init__(**kwargs)

        self.folder_name = TextInput(text='C:\\Users\\', multiline=False)
        select_button = Button(text='Select Folder')
        refresh_button = Button(text='Refresh')
        self._sort_by_size = False
        self._sort_button = Button(text='Sort: Name')

        if on_select:
            select_button.bind(on_press=lambda _: on_select(self.folder_name.text))
        if on_refresh:
            refresh_button.bind(on_press=lambda _: on_refresh())
        if on_sort:
            def toggle_sort(_):
                self._sort_by_size = not self._sort_by_size
                self._sort_button.text = 'Sort: Size' if self._sort_by_size else 'Sort: Name'
                on_sort(self._sort_by_size)
            self._sort_button.bind(on_press=toggle_sort)

        self.add_widget(self.folder_name)
        self.add_widget(select_button)
        self.add_widget(refresh_button)
        self.add_widget(self._sort_button)

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
            on_sort=self.change_sort,
        )
        self.file_list_view = FileListView(size_provider=get_directory_size, show_hidden=True)
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

    def change_sort(self, by_size):
        self.file_list_view.set_sort(by_size)

    def refresh(self):
        """Invalidates the cache and refreshes the file list."""
        get_directory_size.cache_clear()
        self.file_list_view._update_files()

if __name__ == '__main__':
    FolderExplorer().run()