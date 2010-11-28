import wsgiref.handlers
import gdata.urlfetch
import urllib
import base64
import logging
import urllib

from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from xml.etree import ElementTree
from google.appengine.ext import db

class MainHandler(webapp.RequestHandler):

	def get(self):
		code = self.request.get("code",default_value="")
	
		if len(code) ==  0:
			oauth_url = "https://graph.facebook.com/oauth/authorize?client_id=174071129287513&redirect_uri=http://rdr2twt.appspot.com/&scope=publish_stream,offline_access"
			self.redirect(oauth_url)
		else:
			token_url = "https://graph.facebook.com/oauth/access_token?client_id=174071129287513&redirect_uri=http://rdr2twt.appspot.com/&client_secret=1943a6ba44874f3a02ea6a5f44e2e037&code=" + code

			result = urlfetch.fetch(token_url)

			access_token = result.content

			data = CronData.all();

			if data.count() == 0:
                        	data = CronData(lastUpdate=1285565492906,accessToken=access_token)
                        	data.put()

			self.response.out.write(access_token)

class CronData(db.Model):
	lastUpdate = db.IntegerProperty();
	accessToken = db.StringProperty();
	
class CronHandler(webapp.RequestHandler):

	def get(self):
		
		result = urlfetch.fetch(url="http://www.google.com/reader/public/atom/user%2F13309615647099913467%2Fstate%2Fcom.google%2Fbroadcast")
		
		xml = ElementTree.fromstring(result.content)
		
		items = xml.findall("{http://www.w3.org/2005/Atom}entry")
		
		old_timestamp = self.getTimestamp()

		logging.debug("old timestamp: %s" % (old_timestamp))

		for item in items:

			timestamp = int(item.get("{http://www.google.com/schemas/reader/atom/}crawl-timestamp-msec"))

			if(timestamp > old_timestamp):
				
				self.post(item)
				
				self.setTimestamp(timestamp)
	
	def post(self, item):

		token = self.getAccessToken()

		href = item.find("{http://www.w3.org/2005/Atom}link").get("href");

		title = item.find("{http://www.w3.org/2005/Atom}title").text

		feedUrl = "https://graph.facebook.com/me/feed?%s&method=post&link=%s" % (token, href) 

		logging.debug("facebook post url: %s" % (feedUrl))
	
		result = urlfetch.fetch(feedUrl)

		logging.debug("result: %s" % (result))

	def getTimestamp(self):	
		
		data = CronData.all();
		
		return data[0].lastUpdate;

	def getAccessToken(self):

                data = CronData.all();

                return data[0].accessToken;
	
	def setTimestamp(self,value):
		
		data = CronData.all().get();
		
		data.lastUpdate = value;
		
		data.put();

def main():
  application = webapp.WSGIApplication([('/', MainHandler), ('/cron', CronHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
