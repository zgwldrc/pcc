retries = 0
try:
    r = self.session.request(method, url, *args, **kwargs)
except requests.exceptions.ConnectTimeout:
    retries += 1

# reconnect is needed
if retries > 0:
    while retries < self.max_reconnect + 1:
        logger.error('connecting to {} timeout, retry({}/{})'.format(url, retries, self.max_reconnect))
        try:
            r = self.session.request(method, url, *args, **kwargs)
        except requests.exceptions.ConnectTimeout:
            retries += 1
            if retries > self.max_reconnect:
                raise
        else:
            break
