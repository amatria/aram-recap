#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2023-onwards Iñaki Amatria-Barral
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import json
import argparse

from recap.cache import Cache
from recap.datasource import RiotAPIProxy, Summoner, Match, MatchList

THIS_SCRIPT_PATH = os.path.realpath(__file__)
THIS_SCRIPT_DIR_PATH = os.path.dirname(THIS_SCRIPT_PATH)
THIS_SCRIPT_DIR_DIR_PATH = os.path.dirname(THIS_SCRIPT_DIR_PATH)


class ARAMCrawlingDriver:
    def __init__(
        self,
        summoner_name,
        date,
        server,
        api_key,
        cache_dir,
        max_requests_per_minute,
    ):
        self._summoner_name = summoner_name
        self._date = date
        self._server = server
        self._api_key = api_key
        self._cache = Cache(cache_dir=cache_dir)
        self._proxy = RiotAPIProxy(max_requests_per_minute=max_requests_per_minute)

    def crawl(self):
        print(f">> Crawling summoner data for '{self._summoner_name}'")
        summoner = Summoner.crawl(
            summoner_name=self._summoner_name,
            server=self._server,
            api_key=self._api_key,
            proxy=self._proxy,
        )
        print(f">> Crawling ARAM match history on {self._date}")
        matches = MatchList.crawl(
            puuid=summoner["puuid"],
            date=self._date,
            server=self._server,
            api_key=self._api_key,
            proxy=self._proxy,
        )
        for match_id in matches:
            cache_entry = f"{match_id}.json"
            if self._cache.exists(cache_entry):
                print(f">> Skipping match '{match_id}': cache hit")
                continue
            print(f">> Crawling match '{match_id}'")
            match = Match.crawl(
                match_id=match_id,
                server=self._server,
                api_key=self._api_key,
                proxy=self._proxy,
            )
            self._cache.store(f"{match_id}.json", json.dumps(match, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crawls all the ARAM matches from a given summoner in a given date",
        epilog="MIT License; Copyright (c) 2023-onwards Iñaki Amatria-Barral",
    )
    parser.add_argument(
        type=str,
        dest="summoner_name",
        metavar="<summoner name>",
        help="summoner to crawl",
    )
    parser.add_argument(
        "-a",
        type=str,
        dest="api_key",
        metavar="<API key>",
        help="set the Riot API key",
    )
    parser.add_argument(
        "-c",
        type=str,
        dest="cache_dir",
        metavar="<cache dir>",
        help="set the path to the cache directory",
    )
    parser.add_argument(
        "-d",
        type=str,
        required=True,
        dest="date",
        metavar="<dd/mm/yyyy>",
        help="set the crawling date",
    )
    parser.add_argument(
        "-r",
        type=int,
        default=40,
        dest="rate",
        metavar="<rate>",
        help="set the maximum number of requests per minute",
    )
    parser.add_argument(
        "-s",
        type=str,
        required=True,
        dest="server",
        metavar="<server>",
        help="set the summoner's server",
    )
    args = parser.parse_args()

    api_key = args.api_key
    if api_key is None:
        with open(os.path.join(THIS_SCRIPT_DIR_DIR_PATH, "secrets.json"), "r") as f:
            api_key = json.load(f)["RIOT_GAMES_API_KEY"]

    cache_dir = args.cache_dir
    if cache_dir is None:
        cache_dir = os.path.join(THIS_SCRIPT_DIR_DIR_PATH, "cache")

    print(f"{parser.prog}: {parser.description}\n")
    ARAMCrawlingDriver(
        summoner_name=args.summoner_name,
        date=args.date,
        server=args.server,
        api_key=api_key,
        cache_dir=cache_dir,
        max_requests_per_minute=args.rate,
    ).crawl()
    print(f"\n{parser.epilog}")
