import click

from llama import marc_export


@click.group()
def cli():
    # move date retrieval here since it will be shared by multiple commands?
    pass


@cli.command()
def run_update_export():
    marc_export.marc_update_export("exlibris/Timdex/UPDATE/")
