import json
from collections.abc import MutableMapping, Iterable

from drf_renderer_xlsx.mixins import XLSXFileMixin
from drf_renderer_xlsx.renderers import XLSXRenderer as BaseXLSXRenderer

class XLSXRenderer(BaseXLSXRenderer):

    def _flatten(self, data, parent_key="", key_sep=".", list_sep="\n "):
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{key_sep}{k}" if parent_key else k
            if isinstance(v, MutableMapping):
                items.extend(self._flatten(v, new_key, key_sep=key_sep).items())
            elif isinstance(v, Iterable) and not isinstance(v, str):
                if len(v) > 0 and (not isinstance(v[0], str) and isinstance(v[0], Iterable)):
                    # array of array; write as json
                    items.append((new_key, json.dumps(v)))
                else:
                    # Flatten the array into a comma separated string to fit
                    # in a single spreadsheet column
                    items.append((new_key, list_sep.join(v)))
            else:
                if isinstance(v, str) and (v.startswith('http://') or v.startswith('https://')):
                    v = '=HYPERLINK("{}", "{}")'.format(v, v)
                items.append((new_key, v))
        return dict(items)
