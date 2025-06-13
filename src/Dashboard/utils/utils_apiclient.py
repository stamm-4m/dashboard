import requests

class ApiClient:
    def __init__(self, base_url):
        """
        Initializes the API client with the base URL.

        :param base_url: Base URL of the API.
        """
        self.base_url = base_url

    def get(self, endpoint, params=None, headers=None):
        """
        Performs a GET request to the API.

        :param endpoint: API endpoint.
        :param params: Query parameters.
        :param headers: Request headers.
        :return: API response in JSON format.
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        return self._handle_response(response)

    def post(self, endpoint, data=None, headers=None):
        """
        Performs a POST request to the API.

        :param endpoint: API endpoint.
        :param data: Data to send in the request body.
        :param headers: Request headers.
        :return: API response in JSON format.
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=data, headers=headers)
        return self._handle_response(response)

    def put(self, endpoint, data=None, headers=None):
        """
        Performs a PUT request to the API.

        :param endpoint: API endpoint.
        :param data: Data to send in the request body.
        :param headers: Request headers.
        :return: API response in JSON format.
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.put(url, json=data, headers=headers)
        return self._handle_response(response)

    def delete(self, endpoint, headers=None):
        """
        Performs a DELETE request to the API.

        :param endpoint: API endpoint.
        :param headers: Request headers.
        :return: API response in JSON format.
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.delete(url, headers=headers)
        return self._handle_response(response)

    def _handle_response(self, response):
        """
        Handles the API response, raising an exception if there is an error.

        :param response: Response object from requests.
        :return: JSON-formatted response.
        :raises Exception: If the response contains an error status code.
        """
        if response.status_code >= 400:
            raise Exception(f"Error {response.status_code}: {response.text}")
        return response.json()
