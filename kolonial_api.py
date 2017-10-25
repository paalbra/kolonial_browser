import requests

class KolonialAPI(object):
    """
    A class that simplifies requesting stuff from the Kolonial.no API:
    https://github.com/kolonialno/api-docs
    """

    def __init__(self, api_url, token, user_agent):
        """
        Construct a new object that is prepered to do requests agains the API.

        :param api_url: Url to the API
        :param token: The authorization token that will be sent to the API in the X-Client-Token header.
        :param user_agent: User-Agent used when contacting the API.
        """
        self._api_url = api_url

        self._api_headers = {"user-agent": user_agent,
                             "content-type": "application/json",
                             "accept": "application/json",
                             "x-client-token": token
                            }

    def ping(self):
        """
        Do a simple request to the API to confirm availability.
        """
        # The API has no "ping" endpoint. So we request a product.
        try:
            self.get_product(0)
        except requests.HTTPError:
            return False
        return True

    def get_product(self, product_id):
        """
        Get a single product from the API. A nonexistent product will return None.

        :param product_id: The ID of the product.
        """
        response = self.get_response_from_path("/products/%d/" % product_id)

        if response.status_code == 404:
            return None

        return response.json()

    def get_search(self, query):
        """
        Perform a search against the API and return the result.

        :param query: The input query.
        """
        response = self.get_response_from_path("/search/?q=%s" % query)

        if response.status_code == 404:
            response.raise_for_status()

        return response.json()


    def get_response_from_path(self, path):
        """
        Perform a HTTP request against the API.

        :param path: The URL path to request, including starting slash.
        """
        full_path = self._api_url + path
        response = requests.get(full_path, headers=self._api_headers)

        if response.status_code not in (200, 404):
            response.raise_for_status()

        return response

