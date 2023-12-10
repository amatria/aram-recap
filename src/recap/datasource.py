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

import time
import datetime
import requests

BASE_RIOT_API_URL = "https://##SERVER##.api.riotgames.com/lol"


class RiotAPIProxy:
    def __init__(self, max_requests_per_minute=40):
        self._last_request_timestamp = datetime.datetime.now().timestamp()
        self._request_timeout = 60 / max_requests_per_minute

    def get(self, url, headers):
        self._wait_timeout()
        return requests.get(url=url, headers=headers)

    def _wait_timeout(self):
        time_since_last_request = (
            datetime.datetime.now().timestamp() - self._last_request_timestamp
        )
        if time_since_last_request < self._request_timeout:
            time.sleep(self._request_timeout - time_since_last_request)
        self._last_request_timestamp = datetime.datetime.now().timestamp()


class Summoner:
    @staticmethod
    def crawl(summoner_name, server, api_key, proxy):
        url = f"{BASE_RIOT_API_URL}/summoner/v4/summoners/by-name/{summoner_name}"
        url = url.replace(
            "##SERVER##", Summoner._server_str_to_subdomain(server=server)
        )
        response = proxy.get(url=url, headers={"X-Riot-Token": api_key})
        if response.status_code != 200:
            raise ValueError("ERROR: Unable to find summoner '{summoner_name}'")
        return response.json()

    @staticmethod
    def _server_str_to_subdomain(server):
        return {"euw": "euw1"}[server.lower()]


class MatchList:
    @staticmethod
    def crawl(puuid, date, server, api_key, proxy):
        start_epoch = int(datetime.datetime.strptime(date, "%d/%m/%Y").timestamp())
        end_epoch = int(start_epoch + 86400)
        url = f"{BASE_RIOT_API_URL}/match/v5/matches/by-puuid/{puuid}/ids?queue=450&start=0&count=100&startTime={start_epoch}&endTime={end_epoch}"
        url = url.replace(
            "##SERVER##", MatchList._server_str_to_subdomain(server=server)
        )
        response = proxy.get(url=url, headers={"X-Riot-Token": api_key})
        if response.status_code != 200:
            raise ValueError("ERROR: Unable to recover match history")
        return response.json()

    @staticmethod
    def _server_str_to_subdomain(server):
        return {"euw": "europe"}[server.lower()]


class Match:
    @staticmethod
    def crawl(match_id, server, api_key, proxy):
        url = f"{BASE_RIOT_API_URL}/match/v5/matches/{match_id}"
        url = url.replace("##SERVER##", Match._server_str_to_subdomain(server=server))
        response = proxy.get(url=url, headers={"X-Riot-Token": api_key})
        if response.status_code != 200:
            raise ValueError(f"ERROR: Unable to recover match '{match_id}'")
        return response.json()

    @staticmethod
    def _server_str_to_subdomain(server):
        return {"euw": "europe"}[server.lower()]
