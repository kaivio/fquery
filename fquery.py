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
    param ('--link','-l',
        action= 'store_true',
        default=False,
        help='alias -q type is link'
    )
    param ('--file','-f',
        action= 'store_true',
        default=False,
        help='alias -q type is file'
    )
    param ('--dir','-d',
        action= 'store_true',
        default=False,
        help='alias -q type is dir'
    )
    param ('-n',
        action='append',
        default=[]
    )


    param ('--depth',
        type=int,
        default=0,
        help="recursion depth"
    )

    (opts,args) = parser.parse_known_args(argv)
    qs = [
        *opts.query,
        *pre_args(args),
        *pre_opts(opts)
    ]

    dir = opts.from_dir or ['.']
    
    
    show(qs)
    show(opts)
    for entry in query(qs,dir,opts.depth):
        path = entry.path
        ppath = list(path)
        for by,span in entry.ctx['spans']:
            if by == 'name':
                b = len(entry.path) - len(entry.name)
                span[0] += b
                span[1] += b

            if by in ['name','path']:
                for i in range(len(ppath)):
                    if i in range(*span):
                        ppath[i] = '[red]'+ppath[i]+'[/red]'

        show(''.join(ppath))
        

def pre_opts(opts):
    qs = []
    optdict = vars(opts)
    for i in ['file','dir','link','dev']:
        optdict.get(i,False) and qs.append(['type','is',i])

    nots = pre_args(opts.n)
    for by,op,iv in nots:
        op = 'not-'+op
        qs.append([by,op,iv])

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
            op ='suffix'
        elif s[-1] == '.':
            op ='prefix'

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
    return (s,op)

        
def test (
        by: str,
        op: str,
        iv: str,
        entry:os.DirEntry
    ) -> bool:
    sign = False
    if op[:4] == 'not-':
        op = op[4:]
        sign = True

    rv = None
    if by == 'name':
        rv = entry.name
    elif by  == 'path':
        rv = entry.path
    elif by == 'type':
        if iv == 'file':
            rv = entry.is_file()
        elif iv == 'dir':
            rv = entry.is_dir()
        elif iv == 'link':
            rv = entry.is_symlink()
        #TODO: other type

        iv = True

    elif by == 'text':
        try:
            rv = read(entry.path)
        except:
            return sign ^ False
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
        return sign ^ False
    ctx = entry.ctx
    spans = ctx['spans'] 
    span = []
    res = False
    iv = type(rv)(iv)
    if op == 'in':
        res = rv in iv
    elif op == 'has':
        pos = rv.find(iv)
        if pos != -1:
            res = True
            span = [
                pos,
                len(rv)-(len(rv)-pos-len(iv))
            ]
    elif op == 'suffix':
        res = rv.endswith(iv)
        span = res and [len(rv)-len(iv),len(rv)] 
    elif op == 'prefix':
        res = rv.startswith(iv)
        span = res and [0,len(iv)] 
    elif op in ['lt','-']:
        res = rv < iv
    elif op in ['rt','+']:
        res = rv > iv
    elif op in ['le','-=']:
        res = rv <= iv
    elif op in ['re','+=']:
        res = rv >= iv
    elif op in ['is','eq','=']:
        res = rv == iv
    
    span and spans.append([by,span])
    return sign^res
    

def query (
        qs:'[(by,op,iv), ...]',
        dir=['.'],
        depth=0
    ):
    if type(dir) in [list,tuple]:
        for d in dir:
            q = query(qs,d,depth)
            for i in q:
                yield i
        return 

    dir_iter = os.scandir(dir) 
    for entry in dir_iter:
        entry:os.DirEntry = MyEntry(entry)
        passed = True
        for q in qs: 
            passed = True
            if not test(*q,entry):
                passed = False
                break

        if passed:
            yield entry
        
        if depth > 0 and entry.is_dir():
           for i in deep_query(qs,entry,passed,depth-1):
               yield i

    dir_iter.close()


def deep_query(qs,entry,preres,depth):
    nots = []
    for by,op,iv in qs:
        if op[0:4] == 'not-':
            op = op[4:]
            if by in ['name','path']:
                nots.append([by,op,iv])

    excluded = False
    if nots:
        for q in nots:
            if test(*q,entry):
                excluded = True
    elif preres:
        excluded = True

    if not excluded:
        return query(qs,entry.path,depth)
    return []

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

class MyEntry():
    ctx = {}
    entry:os.DirEntry
    def  __init__(self,entry):
        self.entry = entry
        self.ctx = {
            'spans':[]
        }
        
    def __getattribute__(self,x):
        if x != 'ctx':
            return object.__getattribute__(object.__getattribute__(self,'entry'),x)
        return object.__getattribute__(self,x)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
