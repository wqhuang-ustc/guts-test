from flask import Flask
from flask import request, jsonify, abort
from flask_pymongo import PyMongo
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
from flask import Response
import bsonjs
from bson.json_util import loads, dumps

class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

users = [
    User(1, 'weiqing', 'happycoding'),
    User(2, 'guts', 'getprotocol'),
]

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user

def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config["MONGO_URI"] = "mongodb://myUserAdmin:happyfriday@ec2-13-53-186-244.eu-north-1.compute.amazonaws.com:27017/mydb?authSource=admin"

mongodb_client = PyMongo(app)
db = mongodb_client.db

jwt = JWT(app, authenticate, identity)

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.route('/', methods=['GET'])
def home():
    return "<h1>Demo for GUTS test</h1><p>This site is a prototype API for showing sales data</p>"

@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity

@app.route('/api/v1/sales/all')
@jwt_required()
def api_all():
    sales_all = []
    bson_sales_all = db.sales.find()
    for sale in bson_sales_all:
        json_sale = dumps(sale)
        sales_all.append(json_sale)
    return Response(sales_all, mimetype='application/json')

@app.route('/api/v1/sales/purchasemethod/<how>')
@jwt_required()
def purchase_how(how):
    data = []
    record_all = db.sales.find({'purchaseMethod': how})
    print(record_all)

    for record in record_all:
        json_record = dumps(record)
        data.append(json_record)
    
    if not data:
        abort(404, description="Resource not found")
    return Response(data, mimetype='application/json')

if __name__ == '__main__':
    app.run(host="0.0.0.0")