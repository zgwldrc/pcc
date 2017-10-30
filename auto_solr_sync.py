#!/usr/bin/env python3
import pathlib
import sys
import os
import logging
import inotify.constants as m_ic
import inotify
import subprocess
import threading
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError
import daemon
import argparse


sys.path.insert(0, str(pathlib.Path('./mylib')))
import myinotify as m_mi

_LOGGER = logging.getLogger(__name__)
_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
def _configure_logging(loglevel=logging.INFO):
    _LOGGER.setLevel(loglevel)

    h = logging.FileHandler('/var/log/autosolr.log')

    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    h.setFormatter(formatter)

    _LOGGER.addHandler(h)

def solr_core_reload(host,port,core):
    '''针对运行中的solr服务，当核心schema文件发生变动就reload核心
    '''
    query = {
        'wt': 'json',
        'action': 'RELOAD',
        'core': core
    }
    url = 'http://' + host + ':' + port + '/solr/admin/cores?' + urlencode(query)

    _LOGGER.info('we are sending request to %s ...' % url)
    try:

        with urlopen(url) as resp:
            _LOGGER.info('response from %s \n%s',url, resp.read().decode())
    except ConnectionRefusedError as e:
        _LOGGER.exception(e)
    except URLError as e:
        _LOGGER.exception(e)
    

def solr_docker_build(core):
    '''针对solr的docker镜像进行重新构建
       目前专用于192.168.1.234
    ''' 
    output = subprocess.check_output('ssh 192.168.1.234 "cd /home/docker/dockerbuild/02.dockerbuild-test/09.xwkj-solrautotest-dockerbuild/ && ./build.sh"', shell=True)
    _LOGGER.info('ssh to 192.168.1.234 exec docker build solr\n' + output.decode())
    

_CALLBACK_REGISTRY = {
    '/home/docker/test/solr/': lambda core: solr_core_reload('192.168.1.158', '30001', core), 
    #'/home/docker/testbranch/solr/': lambda core: solr_core_reload('192.168.1.158', '30011', core), 
    '192.168.1.188:/home/bufan/test/solr/': lambda core: solr_core_reload('192.168.1.188', '8983', core), 
    '192.168.1.234:/home/docker/dockerbuild/02.dockerbuild-test/09.xwkj-solrautotest-dockerbuild/solr/': solr_docker_build
}

def event_handler(event, rsync_dest_dir):
    '''处理来自inotify的事件
       需要注意的是inotify的event中f_path,f_name类型为bytes
    '''
    header, e_type, f_path, f_name = event
    full_path = os.path.join(f_path, f_name)
    logformat = '%(thread)s \n同步到：%(rsync_to)s\n事件类型：%(e_type)s\n文件路径：%(file_path)s\n%(rsync_output)s'
    
    command_exec = None
    callback = None
    core = None
    # 针对目录操作的监控
    if header.mask & inotify.constants.IN_CREATE and header.mask & inotify.constants.IN_ISDIR:
        command_exec = ['rsync', '-avR', full_path.decode(), rsync_dest_dir]
    elif header.mask & inotify.constants.IN_CLOSE_WRITE:
        command_exec = ['rsync', '-avR', full_path.decode(), rsync_dest_dir]
        if f_name == b'schema.xml':
            core = pathlib.PurePath(f_path.decode()).parent.stem
            callback = _CALLBACK_REGISTRY[rsync_dest_dir]
            
    elif header.mask & (inotify.constants.IN_DELETE | inotify.constants.IN_MOVED_TO):
        command_exec = ['rsync', '-avR', '--delete', '--exclude=data',str(pathlib.PurePath(full_path.decode()).parent), rsync_dest_dir]

    if command_exec:
        rsync_output = subprocess.check_output(command_exec).decode()

        logoutput = logformat % {'thread': threading.current_thread(),
                             'rsync_to': rsync_dest_dir,
                             'e_type': e_type, 
                             'file_path': full_path.decode(),
                             'rsync_output': rsync_output} 
        _LOGGER.info(logoutput)
    
    if callback:
        callback(core)

    
    
if __name__ == '__main__':    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--debug', action='store_true')
    argparser.add_argument('-f', '--foreground', action='store_true')
    args = argparser.parse_args()
    
    
    def main():
        if args.debug:
            _configure_logging(loglevel=logging.DEBUG)
        else:
            _configure_logging(loglevel=logging.INFO)
        watching_dir = '/home/kuang/solr'
        ddir_list = [ddir for ddir in _CALLBACK_REGISTRY]
        os.chdir(watching_dir)
        mi = m_mi.MyInotify(watch_dir='.', exclude=r'\w+/data|configsets|.*\.swp?x?$|.*~$', mask=(m_ic.IN_CREATE|\
                                  m_ic.IN_DELETE|\
                                  m_ic.IN_CLOSE_WRITE|\
                                  m_ic.IN_MOVE))
        try:
            for e in mi.event_gen():
                t_list = []
                for ddir in ddir_list:
                    t=threading.Thread(target=event_handler, args=(e, ddir))
                    t.start()
                    _LOGGER.debug('线程%s启动' % t.name)
                    t_list.append(t)
                    
                _LOGGER.debug('当前活动线程数量：%s' % threading.active_count())
    
                for t in t_list:
                    t.join()
                    _LOGGER.debug('线程%s结束' % t.name)
    
                _LOGGER.debug('当前活动线程数量：%s' % threading.active_count())
        finally:
            for wd in mi.runtimeq:
                mi.remove_watch(wd)
    if args.foreground:
        main()
    else:
        with daemon.DaemonContext():
            main()
