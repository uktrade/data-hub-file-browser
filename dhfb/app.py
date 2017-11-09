import os
import time

import boto3

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, make_response, flash, Response

from flask_env import MetaFlaskEnv


app = Flask(__name__)
app.config.from_object(__name__)


class Configuration(metaclass=MetaFlaskEnv):
    ENV_PREFIX = 'DHFB_'
    AWS_KEY_ID = ''
    AWS_SECRET = ''
    S3_BUCKET_NAME = ''
    CHUNK_SIZE = 1024

app.config.from_object(Configuration)


def get_s3_client():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    def _get_s3_client():
        s3_client = boto3.client(
            's3',
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
        s3_response = s3.get_object(Bucket=app.config['S3_BUCKET_NAME'], Key=path)
    except s3.exceptions.NoSuchKey as e:
        return _ls(path)

    def generate_file(result):
        for chunk in iter(lambda: result['Body'].read(int(app.config['CHUNK_SIZE'])), b''):
            yield chunk

    _, filename = os.path.split(path)
    return Response(generate_file(s3_response), mimetype=s3_response['ContentType'],
                    headers={'Content-Disposition': 'attachment;filename=' + filename})


@app.route('/storage/<path:path>')
@app.route('/storage/')
def storage_ls(path=None):
    if path is None:
        return _ls('')
    elif path.endswith('/'):
        return _ls(path[:-1])
    else:
        return _get(path)


@app.route('/')
def index():
    abort(403)


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
