"""
    isort:skip_file
"""

import sys
import os
import time

import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet

from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

# from .lib import support

RECENT_ITEMS = 'RECENT_ITEMS'
RECENT_FILES = 'RECENT_FILES'
RECENT_FOLDERS = 'RECENT_FOLDERS'

RECENT_ITEMS_DIR = kpu.shell_known_folder_path('{AE50C081-EBD2-438A-8655-8A092E34987A}')

class RecentItems(kp.Plugin):

    _debug = True

    _recent_items = []
    _recent_files = []
    _recent_folders = []

    def __init__(self):
        super().__init__()

    def on_start(self):
        self.update_recent_items_list()

    def on_catalog(self):
        items = []

        items.append(self.create_item(
            data_bag=RECENT_ITEMS,
            category=kp.ItemCategory.KEYWORD,
            label='Recent Items',
            short_desc='Recent Items',
            target=RECENT_ITEMS_DIR,
            args_hint=kp.ItemArgsHint.ACCEPTED,
            # args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE,
        ))

        self.set_catalog(items + self._recent_items)


    def on_suggest(self, user_input, items_chain):

        if items_chain and items_chain[0].category() == kp.ItemCategory.KEYWORD:

            if items_chain[-1].data_bag() == RECENT_ITEMS:
                self.set_suggestions(self._recent_items, kp.Match.FUZZY, kp.Sort.NONE)

            if items_chain[-1].data_bag() == RECENT_FILES:
                self.set_suggestions(self._recent_items, kp.Match.FUZZY, kp.Sort.NONE)

            if items_chain[-1].data_bag() == RECENT_FOLDERS:
                self.set_suggestions(self._recent_items, kp.Match.FUZZY, kp.Sort.NONE)

        return

    def on_execute(self, item, action):
        if item.data_bag() == RECENT_ITEMS:
            kpu.explore_file(RECENT_ITEMS_DIR)
        else:
            kpu.execute_default_action(self, item, action)
            update_file_access_time(item.target())

    def on_activated(self):
        self.update_recent_items_list()

    def on_deactivated(self):
        pass

    def on_events(self, flags):
        pass

    def update_recent_items_list(self):
        file_items = []

        items = get_recent_items()
        for item in items:

            file_items.append(self.create_item(
                category=kp.ItemCategory.FILE,
                label=item['name'],
                short_desc=item['target_path'],
                target=item['source_path'],
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                # hit_hint=kp.ItemHitHint.KEEPALL
                hit_hint=kp.ItemHitHint.IGNORE,
            ))

        self._recent_items = file_items


# Returns contents of the recent items directory.
def get_recent_items():
    recent_files_dir = kpu.shell_known_folder_path(
        '{AE50C081-EBD2-438A-8655-8A092E34987A}'
    )

    items = []

    with os.scandir(recent_files_dir) as item:
        for entry in item:
            if entry.is_file():
                fullpath = os.path.join(recent_files_dir, entry.name)

                try:
                    link_props = kpu.read_link(fullpath)
                except OSError:
                    pass
                else:
                    link_target = link_props['target']

                    if not Path(link_target).name == '':
                        link_name = Path(link_target).name
                    else:
                        link_name = entry.name

                    if os.path.exists(link_target):
                        items.append({
                            'name': link_name,
                            'target_path': link_target,
                            'source_path': fullpath,
                            'access_time': os.path.getatime(fullpath),
                            'is_dir': os.path.isdir(link_target),
                        })

    items.sort(key=lambda x: x['access_time'], reverse=True)

    return items


def update_file_access_time(fullpath):
    access_time = time.time()
    modified_time = os.path.getmtime(fullpath)
    os.utime(fullpath, (access_time, modified_time))
