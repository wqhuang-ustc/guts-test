from flask import Flask
from flask import request, jsonify
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
app.config["MONGO_URI"] = "mongodb://ec2-13-53-186-244.eu-north-1.compute.amazonaws.com:27017/mydb"

mongodb_client = PyMongo(app)
db = mongodb_client.db

jwt = JWT(app, authenticate, identity)

# Create sales test data here to simulate the result from Mongodb

sales_records = [
    {'id': 0,
     'title': 'A Fire Upon the Deep',
     'author': 'Vernor Vinge',
     'first_sentence': 'The coldsleep itself was dreamless.',
     'year_published': '1992'},
    {'id': 1,
     'title': 'The Ones Who Walk Away From Omelas',
     'author': 'Ursula K. Le Guin',
     'first_sentence': 'With a clamor of bells that set the swallows soaring, the Festival of Summer came to the city Omelas, bright-towered by the sea.',
     'published': '1973'},
    {'id': 2,
     'title': 'Dhalgren',
     'author': 'Samuel R. Delany',
     'first_sentence': 'to wound the autumnal city.',
     'published': '1975'}
]

@app.route('/', methods=['GET'])
def home():
    return "<h1>Demo for GUTS test</h1><p>This site is a prototype API for showing sales data</p>"

@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity

@app.route('/api/v1/sales/all')
# @jwt_required()
def api_all():
    bson_sales = db.sales.find_one()
    # convert the record to json
    sales = dumps(bson_sales)
    
    sales_all = []
    bson_sales_all = db.sales.find()
    for sale in bson_sales_all:
        json_sale = dumps(sale)
        sales_all.append(json_sale)
    return Response(sales_all, mimetype='application/json')

if __name__ == '__main__':
    app.run()