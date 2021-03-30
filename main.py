from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import requests
import json
import uuid


# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
#cred = credentials.Certificate('key.json')
#firebase_admin.initialize_app(cred)
#db = firestore.client()
#stations_ref = db.collection('stations')


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return "<h1><center>Welcome to Solar App API!</center></h1>"



@app.route('/populate')
def populate():

    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations?limit=1000"
    token = "ylPeWbpuHSsbXHmtqurCJXfejdryavRe"
    headers = {
        'token': token,
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    response = requests.get(url, headers=headers).text
    response_info = json.loads(response)

    # Initialize Firestore DB
    cred = credentials.Certificate('key.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    for result in response_info['results']:
        doc_id = str(uuid.uuid4().hex)
        db.collection(u'stations').document(u'{}'.format(doc_id)).set(result)


    return response_info['metadata']



@app.route('/stations', methods=['GET', 'POST'])
def getStations():

    if request.method == 'GET':

        # store the request parameters in  variables
        #lat = request.get_json().get('lat')
        lat = '47.59163'
        print(lat)
        #lng = request.get_json().get('lng')
        lng = '-122.1549'
        print(lng)
        #start = request.get_json().get('start')
        #print(start)
        #end = request.get_json().get('end')
        #print(end)

        # convert latitude and longitude to FIPS to set locationid for filtering stations
        url = "https://api.opencagedata.com/geocode/v1/json"
        key = "17953106d8134918b9ffdd624065750a"
        language = "en"
        coordinates = "{}, {}".format(lat, lng)
        headers = {
            'key': key,
            'language': language,
            'coordinates': coordinates,
            'Content-Type': 'application/json; charset=utf-8'
        }
    
        response = requests.get(url, headers=headers).text
        response_info = json.loads(response)



        data = response_info['results']['FIPS']['county']
        return jsonify({"FIPS": data}), 201
    else:
        return jsonify({"data": "Data Uploaded"})


# Create a Product
@app.route('/product', methods=['POST'])
def add_product():
  name = request.json['name']
  description = request.json['description']
  price = request.json['price']
  qty = request.json['qty']

  new_product = Product(name, description, price, qty)

  db.session.add(new_product)
  db.session.commit()

  return product_schema.jsonify(new_product)

# Get All Products
@app.route('/product', methods=['GET'])
def get_products():
  all_products = Product.query.all()
  result = products_schema.dump(all_products)
  return jsonify(result.data)

# Get Single Products
@app.route('/product/<id>', methods=['GET'])
def get_product(id):
  product = Product.query.get(id)
  return product_schema.jsonify(product)

# Update a Product
@app.route('/product/<id>', methods=['PUT'])
def update_product(id):
  product = Product.query.get(id)

  name = request.json['name']
  description = request.json['description']
  price = request.json['price']
  qty = request.json['qty']

  product.name = name
  product.description = description
  product.price = price
  product.qty = qty

  db.session.commit()

  return product_schema.jsonify(product)

# Delete Product
@app.route('/product/<id>', methods=['DELETE'])
def delete_product(id):
  product = Product.query.get(id)
  db.session.delete(product)
  db.session.commit()

  return product_schema.jsonify(product)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)