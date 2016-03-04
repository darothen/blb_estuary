#!/usr/bin/env bash
""" BLB Estuary Model User Interface

This Flask app serves a simple applet with an embedded Bokeh app which lets
users interact with the estuary box model developed for the Blue Lobster
Bowl at MIT (March 5, 2016).


Running locally in development mode
-----------------------------------

Navigate to this directory. Start the bokeh server,

$ bokeh serve --allow-websocket-origin=localhost:5000 . &

This will serve the app which provides the estuary model gui. We wish to
provide a webpage with the app embedded in it, via a simple Flask app. The
Flask app is launched directly via Python,

$ python client.py

The default settings should be fine for this purpose. Now, you can connect
to the app by pointing your browser to localhost:5000/estuary


Deploying on Yavin Prime
------------------------

Again, navigate to this directory. Start the bokeh server, with a configuration
for accepting incoming client connections across domains,

$ bokeh serve --allow-websocket-origin {HOST}:{FLASK-PORT} --host {HOST}:{BOKEH-PORT} . &

Note the selection of arguments which will be passed to client via the
command-line interface, which is done right after this:

$ python client.py --host {HOST} --flask-port {FLASK-PORT} \
                   --bokeh-port {BOKEH-PORT} --deploy

Leave it running, and you're all set! You'll see Flask and Bokeh update you
as clients connect/disconnect to the app.

"""

import flask
from bokeh.embed import autoload_server
from bokeh.util.string import encode_utf8

from argparse import ArgumentParser, RawTextHelpFormatter
parser = ArgumentParser(description=__doc__,
                        formatter_class=RawTextHelpFormatter)
parser.add_argument("--host", type=str, default="yavinprime.mit.edu",
                    help="Hostname of deployment Bokeh server "
                         "(ignored during debug mode)")
parser.add_argument("--flask-port", type=int, default=5000,
                    help="Port for serving Flask app")
parser.add_argument("--bokeh-port", type=int, default=5006,
                    help="Port where Bokeh server is listening")
parser.add_argument("--deploy", action="store_true",
                    help="Run in deployment mode; if omitted, runs in debug")

# Set up flask app
app = flask.Flask("Estuary GUI")


@app.route("/estuary")
def root():
    """ Returns the web interface to the estuary model """

    bokeh_div = autoload_server(None, session_id=None,
                                app_path='/app', url='')
    left, right = bokeh_div.split('src="')
    bokeh_div = left + 'src="http://yavinprime.mit.edu:5006' + right

    html = flask.render_template(
        'app.html',
        # bokeh=autoload_server(None, session_id=None,
        #                       app_path='/app', url=''),
        bokeh=bokeh_div,
    )
    return encode_utf8(html)


@app.route('/static/<path:path>')
def static_proxy_(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


if __name__ == "__main__":

    args = parser.parse_args()

    # Set up flask app
    app = flask.Flask("Estuary GUI")
    app.debug = not args.deploy

    HOST = '0.0.0.0'
    PORT = args.flask_port

    @app.route("/estuary")
    def root():
        """ Returns the web interface to the estuary model """

        # Over-write url if in deployment; else, accept default.
        autoload_kws = dict(app_path="/app", session_id=None)
        if args.deploy:
            autoload_kws['url'] = ''
        bokeh_div = autoload_server(None, **autoload_kws)
        if args.deploy:
            left, right = bokeh_div.split('src="')
            deployment_src = 'src="http://{:s}:{:d}'.format(
                args.host, args.bokeh_port
            )
            bokeh_div = left + deployment_src + right

        html = flask.render_template(
            'app.html',
            # bokeh=autoload_server(None, session_id=None,
            #                       app_path='/app', url=''),
            bokeh=bokeh_div,
        )
        return encode_utf8(html)

    @app.route('/static/<path:path>')
    def static_proxy_(path):
        # send_static_file will guess the correct MIME type
        return app.send_static_file(path)

    # Run the app
    app.run(port=PORT, host=HOST)
