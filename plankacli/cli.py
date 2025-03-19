import click
import random
import plankapy

from plankacli.logger import get_logger, adjust_log_level
from plankacli.config import Config

logger = get_logger(__name__)


@click.group()
@click.option(
    "--verbose", "-v", count=True, help="Increase verbosity of log output"
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Make the tool very quiet"
)
@click.option("--url", "-U", help="URL of Planka instance")
@click.option(
    "--token",
    "-T",
    help="Planka access token to use (token:httpOnlyToken)",
)
@click.option(
    "--config",
    "-c",
    help="Config file to read",
    type=click.Path(path_type=pathlib.Path),
)
@click.option(
    "--project", "-p", help="Name of project to work on"
)
@click.option("--board", "-b", help="Name the board to work on")
@click.pass_context
def main(ctx, verbose, quiet, url, token, config, project, board):
    """A command-line interface to Planka"""

    adjust_log_level(logger, verbose, quiet=quiet)

    config = Config(config)

    url = url or config.get("url")
    if not url:
        raise click.UsageError("No URL specified, and none in config")

    token = token or config.get("token")
    if not token:
        raise click.UsageError("No API token specified, and none in config")

    project = project or config.get("project")
    if not project:
        raise click.UsageError("No project name specified, and none in config")

    board = board or config.get("board")
    if not board:
        raise click.UsageError("No board name specified, and none in config")

    tokens = token.split(":", 1)
    if len(tokens) == 2:
        tokens = {"access_token": tokens[0], "http_only_token": tokens[1]}
    else:
        logger.warning("No httpOnlyToken provided")
        tokens = {"access_token": tokens[0], "http_only_token": None}

    planka = plankapy.Planka(url=url, **tokens)

    ctx.obj = {
        "planka": planka,
        "project_name": project,
        "board_name": board,
        "config": config
    }


@main.group()
def list():
    """Commands to manipulate lists"""


@list.command()
@click.option(
    "--tag", "-t", multiple=True, help="Only clear cards with this tag"
)
@click.argument("list", nargs=-1)
@click.confirmation_option(
    prompt="Are you sure you want to clear the specified lists?"
)
@click.pass_obj
def clear(obj, tag, list):
    """Clear ALL cards from the specified lists"""
    boardselector = {
        "project_name": obj["project_name"],
        "board_name": obj["board_name"],
    }
    cardctrl = plankapy.Card(obj["planka"])
    labelctrl = plankapy.Label(obj["planka"])
    labels = {
        l["id"]
        for l in labelctrl.get(**boardselector)
        if l["name"] in set(tag)
    }

    for l in list:
        n = 0
        for n, card in enumerate(
            cardctrl.get(**boardselector, list_name=l), 1
        ):
            oid = card["item"]["id"]
            if labels:
                cardlabels = {l["labelId"] for l in cardctrl.get_labels(oid=oid)}
                if not labels & cardlabels:
                    logger.debug(
                        f"Skipping deletion of card with ID {oid} "
                        f"without any labels in {', '.join(tag)}"
                    )
                    continue
            cardctrl.delete(oid=oid)
            logger.debug(f"Deleted card with ID {oid}")
        logger.debug(f"Cleared {n} card(s) off list {l}")


@main.group()
def label():
    """Commands to manipulate labels (tags)"""


@label.command()
@click.argument("label", nargs=-1)
@click.pass_obj
def delete(obj, label):
    """Delete the specified labels"""
    boardselector = {
        "project_name": obj["project_name"],
        "board_name": obj["board_name"],
    }
    labelctrl = plankapy.Label(obj["planka"])

    for l in label:
        try:
            lobj = labelctrl.get(**boardselector, label_name=l)
            labelctrl.delete(oid=lobj["id"])
            logger.info(f"Deleted label {l}")

        except plankapy.plankapy.InvalidToken:
            logger.warning(f"Label does not exist: {l}")


@label.command()
@click.pass_obj
def colours(obj):
    """Enumerate the available colour names"""
    labelctrl = plankapy.Label(obj["planka"])
    click.echo("\n".join(sorted(labelctrl.colors())))


@main.group()
def card():
    """Commands to manipulate cards"""


@card.command()
@click.argument("id", type=click.INT, nargs=-1)
@click.pass_obj
def delete(obj, id):
    """Delete cards by their IDs"""
    listselector = {
        "project_name": obj["project_name"],
        "board_name": obj["board_name"],
    }
    cardctrl = plankapy.Card(obj["planka"])
    for card in id:
        cardctrl.delete(oid=card, **listselector)
        logger.info(f"Deleted card with ID {card}")


@card.command()
@click.option(
    "--list",
    "-l",
    "listname",
    required=True,
    help="Name of the list where to add cards",
)
@click.option(
    "--position",
    "-p",
    type=click.INT,
    default=0,
    help="Position of new cards in list",
)
@click.option(
    "--due-date",
    "-d",
    type=click.DateTime(),
    help="Due date for new cards",
)
@click.option("--tag", "-t", multiple=True, help="Tag to add to new card")
@click.option(
    "--member", "-m", multiple=True, help="Member to add to new card"
)
@click.argument("name", nargs=-1)
@click.pass_obj
def add(obj, listname, position, due_date, tag, member, name):
    """Add named cards to the specified list"""
    boardselector = {
        "project_name": obj["project_name"],
        "board_name": obj["board_name"],
    }
    listselector = boardselector | {
        "list_name": listname,
    }

    labelctrl = plankapy.Label(obj["planka"])
    userctrl = plankapy.User(obj["planka"])
    colours = labelctrl.colors()
    created_labels = set()

    for cardname in name:
        carddata = {
            "name": cardname,
            # "description": "str",
            "position": position,
            # "stopwatch": "Stopwatch",
        }

        if due_date:
            carddata["dueDate"] = str(due_date)

        cardctrl = plankapy.Card(obj["planka"], **carddata)
        card = cardctrl.create(**listselector)
        cid = card["item"]["id"]
        logger.info(f"Created new card with ID {cid}")

        for t in tag:
            colour = None
            tname, sep, colour = t.rpartition(":")
            if not tname:
                # rpartition returns (None, None, tname) if no colour appended
                tname, colour = colour, None

            if colour and colour not in colours:
                # not a known colour
                tname = sep.join((tname, colour))
                colour = None

            for i in range(2):
                # try this twice so if it fails the first time, create the
                # label and try again… once more.
                try:
                    labelctrl.add(
                        card_id=cid, label_name=tname, **boardselector
                    )
                    if colour and tname not in created_labels:
                        logger.warning(
                            f"Ignored colour '{colour}' as label already exists: {tname}"
                        )
                    logger.info(f"Added label '{tname}' to card with ID {cid}")
                    break

                except plankapy.plankapy.InvalidToken:
                    if not colour:
                        colour = random.choice(colours)
                        logger.debug(f"Chose random color: {colour}")

                    labeldata = {
                        "name": tname,
                        # "description": "str",
                        "position": 0,
                        "color": colour,
                        # "stopwatch": "Stopwatch",
                    }
                    labelctrl = plankapy.Label(obj["planka"], **labeldata)
                    labelctrl.create(**boardselector)
                    logger.info(f"Created label '{tname}'")
                    created_labels.add(tname)

        for m in member:
            try:
                user = userctrl.get(name=m)
                userctrl.add(card_id=cid, user_id=user["id"])
            except plankapy.plankapy.InvalidToken:
                logger.error(f"User does not exist: {m}")
                continue
