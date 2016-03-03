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
app.debug = False
HOST = '0.0.0.0'
PORT = 5000


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
    print(__doc__)
    app.run(port=PORT, host=HOST)
