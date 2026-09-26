"""Small, portable timing snapshots of explicitly supplied attempts, never authority.

Missing legacy timestamps stay unknown. Reservations identify reused calls; a
replacement with a fresh reservation remains a separate attempt, even if its
request bytes match. No payloads, credentials, or filesystem mtimes are retained.
"""
from datetime import datetime
import portable_articles as pa
from article_runtime import absolute, sha, require


def seconds(start, end):
    if start is None or end is None: return None
    value=(datetime.fromisoformat(end.replace('Z','+00:00'))-
           datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds()
    return max(0, value)


def union_seconds(intervals):
    intervals=sorted((datetime.fromisoformat(a.replace('Z','+00:00')).timestamp(),
                      datetime.fromisoformat(b.replace('Z','+00:00')).timestamp()) for a,b in intervals if a and b)
    if not intervals: return None
    total=0; start,end=intervals[0]
    for a,b in intervals[1:]:
        if a>end: total+=max(0,end-start); start,end=a,b
        else: end=max(end,b)
    return total+max(0,end-start)


def _load(path):
    return pa.load(path) if path.is_file() else {}


def summarize(*, source_attempts=(), enrichment_attempts=()):
    requests={}; attempts=[]; reused=0
    for kind,roots in (('source',source_attempts),('enrichment',enrichment_attempts)):
        for root in dict.fromkeys(map(absolute,roots)):
            require(root.is_dir(),'timing-attempt-directory-required')
            phases=[]
            for phase in (('initial','classification','association') if kind=='source' else ('enrichment',)):
                base=root if kind=='source' else root/'enrichment'
                plan=_load(base/(phase+'-plan.json' if kind=='source' else 'prepared.json'))
                if not plan: continue
                session=_load(base/(phase+'-session.json' if kind=='source' else 'execution-start.json'))
                complete=_load(base/(phase+'-complete.json' if kind=='source' else 'execution-complete.json'))
                phases.append(dict(phase=phase,started_at=session.get('started_at'),
                    ended_at=complete.get('ended_at',complete.get('finished_at')),
                    elapsed_seconds=seconds(session.get('started_at'),complete.get('ended_at',complete.get('finished_at'))),
                    executions=[pa.load(p) for p in sorted((base/'execution-runs').glob('*.json'))] if kind=='enrichment' else [],
                    vlm_concurrency=session.get('vlm_concurrency'),concurrency_source=session.get('concurrency_source')))
                for row in plan['requests']:
                    d=absolute(base/row['directory']); require(d.is_relative_to(base) and d!=base,'timing-request-path-escape')
                    reservation=d/'reservation.json'
                    if not reservation.is_file(): continue
                    identity=kind+':'+sha(reservation)
                    if identity in requests: reused+=1; continue
                    reserved=pa.load(reservation)
                    outcome=_load(d/('call.json' if kind=='source' else 'outcome.json'))
                    failure=_load(d/'failure.json') if kind=='enrichment' else {}
                    timing=outcome or failure
                    successful=bool(outcome.get('complete')) if kind=='source' else bool(outcome)
                    status='successful' if successful else ('failed' if failure.get('status')=='failed' or
                        (kind=='source' and outcome.get('status') not in (None,'in-flight','uncertain','transport-timeout','transport-failure')) else 'uncertain')
                    usage=outcome.get('usage')
                    if not isinstance(usage,dict):
                        # Legacy and rejected responses may report usage without an accepted outcome.
                        try: usage=_load(d/'response-body.json').get('usage',{})
                        except (ValueError,UnicodeError,AttributeError): usage={}
                    if not isinstance(usage,dict): usage={}
                    usage={k:v for k,v in usage.items() if k in ('prompt_tokens','completion_tokens','total_tokens') and type(v) is int and v>=0}
                    requests[identity]=dict(reservation_sha256=identity.split(':',1)[1],kind=kind,phase=phase,status=status,
                        started_at=timing.get('started_at',reserved.get('started_at')),
                        request_started_at=timing.get('request_started_at'),response_received_at=timing.get('response_received_at'),
                        ended_at=timing.get('ended_at'),usage=usage,
                        vlm_concurrency=reserved.get('vlm_concurrency',session.get('vlm_concurrency')),
                        concurrency_source=reserved.get('concurrency_source',session.get('concurrency_source')))
            require(phases,'timing-attempt-has-no-plan')
            attempts.append(dict(kind=kind,attempt_id=pa.digest(str(root)),phases=phases))
    rows=list(requests.values()); intervals=[(r['started_at'],r['ended_at']) for r in rows]
    events=sorted((datetime.fromisoformat(r[k].replace('Z','+00:00')).timestamp(),delta) for r in rows
        if r['request_started_at'] and r['response_received_at']
        for k,delta in (('request_started_at',1),('response_received_at',-1)))
    active=peak=0
    for _,delta in events: active+=delta; peak=max(peak,active)
    return dict(schema='paper-operation-timing-v1',scope='registered-attempts-only; operational diagnostics, not scientific acceptance',
        attempts=attempts,requests=rows,
        counts=dict(total=len(rows),successful=sum(r['status']=='successful' for r in rows),
            failed=sum(r['status']=='failed' for r in rows),uncertain=sum(r['status']=='uncertain' for r in rows),reused=reused),
        request_wall_seconds=union_seconds(intervals),
        observed_peak_in_flight=peak if events else None,
        requests_missing_response_timing=sum(not (r['request_started_at'] and r['response_received_at']) for r in rows),
        request_elapsed_sum_seconds=sum(seconds(a,b) or 0 for a,b in intervals) if any(a and b for a,b in intervals) else None,
        requests_missing_timing=sum(not (a and b) for a,b in intervals),
        usage={k:sum(r['usage'].get(k,0) for r in rows) for k in ('prompt_tokens','completion_tokens','total_tokens')},
        requests_missing_usage=sum(not r['usage'] for r in rows))


def route_snapshot(value, plan, history):
    """Receipt-to-receipt intervals include operator wait, not just CPU time."""
    previous=plan['planned_at']; intervals=[]
    for row in history:
        if row['stage'] in ('archive-build','publish'): break
        intervals.append(dict(stage=row['stage'],started_at=previous,ended_at=row['created_at'],
            elapsed_seconds=seconds(previous,row['created_at'])))
        previous=row['created_at']
    return dict(value,route_intervals=intervals,snapshot_boundary='before-publication; receipt intervals include operator wait')


def concise(value):
    return {k:v for k,v in value.items() if k not in ('requests','attempts','route_intervals')} if value else None
