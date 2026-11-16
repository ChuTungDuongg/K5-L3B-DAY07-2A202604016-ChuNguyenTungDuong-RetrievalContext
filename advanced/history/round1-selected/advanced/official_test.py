"""Claim a single official Test execution; never silently rerun it."""
import json
import os
import sys
from datetime import datetime

from .analyze import RESULTS, read
from .budget import save
from .run import main as run_main, fingerprints, verify_selection
from .source import ROOT, digest, verify_images


def main():
    selection=read(RESULTS/'selection-freeze.json')
    verify_selection(selection,selection['config_name'],selection['config'],fingerprints(),
                     digest(ROOT/'advanced/benchmark/freeze.json'))
    verify_images()
    before={p.name for p in (RESULTS/'runs').iterdir() if p.is_dir()}
    if any(read(RESULTS/'runs'/name/'config.json')['split']=='test' for name in before):
        raise ValueError('A Test run already exists; official reruns are not allowed')
    marker=RESULTS/'official-test.json'
    claim={'claimed_local':datetime.now().astimezone().isoformat(),'state':'claimed',
           'selection_sha256':digest(RESULTS/'selection-freeze.json'),
           'policy':'One official run. A failed claim must be audited; do not delete it to select a better outcome.'}
    fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(claim,stream,ensure_ascii=False,indent=2)
    sys.argv=['advanced.run','--split','test','--config',selection['config_name']]
    try:
        run_main()
        created=[p.name for p in (RESULTS/'runs').iterdir() if p.is_dir() and p.name not in before]
        if len(created)!=1:raise ValueError('Unexpected number of claimed runs')
        claim.update(state='completed',run_id=created[0],completed_local=datetime.now().astimezone().isoformat())
    except Exception as exc:
        claim.update(state='failed',error_type=type(exc).__name__,error=str(exc));raise
    finally:save(marker,claim)


if __name__=='__main__':main()
