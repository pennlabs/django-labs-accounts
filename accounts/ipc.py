import requests


# IPC on behalf of a user for when a user in a product wants to use an
# authenticated route on another product.
def authenticated_request(
    user,
    method,
    url,
    params=None,
    data=None,
    headers=None,
    cookies=None,
    files=None,
    auth=None,
    timeout=None,
    allow_redirects=True,
    proxies=None,
    hooks=None,
    stream=None,
    verify=None,
    cert=None,
    json=None,
):
    """
    Helper method to make an authenticated request using the user's access token
    NOTE be ABSOLUTELY sure you only make a request to Penn Labs products, otherwise
    you will expose user's access tokens to the URL you provide and bad things will
    happen
    """

    # Update Headers
    headers = {} if headers is None else headers
    headers["Authorization"] = f"Bearer {user.accesstoken.token}"

    # Make the request
    # We're only using a session to provide an easy wrapper to define the http method
    # GET, POST, etc in the method call.
    s = requests.Session()
    return s.request(
        method=method,
        url=url,
        params=params,
        data=data,
        headers=headers,
        cookies=cookies,
        files=files,
        auth=None,
        timeout=None,
        allow_redirects=allow_redirects,
        proxies=proxies,
        hooks=hooks,
        stream=stream,
        verify=verify,
        cert=cert,
        json=json,
    )
