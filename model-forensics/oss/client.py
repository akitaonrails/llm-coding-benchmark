"""Explicit provider routing for the gpt-oss experiment; no retry/fallback."""
import json
import os
import time
import urllib.error
import urllib.request
import experiment as e


def call(profile,messages,max_tokens,timeout,secrets):
    body=dict(model=profile['model'],messages=messages,max_tokens=max_tokens,stream=False,**profile.get('parameters',{}))
    request=urllib.request.Request(profile['base_url']+'/chat/completions',data=e.kit.canonical(body).encode(),
        headers={'Authorization':'Bearer '+os.environ[profile['key_env']],'Content-Type':'application/json'})
    start=time.monotonic();row=dict(started_at=e.kit.now(),request_sha256=e.kit.digest(body),requested_max_tokens=max_tokens)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),e.kit.NoRedirect())
    try:
        with opener.open(request,timeout=timeout) as response:
            row['http_status']=response.status;raw=response.read(2_000_001)
            if len(raw)>2_000_000:row['status']='oversize_response'
            else:
                try:
                    data=json.loads(raw)
                    if data.get('error'):row.update(status='provider_error',error=data['error'])
                    else:
                        ch=data['choices'][0];text=ch['message'].get('content');finish=ch.get('finish_reason')
                        if text is not None and not isinstance(text,str):raise TypeError()
                        row.update(status='truncated' if finish=='length' else 'empty' if not text else 'ok' if finish=='stop' else 'nonstandard_finish',
                            text=text,finish_reason=finish,usage=data.get('usage'),provider=data.get('provider'),response_model=data.get('model'),system_fingerprint=data.get('system_fingerprint'),logprobs=ch.get('logprobs'))
                except (ValueError,TypeError,IndexError,KeyError,AttributeError):row['status']='invalid_response'
    except urllib.error.HTTPError as err:
        row.update(status='http_error',http_status=err.code)
        try:row['error']=json.loads(err.read(16000)).get('error')
        except (ValueError,AttributeError,OSError):pass
        finally:err.close()
    except (urllib.error.URLError,TimeoutError,OSError) as err:row.update(status='transport_error',error_type=type(err).__name__)
    row.update(finished_at=e.kit.now(),elapsed_seconds=time.monotonic()-start)
    return e.kit.redact(row,secrets)
