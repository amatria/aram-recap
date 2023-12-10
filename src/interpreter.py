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
from recap.datasource import RiotAPIProxy, Summoner


THIS_SCRIPT_PATH = os.path.realpath(__file__)
THIS_SCRIPT_DIR_PATH = os.path.dirname(THIS_SCRIPT_PATH)
THIS_SCRIPT_DIR_DIR_PATH = os.path.dirname(THIS_SCRIPT_DIR_PATH)


class ARAMInterpreterDriver:
    def __init__(
        self,
        summoner_name,
        server,
        api_key,
        cache_dir,
        max_requests_per_minute,
    ):
        self._summoner_name = summoner_name
        self._server = server
        self._api_key = api_key
        self._cache = Cache(cache_dir=cache_dir)
        self._proxy = RiotAPIProxy(max_requests_per_minute=max_requests_per_minute)

    def interpret(self):
        print(f">> Crawling summoner data for '{self._summoner_name}'")
        summoner = Summoner.crawl(
            summoner_name=self._summoner_name,
            server=self._server,
            api_key=self._api_key,
            proxy=self._proxy,
        )
        print(">> Filtering matches")
        matches = self._filter_matches_by_puuid(puuid=summoner["puuid"])
        print(">> Computing statistics")
        total_time_in_game = self._compute_time_in_game(matches=matches)
        total_poros_casted = self._compute_poro_casts(
            matches=matches, puuid=summoner["puuid"]
        )
        print(
            f"""  - Number of matches: {len(matches)}
  - Time spent in game: {self._seconds_to_text(seconds=total_time_in_game)}
  - Poro casts: {total_poros_casted}"""
        )

    def _filter_matches_by_puuid(self, puuid):
        ret = []
        for entry in self._cache.entries():
            with open(entry, "r") as f:
                match_info = json.load(f)
                if puuid in match_info["metadata"]["participants"]:
                    ret.append(match_info)
        return ret

    def _compute_time_in_game(self, matches):
        ret = 0
        for match in matches:
            ret += match["info"]["gameDuration"]
        return ret

    def _seconds_to_text(self, seconds):
        days = seconds // 86400
        hours = (seconds - days * 86400) // 3600
        minutes = (seconds - days * 86400 - hours * 3600) // 60
        seconds = seconds - days * 86400 - hours * 3600 - minutes * 60
        return f"{days}d {hours}h {minutes}m {seconds}s"

    def _compute_poro_casts(self, matches, puuid):
        ret = 0
        for match in matches:
            for participant in match["info"]["participants"]:
                if participant["puuid"] != puuid:
                    continue
                for spell_id in [1, 2]:
                    id = participant[f"summoner{spell_id}Id"]
                    casts = participant[f"summoner{spell_id}Casts"]
                    if id == 32:
                        ret += casts
        return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interprets all the ARAM matches in the cache from a given summoner",
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
    ARAMInterpreterDriver(
        summoner_name=args.summoner_name,
        server=args.server,
        api_key=api_key,
        cache_dir=cache_dir,
        max_requests_per_minute=args.rate,
    ).interpret()
    print(f"\n{parser.epilog}")
