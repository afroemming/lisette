# Lisette
A Discord bot for making lists together

## Setup
### Basic example
0. Install Python 3.11


1. Get program code and install via pip
```
git clone https://github.com/afroemming/lisette
cd lisette
pip install --user .
```
2. Create a '.env' file with at least required variables, or provide enviroment variables some other way.
3. Run in terminal via `lisette`, or if using an env file `lisette --env_file [path to file]`.

### Development
Run `make install` to make venv and install package/ dev helpers into it.

### Enviroment variables
* `LISETTE_DB_URL`: (required) Url/ path to database of the form eg. 'mysql://example.com' or for a local file 'sqlite:///[path]', replace [path] with your desired path (empty for same directory)
* `LISETTE_BOT_TOKEN`: (required) Discord token for bot account
* `LISETTE_LOG_LEVEL`: (optional) Log level. Valid options: DEBUG, INFO, WARNING, CRITICAL 