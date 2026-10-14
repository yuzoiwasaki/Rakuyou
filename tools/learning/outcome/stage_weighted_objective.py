"""Fixed progress-weighted winner loss, normalized within four training strata."""
import math
from tools.learning.outcome.outcome_objective import GAIN, supervised


def training_samples(records):
    groups = {}
    enabled = []
    for record in records:
        sample = record['sample']
        if not supervised([sample]):
            continue
        side = record['row']['side_to_move']
        progress = record['features']['progress']
        if side not in ('black', 'white') or not math.isfinite(progress) or not 0 <= progress <= 1:
            raise ValueError('Invalid saved side/progress')
        group = (side, sample['target'])
        weight = .25 + .75 * progress
        groups.setdefault(group, []).append(weight)
        enabled.append((record, group, weight))
    expected = {(side, target) for side in ('black', 'white') for target in (0., 1.)}
    if set(groups) != expected or any(len(v) != 64 for v in groups.values()):
        raise ValueError('Expected four fixed64 training strata')
    means = {k: math.fsum(v) / 64 for k, v in groups.items()}
    return [{**r['sample'], 'weight': w / means[g]} for r, g, w in enabled]


def objective(rows, delta, l2=0):
    rows = supervised(rows)
    if not rows or not math.isfinite(l2) or l2 < 0 or any(not math.isfinite(v) for v in delta.values()):
        raise ValueError('Invalid weighted objective state')
    weights = [r['weight'] for r in rows]
    if any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError('Positive finite weights required')
    if abs(math.fsum(weights) - len(rows)) > 1e-10:
        raise ValueError('Expected normalized total weight')
    gradient = {k: l2*v for k, v in delta.items()}
    loss = 0
    for row in rows:
        cp = row['base_cp'] + math.fsum(v*delta.get(k, 0) for k, v in row['factors'].items())
        z = GAIN*cp
        signed = z if row['target'] == 0 else -z
        loss += row['weight']*(max(signed, 0) + math.log1p(math.exp(-abs(signed))))
        probability = 1/(1+math.exp(-z)) if z >= 0 else math.exp(z)/(1+math.exp(z))
        d = row['weight']*GAIN*(probability-row['target'])/len(rows)
        for k, v in row['factors'].items():
            gradient[k] = gradient.get(k, 0) + d*v
    return loss/len(rows) + .5*l2*math.fsum(v*v for v in delta.values()), gradient
