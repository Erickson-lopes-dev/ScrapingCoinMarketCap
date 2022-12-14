from typing import List

import requests
from bs4 import BeautifulSoup as bs4
from loguru import logger

from .exceptions import CryptoNotExists, PageNotFound, DataCollectionError
from .models import CryptoCurrency, CryptoCurrencySingle


class ScrapingCryptoCurrency:
    def __init__(self):
        logger.add(f'logs/{__class__.__name__}.log')
        logger.add(f'logs/{__class__.__name__}_dict.log', serialize=True)

        self.__url_main: str = "https://coinmarketcap.com/"
        self.__url_single: str = 'https://coinmarketcap.com/currencies/'

    @property
    def url_main(self) -> str:
        return self.__url_main

    @property
    def url_single(self) -> str:
        return self.__url_single

    @classmethod
    def get_data(cls, url: str) -> bs4:
        try:
            r = requests.get(url)
        except requests.exceptions.ConnectionError:
            logger.exception(f'Connection error')
            raise ConnectionError(f'Connection error')

        match r.status_code:
            case 200:
                logger.info(f'Get data from {url}')
                soup = bs4(r.text, "html.parser")
                return soup
            case 404:
                logger.warning(f'Page not found {url}')
                raise PageNotFound("Page not found")
            case _:
                logger.error(f"Error {r.status_code} {r.reason}")
                raise Exception("Status Code (Error): {}".format(r.status_code))

    def get_all_top_10_crypto_currency(self) -> List[CryptoCurrency]:
        list_of_currencies: List[CryptoCurrency] = []

        soup = self.get_data(self.__url_main)
        try:
            for crypto_tr in soup.find_all('tr'):
                if crypto_tr.find('span', class_='icon-Star'):
                    # name
                    names = crypto_tr.findAllNext('td')[2]
                    name = names.findNext(color='text')
                    initials = names.findNext(color='text3')

                    # icon
                    icon = crypto_tr.find(class_='coin-logo')['src']

                    # price
                    price = crypto_tr.findAllNext('td')[3].text
                    price = float(price.replace('$', '').replace(',', ''))

                    # market cap
                    market_cap = crypto_tr.findAllNext('td')[7].findAllNext('span')[1].text
                    market_cap = float(market_cap.replace('$', '').replace(',', ''))

                    # volume
                    volume = crypto_tr.findAllNext('td')[8].findNext(color='text').text
                    volume = float(volume.replace('$', '').replace(',', ''))

                    # circulating supply
                    circulating_supply = crypto_tr.findAllNext('td')[9].findNext(color='text').text
                    circulating_supply = float(circulating_supply.split()[0].replace(',', ''))

                    # add to list
                    list_of_currencies.append(CryptoCurrency(
                        icon=icon,
                        name=name.text,
                        symbol=initials.text,
                        price=price,
                        marketCap=market_cap,
                        volume=volume,
                        circulating_supply=circulating_supply
                    ))
        except Exception as dce:
            logger.exception(f'Error {dce}')
            raise DataCollectionError(dce)

        return list_of_currencies

    def get_single_crypto_currency(self, name: str) -> CryptoCurrencySingle:
        try:
            soup: bs4 = self.get_data(self.__url_single + name.upper())
        except PageNotFound:
            logger.warning(f'Crypto currency {name} not exists')
            raise CryptoNotExists(f'Crypto currency {name} not exists')

        try:
            # name
            name_section: bs4 = soup.find(class_="nameSection")
            rank = int(name_section.find(class_="namePillPrimary").text.replace('Rank #', ''))

            symbol: str = name_section.find(class_='nameSymbol').text
            icon: str = name_section.find(class_='nameHeader').find('img')['src']

            price: float = float(soup.find(class_='priceValue').text.replace('$', '').replace(',', ''))

            market_cap: float = float(soup.find_all(class_='statsValue')[0].text.replace('$', '').replace(',', ''))
            volume: float = float(soup.find_all(class_='statsValue')[2].text.replace('$', '').replace(',', ''))
            circulating_supply: float = float(
                soup.find_all(class_='statsValue')[3].text.split()[0].replace('$', '').replace(',', ''))

            return CryptoCurrencySingle(
                name=name,
                symbol=symbol,
                icon=icon,
                rank=rank,
                price=price,
                marketCap=market_cap,
                volume=volume,
                circulating_supply=circulating_supply)

        except Exception as dce:
            logger.exception(f'Error {dce}')
            raise DataCollectionError(dce)
