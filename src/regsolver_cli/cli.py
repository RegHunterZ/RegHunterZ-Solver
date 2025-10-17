"""
Basic CLI for the RegSolver helper toolset.
- Provides a `parse` command that reads a hand-history (text) file and prints a minimal summary.
This is a skeleton: extend parsing logic to your hand-history format.
"""
import os
import json
import click
from pathlib import Path

@click.group()
def main():
    """RegSolver CLI — utility commands for parsing and exporting."""
    pass

@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--format", "-f", "outfmt", default="json", type=click.Choice(["json","csv","text"]), help="Export format")
@click.option("--show", is_flag=True, help="Print parsed summary to stdout")
def parse(input_file, outfmt, show):
    """
    Parse a hand-history or data file and produce a summary + optional export.
    This skeleton does basic breakdown: lines count and simple metadata placeholder.
    """
    p = Path(input_file)
    with p.open("r", encoding="utf-8", errors="ignore") as fh:
        lines = [l.rstrip("\n") for l in fh]
    # Placeholder parsing: user should replace with domain parser
    summary = {
        "file": str(p),
        "lines": len(lines),
        "size_bytes": p.stat().st_size,
        "sample_top_lines": lines[:5],
    }
    # default output file in same folder
    outpath = p.with_suffix(".parsed." + outfmt)
    if outfmt == "json":
        with open(outpath, "w", encoding="utf-8") as of:
            json.dump(summary, of, indent=2, ensure_ascii=False)
    elif outfmt == "csv":
        # minimal csv: key,value per line
        with open(outpath, "w", encoding="utf-8") as of:
            for k,v in summary.items():
                of.write(f'"{k}","{str(v).replace('\"', '')}"\n')
    else:  # text
        with open(outpath, "w", encoding="utf-8") as of:
            for k,v in summary.items():
                of.write(f"{k}: {v}\n")
    if show:
        click.echo("Parsed summary:")
        click.echo(json.dumps(summary, indent=2, ensure_ascii=False))
    click.echo(f"Wrote summary to: {outpath}")

if __name__ == "__main__":
    main()
