#!/usr/bin/env python3
"""Bounded eight-coordinate RMSprop state; no engine, data loader or bin writer.

The caller supplies the gradient of a MEAN loss including delta-only L2.
No real-data training command is provided. Checkpoints bind config and input IDs.
"""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import hashlib
import json
import math
import random
import sys
from dataclasses import asdict, dataclass, replace

from tools.learning.core.king_safety_objective import finite, vector

SCHEMA = "rakuyou-king-safety-updater-v1"


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Config:
    max_updates: int = 20
    batch_size: int = 128
    seed: int = 20261011
    step_rate_cp: float = .05
    max_step_cp: float = .05
    delta_limit_cp: float = .5
    decay: float = .9975
    epsilon: float = 1e-12
    l2: float = 1e-4
    average_decay: float = .9995

    def validate(self):
        for key,limit in (("max_updates",20),("batch_size",128)):
            value=getattr(self,key)
            if type(value) is not int or not 1<=value<=limit:
                raise ValueError("Invalid bounded setting: "+key)
        if type(self.seed) is not int:
            raise ValueError("Integer seed required")
        for key in ("step_rate_cp","max_step_cp","delta_limit_cp","epsilon"):
            if finite(getattr(self,key))<=0:
                raise ValueError("Positive setting required: "+key)
        if self.step_rate_cp>.05 or self.max_step_cp>.05 or self.delta_limit_cp>.5:
            raise ValueError("Pilot parameter limits exceeded")
        for key in ("decay","average_decay"):
            if not 0<=finite(getattr(self,key))<1:
                raise ValueError("Decay outside [0,1)")
        if finite(self.l2)<0:
            raise ValueError("Nonnegative L2 required")


@dataclass(frozen=True)
class State:
    updates: int
    delta: tuple
    squared_gradient: tuple
    average_sum: tuple
    average_mass: float
    rng_state: tuple

    def average(self):
        return tuple(x/self.average_mass for x in self.average_sum) if self.average_mass else (0.0,)*8


def validate_state(state,config):
    config.validate()
    if type(state.updates) is not int or not 0<=state.updates<=config.max_updates:
        raise ValueError("Invalid update counter")
    d,a,s=vector(state.delta),vector(state.squared_gradient),vector(state.average_sum)
    if any(abs(v)>config.delta_limit_cp for v in d) or any(v<0 for v in a):
        raise ValueError("Invalid bounded optimizer state")
    mass=finite(state.average_mass)
    expected=math.fsum(config.average_decay**i for i in range(state.updates))
    if abs(mass-expected)>1e-12 or any(abs(v)>mass*config.delta_limit_cp+1e-12 for v in s):
        raise ValueError("Invalid averaging state")
    if state.updates==0 and any(v!=0 for v in d+a+s):
        raise ValueError("Initial state must be zero")
    rng=random.Random()
    try:
        rng.setstate(state.rng_state)
    except (TypeError,ValueError,OverflowError,IndexError) as error:
        raise ValueError("Invalid RNG state") from error


def initial(config=Config()):
    config.validate()
    return State(0,(0.0,)*8,(0.0,)*8,(0.0,)*8,0.0,random.Random(config.seed).getstate())


def sample_batch(state,population_size,config=Config()):
    validate_state(state,config)
    if state.updates>=config.max_updates:
        raise ValueError("Update limit reached")
    if type(population_size) is not int or population_size<1:
        raise ValueError("Nonempty population required")
    rng=random.Random();rng.setstate(state.rng_state)
    ids=rng.sample(range(population_size),min(population_size,config.batch_size))
    return ids,replace(state,rng_state=rng.getstate())


def step(state,gradient,config=Config()):
    validate_state(state,config)
    if state.updates>=config.max_updates:
        raise ValueError("Update limit reached")
    g=vector(gradient)
    a=tuple(config.decay*v+x*x for v,x in zip(state.squared_gradient,g))
    if any(not math.isfinite(v) for v in a):
        raise ValueError("Squared gradient overflow")
    def clamp(v,limit):return min(limit,max(-limit,v))
    moves=tuple(clamp(config.step_rate_cp*x/math.sqrt(v+config.epsilon),config.max_step_cp)
                for x,v in zip(g,a))
    d=tuple(clamp(v-x,config.delta_limit_cp) for v,x in zip(state.delta,moves))
    result=State(state.updates+1,d,a,
        tuple(config.average_decay*v+x for v,x in zip(state.average_sum,d)),
        config.average_decay*state.average_mass+1.0,state.rng_state)
    validate_state(result,config)
    return result


def checkpoint(state,config,binding):
    validate_state(state,config)
    if not isinstance(binding,dict) or not binding:
        raise ValueError("Input/config binding required")
    body=dict(schema=SCHEMA,python_runtime=list(sys.version_info[:3]),
              config=asdict(config),config_sha256=fingerprint(asdict(config)),
              binding=binding,binding_sha256=fingerprint(binding),state=asdict(state))
    return {**body,"content_sha256":fingerprint(body)}


def _tuples(value):
    return tuple(_tuples(v) for v in value) if isinstance(value,list) else value


def restore(payload,config,binding):
    config.validate()
    body={k:v for k,v in payload.items() if k!="content_sha256"}
    if body.get("schema")!=SCHEMA or fingerprint(body)!=payload.get("content_sha256"):
        raise ValueError("Checkpoint content/schema mismatch")
    if body.get("python_runtime")!=list(sys.version_info[:3]):
        raise ValueError("Checkpoint Python runtime mismatch")
    if body.get("config")!=asdict(config) or body.get("config_sha256")!=fingerprint(asdict(config)):
        raise ValueError("Checkpoint config mismatch")
    if body.get("binding")!=binding or body.get("binding_sha256")!=fingerprint(binding):
        raise ValueError("Checkpoint input binding mismatch")
    raw=body["state"]
    if set(raw)!={"updates","delta","squared_gradient","average_sum","average_mass","rng_state"}:
        raise ValueError("Checkpoint state fields mismatch")
    result=State(raw["updates"],tuple(raw["delta"]),tuple(raw["squared_gradient"]),
                 tuple(raw["average_sum"]),raw["average_mass"],_tuples(raw["rng_state"]))
    validate_state(result,config)
    return result
