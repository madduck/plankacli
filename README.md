# plankacli — a CLI tool to interact with Planka

This command-line tool exists to facilitate interaction with [Planka](https://docs.planka.cloud/). It uses the [plankapy API client library](https://github.com/hwelch-fle/plankapy) to do the heavy lifting.

This tool is work in progress, and I will add functionality as I need it. Feel free to open pull requests if you need something, should be relatively easy to add the glue between the [click](https://click.palletsprojects.com/) library, and the API client.

## Call for help — uploading to PyPi

I would love to publish this to [PyPi](https://pypi.org/), but I don't know how. So if someone could set up a CI pipeline on Github for me, or help me do this, that would be great!

## Installation

The recommended way to install `plankacli` is using a virtual environment for now. I personally love using [direnv](https://direnv.net/) for this:

```bash
mkdir ~/code/plankacli
cd ~/code/plankacli

echo layout python3 > .envrc
direnv allow .

git clone https://github.com/madduck/plankacli
cd plankacli

pip install -e .

plankacli …
```

Now, to run, you need to switch to the directory:

```bash
(~/code/plankacli && plankacli …)
```

Alternatively, if you have a custom `bin` directory in your `$PATH`, then add a symlink there (I trust you'll amend the paths accordingly):

```bash
cd ~/bin
ln -s ../code/plankacli/.direnv/*/bin/plankacli
cd

plankacli …
```

## Usage

```
$ plankacli --help
Usage: plankacli [OPTIONS] COMMAND [ARGS]...

  A command-line interface to Planka

Options:
  -v, --verbose       Increase verbosity of log output
  -q, --quiet         Make the tool very quiet
  -U, --url TEXT      URL of Planka instance
  -T, --token TEXT    Planka access token to use (token:httpOnlyToken)
  -p, --project TEXT  Name of project to work on
  -b, --board TEXT    Name the board to work on
  --help              Show this message and exit.

Commands:
  card   Commands to manipulate cards
  label  Commands to manipulate labels (tags)
  list   Commands to manipulate lists
```

Note how the token actually comprises two tokens, which you currently need to obtain from a browser session, at least until [Planka adds API key support](https://github.com/plankanban/planka/issues/945).

Instead of providing URL and API tokens with each call, you can also create a configuration file (default: `$XDG_CONFIG_DIR/pngx/config`) like so:

```
url = "https://kanban.example.org"
token = "iubYG79b6BfjnKJB8778bkHBJjhbkjbkkkjbKkjbi…:3582eea-04d1-11f0-997f-107c61246ef8"

project = "My Project"
```

### Manipulating cards

```
$ plankacli card --help
Usage: plankacli card [OPTIONS] COMMAND [ARGS]...

  Commands to manipulate cards

Options:
  --help  Show this message and exit.

Commands:
  add     Add named cards to the specified list
  delete  Delete cards by their IDs
```

#### Adding cards

```
$ plankacli card add --help
Usage: plankacli card add [OPTIONS] [NAME]...

  Add named cards to the specified list

Options:
  -l, --list TEXT                 Name of the list where to add cards
                                  [required]
  -p, --position INTEGER          Position of new cards in list
  -d, --due-date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  Due date for new cards
  -t, --tag TEXT                  Tag to add to new card
  -m, --member TEXT               Member to add to new card
  --help                          Show this message and exit.
```

#### Deleting cards

```
$ plankacli card delete --help
Usage: plankacli card delete [OPTIONS] [ID]...

  Delete cards by their IDs

Options:
  --help  Show this message and exit.
```

### Manipulating labels

```
$ plankacli label --help
Usage: plankacli label [OPTIONS] COMMAND [ARGS]...

  Commands to manipulate labels (tags)

Options:
  --help  Show this message and exit.

Commands:
  colours  Enumerate the available colour names
  delete   Delete the specified labels
```

#### Listing label colour names

```
$ plankacli label colours --help
Usage: plankacli label colours [OPTIONS]

  Enumerate the available colour names

Options:
  --help  Show this message and exit.
```

#### Deleting labels

```
$ plankacli label delete --help
Usage: plankacli label delete [OPTIONS] [LABEL]...

  Delete the specified labels

Options:
  --help  Show this message and exit.
```

### Manipulating lists

```
$ plankacli list --help
Usage: plankacli list [OPTIONS] COMMAND [ARGS]...

  Commands to manipulate lists

Options:
  --help  Show this message and exit.

Commands:
  clear  Clear ALL cards from the specified lists
```

#### Clearing a list

```
$ plankacli list clear --help
Usage: plankacli list clear [OPTIONS] [LIST]...

  Clear ALL cards from the specified lists

Options:
  -t, --tag TEXT  Only clear cards with this tag
  --yes           Confirm the action without prompting.
  --help          Show this message and exit.
```

## Contributing

To contribute, please ensure you have the appropriate dependencies installed:

```
$ pip install -e .[dev]
```

and then install the Git pre-commit hooks that ensure that any commits conform
with the Flake8 and Black conventions used by this project:

```
$ pre-commit install
```

## Legalese

`plankacli` is © 2025 martin f. krafft <plankacli@pobox.madduck.net>.

It is released under the terms of the MIT Licence.
