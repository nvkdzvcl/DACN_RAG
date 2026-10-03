"""Serve the existing Vite build on the API origin when explicitly enabled."""
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app, directory):
    directory = Path(directory).resolve()
    pages = {'/': 'index.html', '/index.html': 'index.html', '/chat': 'index.html',
             '/widget-demo.html': 'widget-demo.html', '/widget.js': 'widget.js'}
    if any(not (directory / name).is_file() for name in set(pages.values())) or not (directory / 'assets').is_dir():
        raise RuntimeError('Frontend build missing. Run npm --prefix frontend run build first.')

    def page(request: Request):
        return FileResponse(directory / pages[request.url.path], headers={'Cache-Control': 'no-cache'})

    for path in pages:
        app.add_api_route(path, page, methods=['GET', 'HEAD'], include_in_schema=False)
    # Explicit paths keep unknown API routes and private files out of SPA fallback.
    app.mount('/assets', StaticFiles(directory=directory / 'assets'), name='frontend-assets')

    if (directory / 'fonts').is_dir():
        app.mount('/fonts', StaticFiles(directory=directory / 'fonts'), name='frontend-fonts')
