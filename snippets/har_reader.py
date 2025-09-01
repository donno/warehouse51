"""Extract information from a HAR (HTTP Archive)."""

import json
import pathlib
import typing


class LogCreator(typing.TypedDict):
    name: str
    version: str
    comment: str


class Timing(typing.TypedDict):
    connect: float
    ssl: float
    send: float
    receive: float
    wait: float


class Request(typing.TypedDict):
   method: str
   url: str
   httpVersion: str
   cookies: list
   headers: list[dict[str, str]]
   queryString: list[dict[str, str]]
   headersSize: int
   bodySize: int


class Entry(typing.TypedDict):
   startedDateTime: str
   """Date and time stamp of the request start (ISO 8601 - YYYY-MM-DDThh:mm:ss.sTZD)."""

   time: int
   """Total elapsed time of the request in milliseconds."""

   request: Request
   response: dict
   cache: dict
   timings: Timing


class Log(typing.TypedDict):
    version: str
    creator: LogCreator
    pages: list
    entries: list[Entry]


def load(path: pathlib.Path) -> Log:
    with path.open("r") as reader:
        return json.load(reader)["log"]


def format_time(value_in_ms: int):
   seconds = value_in_ms / 1000
   if seconds < 1.2:
      return f"{value_in_ms:.2f}ms"
   return f"{seconds:.2f}s"


if __name__ == "__main__":
   contents = load(pathlib.Path.cwd() / "example.har")
   for entry in contents["entries"]:
      if entry["request"]["method"] == "POST":
         print(format_time(entry["time"]), end=',')
