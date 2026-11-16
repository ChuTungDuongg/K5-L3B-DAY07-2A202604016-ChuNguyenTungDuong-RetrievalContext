"""Claim one official Test per round; all rounds retain a single shared budget."""
import argparse
import json
import os
from datetime import datetime

from .analyze import read
from .budget import save
from .run import main as run_main, fingerprints, verify_selection, round_results, benchmark_directory
from .source import ROOT, digest, verify_images


def claim_official(number=1, *, root=None):
    results = round_results(number, root)
    for directory in sorted((results/'runs').glob('*')):
        if directory.is_dir() and (directory/'config.json').exists() and read(directory/'config.json')['split'] == 'test':
            raise ValueError('A Test run already exists in this round; official reruns are not allowed')
    marker = results/'official-test.json'
    claim = {'round': number, 'claimed_local': datetime.now().astimezone().isoformat(), 'state': 'claimed',
             'selection_sha256': digest(results/'selection-freeze.json'),
             'policy': 'One official run per round. A failed claim must be audited; never delete it to select a better result.'}
    marker.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(claim, stream, ensure_ascii=False, indent=2)
    return marker, claim


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    results = round_results(args.round)
    selection = read(results/'selection-freeze.json')
    verify_selection(selection, selection['config_name'], selection['config'], fingerprints(),
                     digest(benchmark_directory(args.round)/'freeze.json'), number=args.round)
    verify_images()
    marker, claim = claim_official(args.round)
    try:
        run_id = run_main(['--round', str(args.round), '--split', 'test', '--config', selection['config_name']], official=True)
        config = read(results/'runs'/run_id/'config.json')
        if config.get('round', 1) != args.round or config['split'] != 'test':
            raise ValueError('Official claim produced a different round/split')
        claim.update(state='completed', run_id=run_id, completed_local=datetime.now().astimezone().isoformat())
    except Exception as exc:
        claim.update(state='failed', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save(marker, claim)
    return run_id


if __name__ == '__main__':
    main()
