try:
    import http.client as http_client
except ModuleNotFoundError:
    import httplib as http_client

# Backup:
UNMOCK_AUTH = "___u__n_m_o_c_k_a_u_t__h_"
HTTPConnectionInit = http_client.HTTPConnection.__init__
HTTPConnectioRequest = http_client.HTTPConnection.request
HTTPConnectionSend = http_client.HTTPConnection.send

