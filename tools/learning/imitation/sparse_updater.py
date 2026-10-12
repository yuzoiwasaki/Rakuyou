"""Fixed full-batch bounded sparse RMSprop; arithmetic only."""
import math
from tools.learning.core.king_safety_updater import fingerprint
CONFIG=dict(max_updates=20,step_rate_cp=.001,max_step_cp=.001,delta_limit_cp=.01,
            decay=.9975,average_decay=.9995,epsilon=1e-12,l2=1e-6)


def initial(keys):
    if not keys or len(keys)!=len(set(keys)):raise ValueError('Unique nonempty keys required')
    return dict(updates=0,delta={k:0.0 for k in sorted(keys)},squared={k:0.0 for k in sorted(keys)},
                average_sum={k:0.0 for k in sorted(keys)},mass=0.0)


def validate(state):
    if type(state['updates']) is not int or not 0<=state['updates']<=20:raise ValueError('Invalid update count')
    keys=set(state['delta'])
    if keys!=set(state['squared']) or keys!=set(state['average_sum']):raise ValueError('Key mismatch')
    if any(not math.isfinite(v) or abs(v)>.01 for v in state['delta'].values()):raise ValueError('Delta bound')
    if any(not math.isfinite(v) or v<0 for v in state['squared'].values()):raise ValueError('Invalid squared gradient')
    expected=math.fsum(CONFIG['average_decay']**i for i in range(state['updates']))
    if not math.isfinite(state['mass']) or abs(state['mass']-expected)>1e-12:raise ValueError('Averaging mass mismatch')
    if any(not math.isfinite(v) or abs(v)>state['mass']*.01+1e-12 for v in state['average_sum'].values()):raise ValueError('Average bound')
    if state['updates']==0 and any(v for k in ('delta','squared','average_sum') for v in state[k].values()):raise ValueError('Initial state not zero')


def step(state,gradient):
    validate(state)
    if state['updates']>=20:raise ValueError('Update limit')
    if set(gradient)!=set(state['delta']) or any(not math.isfinite(v) for v in gradient.values()):raise ValueError('Invalid gradient keys/values')
    result=dict(updates=state['updates']+1,delta={},squared={},average_sum={},mass=.9995*state['mass']+1)
    for k,g in gradient.items():
        v=.9975*state['squared'][k]+g*g
        change=max(-.001,min(.001,.001*g/math.sqrt(v+1e-12)))
        delta=max(-.01,min(.01,state['delta'][k]-change))
        result['delta'][k]=delta;result['squared'][k]=v
        result['average_sum'][k]=.9995*state['average_sum'][k]+delta
    validate(result);return result


def average(state):
    validate(state)
    return {k:v/state['mass'] if state['mass'] else 0.0 for k,v in state['average_sum'].items()}


def checkpoint(state,binding):
    validate(state)
    body=dict(schema='rakuyou-sparse-imitation-checkpoint-v1',config=CONFIG,binding=binding,state=state)
    return {**body,'content_sha256':fingerprint(body)}


def restore(payload,binding):
    body={k:v for k,v in payload.items() if k!='content_sha256'}
    if body.get('schema')!='rakuyou-sparse-imitation-checkpoint-v1' or body.get('config')!=CONFIG or body.get('binding')!=binding or fingerprint(body)!=payload.get('content_sha256'):
        raise ValueError('Checkpoint binding/config/content changed')
    validate(body['state']);return body['state']
