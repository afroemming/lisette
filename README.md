# Lisette
A Discord bot for making lists together

## Use
Lisette provides a set of commands for creating and editing lists collaboratively 
in Discord messages.

Commands are:
* `/lists new [name]` - Make a new list in current channel with [name].
* `/lists del [name]` - Delete list with [name]
* `/lists info` - List all lists in current guild.

* `/tasks edit [list]` - Gives a dialog window to edit all of a list tasks.
* `/tasks new [list] [content]` - Add a single task.
* `/tasks del [list] [nums]` - Delete tasks [nums], where nums is a string of space seperated positions, zero-indexed. Ie. '0 1 3'
* `/tasks chk [list] [nums]` - Mark tasks as checked, arguments are as in del.


## Setup
### Basic example
0. Install docker, docker compose.
1. Provide token and db file path by enviroment var, cli arg, or file.
2. Bring up with doker compose

### Development
0. Requires poetry to install and manage enviroment.
1. Install dependencies with `make install`
2. Provide .env file in root dir with required options if you want to run.
3. Run tests with `make test`
4. Run app with `make run`
5. Run app with debug logging by `make run-debug`

### Enviroment variables
All can be suffixed by '_FILE" to lookup value from a file given a path.
* `LISETTE_DB_URL`: (required) Url/ path to database of the form eg. 'mysql://example.com' or for a local file 'sqlite:///[path]', replace [path] with your desired path (empty for same directory)
* `LISETTE_TOKEN`: (required) Discord token for bot account
* `LISETTE_LOG_LEVEL`: (optional) Log level. Valid options: DEBUG, INFO, WARNING, CRITICAL 

### CLI Args
* --log-level [str]: As like above
* --token [str]: As like above
* --db-url [path]: As like above
* --env-file [path]: Load options from an env file at path. 

## Scopes and permissions
Lisette requires the bot and applications.command scope, and send messages permission.

## Privacy
See [Privacy policy](docs/PRIVACY.md)
