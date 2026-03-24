# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

```bash
uv sync
```

## Running the App

```bash
uv run main.py
```

## Architecture

Single-file app (`main.py`) built on Kivy:

- `get_directory_size(path)` — recursive directory size calculator with `@functools.cache`. Cache persists for the app's lifetime and must be explicitly cleared via `cache_clear()`.
- `FileListView(FileChooserListView)` — overrides Kivy's file chooser to inject folder sizes into list entries via the `on_entry_added` event. Size labels are written directly into the entry's child widget tree (`entry.children[0].children[0]`).
- `FolderExplorer(App)` — top-level Kivy app. Wires up a path text input, a "Select Folder" button, and a "Refresh" button (which clears the cache and re-renders).

**Known limitation:** `get_directory_size` runs synchronously on the main thread, freezing the UI until all sizes are computed.
