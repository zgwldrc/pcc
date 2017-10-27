#!/usr/bin/env python3
# xiayu
import argparse
import os
import logging
import pathlib
import re
import sys
import inotify
from inotify.adapters import Inotify

_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

_LOGGER = logging.getLogger(__name__)

def _configure_logging(loglevel=logging.INFO):
    _LOGGER.setLevel(loglevel)

    ch = logging.StreamHandler()

    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)

    _LOGGER.addHandler(ch)

class MyInotify(Inotify):
    def __init__(self, watch_dir='/tmp',exclude=None, mask=inotify.constants.IN_ALL_EVENTS):
        super(MyInotify, self).__init__()
        if exclude is not None:
            self.exclude = re.compile(exclude.encode())
            _LOGGER.debug('self.exclude is %s', self.exclude)
        self.initq = []
        self.mask = mask
        q = [pathlib.Path(watch_dir)]
        while q:
            current_path = q[0]
            del q[0]
            self.initq.append(bytes(current_path))
            for i in current_path.iterdir():
                if i.is_dir():
                    if (hasattr(self, 'exclude') and self.exclude.match(bytes(i))):
                        continue
                    q.append(i)
        _LOGGER.debug('init watching dirs %s',self.initq)
        
        
        self._load_tree()
        self.runtimeq = self.initq


    def _load_tree(self):
        for i in self.initq:
            self.add_watch(i, mask=self.mask)

    def event_gen(self):
        """This is a secondary generator that wraps the principal one, and 
        adds/removes watches as directories are added/removed.
        """

        for event in super(MyInotify, self).event_gen():
            if event is not None:
                (header, type_names, path, filename) = event
                
                full_path = os.path.join(path, filename)
                if hasattr(self, 'exclude') and self.exclude.match(full_path):
                    _LOGGER.debug('exclude %s', full_path)
                    _LOGGER.debug('in function event_gen() check if hasattr exclude ? %s', hasattr(self, 'exclude') or None)                  
                    _LOGGER.debug('in function event_gen() check if self.exclude: %s match  %s: %s', self.exclude, full_path, self.exclude.match(full_path) or None)
                    continue

                if header.mask & inotify.constants.IN_ISDIR:
                    if header.mask & (inotify.constants.IN_CREATE|inotify.constants.IN_MOVED_TO):
                        self.add_watch(full_path, mask=self.mask)
                        self.runtimeq.append(full_path)
                        _LOGGER.debug('current monitoring dirs: %s' % self.runtimeq)
                    elif header.mask & (inotify.constants.IN_DELETE|inotify.constants.IN_MOVED_FROM):
                        # The watch would've already been cleaned-up internally.
                        self.remove_watch(full_path, superficial=True)
                        self.runtimeq.remove(full_path)
                        _LOGGER.debug('current monitoring dirs: %s' % self.runtimeq)
                yield event

    def watch(self):
        for e in self.event_gen():
            _LOGGER.info(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('watch_dir', default='/tmp', help='which dir to monitoring, default to /tmp')
    parser.add_argument('-e', '--exclude', help='exclude re pattern')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode')
    args = parser.parse_args()
    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    _configure_logging(loglevel)

    ino = MyInotify(watch_dir=args.watch_dir, exclude=args.exclude, mask=(inotify.constants.IN_CREATE|\
                          inotify.constants.IN_DELETE|\
                          inotify.constants.IN_CLOSE_WRITE|\
                          inotify.constants.IN_MOVE))
    try:
        ino.watch()
    except KeyboardInterrupt:
        pass
    finally:
        for i in ino.runtimeq:
            ino.remove_watch(i)
