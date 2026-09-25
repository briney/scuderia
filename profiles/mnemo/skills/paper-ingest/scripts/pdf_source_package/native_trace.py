"""Read-only native scope events; no inferred clipping lifetime from drawing levels.

MuPDF's installed fitz/device.h and FzDevice2 expose each clip/pop and group/end
callback. Sequence numbers here count ALL paint callbacks, including empty paths.
"""


from collections import Counter


import pymupdf as fitz


PAINTS = {'fill_path': 'fill-path', 'stroke_path': 'stroke-path',
          'fill_text': 'fill-text', 'stroke_text': 'stroke-text',
          'ignore_text': 'ignore-text', 'fill_shade': 'fill-shade',
          'fill_image': 'fill-image', 'fill_image_mask': 'fill-imgmask'}


PATH_CLIPS = ('clip_path', 'clip_stroke_path')


HIDDEN_CLIPS = ('clip_text', 'clip_stroke_text', 'clip_image_mask')


class NativeTrace(fitz.mupdf.FzDevice2):
    def __init__(self):
        super().__init__()
        self.events, self.paints, self.stack, self.scopes, self.anomalies = [], [], [], [], []
        for name in (*PAINTS, *PATH_CLIPS, *HIDDEN_CLIPS, 'pop_clip', 'begin_group', 'end_group',
                     'begin_mask', 'end_mask', 'begin_tile', 'end_tile'):
            getattr(self, 'use_virtual_' + name)()

    def event(self, name):
        index = len(self.events)
        self.events.append({'event': name, 'before_paint': len(self.paints)})
        return index

    def paint(self, name):
        self.paints.append({'seqno': len(self.paints), 'type': PAINTS[name],
                            'stack': [dict(s) for s in self.stack]})

    def open_scope(self, name):
        index = self.event(name)
        represented = name in PATH_CLIPS or name == 'group'
        occurrence = len(self.scopes) + 1 if represented else None
        scope = {'type': name, 'occurrence': occurrence, 'level': len(self.stack), 'event_index': index}
        if represented:
            self.scopes.append({**scope, 'parents': [s['occurrence'] for s in self.stack if s['occurrence'] is not None]})
        self.stack.append(scope)

    def pop_clip(self, *args):
        self.event('pop_clip')
        if not self.stack or self.stack[-1]['type'] == 'group':
            self.anomalies.append({'event': 'unexpected_pop_clip', 'before_paint': len(self.paints)})
        else:
            self.stack.pop()

    def begin_group(self, *args):
        self.open_scope('group')
        self.events[-1]['event'] = 'begin_group'

    def end_group(self, *args):
        self.event('end_group')
        if not self.stack or self.stack[-1]['type'] != 'group':
            self.anomalies.append({'event': 'unexpected_end_group', 'before_paint': len(self.paints)})
        else:
            self.stack.pop()

    def begin_mask(self, *args):
        self.event('begin_mask')
        self.anomalies.append({'event': 'unsupported_soft_mask', 'before_paint': len(self.paints)})

    def end_mask(self, *args):
        self.open_scope('soft-mask')
        self.events[-1]['event'] = 'end_mask'

    def begin_tile(self, *args):
        self.event('begin_tile')
        self.anomalies.append({'event': 'unsupported_tile', 'before_paint': len(self.paints)})
        return 0

    def end_tile(self, *args):
        self.event('end_tile')


def _paint_callback(name):
    def callback(self, *args):
        self.paint(name)
    return callback


def _clip_callback(name):
    def callback(self, *args):
        self.open_scope(name)
    return callback


for _name in PAINTS:
    setattr(NativeTrace, _name, _paint_callback(_name))


for _name in (*PATH_CLIPS, *HIDDEN_CLIPS):
    setattr(NativeTrace, _name, _clip_callback(_name))


def trace_page(page, bboxlog, records):
    device = NativeTrace()
    fitz.mupdf.fz_run_page(page.this, device, fitz.mupdf.FzMatrix(), fitz.mupdf.FzCookie())
    fitz.mupdf.fz_close_device(device)
    matches = [p['type'] for p in device.paints] == [b['type'] for b in bboxlog]
    blockers = list(device.anomalies)
    if not matches:
        blockers.append({'event': 'native-paint-sequence-does-not-match-bboxlog'})
    if device.stack:
        blockers.append({'event': 'unclosed-native-scopes'})
    represented = [(i, r) for i, r in enumerate(records) if r['type'] in ('clip', 'group')]
    correspondence = []
    if len(represented) != len(device.scopes):
        blockers.append({'event': 'extended-scope-record-count-mismatch'})
    else:
        for (index, record), scope in zip(represented, device.scopes):
            expected = 'group' if scope['type'] == 'group' else 'clip'
            if record['type'] != expected or record['level'] != scope['level']:
                blockers.append({'event': 'extended-scope-kind-or-level-mismatch', 'drawing_index': index})
            correspondence.append({'scope_occurrence': scope['occurrence'], 'drawing_index': index,
                                   'native_event_index': scope['event_index'], 'native_kind': scope['type'],
                                   'level': scope['level'], 'parents': scope['parents']})
    return {'paint_sequence_matches_bboxlog': matches, 'paint_count': len(device.paints),
            'events': device.events, 'paints': device.paints, 'represented_scopes': device.scopes,
            'scope_record_correspondence': correspondence, 'blockers': blockers,
            'event_counts': dict(Counter(e['event'] for e in device.events)),
            'unclosed_scopes': device.stack,
            'occurrence_numbering': 'One shared counter for represented path/stroke clips and transparency groups; hidden clips have null occurrence but tracked native lifetime.'}
