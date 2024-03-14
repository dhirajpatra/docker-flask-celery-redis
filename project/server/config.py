# project/server/config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    """Base configuration."""

    WTF_CSRF_ENABLED = True
    REDIS_URL = "redis://redis-prod:6379/0"
    # REDIS_URL = "redis://localhost:6379/0"
    QUEUES = ["default"]
    TTL = 30
    PROPAGATE_EXCEPTIONS = True
    JSON_SORT_KEYS = False
    MAX_TIME_TO_WAIT = 10
    TASKS = ['Short task', 'Long task', 'Task raises error']


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    WTF_CSRF_ENABLED = False


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
