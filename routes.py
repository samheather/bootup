routes_onerror = [
  ('init/400', '/init/default/login'),
  ('init/*', '/init/static/fail.html'),
  ('*/404', '/init/static/cantfind.html'),
  ('*/*', '/init/error/index')
]
