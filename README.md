# data-hub-file-browser

## Running in Docker

Linting and application testing can be performed in Docker.

### Setting up

Build the Docker image for docker-compose to use.

```bash
$ docker-compose -f docker-compose.test.yml build
```

### Running tests

```bash
$ docker-compose -f docker-compose.test.yml run app ./test.sh
```

This will first of all run the Flake8 linter, then the app tests.

## Environment Variables supported
- DHFB_AWS_KEY_ID = ''
- DHFB_AWS_SECRET = ''
- DHFB_S3_BUCKET_NAME = ''
- ABC_CLIENT_ID = ''
- ABC_CLIENT_SECRET = ''
- ABC_BASE_URL = ''
- ABC_TOKEN_URL = ''
- ABC_AUTHORIZE_URL = ''
- ABC_LOGOUT_URL = ''

### Optional
- DHFB_CHUNK_SIZE = 1024
