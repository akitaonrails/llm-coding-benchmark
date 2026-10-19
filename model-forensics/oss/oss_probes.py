"""Output fingerprints: no token-count measurements and no inherited target data."""
import json
import random
import unicodedata
import panel


def build():
    import tiktoken
    enc=tiktoken.get_encoding('o200k_base');vocab=[]
    for token in range(160000,199900):
        try:s=enc.decode_single_token_bytes(token).decode('utf-8')
        except (UnicodeDecodeError,KeyError):continue
        if 3<=len(s)<=14 and s.isprintable() and not s.isascii() and not s.isspace() and all(unicodedata.category(c)[0]!='C' for c in s):vocab.append((token,s))
    r=random.Random(914107);selected=r.sample(vocab,12);out=[]
    for i,(token,s) in enumerate(selected):
        out.append(dict(id=f'copy-{i}',family='rare-copy',block=f'copy-{i}',kind='exact',expected=s,
            prompt='Return a JSON string containing exactly the characters between START and END. Do not translate, normalize, repair, or explain. START'+s+'END',token_id=token))
    # Common-string controls reveal generic copying/formatting failures.
    for i,s in enumerate(['你好世界','مرحبا','strawberry','ação']):
        out.append(dict(id=f'copy-control-{i}',family='copy-control',block=f'copy-control-{i}',kind='exact',expected=s,
            prompt='Return a JSON string containing exactly the characters between START and END. Do not translate, normalize, repair, or explain. START'+s+'END'))
    # Task responses, not tokenizer vocabulary/counts, are analyzed.
    for i,f in enumerate(panel.FAMILIES):
        p=panel.task(f,901000+i*31)
        out.append(dict(id=f'algorithm-{f}',block=f'algorithm-{f}',**p))
    optionsets=[['amber','indigo','ochre','teal'],['17','29','43','71'],['elm','fir','ash','yew'],['circle','oval','square','star'],['rio','mar','sol','lua'],['nube','lago','flor','hoja'],['left','right','up','down'],['ivory','copper','silver','bronze'],['猫','犬','鳥','魚'],['north','west','east','south']]
    for i,options in enumerate(optionsets):
        for version in [0,1]:
            order=options if version==0 else options[::-1]
            out.append(dict(id=f'choice-{i}-{version}',block=f'choice-{i}',family='choice',kind='choice',options=options,
                prompt='Choose exactly one item from this list: '+', '.join(order)+'. Return only that item.'))
    assert len(out)==48
    return out
