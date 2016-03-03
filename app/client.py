"""

bokeh serve --allow-websocket-origin=127.0.0.1:5000 . &
python client.py

- be sure client.py flask app is running on port 5000, and it should load just fine.

"""

import flask
from bokeh.embed import autoload_server
from bokeh.util.string import encode_utf8

# Set up flask app
app = flask.Flask("Estuary GUI")
app.debug = True
PORT = 5000


@app.route("/estuary")
def root():
    """ Returns the web interface to the estuary model """

    html = flask.render_template(
        'app.html',
        bokeh=autoload_server(None, session_id=None, app_path='/app'),
    )
    return encode_utf8(html)


@app.route('/static/<path:path>')
def static_proxy_(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


if __name__ == "__main__":
    print(__doc__)
    app.run(port=PORT)
