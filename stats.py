import os

from flask import Flask, jsonify, request
from redis import StrictRedis

app = Flask(__name__)
redis = StrictRedis()


@app.route('/repo/<path:repo>', methods=['GET', 'POST'])
def repo_stats(repo):
    if request.method == 'GET':
        return get_stats(repo)
    else:
        return update_stats(repo, request)


def update_stats(repo, request):
    pipe = redis.pipeline()
    date = request.json.get('date')
    branch = request.json.get('branch')
    commit = request.json.get('commit')
    files = request.json.get('files')

    for file in files:
        full_name = "{repo}:{file_name}".format(repo=repo, file_name=file['name'])
        key = "shrunk:{0}".format(repo)
        size = file['size']
        pipe.sadd(key, full_name)
        mapping = {
            'name': file['name'],
            'size:original': size['original'],
            'size:remaining': size['remaining'],
            'size:reduced': size['reduced'],
            'date': date,
            'branch': branch,
            'commit': commit,
        }
        pipe.hmset(full_name, mapping)

        # Update totals
        pipe.hincrby('total', 'size:original', amount=size['original'])
        pipe.hincrby('total:{0}'.format(repo), 'size:original', amount=size['original'])
        pipe.hincrby('total', 'size:remaining', amount=size['remaining'])
        pipe.hincrby('total:{0}'.format(repo), 'size:remaining', amount=size['remaining'])
        pipe.hincrby('total', 'size:reduced', amount=size['reduced'])
        pipe.hincrby('total:{0}'.format(repo), 'size:reduced', amount=size['reduced'])
        pipe.execute()

    return "OK"


def get_stats(repo):
    keys = redis.smembers("shrunk:{0}".format(repo))
    files = [redis.hgetall(key) for key in keys]
    total = redis.hgetall('total:{0}'.format(repo))
    return jsonify(files=files, total=total)


def bool_env(val):
    """Replaces string based environment values with Python booleans"""
    return True if os.environ.get(val, False) == 'True' else False

if __name__ == '__main__':
    app.debug = bool_env('DEBUG')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
