from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################


######################################################################
# Health endpoint
######################################################################
@app.route('/health', methods=['GET'])
def health():
    return {"status":"OK"}, 200

######################################################################
# Count endpoint
######################################################################
@app.route('/count', methods=['GET'])
def count():
    number_of_songs = db.songs.count_documents({})
    print(number_of_songs)

    return {"count": number_of_songs}, 200

######################################################################
# GET /song endpoint
######################################################################
@app.route('/song', methods=['GET'])
def songs():

    list_of_songs = db.songs.find({}, {'_id':0})

    return {'songs': json.loads(json_util.dumps(list_of_songs))}, 200

######################################################################
# GET /song/id endpoint
######################################################################
@app.route('/song/<int:id>', methods=['GET'])
def get_song_by_id(id):

    song = db.songs.find_one({'id':id})

    if song:
        return json.loads(json_util.dumps(song)), 200
    else:
        return {'message':'song with id not found'}, 404

######################################################################
# POST /song endpoint
######################################################################
@app.route('/song', methods=['POST'])
def create_song():

    new_song = request.json

    song = db.songs.find_one({'id':new_song['id']})

    if song:
        return {'Message': f"song with id {new_song['id']} already present"}
    else:
        insert_new= db.songs.insert_one(new_song)
    
    return {'inserted id': {"$oid": str(insert_new.inserted_id)}}

######################################################################
# PUT /song/id endpoint
######################################################################
@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):

    updated_data = request.json

    song_to_update = db.songs.find_one({'id': id})

    if song_to_update:
        update_response = db.songs.update_one({'id': id}, {'$set': updated_data})

        if update_response.modified_count == 0:
            return {"message":"song found, but nothing updated"}, 200
        

        return parse_json(db.songs.find_one({'id': id})), 201

    else:
        return jsonify(message='song not found'), 404

######################################################################
# DELETE /song/id endpoint
######################################################################
@app.route('/song/<int:id>', methods=['DELETE'])
def delete_song(id):

    delete_response = db.songs.delete_one({'id': id})

    if delete_response.deleted_count == 0:
        return {"message": "song not found"}, 404

    return {}, 204