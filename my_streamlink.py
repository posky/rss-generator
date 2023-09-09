"""Parse curl command and generate streamlink command."""
import argparse
import shlex
import sys
from collections import OrderedDict
from typing import NamedTuple

import clipboard

parser = argparse.ArgumentParser()
parser.add_argument("command")
parser.add_argument("url")
parser.add_argument("-H", "--header", action="append", default=[])
parser.add_argument("--compressed", action="store_true")

exclude_headers = ["sec-ch-ua", "user-agent"]


class ParsedContext(NamedTuple):
    """Parsed curl command."""

    url: str
    headers: OrderedDict[str, str]


def normalize_newlines(multiline_text: str) -> str:
    r"""Replaces all occurrences of " \\\n" with " " in the given multiline_text.

    Args:
        multiline_text: The input multiline text.

    Returns:
        The normalized multiline text.
    """
    return multiline_text.replace(" \\\n", " ")


def parse_context(curl_command: str) -> ParsedContext:
    """Parse the given curl command and extract the relevant information.

    Args:
        curl_command (str): The curl command to parse.

    Returns:
        ParsedContext: The parsed context containing the extracted information.
    """
    tokens = shlex.split(normalize_newlines(curl_command), posix=False)
    parsed_args = parser.parse_args(tokens)
    if parsed_args.url.startswith("'"):
        parsed_args.url = parsed_args.url[1:]
    if parsed_args.url.endswith("'"):
        parsed_args.url = parsed_args.url[:-1]

    quoted_headers = OrderedDict()
    for curl_header in parsed_args.header:
        header_key, header_value = curl_header.split(":", 1)
        if header_key.startswith("'"):
            header_key = header_key[1:]
        if header_value.endswith("'"):
            header_value = header_value[:-1]
        if any([x in header_value.strip() for x in [" ", '"']]):
            header_value = f"'{header_value.strip()}'"

        if header_key.lower() not in exclude_headers:
            quoted_headers[header_key] = header_value.strip()

    return ParsedContext(url=parsed_args.url, headers=quoted_headers)


def generate_streamlink_command(parsed_context: ParsedContext) -> str:
    """Generates a streamlink command based on the provided parsed context.

    Args:
        parsed_context (ParsedContext): The parsed context object containing the URL,
            headers, and other information.

    Returns:
        str: The generated streamlink command as a string.
    """
    tokens = ["streamlink", parsed_context.url, "best"]

    for key, value in parsed_context.headers.items():
        tokens += ["--http-header", f"{key}={value}"]

    return " ".join(tokens)


def main() -> None:
    """This function is the main entry point of the program.

    It prompts the user for the input type (0 for request header and 1 for curl command)
    and then performs the appropriate actions based on the input type.
    If the input type is 0, it prompts the user for the request URL and
    the request headersuntil the end of input is reached. It then constructs a curl
    command string using the provided URL and headers. If the input type is 1,
    it prompts the user for the curl command until the end of input is reached.
    It then assigns the provided curl command to the `curl_command` variable. After that,
    it calls the `parse_context` function with `curl_command` as the argument to parse
    the context of the curl command and assigns the returned result to the `result`
    variable. Next, it calls the `generate_streamlink_command` function with `result`
    as the argument to generate the streamlink command and assigns the returned
    command to the `streamlink_command` variable. Finally, it prints the
    `streamlink_command` and copies it to the clipboard using the `clipboard.copy`
    function.

    Args:
    - None

    Returns:
    - None
    """
    input_type = input("Request header: 0, curl command: 1  ")
    if input_type == "0":
        url = input("Input request url: ")
        print("Input request headers (End: Ctrl-z)")
        lines = sys.stdin.readlines()[1:]
        commands = [f"curl '{url}'"]
        for line in lines:
            new_line = line.split("\n")[0]
            commands.append(f"-H '{new_line}'")
        curl_command = "".join(commands)

    elif input_type == "1":
        print("Input curl command (End: Ctrl-z)")
        lines = sys.stdin.readlines()
        curl_command = "".join(lines)
    else:
        print("not proper input")
        return None

    result = parse_context(curl_command)
    streamlink_command = generate_streamlink_command(result)
    print(streamlink_command)

    clipboard.copy(streamlink_command)


if __name__ == "__main__":
    main()
