import logging


_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

_LOGGER = logging.getLogger(__name__)

def _configure_logging(loglevel=logging.INFO):
    _LOGGER.setLevel(loglevel)

    ch = logging.StreamHandler()

    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)

    _LOGGER.addHandler(ch)
    
# 或直接使用模块方法, 这样设定后就不需要执行 _configure_logging()函数了
logging.basicConfig(format=_DEFAULT_LOG_FORMAT, level=logging.INFO)


