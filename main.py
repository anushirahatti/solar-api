from flask import Flask, jsonify


app = Flask(__name__)


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return jsonify({"data": "Good Afternoon, Aniruddha!!!"})

@app.route('/stations')
def getStations():
    """Return a friendly HTTP greeting."""
    return jsonify({"stations": "Here are the requested stations..."})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)