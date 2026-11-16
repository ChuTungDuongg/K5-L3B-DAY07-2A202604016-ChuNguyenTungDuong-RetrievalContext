"""Strict advanced grading: all published cases stay in the denominator."""
from collections import Counter


def summarize(cases,traces,reviews,*,labels_confirmed=False):
    if len({c['id'] for c in cases})!=len(cases): raise ValueError('Duplicate cases')
    if len({t['query_id'] for t in traces})!=len(traces): raise ValueError('Duplicate traces')
    if len({r['query_id'] for r in reviews})!=len(reviews): raise ValueError('Duplicate labels')
    by_id={t['query_id']:t for t in traces};labels={r['query_id']:r for r in reviews}
    output={'passed':0,'total':len(cases),'errors':0,'missing_results':0,'unreviewed':0,'groups':{}}
    for case in cases:
        trace=by_id.get(case['id']);review=labels.get(case['id'])
        group=output['groups'].setdefault(case['group'],{'passed':0,'total':0,'errors':0})
        group['total']+=1
        if trace is None: output['missing_results']+=1
        elif trace.get('status')=='error': output['errors']+=1;group['errors']+=1
        elif review is None: output['unreviewed']+=1
        else:
            if type(review.get('passed')) is not bool or not review.get('reason'): raise ValueError('Invalid review')
            if review['passed']: output['passed']+=1;group['passed']+=1
    output['rate']=output['passed']/output['total'] if cases else 0
    output['score_threshold_met']=bool(cases and output['passed']*10>=output['total']*9)
    output['labels_confirmed']=labels_confirmed
    output['threshold_met']=output['score_threshold_met'] and labels_confirmed
    output['label_status']='learner_confirmed' if labels_confirmed else 'assistant_proposed_pending_learner_confirmation'
    return output
