#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This is a saltstack custom modules writing in python2
SORT_BY = {
    'mem': 2,
    'cpu': 4
}

def _usage(n=10,header=True,sort_by="mem"):
    
    header_cmd = "|awk 'BEGIN{print \"process_id mem_usage mem% cpu% container_name\"}{print $0}'"
    cmd = "tmp1=$(mktemp) && tmp2=$(mktemp) \
    && docker ps -q | xargs docker inspect -f '{{.State.Pid}} {{.Name}}' | \
    awk '{sub(\"/\",\"\",$2);print $0}' | sort -k1 -n | tee $tmp1 | \
    awk '{print $1}' |xargs ps -o pid=,rss=,pmem=,pcpu= -p > $tmp2 && join $tmp2 $tmp1 | \
    sort -k%s -nr | head -n %s %s | column -t && rm -f $tmp2 $tmp1" % (SORT_BY[sort_by],str(n), header_cmd if header else "")
    
    return __salt__['cmd.shell'](cmd)

def mem(n=10,header=True):
    """
    return top nth docker container which take up the mem usage for this minion
    CLI Example:
        salt '*' container_rank_by.mem [n] [header=True]
    """
    return _usage(n,header,"mem")

def cpu(n=10,header=True):
    """
    return top nth docker container which take up the mem usage for this minion
    CLI Example:
        salt '*' container_rank_by.cpu [n] [header=True]
    """
    return _usage(n,header,"cpu")


    


