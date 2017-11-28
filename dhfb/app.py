import os
import time
from functools import wraps

import boto3

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, make_response, flash, Response

from flask_env import MetaFlaskEnv
from flask_oauthlib.client import OAuth


app = Flask(__name__)
app.config.from_object(__name__)


class Configuration(metaclass=MetaFlaskEnv):
    ENV_PREFIX = 'DHFB_'
    AWS_KEY_ID = ''
    AWS_SECRET = ''
    S3_BUCKET_NAME = ''
    CHUNK_SIZE = 1024
    ABC_CLIENT_ID = ''
    ABC_CLIENT_SECRET = ''
    ABC_BASE_URL = ''
    ABC_TOKEN_URL = ''
    ABC_AUTHORIZE_URL = ''
    ABC_LOGOUT_URL = ''

app.config.from_object(Configuration)


oauth = OAuth(app)

abc = oauth.remote_app(
   'abc',
   base_url=app.config['ABC_BASE_URL'],
   request_token_url=None,
   access_token_url=app.config['ABC_TOKEN_URL'],
   authorize_url=app.config['ABC_AUTHORIZE_URL'],
   consumer_key=app.config['ABC_CLIENT_ID'],
   consumer_secret=app.config['ABC_CLIENT_SECRET'],
   access_token_method='POST'
)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'abc_token' in session:
            me = abc.get('/api/v1/user/me/')
            if me.status != 200:
                return redirect(url_for('login', next=request.url))
        else:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@abc.tokengetter
def get_abc_oauth_token():
    return session.get('abc_token')


@app.route('/login')
def login():
    if 'next' in request.args:
        session['next'] = request.args['next']  # fallback as ABC don't yet understand next
    return abc.authorize(callback=url_for('authorized', _external=True), next=request.args['next'])


@app.route('/logout')
def logout():
    session.pop('abc_token', None)
    return redirect(app.config['ABC_LOGOUT_URL'])


@app.route('/login/authorized')
def authorized():
    resp = abc.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason=%s error=%s resp=%s' % (
            request.args['error'],
            request.args['error_description'],
            resp)
    session['abc_token'] = (resp['access_token'], '')

    if 'next' in request.args:
        next_url = request.args['next']
    elif 'next' in session:
        next_url = session.pop('next', None)
    else:
        next_url = url_for('index')
    print(next_url)
    return redirect(next_url)


def get_s3_client():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    def _get_s3_client():
        s3_client = boto3.client(
            's3',
            use_ssl=True,
            aws_access_key_id=app.config['AWS_KEY_ID'],
            aws_secret_access_key=app.config['AWS_SECRET']
        )
        return s3_client

    if not hasattr(g, 's3_client'):
        g.s3_client = _get_s3_client()
    return g.s3_client


def _ls(path):
    """
    renders list of files in a given path (namespace)
    :param path:
    :return: response object of rendered page
    """
    s3 = get_s3_client()

    if not path:
        original_path = ''
        path = ''
    else:
        original_path = path
        path += '/'

    s3_response = s3.list_objects(Bucket=app.config['S3_BUCKET_NAME'], Prefix=path, Delimiter='/')

    if 'Contents' in s3_response:
        ls_dict = map(lambda x: {
            'name': os.path.split(x['Key'])[1],
            'size': x['Size'],
            'path': '/storage/'+x['Key']
        }, s3_response['Contents'])
        return render_template('ls.html', path=original_path, contents=ls_dict)
    else:
        return render_template('ls_empty.html', path=original_path)


def _get(path):
    """
    attempts to get a file from s3 and stream it
    no file is locally stored
    if file doesn't exist (NoSuchKey) then falls back to listing objects from namespace/dir
    :param path:
    :return: http response object
    """
    s3 = get_s3_client()

    try:
        s3_response = s3.get_object(Bucket=app.config['S3_BUCKET_NAME'],
                                    Key=path)
    except s3.exceptions.NoSuchKey as e:
        return _ls(path)

    def generate_file(result):
        for chunk in iter(lambda: result['Body'].read(int(app.config['CHUNK_SIZE'])), b''):
            yield chunk

    _, filename = os.path.split(path)
    response = Response(generate_file(s3_response), mimetype=s3_response['ContentType'])
    response.headers.add('Content-Disposition', 'attachment', filename=filename)
    return response


@app.route('/storage/<path:path>')
@app.route('/storage/')
@login_required
def storage(path=None):
    if path is None:
        return _ls('')
    elif path.endswith('/'):
        return _ls(path[:-1])
    else:
        return _get(path)


@app.route('/')
@login_required
def index():
    return redirect(url_for('storage'))


@app.route('/check')
def check():
    start_time = time.perf_counter()

    try:
        s3 = get_s3_client()
        s3_response = s3.list_objects(Bucket=app.config['S3_BUCKET_NAME'], Prefix='', Delimiter='')
        if 'Contents' in s3_response:
            status = 'OK'
        else:
            status = 'Empty S3'
    except Exception as e:
        status = 'S3 error: {}'.format(e)

    totaltime = time.perf_counter() - start_time
    rendered = render_template('pingdom.xml', status=status, totaltime=totaltime)
    response = make_response(rendered)
    response.headers["Content-Type"] = "application/xml"
    return response


