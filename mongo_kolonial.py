import logging
from datetime import datetime

import pymongo
from bson.son import SON


def pop_underscore(document):
    # TODO Wow. Such ugly(?)
    document.pop("_id", None)
    document.pop("_inserted_time", None)
    document.pop("_refreshed_time", None)


class MongoKolonial(object):
    """
    A class that is meant to simplify the management of the    local Kolonial product database.
    """

    def __init__(self, database_name, collection_name):
        self._client = pymongo.MongoClient()
        self._db = self._client[database_name]
        self._collection = self._db[collection_name]

    def get_count(self, ):
        """
        Get the number of products in the database.
        """
        return len(self.get_products())

    def get_products(self, keep_underscore=False):
        """
        Get all products in the database.
        """
        sort = {"$sort": SON([("id", pymongo.ASCENDING), ("_inserted_time", pymongo.DESCENDING)])}
        group = {"$group": {"_id": "$id", "doc": {"$first": "$$ROOT"}, "count": {"$sum": 1}}}
        match = {"$match": {"doc.name": {"$exists": True}}}
        cursor = self._collection.aggregate([sort, group, match])

        docs = [e["doc"] for e in cursor]

        if not keep_underscore:
            for doc in docs:
                pop_underscore(doc)

        return docs

    def get_product(self, product_id, keep_underscore=False):
        """
        Get a single product from the database.
        """
        product = self._collection.find_one({"id": product_id, "name": {"$exists": True}}, sort=[("_inserted_time", pymongo.DESCENDING)])
        if product:
            if not keep_underscore:
                pop_underscore(product)
            return product
        else:
            return None

    def get_padding(self):
        """
        When products are sorted by id, this will get the number of nonexisting products in sequence with the highest ids.

        We're interested in this "padding" since we do not know the highest product id at Kolonial and therefore have to guess when to stop getting new ids.

        The returned padding will never be less than zero.
        """
        max_id = self.get_max_id()
        max_id_existing = self.get_max_id(only_existing=True)

        if max_id is None or max_id_existing is None:
            return None
        else:
            return max_id - min(max_id, max_id_existing)

    def get_max_id(self, only_existing=False):
        """
        Get the highest product id in the database.

        :param only_existing: Will only return the max id of existing products if set.
        """

        if only_existing:
            find_filter = {"name": {"$exists": True}}
        else:
            find_filter = None

        document = self._collection.find_one(find_filter, sort=[("id", pymongo.DESCENDING)])

        if document:
            return document["id"]
        else:
            return None

    def infresh_product(self, product):
        """
        Insert og refresh given product.

        A new document will be inserted if the product differs from currently existing product.

        If the product already exist the old one will be refreshed.
        """
        current_product = self.get_product(product["id"], keep_underscore=True)
        if current_product:
            current_object_id = current_product["_id"]
            pop_underscore(current_product)
            if current_product == product:
                logging.info("Refreshing refresh time on unchanged product: {}".format(product["id"]))
                self._collection.update({"_id": current_object_id}, {"$set": {"_refreshed_time": datetime.utcnow()}})
            else:
                logging.info("Refreshing product with changes: {}".format(product["id"]))
                now = datetime.utcnow()
                product["_inserted_time"] = now
                product["_refreshed_time"] = now
                self._collection.insert(product)
        else:
            # This is a new product
            logging.info("Inserting new product: {}".format(product["id"]))
            now = datetime.utcnow()
            product["_inserted_time"] = now
            product["_refreshed_time"] = now
            self._collection.insert(product)
