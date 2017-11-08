import os

import boto3

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, Response

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


def _ls(path):
    """
    renders list of files in a given path (namespace)
    :param path:
    :return: response object of rendered page
    """
    s3 = boto3.client('s3')

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
    s3 = boto3.client('s3')

    try:
        s3_response = s3.get_object(Bucket=app.config['S3_BUCKET_NAME'], Key=path)
    except s3.exceptions.NoSuchKey as e:
        return _ls(path)

    def generate_file(result):
        for chunk in iter(lambda: result['Body'].read(app.config['CHUNK_SIZE']), b''):
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


