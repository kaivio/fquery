import sys,os,re,json
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

def main():
    print('hello, world!')


def abstime(timeago:str,now=datetime.now()) -> float:
    tm = now.timetuple()
    i = re.match('[+-]?[\d][\d.]*',timeago)
    if i:
        i = i.group(0)

    u = timeago[len(i):]
    i = int(i)
    ago = now 

    if len(u) == 0 or u[0] == 's':
        ago = now - relativedelta(seconds=i)
    elif u in ['M','mon','month']:
        ago = now - relativedelta(months=i)
    elif re.match(r'm(in(ute))?',u):
        ago = now - relativedelta(minutes=i)
    elif u[0] == 'h':
        ago = now - relativedelta(hours=i)
    elif u[0] == 'd':
        ago = now - relativedelta(days=i)
    elif u[0] == 'y':
        ago = now - relativedelta(years=i)

    
    return ago.timestamp()



def parse_size(TGMKib:str) -> int:
    s = TGMKib.lower()
    k = 1024
    if s[-1] == 'b':
        s = s[:-1]

    if s[-1] == 'i':
        k = 1000
        s = s[:-1]

    u = s[-1]
    n = float(s[:-1])
    
    for i in 'kmgt':
        n *= k
        if u == i:
            break
    else:
        n = int(s)
    
    return int(n)






if __name__ == "__main__":
    main()
