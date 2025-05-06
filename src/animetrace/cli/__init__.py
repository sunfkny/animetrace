from typing import Annotated

import httpx
import typer

import animetrace
from animetrace.api.search import SearchModel

app = typer.Typer(no_args_is_help=True)


@app.command(no_args_is_help=True)
def search(
    file_or_url: Annotated[str, typer.Argument()],
    model: Annotated[SearchModel, typer.Option()] = SearchModel.anime,
    base_url: Annotated[
        str, typer.Option(help="The base URL for AnimeTrace API")
    ] = "https://api.animetrace.com",
    endpoint: Annotated[
        str, typer.Option(help="The endpoint for AnimeTrace API")
    ] = "v1/search",
    multi: Annotated[
        bool,
        typer.Option(
            help="Whether to show multiple results",
        ),
    ] = True,
    ai_detect: Annotated[
        bool,
        typer.Option(
            help="Whether to enable AI image detection",
        ),
    ] = False,
):
    try:
        response_model_data = animetrace.search(
            file_or_url,
            model=model,
            base_url=base_url,
            endpoint=endpoint,
            is_multi=multi,
            ai_detect=ai_detect,
        )
    except httpx.HTTPStatusError as e:
        typer.echo(e.response.text)
        typer.echo(e)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(e)
        raise typer.Exit(1)

    for item in response_model_data:
        typer.echo(f"{item.box_id} {item.box}")
        for c in item.character:
            typer.echo(f"{c.get_character_normalized()} ({c.work})")


def main():
    app()
