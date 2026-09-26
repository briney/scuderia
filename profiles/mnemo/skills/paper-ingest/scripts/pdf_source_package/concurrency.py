"""Per-operation inference pool; reservations and result handling stay serial."""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import os

DEFAULT_VLM_CONCURRENCY = 3


def concurrency_limit(value=None):
    if value is None:
        value = int(os.environ.get('PAPER_INGEST_VLM_CONCURRENCY', DEFAULT_VLM_CONCURRENCY))
    if type(value) is not int or value < 1:
        raise ValueError('vlm-concurrency-must-be-positive-integer')
    return value


def run_requests(rows, prepare, request, consume, *, vlm_concurrency=None, stopped=lambda: False):
    """Only request runs in workers. Drain all dispatched calls before raising.

    consume receives the Future so it can persist transport exceptions too;
    returning True stops dispatch without discarding other in-flight results.
    """
    limit = concurrency_limit(vlm_concurrency)
    rows = iter(rows); pending = {}; error = None; stop = False; exhausted = False
    with ThreadPoolExecutor(max_workers=limit, thread_name_prefix='paper-vlm') as pool:
        try:
            while True:
                # Recheck after every serial export and reservation: another
                # response may have completed while the coordinator was busy.
                done = [future for future in pending if future.done()]
                if done:
                    for future in done:
                        item = pending.pop(future)
                        try:
                            stop = bool(consume(item, future)) or stop
                        except BaseException as exc:
                            error = error or exc
                            stop = True
                    continue
                if not (stop or exhausted or stopped()) and len(pending) < limit:
                    try:
                        row = next(rows)
                    except StopIteration:
                        exhausted = True
                        continue
                    item = prepare(row)
                    pending[pool.submit(request, item)] = item
                    continue
                if not pending:
                    break
                wait(pending, return_when=FIRST_COMPLETED)
        except BaseException as exc:
            error = error or exc
        finally:
            # Preparation failures and interruptions also retain active outcomes.
            for future, item in pending.items():
                try:
                    consume(item, future)
                except BaseException as exc:
                    error = error or exc
    if error is not None:
        raise error
