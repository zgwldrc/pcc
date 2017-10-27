#!/usr/bin/env python3
import pathlib
import sys
import os
import logging
import inotify.constants as m_ic
import inotify

sys.path.insert(0, str(pathlib.Path('.')))
import myinotify as m_mi

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
#_LOGGER = logging.getLogger(__name__)

watching_dir = '/home/kuang/solr'
os.chdir(watching_dir)
mi = m_mi.MyInotify(watch_dir='.', exclude='\w+/data|configsets|.*\.swp?x?$|.*~$', mask=(m_ic.IN_CREATE|\
                          m_ic.IN_DELETE|\
                          m_ic.IN_CLOSE_WRITE|\
                          m_ic.IN_MOVE))

def event_handler(event, rsync_dest_dir):
    header, e_type, f_path, f_name = event
    full_path = os.path.join(f_path, f_name)
    # 针对目录操作的监控
    if header.mask & inotify.constants.IN_CREATE and header.mask & inotify.constants.IN_ISDIR:
        command_exec = ['rsync', '-avR', full_path.decode(), rsync_dest_dir]
        logging.debug('目录: %s, 被创建了, 应执行指令- %s',full_path.decode(), ' '.join(command_exec))
    elif header.mask & inotify.constants.IN_CLOSE_WRITE:
        command_exec = ['rsync', '-avR', full_path.decode(), rsync_dest_dir]
        logging.debug('文件: %s, 被修改了, 应执行指令- %s',full_path.decode(), ' '.join(command_exec))
    elif header.mask & (inotify.constants.IN_DELETE | inotify.constants.IN_MOVED_TO):
        command_exec = ['rsync', '-avR', '--delete', '--exclude=data',str(pathlib.PurePath(full_path.decode()).parent), rsync_dest_dir]
        logging.debug('%s, 被删除了or move_to, 应执行指令- %s',full_path.decode(), ' '.join(command_exec))
    
try:
    for e in mi.event_gen():
        #_LOGGER.info(e)
        event_handler(e, '192.168.1.234:/tmp/abc')

finally:
    for wd in mi.runtimeq:
        mi.remove_watch(wd)
