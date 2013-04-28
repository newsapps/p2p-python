Python wrapper for P2P Content Services
------------------

Configuration settings. Set these values in your environment or your Django settings.

  P2P_API_KEY = your_p2p_api_key
  P2P_API_URL = url_of_p2p_endpoint
  P2P_API_DEBUG = plz  # display an http log

  # Optional
  P2P_IMAGE_SERVICES_URL = url_of_image_services_endpoint
  
To get a connection object based on these settings:

  from p2p import get_connection
  p2p = get_connection()

Or you can create a connection object manually. You'll want to do this in order to enable caching.

  from p2p import P2P, cache
  p2p = P2P(
      url='url_of_p2p_endpoint',
      auth_token='your_p2p_api_key',
      debug=False or True,
      image_services_url='url_of_image_services_endpoint',
      cache=cache.DictionaryCache()
  )

