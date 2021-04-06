from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests
import json
import uuid
from flask_cors import CORS, cross_origin
from geojson import Feature, Point
from turfpy.transformation import circle
from turfpy.measurement import bbox


# Initialize Flask app
app = Flask(__name__)

# securing the Backend API by allowing ONLY our Frontend application URL to access the API. 
api_cors_config = {
  "origins": ["https://solar-app-mecbn52fuq-uc.a.run.app"],
  "methods": ["OPTIONS", "GET", "POST"],
  "allow_headers": ["Authorization", "Content-Type"]
}

CORS(app)


@app.route('/')
def hello():
    """Return a friendly HTTP greeting and display API options."""
    return "<center><h1>Welcome to Solar App API!</h1> <br/><br/> <h3><strong><p>Here are the options:</p> <ul><li>/stations</li><li>/data</li></ul></strong></h3></center>"


# /stations - for querying the stations with user search criteria
@app.route('/stations', methods=['POST', 'GET'])
@cross_origin(**api_cors_config)
def getStations():
    """
    Takes the query inputs, returns filtered list of station that fit the query criteria.

    Parameters:
        lat    -  latitude
        lng    -  longitude
        start  -  start date
        end    -  end date
        net    -  net (in degrees) 

    Returns:
        results  -   list of stations
        count    -   number of stations
        doc_id   -   id of the document in database that contains retrieved data
        extent   -   extent under consideration
    
    """

    # store the request parameters in variables
    lat = request.get_json().get('lat')
    print(lat)
    lng = request.get_json().get('lng')
    print(lng)
    start = request.get_json().get('start')
    print(start)
    end = request.get_json().get('end')
    print(end)
    net = request.get_json().get('net')
    print(net)        

    # use latitude, longitude and net (in degrees) to generate values for extent        
    center = Feature(geometry=Point((float(lng), float(lat))))
    cc = circle(center, radius=int(net), steps=10, units='deg')
    print(json.dumps(cc, indent=4, sort_keys=True))
    print(bbox(cc))
    bbox_list = list(bbox(cc))
    extent = str(bbox_list[1]) + "," + str(bbox_list[0]) + "," + str(bbox_list[3]) + "," + str(bbox_list[2])
    print(extent) 
        

    # Initialize Firestore DB if not already initialized
    cred = credentials.Certificate('key.json')
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()

    # construct query to check if the data exists in the database
    query_ref = db.collection(u'queries').where(u'latitude', u'==', u'{}'.format(lat)).where(u'longitude', u'==', u'{}'.format(lng)).where(u'net', u'==', u'{}'.format(net)).where(u'extent', u'==', u'{}'.format(extent)).where(u'startDate', u'==', u'{}'.format(start)).where(u'endDate', u'==', u'{}'.format(end))
    docs = query_ref.stream()

    # check length of docs
    listSize = len(list(docs))
    print(listSize)      

    # if data doesn't exist in database, fetch data from API, store in database and return the query results
    if listSize == 0:

        # set the user parameters to NCDC URL and get filtered results
        url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations?limit=1000&datasetid=NORMAL_DLY&datatypeid=DLY-TAVG-NORMAL&datatypeid=DLY-TAVG-STDDEV&extent={}&startdate={}&enddate={}".format(extent, start, end)            

        token = "ylPeWbpuHSsbXHmtqurCJXfejdryavRe"
            
        headers = {
            'token': token,
            'Content-Type': 'application/json; charset=utf-8'
        }
    
        response = requests.get(url, headers=headers).text
        response_info = json.loads(response)
            
        if len(response_info) == 0:
            return jsonify({"Info": "No results available to match the query. Please submit modified query."}), 200

        # create a new doc entry for the user query in firebase
        doc_id = str(uuid.uuid4().hex)

        # store retrieved data in firestore
        doc_ref = db.collection(u'queries').document(u'{}'.format(doc_id))
        doc_ref.set({
            u'id': u'{}'.format(doc_id),
            u'latitude': u'{}'.format(lat),
            u'longitude': u'{}'.format(lng),
            u'net': u'{}'.format(net),
            u'startDate': u'{}'.format(start),
            u'endDate': u'{}'.format(end),
            u'extent': u'{}'.format(extent),
            u'dataCoverage': u'',
            u'results': response_info['results'],
            u'resultsCount': response_info['metadata']['resultset']['count'] 
        })

        return jsonify({"results": response_info['results'], "count": response_info['metadata']['resultset']['count'], "doc_id": doc_id, "extent": extent}), 200


    # if data exists, return the query results from database    
    else: 

        docId = ''

        # get id of the query document which contains same query
        docs = query_ref.stream()
        for doc in docs:
            docId = doc.id

        # fetch the document by obtained document id
        doc_rf = db.collection(u'queries').document(u'{}'.format(docId))
        doc = doc_rf.get()

        if doc.exists:
            response_info = doc.to_dict()
            return jsonify({"results": response_info['results'], "count": response_info['resultsCount'], "doc_id": docId, "extent": response_info['extent']}), 200
        else:
            return jsonify({"results": [], "count": 0, "doc_id": "", "extent": ""}), 200




# /data - for pulling the temperature data from the user selected station
@app.route('/data', methods=['POST', 'GET'])
@cross_origin(**api_cors_config)
def getdata():
    """
    Takes the query inputs, returns normal daily temperature data for the given set of inputs.

    Parameters:
        docId    -  id of the query document in database that contains retrieved data
        sid      -  station id
        start    -  start date
        end      -  end date
        extent   -  extent to consider 

    Returns:
        results       -   list of daily average temperature normal
        count         -   number of stations for daily average temperature normal
        results_std   -   list of daily average temperature std dev
        count_std     -   number of stations for daily average temperature std dev
    
    """

    # store the request parameters in  variables
    docId = request.get_json().get('doc_id')
    print(docId)
    sid = request.get_json().get('stationid')
    print(sid)
    extent = request.get_json().get('extent')
    print(extent)
    start = request.get_json().get('start')
    print(start)
    end = request.get_json().get('end')
    print(end)


    # Initialize Firestore DB if not already initialized
    cred = credentials.Certificate('key.json')
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()

    # construct query to check if the data exists in the database
    query_ref = db.collection(u'temps').where(u'query_doc', u'==', u'{}'.format(docId)).where(u'stationid', u'==', u'{}'.format(sid)).where(u'startDate', u'==', u'{}'.format(start)).where(u'endDate', u'==', u'{}'.format(end))
    docs = query_ref.stream()

    # check length of docs
    listSize = len(list(docs))
    print(listSize)      

    # if data doesn't exist in database, fetch data from API, store in database and return the query results
    if listSize == 0:

        # set the user parameters to NCDC URL and get daily normal temperature results
        url_norm = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data?limit=1000&datasetid=NORMAL_DLY&datacategoryid=TEMP&units=standard&datatypeid=DLY-TAVG-NORMAL&startdate={}&enddate={}&stationid={}".format(start, end, sid)
        url_std = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data?limit=1000&datasetid=NORMAL_DLY&datacategoryid=TEMP&units=standard&datatypeid=DLY-TAVG-STDDEV&startdate={}&enddate={}&stationid={}".format(start, end, sid)            
            
        token = "ylPeWbpuHSsbXHmtqurCJXfejdryavRe"

        headers = {
            'token': token,
            'Content-Type': 'application/json; charset=utf-8'
        }
    
        response = requests.get(url_norm, headers=headers).text
        response_info = json.loads(response)

        response_std = requests.get(url_std, headers=headers).text
        response_std_info = json.loads(response_std)
            
        if len(response_info) == 0 and len(response_std_info) == 0:
            return jsonify({"Info": "Temperature data not available for the selected station."}), 200

        # create a new doc entry for the selected station in firebase
        doc_id = str(uuid.uuid4().hex)

        # store retrieved temperature data in firestore
        doc_ref = db.collection(u'temps').document(u'{}'.format(doc_id))
        doc_ref.set({
            u'id': u'{}'.format(doc_id),
            u'stationid': u'{}'.format(sid),
            u'query_doc': u'{}'.format(docId),
            u'extent': u'{}'.format(extent),
            u'startDate': u'{}'.format(start),
            u'endDate': u'{}'.format(end),
            u'dataCoverage': u'',
            u'results': response_info['results'],
            u'resultsCount': response_info['metadata']['resultset']['count'],
            u'results_std': response_std_info['results'],
            u'resultsCount_std': response_std_info['metadata']['resultset']['count'] 
        })

        return jsonify({ "results": response_info['results'], "count": response_info['metadata']['resultset']['count'], "results_std": response_std_info['results'], "count_std": response_std_info['metadata']['resultset']['count'] }), 200


    # if data exists, return the query results from database    
    else: 

        docId = ''

        # get id of the query document which contains same query
        docs = query_ref.stream()
        for doc in docs:
            docId = doc.id

        # fetch the document by obtained document id
        doc_rf = db.collection(u'temps').document(u'{}'.format(docId))
        doc = doc_rf.get()

        if doc.exists:
            response_info = doc.to_dict()
            return jsonify({"results": response_info['results'], "count": response_info['resultsCount'], "results_std": response_info['results_std'], "count_std": response_info['resultsCount_std']}), 200
        else:
            return jsonify({"results": [], "count": 0, "results_std": [], "count_std": 0}), 200



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False)
