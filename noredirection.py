from urllib.request import Request, urlopen, HTTPErrorProcessor, build_opener

class NoRedirection(HTTPErrorProcessor):
# http://stackoverflow.com/questions/554446/how-do-i-prevent-pythons-urllib2-from-following-a-redirect
    def http_response(self, request, response):
        return response
    https_response = http_response