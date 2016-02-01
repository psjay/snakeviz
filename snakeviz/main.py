#!/usr/bin/env python

import pstats
import base64
import cProfile
import io
import logging
import os.path
import pickle
import re  # noqa
from pstats import Stats

import tornado.ioloop
import tornado.web

from snakeviz.stats import table_rows, json_stats

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'debug': True,
    'gzip': True
}


class DictSourceStats(Stats):
    def load_stats(self, arg):
        self.stats = arg


class VizHandler(tornado.web.RequestHandler):

    def get(self):
        pr = cProfile.Profile()
        pr.enable()
        re.compile("foo|bar")
        pr.disable()
        sortby = 'cumulative'
        ps = pstats.Stats(pr).sort_stats(sortby)
        self.render(
            'viz.html', profile_name='Visual Profiler',
            table_rows=table_rows(ps), callees=json_stats(ps))

    def post(self):
        content = self.get_argument('content')
        s = None
        if not content or not content.strip():
            raise tornado.web.HTTPError(400)
        try:
            content = base64.b64decode(content)
            s = DictSourceStats(pickle.loads(content))
        except Exception:
            logging.warn('Load stats failed.', exc_info=True)
            raise tornado.web.HTTPError(400)

        if not isinstance(s, Stats):
            raise tornado.web.HTTPError(400)

        self.render(
            'viz.html', profile_name='Visual Profiler',
            table_rows=table_rows(s), callees=json_stats(s))


handlers = [(r'/', VizHandler)]

app = tornado.web.Application(handlers, **settings)


def main():
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
