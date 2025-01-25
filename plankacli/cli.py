import click
import random
from datetime import datetime
import plankapy as ppy
from plankapy import helpers as ppyh

from plankacli.logger import get_logger, adjust_log_level

logger = get_logger(__name__)


@click.group()
@click.option(
    "--verbose", "-v", count=True, help="Increase verbosity of log output"
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Increase verbosity of log output"
)
@click.option("--url", "-u", required=True, help="URL of Planka instance")
@click.option(
    "--token",
    "-t",
    required=True,
    help="Planka access token to use (token:httpOnlyToken)",
)
@click.option(
    "--project", "-p", required=True, help="Name of project to work on"
)
@click.option("--board", "-b", required=True, help="Name the board to work on")
@click.pass_context
def main(ctx, verbose, quiet, url, token, project, board):
    adjust_log_level(logger, verbose, quiet=quiet)

    auth = ppy.TokenAuth(token)
    planka = ppy.Planka(url=url, auth=auth)

    project = ppyh.by_project_name(planka.projects, project)
    if not project:
        logger.error(f"Project '{project}' not found")
        ctx.exit(1)
    project = project[0]

    board = ppyh.by_board_name(project.boards, board)
    if not board:
        logger.error(f"Board '{board}' not found")
        ctx.exit(1)
    board = board[0]

    ctx.obj = {
        "planka": planka,
        "project": project,
        "board": board,
    }


@main.group()
def lst():
    pass


@lst.command()
@click.option(
    "--tag", "-t", multiple=True, help="Only clear cards with this tag"
)
@click.argument("list", nargs=-1)
@click.confirmation_option(
    prompt="Are you sure you want to clear the specified lists?"
)
@click.pass_obj
def clear(obj, label_name: str, list_name: str):
    """Clear ALL cards from the specified lists that have the specified label
    
    Args:
        obj (dict): Context object (gets Planka)
        label (str): Name of the label to clear (optional)
        list (str): Name of the list to clear
    """
    board: ppy.Board = obj["board"]

    _list = ppyh.by_list_name(board.lists, list_name)
    if not _list:
        logger.error(f"List '{list_name}' not found")
        return

    _list = _list[0]

    label = ppyh.by_label_name(board.labels, label_name)

    if not label:
        logger.error(f"Label '{label_name}' not found")
        return
    
    label = label[0]

    for card in _list.cards:
        if label and label not in card.labels:
            continue

        card.delete()
        logger.info(f"Deleted card with ID {card.id}")

@main.group()
def label():
    pass


@label.command()
@click.argument("label", nargs=-1)
@click.pass_obj
def delete(obj, label_names: list[str]):
    """Delete the specified labels from the board
    
    Note:
        Calling with no arguments will delete all labels from the board

    Args:
        obj (dict): Context object
        label_names (list[str]): Names of the labels to delete
    """

    board: ppy.Board = obj["board"]

    labels: list[ppy.Label] = [ppyh.by_label_name(board.labels, name) for name in label_names]
    if not labels:
        logger.error(f"Label(s) '{label_names}' not found")
        return

    for label in labels:
        label.delete()
        logger.info(f"Deleted label '{label.name}'")


@label.command()
@click.pass_obj
def colours(obj):
    click.echo(
        "\n".join(
            sorted(
                ppy.constants.LabelColor.__args__)
                )
            )


@main.group()
def card():
    pass


@card.command()
@click.argument("id", type=click.INT, nargs=-1)
@click.pass_obj
def delete(obj, id):
    """Delete a card by its id
    
    Args:
        obj (dict): Context object (uses board context)
        id (int): ID of the card to delete
    """
    board: ppy.Board = obj["board"]

    for card in board.cards:
        if card.id == id:
            card.delete()
            logger.info(f"Deleted card with ID {id}")
            return


@card.command()
@click.option(
    "--list_name",
    "-l",
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
@click.option("--label_names", "-l", multiple=True, help="Label(s) to add to new card")
@click.option(
    "--user_names", "-u", multiple=True, help="User(s) to add to new card"
)
@click.argument("name", nargs=-1)
@click.pass_obj
def add(obj, name: str, list_name: str, position, 
        due_date: datetime | None = None, 
        label_names: list[str] | None = None, user_names: list[str] | None = None):
    """Add named cards to the specified list"""
    board: ppy.Board = obj["board"]

    _list = ppyh.by_list_name(board.lists, list_name)
    if not _list:
        logger.error(f"List '{list_name}' not found")
        return
    _list = _list[0]

    users = [user for user in board.users if user.name in user_names] or None
    labels = [label for label in board.labels if label.name in label_names] or None

    for card_name in name:
        card = ppy.Card(
            name = name,
            position=position or 0,
            dueDate=due_date.isoformat() if due_date else None,
        )
        card = _list.create_card(card)
        for user in users:
            card.add_member(user)
        for label in labels:
            card.add_label(label)
