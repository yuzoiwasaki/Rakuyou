"""Geometric supported-gold advancement for selection; no engine or updates."""
FEATURE='unpromoted_gold_defended_by_other_gold_or_unpromoted_silver_advance_steps_capped3'


def gold_advance_details(pieces):
    result=[]
    for square,piece in pieces.items():
        if piece not in ('G','g'):continue
        upper=piece=='G';forward=-1 if upper else 1
        rank=ord(square[1])-ord('a')+1
        advance=min(3,max(0,8-(rank if upper else 10-rank)))
        supporters=[]
        for source,kind in pieces.items():
            if source==square or kind not in (('G','S') if upper else ('g','s')):continue
            offsets=[(-1,forward),(0,forward),(1,forward),(-1,0),(1,0),(0,-forward)] if kind.upper()=='G' else [(0,forward),(-1,-1),(1,-1),(-1,1),(1,1)]
            if (int(square[0])-int(source[0]),ord(square[1])-ord(source[1])) in offsets:
                supporters.append(source)
        result.append(dict(square=square,color='black' if upper else 'white',advance=advance,
                           supporters=sorted(supporters),score=advance if supporters else 0))
    return sorted(result,key=lambda x:x['square'])


def scores(details):
    return {side:sum(g['score'] for g in details if g['color']==side) for side in ('black','white')}


def bucket(details,side):
    own=[g for g in details if g['color']==side and g['advance']>=2]
    if not own:return None
    advance=max(g['advance'] for g in own)
    defended=any(g['supporters'] for g in own if g['advance']==advance)
    return f"{side}:rank{'4' if advance==2 else '5plus'}:{'supported' if defended else 'unsupported'}"
