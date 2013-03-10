import os
import urlparse

from flask import Flask, abort, jsonify, request
from logbook import error, info
from redis import StrictRedis
from redis.exceptions import ConnectionError

app = Flask(__name__)

if os.environ.get('REDISCLOUD_URL'):
    url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
    redis = StrictRedis(host=url.hostname, port=url.port, password=url.password)
else:
    redis = StrictRedis()


@app.route('/total')
def total():
    """Returns the total stats across all repos"""
    try:
        total = redis.hgetall('total')
    except ConnectionError:
        abort(503)
    return jsonify(total=total)


@app.route('/repo/<path:repo>', methods=['GET', 'POST'])
def repo_stats(repo):
    """Router for repo stats"""
    if request.method == 'GET':
        return get_stats(repo)
    else:
        return update_stats(repo, request)


def update_stats(repo, request):
    """Updates the stats for a specific repo"""
    try:
        pipe = redis.pipeline()
        print request
        print request.form
        print request.json
        images = request.json.get('images')

        for image in images:
            full_name = "{repo}:{image_name}".format(repo=repo, image_name=image['name'])
            key = "shrunk:{0}".format(repo)
            size = image['size']
            pipe.sadd(key, full_name)
            mapping = {
                'name': image['name'],
                'size:original': size['original'],
                'size:remaining': size['remaining'],
                'size:reduced': size['reduced'],
            }
            pipe.hmset(full_name, mapping)

            # Update totals
            pipe.hincrby('total', 'size:original', amount=size['original'])
            pipe.hincrby('total:{0}'.format(repo), 'size:original', amount=size['original'])
            pipe.hincrby('total', 'size:remaining', amount=size['remaining'])
            pipe.hincrby('total:{0}'.format(repo), 'size:remaining', amount=size['remaining'])
            pipe.hincrby('total', 'size:reduced', amount=size['reduced'])
            pipe.hincrby('total:{0}'.format(repo), 'size:reduced', amount=size['reduced'])

        info("UPDATE STATS FOR {0}: {1}".format(repo, pipe.command_stack))
        pipe.execute()
    except ConnectionError:
        abort(503)

    return "OK"


def get_stats(repo):
    """Gets the stats for a specific repo"""
    info("GET STATS FOR {0}".format(repo))

    try:
        keys = redis.smembers("shrunk:{0}".format(repo))
        if not keys:
            error("REPO NOT FOUND: {0}".format(repo))
            abort(404)

        files = [redis.hgetall(key) for key in keys]
        total = redis.hgetall('total:{0}'.format(repo))
    except ConnectionError:
        abort(503)
    return jsonify(files=files, total=total)


def bool_env(val):
    """Replaces string based environment values with Python booleans"""
    return True if os.environ.get(val, False) == 'True' else False

if __name__ == '__main__':
    app.debug = bool_env('DEBUG')
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)
