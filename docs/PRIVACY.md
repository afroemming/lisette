# Lisette Privacy Policy
## What data is collected and stored
Lisette collects and stores certain information for its own operation. The data 
stored includes:

### Information stored in database.
* Certain text provided to the app: task contents and list names. This is 
necessary so that Lisette can have a version of lists that it can modify 
internally without needing to read it's messages from Discord.
* IDs of messages that the app has written to. This is neccesary so that Lisette
can output edits to lists to Discord with the user providing a list name, rather
than a message id.
* IDs of guilds that Lisette has written lists to. This is neccesary for Lisette
 to restrict manipulation of lists by users on a per guild basis.

### Additional information stored by logging.
When Lisette bot is run with INFO or WARNING level logging (normal
operation), on failed lookups of a list (for instance, if a user misspells the 
name of a list) the guild id associated with the command that triggered the 
lookup is logged.

When Lisette bot is run with DEBUG level logging (should not be used
in production), it may log additional data about the context of commands given 
to it (ie. id of user invoking command, any other information that Pycord logs
with a DEBUG log level.)

## Sharing of infomation
* All information that the app collects is neccesarily shared with the hosting 
provider of the app's server. 
* Information that the app collects in its database is shared with a third party
storage provider in an encrypted form for backup.