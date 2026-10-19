"""Frozen programmatic probes. Reference functions never execute model text."""
import itertools
import json
import random
import re

FAMILIES = ['count', 'substring', 'sort', 'rotate', 'replace', 'nest', 'modular', 'rle', 'stack', 'csv', 'base', 'subsequence']


def task(family, seed):
    r = random.Random(seed)
    if family == 'count':
        s = ''.join(r.choice('abccddeeffg') for _ in range(71))
        q, a = f'Count lowercase c in {s}', s.count('c')
    elif family == 'substring':
        s = ''.join(r.choice('ab') for _ in range(61))
        q, a = f'Count overlapping occurrences of aba in {s}', sum(s[i:i+3] == 'aba' for i in range(len(s)-2))
    elif family == 'sort':
        xs = r.sample(range(10, 99), 9)
        q, a = f'Sort these integers by (digit sum ascending, then integer descending); return the fourth integer: {xs}', sorted(xs, key=lambda x:(sum(map(int,str(x))), -x))[3]
    elif family == 'rotate':
        s = ''.join(r.choice('abcdefghjkmnpqr') for _ in range(23)); k = r.randint(3, 11)
        q, a = f'Rotate {s} left by {k} characters, then reverse the result', (s[k:]+s[:k])[::-1]
    elif family == 'replace':
        s = ''.join(r.choice('ab') for _ in range(33)); a = s.replace('ab','ba').replace('aa','b')
        q = f'On {s}, perform two sequential literal non-overlapping replace-all passes, left to right: first ab -> ba, then aa -> b. Do not recursively reprocess replacement text within a pass'
    elif family == 'nest':
        s='';depth=best=0
        for _ in range(18):
            if depth and r.random()<.45: s+=')';depth-=1
            else:s+='(';depth+=1;best=max(best,depth)
        s+=')'*depth
        q,a=f'What is the maximum parenthesis nesting depth in {s}',best
    elif family == 'modular':
        start=r.randrange(13);ops=[(r.randint(2,7),r.randint(1,9)) for _ in range(8)];a=start
        for mul,add in ops:a=(a*mul+add)%17
        q=f'Start x={start}. For each (m,b) pair update x=(x*m+b) modulo 17, in order: {ops}. Return final x'
    elif family == 'rle':
        groups=[(r.choice('abcd'),r.randint(1,7)) for _ in range(9)];s=''.join(c*n for c,n in groups)
        a=''.join(f'{c}{len(list(g))}' for c,g in itertools.groupby(s));q=f'Run-length encode {s} as each character followed by its decimal run length, without separators'
    elif family == 'stack':
        ops=[];stack=[]
        for _ in range(19):
            if stack and r.random()<.4:ops.append('pop');stack.pop()
            else:v=r.randrange(100);ops.append(f'push {v}');stack.append(v)
        q=f'An initially empty stack executes: {"; ".join(ops)}. Return its final contents bottom-to-top as comma-separated integers, or EMPTY if empty';a=','.join(map(str,stack)) or 'EMPTY'
    elif family == 'csv':
        fields=[r.choice(['ab','c,d','e"f','','g,h,i']) for _ in range(9)]
        line=','.join('"'+s.replace('"','""')+'"' for s in fields)
        q,a=f'How many fields are in this single CSV record, using RFC-style double-quoted fields and doubled quote escapes? {line}',len(fields)
    elif family == 'base':
        n=r.randrange(5000,50000);q,a=f'Convert hexadecimal {n:x} to a base-7 integer, with no prefix',base7(n)
    else:
        s=''.join(r.choice('abc') for _ in range(28));a=sum(s[i]+s[j]+s[k]=='abc' for i in range(len(s)) for j in range(i+1,len(s)) for k in range(j+1,len(s)))
        q=f'Count index triples i<j<k whose characters spell abc in {s}. Indices may be nonconsecutive'
    return {'family':family,'kind':'exact','prompt':q+'. Return only the answer, no explanation or code fences.', 'expected':str(a)}


def base7(n):
    out=''
    while n:out=str(n%7)+out;n//=7
    return out or '0'


def behavioral():
    discovery=[];holdout={}
    for fidx,f in enumerate(FAMILIES):
        for i in range(4):discovery.append(dict(id=f'd-{f}-{i}',block=f,**task(f,18000+fidx*100+i)))
        holdout[f]=[dict(id=f'h-{f}-{i}',block=f,**task(f,81000+fidx*100+i)) for i in range(2)]
    choices=[]
    sets=[['17','23','41','68'],['A','K','M','Z'],['red','blue','green','yellow'],['circle','square','triangle','oval'],['rio','mar','sol','lua'],['nube','lago','flor','hoja'],['oak','pine','birch','elm'],['copper','silver','iron','tin'],['north','south','east','west'],['猫','犬','鳥','魚'],['chat','chien','oiseau','poisson'],['moss','fern','reed','ivy']]
    for i,options in enumerate(sets):
        for v in range(4):
            order=options[::-1] if v==1 else options
            lead='Select one item' if v!=2 else 'Pick whichever single option you prefer'
            q=f'{lead}: {", ".join(order)}. Return exactly one listed item and nothing else.'
            if v==3:q='Context: the document identifier is ZK-482.\n'+q
            choices.append(dict(id=f'p-{i:02}-{v}',block=f'choice-{i:02}',family='choice',kind='choice',variant=v,options=options,prompt=q))
    return discovery,holdout,choices


def tokens():
    r=random.Random(6100941);out=[]
    vocab={
      'ascii':['antidisestablishmentarianism','hello','benchmark','xyzzy','HTTPServer','CamelCase'],
      'numbers':['0123456789','0xdeadbeef','123_456','1.234e-10','00000','987654321'],
      'spaces':[' ','  ','\t','\n','\r\n',' \t '],
      'code':['fn main(){}','x->y::z','[a,b,c]','SELECT * FROM t;','lambda x:x+1','\\n\\t'],
      'cjk':['漢字','ひらがな','カタカナ','中文测试','零〇','한국어'],
      'arabic':['مرحبا','بالعالم','العربية','لغة','سلام','اختبار'],
      'unicode':['é','e\u0301','ＡΑАA','\u200b','\u00a0','𝒜𝔅'],
      'emoji':['👩\u200d💻','🏳️\u200d🌈','👍🏽','🇧🇷','🧑\u200d🔬','🙂']}
    seen=set()
    for family,parts in vocab.items():
        for i in range(128):
            while True:
                s=''.join(r.choice(parts) for _ in range(r.randint(3,18)))
                if s not in seen:break
            seen.add(s)
            out.append(dict(id=f't-{family}-{i:03}',family=family,kind='tokens',prompt=s,split='offset' if i%4==0 else 'holdout'))
    return out
