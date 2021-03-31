from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import requests
import json
import uuid
from opencage.geocoder import OpenCageGeocode


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
    return "<center><h1>Welcome to Solar App API!</h1> <br/><br/> <h3><strong><p>Here are the options:</p> <ul><li>/stations</li></ul></strong></h3></center>"



@app.route('/stations', methods=['GET', 'POST'])
def getStations():

    if request.method == 'GET':

        # store the request parameters in  variables
        #lat = request.get_json().get('lat')
        lat = '47.59163'
        print(lat)
        #lng = request.get_json().get('lng')
        lng = '-120.1549'
        print(lng)
        #start = request.get_json().get('start')
        start = '2018-10-03'
        print(start)
        #end = request.get_json().get('end')
        end = '2019-09-10'
        print(end)


        # convert latitude and longitude to FIPS to set locationid for filtering stations        
        key = "17953106d8134918b9ffdd624065750a"
        geocoder = OpenCageGeocode(key)
        results = geocoder.reverse_geocode(lat, lng)
        country_code = results[0]['components']['country_code']
        fips = ''
        if country_code == 'us':
            fips = results[0]['annotations']['FIPS']['county']
        else:
            return jsonify({"Info": "Not a location within United States. Please choose location within the United States."})


        # Initialize Firestore DB if not already initialized
        cred = credentials.Certificate('key.json')

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()

        # construct query to check if the data exists in the database
        query_ref = db.collection(u'queries').where(u'latitude', u'==', u'{}'.format(lat)).where(u'longitude', u'==', u'{}'.format(lng)).where(u'fips', u'==', u'{}'.format(fips)).where(u'startDate', u'==', u'{}'.format(start)).where(u'endDate', u'==', u'{}'.format(end))
        docs = query_ref.stream()

        # check length of docs
        listSize = len(list(docs))
        print(listSize)      

        # if data doesn't exist in database, fetch data from API, store in database and return the query results
        if listSize == 0:

            # set the user parameters to NCDC URL and get filtered results
            url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations?limit=1000&locationid=FIPS:{}&startdate={}&enddate={}".format(fips, start, end)
            #url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations/COOP:010125"
            token = "ylPeWbpuHSsbXHmtqurCJXfejdryavRe"
            headers = {
                'token': token,
                'Content-Type': 'application/json; charset=utf-8'
            }
    
            response = requests.get(url, headers=headers).text
            response_info = json.loads(response)
            
            if len(response_info) == 0:
                return jsonify({"Info": "No results available to match the query. Please submit modified query."})

            # store retrieved data in firestore
            # create a new doc entry for the user query in firebase
            doc_id = str(uuid.uuid4().hex)

            doc_ref = db.collection(u'queries').document(u'{}'.format(doc_id))
            doc_ref.set({
                u'id': u'{}'.format(doc_id),
                u'latitude': u'{}'.format(lat),
                u'longitude': u'{}'.format(lng),
                u'fips': u'{}'.format(fips),
                u'startDate': u'{}'.format(start),
                u'endDate': u'{}'.format(end),
                u'extent': u'',
                u'dataCoverage': u'',
                u'results': response_info['results'],
                u'resultsCount': response_info['metadata']['resultset']['count'] 
            })

            return jsonify({"results": response_info['results']}), 201


        # if data exists, return the query results from database    
        else: 

            docId = ''

            docs = query_ref.stream()
            for doc in docs:
                docId = doc.id

            doc_rf = db.collection(u'queries').document(u'{}'.format(docId))

            doc = doc_rf.get()
            if doc.exists:
                response_info = doc.to_dict()
                return jsonify({"results": response_info['results']}), 201
            else:
                return jsonify({"results": []})
 

    else:
        return jsonify({"data": "Data Uploaded"}), 201


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