import sys,os,re,json
from pathlib import Path
from datetime import datetime

def main():
    print('hello, world!')

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
