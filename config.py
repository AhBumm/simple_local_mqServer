"""
Configuration for simple_local_mqServer Huey backend.

Default backend changed to SqliteHuey (local Sqlite DB) for easy local development
and zero external dependencies. To use Redis instead, change the `backend`
value to 'redis' and provide the proper connection values.
"""

# Huey backend choices: 'sqlite' or 'redis'
DEFAULT_HUEY = {
    # Choose the backend: 'sqlite' (default) or 'redis'
    'backend': 'sqlite',

    # Sqlite specific options
    'sqlite_file': 'huey.sqlite.db',

    # Redis specific options (used when backend == 'redis')
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'results': True,
    },

    # Common options
    'immediate': False,  # if True, run tasks synchronously (useful for tests)
    'results': True,     # whether to store task results
    'utc': True,
}
