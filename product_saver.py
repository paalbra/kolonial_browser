from datetime import datetime
import configparser
import pymongo

from kolonial_api import KolonialAPI
from mongo_kolonial import MongoKolonial

config = configparser.ConfigParser()
config.read("config.ini")

token = config["api"]["token"]
user_agent = config["api"]["useragent"]
api_url = config["api"]["url"]

api = KolonialAPI(api_url, token, user_agent)

mongo_kolonial = MongoKolonial("kolonial", "products")

# We do not know how many products there are in the API.
# The padding value is how many nonexisting product we should get after the last known, existing product id.
padding = 1000

current_padding = mongo_kolonial.get_padding()

if current_padding is None:
    print("We can't calculate current padding. Need more products.")
    max_id = mongo_kolonial.get_max_id()
    if max_id is None:
        print("We have no products. Get the first one.")
        product = api.get_product(1)
        if not product:
            product = {"id": next_id}
        mongo_kolonial.infresh_product(product)
    else:
        print("Current max is found. Get the next.")
        next_id = max_id + 1
        product = api.get_product(next_id)
        if not product:
            product = {"id": next_id}
        mongo_kolonial.infresh_product(product)
elif current_padding < padding:
    print("We have not reached the desired padding (%d < %d). We need to get more products." % (current_padding, padding))
    max_id = mongo_kolonial.get_max_id()
    next_id = max_id + 1
    product = api.get_product(next_id)
    if not product:
        product = {"id": next_id}
        print("Inserting empty product:", product["id"])
    else:
        print("Inserting product:", product["id"])
    mongo_kolonial.infresh_product(product)
else:
    print("The database is complete.")
    print("Do maintenance/update existing products.")
    products = mongo_kolonial.get_products(keep_underscore=True)
    products.sort(key=lambda product: product["_refreshed_time"])
    for product in products[:10]:
        # Refresh the oldest products
        print("I want to update:", product["_id"], product["id"], product["_refreshed_time"])
        new_product = api.get_product(product["id"])
        if not new_product:
            new_product = {"id": product["id"]}
            print("Refresh with empty product:", new_product["id"])
        else:
            print("Refresh with product:", new_product["id"])
        mongo_kolonial.infresh_product(new_product)

