"""Bounded canonical JSON retrieval; raw source records cached outside the brain."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime

class MetadataUnavailable(urllib.error.URLError):
    pass


def transient(exc):
    return (isinstance(exc,urllib.error.HTTPError) and exc.code in (429,500,502,503,504)) or (isinstance(exc,(urllib.error.URLError,TimeoutError)) and not isinstance(exc,urllib.error.HTTPError))


def fetch_json(url,retries=1,backoff=2.0,*,cache=None,ua='mnemo-metadata/1',timeout=10):
    path=None
    if cache:
        from article_archive_compat.article_runtime import outside_instance, absolute
        directory=outside_instance(cache); directory.mkdir(parents=True,exist_ok=True)
        path=absolute(directory/(hashlib.sha256(url.encode()).hexdigest()+'.json'))
        if path.exists():
            row=json.loads(path.read_text()); raw=row['raw'].encode()
            if row['url']!=url or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('metadata-cache-binding')
            if 0<=time.time()-row['fetched_at']<86400:return json.loads(raw)
    deadline=time.monotonic()+30
    for attempt in range(min(retries,1)+1):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':ua})
            with urllib.request.urlopen(request,timeout=min(timeout,max(.1,deadline-time.monotonic()))) as response:
                raw=response.read(16_000_001)
            if len(raw)>16_000_000:raise ValueError('metadata-response-too-large')
            text=raw.decode('utf-8'); result=json.loads(text)
            if path:
                row=dict(url=url,raw=text,sha256=hashlib.sha256(raw).hexdigest(),fetched_at=time.time())
                fd,name=tempfile.mkstemp(dir=path.parent,prefix='.metadata-')
                try:
                    with os.fdopen(fd,'w') as stream:json.dump(row,stream);stream.flush();os.fsync(stream.fileno())
                    os.replace(name,path)
                finally:
                    if os.path.exists(name):os.unlink(name)
            return result
        except (urllib.error.URLError,TimeoutError) as exc:
            if not transient(exc):raise
            delay=backoff
            header=getattr(exc,'headers',None)
            retry_after=header.get('Retry-After') if header else None
            if retry_after:
                try:delay=max(delay,float(retry_after))
                except ValueError:
                    try:delay=max(delay,parsedate_to_datetime(retry_after).timestamp()-time.time())
                    except (ValueError,TypeError):pass
            if attempt>=min(retries,1) or delay>5 or time.monotonic()+delay>=deadline:
                raise MetadataUnavailable('temporarily-unavailable; defer metadata verification, retain job') from exc
            time.sleep(delay)


def epmc_record(pmid,fetch_json):
    query=urllib.parse.quote('EXT_ID:'+str(pmid)+' AND SRC:MED')
    data=fetch_json('https://www.ebi.ac.uk/europepmc/webservices/rest/search?query='+query+'&format=json&resultType=core')
    rows=[r for r in data.get('resultList',{}).get('result',[]) if str(r.get('id'))==str(pmid) and r.get('source')=='MED']
    if len(rows)!=1:return None
    row=rows[0]
    if 'authorList' not in row:raise ValueError('Europe PMC record lacks complete author list')
    authors=row['authorList'].get('author',[])
    return dict(title=row.get('title',''),year=row.get('pubYear'),doi=(row.get('doi') or '').lower() or None,
        n_authors=sum(not a.get('collectiveName') for a in authors),source='Europe PMC',
        first_author=next((a.get('fullName','') for a in authors if not a.get('collectiveName')),''),name_format='surname_first',
        retracted=any('retract' in p.lower() for p in row.get('pubTypeList',{}).get('pubType',[])))
