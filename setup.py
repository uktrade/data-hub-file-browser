from setuptools import setup

setup(
    name='dhfb',
    packages=['dhfb'],
    include_package_data=True,
    install_requires=[
        'flask', 'boto3', 'Flask-Env', 'gunicorn', 'flask_oauthlib'
    ],
)
