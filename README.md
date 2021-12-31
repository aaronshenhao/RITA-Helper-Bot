# RITA-Helper-Bot
For the RITA Discord Bot. It's purpose is to simplify connecting channels together for automatic translation. Currently, it assumes that each language has it's own category, and uses that to figure out a channel's language. A group of channels represent a single channel, split into multiple languages with automatic translation. The bot simplifies setting up the auto-translation by automatically calling `!tr channel from <lang1> to <lang2> for <#channel>`.

It was roughly put together for usage on a single server. It'll be better to incorporate these changes into the RITA bot itself.

## Commands

### General
- `$mb ping`: Bot replies with "Pong!"

### Category
- `$mb category set <language>`: Assigns a language to the category of the current channel.
- `$mb category unset <language>`: Unsets the language of the category of the current channel.
- `$mb category list`: Lists all categories, with their language.
- `$mb category get`: Prints the language of the category of the current channel.

### Group
- `$mb group create <group>`: Creates a new group.
- `$mb group delete <group>`: Deletes a group.
- `$mb group list`: Lists all groups, with the number of channels in them.
- `$mb group get`: Prints the groups of the current channel.

### Channel
- `$mb channel add <group>`: Adds a channel to a group.
- `$mb channel remove <group>`: Removes a channel from the group.

### (Un)Linking
- `$mb (un)link channel`: Creates all outgoing translations from the current channel.
- `$mb (un)link group`: Creates all outgoing translations for all channels in the group of the current channel.
- `$mb (un)link category`: Creates all outgoing translations for all channels in the current category.
- `$mb (un)link all`: Creates all outgoing translations.
