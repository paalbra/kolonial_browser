from flask import Flask, jsonify
import configparser

from kolonial_api import KolonialAPI

app = Flask(__name__)

config = configparser.ConfigParser()
config.read("config.ini")

token = config["api"]["token"]
user_agent = config["api"]["useragent"]
api_url = config["api"]["url"]

api = KolonialAPI(api_url, token, user_agent)

@app.route("/api/products/<int:product_id>")
def get_product(product_id):
    product = api.get_product(product_id)
    if product:
        return jsonify(product)
    else:
        return (jsonify({"error": "The product does not exist!"}), 404)

@app.route("/api/search/<query>")
def get_search(query):
    return jsonify(api.get_search(query))

@app.route("/api/*/<path:path>")
def get_wildcard(path):
    response = api.get_response_from_path("/" + path)
    if response.headers.get("Content-Type") == "application/json":
        return (jsonify(response.json()), response.status_code)
    else:
        return (response.text, response.status_code)

