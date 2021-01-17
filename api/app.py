from flask import Flask, request
import utils


app = Flask(__name__)


@app.route('/api/v1/search', methods=['GET'])
def search():
    query = request.args.get('q', None)
    if not query:
        return {'message': 'Query parameter missing'}, 400
    results = utils.search_db(query)
    if results:
        return results, 200
    return {'message': 'No CPUs found matching that search'}, 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
