from flask import Flask, jsonify, request
from firebase_admin import credentials, firestore, initialize_app
import os
import requests
import json


# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
#stations_ref = db.collection('stations')


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""

    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations/"
    token = "ylPeWbpuHSsbXHmtqurCJXfejdryavRe"
    headers = {
        'token': token,
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    r = requests.get(url, headers=headers)

    print(type(r))
    print(r)


    return jsonify({"data": "Good Afternoon, Aniruddha!!!"})

@app.route('/stations', methods=['GET', 'POST'])
def getStations():

    if request.method == 'GET':
        data = {"stations": "Here are the requested stations..."}
        return jsonify({"data": data}), 201
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