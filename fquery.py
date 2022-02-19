import sys,os,re,json
from pathlib import Path
from datetime import datetime
import argparse

from rich.console import Console
from rich.traceback import install
from rich import inspect
install(show_locals=True,suppress=[])
console = Console()
show = console.print 

from util import *

def main():
    fq() 
    

def fq(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    param = parser.add_argument
    param ('--query','-q',
        metavar='condition'.upper(),
        nargs=3,
        action='append',
        default=[]
    )
    param ('--from', 
        dest='from_dir',
        action='append',
        default=[],
        help='default CWD'
    )
    param ('--text',
        action='append',
        default=[],
        help='alias -q text has <TEXT>'
    )
    (opts,args) = parser.parse_known_args(argv)
    qs = [
        *opts.query,
        *pre_args(args),
        *pre_opts(opts)
    ]

    dir = opts.from_dir or ['.']
    
    
    show(qs)
    for entry in query(qs,dir):
        show(entry.path)

def pre_opts(opts):
    qs = []
    for text in opts.text:
        qs.append(['text','has',text])

    return qs

def pre_args(args):
    qs = []
    for s in args:
        by = 'name'
        op ='has'
        if re.fullmatch(r'[\+\-]?\d[\d\.]?[TGMK]i?b?[\-\+]?\=?$',s,re.I):
            by = 'size'
            (s,op) = split_op(s,'le')
            
        elif re.fullmatch(r'[\+\-\.\d]+([ydhs].*|min(ute)?|(mo)?n(th)?)[\-\+]?\=?$',s,re.I):
            by = 'mtime'
            (s,op) = split_op(s,'re')



        elif s[0] == '/':
            s = s[1:]
            if s[-1] == '/':
                s = s[:-1]
                op ='find'

        elif s[0] == '.':
            op ='prefix'
        elif s[-1] == '.':
            op ='suffix'

        qs.append([by,op,s])


    return qs

def split_op(s,default) -> (str,str):
    'split 1k+ 2s+ 10m-= ... '
    has_op = re.fullmatch(r'.*?([\+\-\=]+)$',s)
    if has_op:
        op = has_op.group(1)
        s = s[:-len(op)]
    else:
        op = default
    show(s,op)
    return (s,op)

        
def test (
        by: str,
        op: str,
        iv: str,
        entry:os.DirEntry
    ) -> bool:

    rv = None
    if by == 'name':
        rv = entry.name
    elif by == 'type':
        rv = ''
        #TODO
    elif by == 'text':
        try:
            rv = read(entry.path)
        except:
            return False
    elif by in [
        'time',
        'atime',
        #'atime_ns',
        'blksize',
        'blocks',
        'ctime',
        #'ctime_ns',
        'dev',
        'gid',
        'ino',
        'mode',
        'mtime',
        #'mtime_ns',
        'nlink',
        'rdev',
        'size',
        'uid',
    ]:
        if by == 'time':
            by = 'mtime'

        stat = entry.stat()
        rv = stat.__getattribute__('st_'+by)

        if by in ['size','blocksize']:
            iv = parse_size(iv)
        elif by in ['mtime','ctime','atime']:
            iv = parse_time(iv)

    if rv == None:
        return False

    iv = type(rv)(iv)
    if op == 'in':
        return rv in iv
    elif op == 'has':
        return iv in rv
    elif op in ['lt','-']:
        return rv < iv
    elif op in ['rt','+']:
        return rv > iv
    elif op in ['le','-=']:
        return rv <= iv
    elif op in ['re','+=']:
        return rv >= iv
    
    return False
    

def query (
        qs:'[(by,op,iv), ...]',
        dir=['.']
    ):
    if type(dir) in [list,tuple]:
        for d in dir:
            q = query(qs,d)
            for i in q:
                yield i
        return 

    dir_iter = os.scandir(dir) 
    for entry in dir_iter:
        passed = True
        for q in qs: 
            (by,op,iv) = q
            if op[:4] == 'not-':
                op = op[4:]
                passed = not passed
    
            if not test(by,op,iv,entry):
                passed = not passed
                break
        if passed:
            yield entry

    dir_iter.close()

def read(file,mode='r'):
    with open(file,mode) as f:
        return f.read()

time_parsed = {}
def parse_time(s:str) -> float:
    if s in time_parsed:
        return time_parsed[s]

    res = 0

    #TODO: process isoformat
    

    res =  abstime(s)
    time_parsed[s] = res
    return res


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
