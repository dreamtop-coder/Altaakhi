import re

from django.utils.deprecation import MiddlewareMixin


class RemoveInventorySearchMiddleware(MiddlewareMixin):
    """Remove legacy Inventory search form from HTML responses when path contains 'inventory'.

    This surgically strips any <form>...</form> blocks that contain an input named
    'q' or a placeholder containing 'Search parts' (English/Arabic heuristic).
    """

    FORM_RE = re.compile(r"<form\b[^>]*>.*?</form>", re.IGNORECASE | re.DOTALL)

    def process_response(self, request, response):
        try:
            path = getattr(request, 'path', '') or ''
            if 'inventory' not in path.lower():
                return response

            content_type = response.get('Content-Type', '')
            if 'text/html' not in content_type.lower():
                return response

            content = response.content.decode(response.charset or 'utf-8', errors='replace')
            changed = False

            def _remove_form(m):
                block = m.group(0)
                low = block.lower()
                if 'name="q"' in low or 'placeholder="search parts"' in low or 'placeholder="بحث' in low or 'placeholder*="بحث"' in low:
                    nonlocal changed
                    changed = True
                    return ''
                return block

            new_content = self.FORM_RE.sub(_remove_form, content)
            if changed:
                response.content = new_content.encode(response.charset or 'utf-8')
                if response.get('Content-Length'):
                    try:
                        response['Content-Length'] = str(len(response.content))
                    except Exception:
                        pass
        except Exception:
            # Fail silently to avoid breaking responses
            return response
        return response
