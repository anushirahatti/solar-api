from flask import Flask, jsonify, request


app = Flask(__name__)


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return jsonify({"data": "Good Afternoon, Aniruddha!!!"})

@app.route('/stations', methods=['GET', 'POST'])
def getStations():
    if request.method == 'GET':
        data = {"stations": "Here are the requested stations..."}
        return jsonify({"data": data}), 201
    else:
        return jsonify({"data": "Data Uploaded"})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)