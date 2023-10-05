import aiohttp
import logging


class TerminalSession:
    def __init__(self, terminal_id: int, url: str, login: str, password: str) -> None:
        self.terminal_id = terminal_id
        self.url = url
        self.__login = login
        self.__password = password
        self.__login_url = url + "/Account/Login"
        self.__table_sales_url = url + "/Admin/_TableSales"
        self.__cookie_jar = aiohttp.CookieJar()
        self._session = aiohttp.ClientSession(cookie_jar=self.__cookie_jar)

    async def __aenter__(self) -> "TerminalSession":
        if self._session.closed:
            self._session = aiohttp.ClientSession(cookie_jar=self.__cookie_jar)

        try:
            if not await self.check_login():
                await self._login()
        except Exception as e:
            logging.error(e)

        return self

    async def __aexit__(self, *args, **kwargs):
        await self.close()

    async def close(self):
        if not self._session.closed:
            await self._session.close()

    async def check_login(self):
        async with self._session.get(self.url) as resp:
            resp.raise_for_status()
            return str(resp.url) == self.url + "/Admin"

    async def _login(self):
        async with self._session.post(
            self.__login_url,
            data={"Login": self.__login, "Password": self.__password},
        ) as resp:
            resp.raise_for_status()
            if self.login_failed(resp):
                raise Exception("Login failed")

        logging.debug("Login successfull id=%s url=%s", self.terminal_id, self.url)

    def login_failed(self, response: aiohttp.ClientResponse):
        return str(response.url) == self.__login_url

    async def get_table_sales_page(self) -> str | None:
        async with self._session.get(self.__table_sales_url) as resp:
            resp.raise_for_status()
            logging.debug(
                "Getting table sales page successfull id=%s url=%s",
                self.terminal_id,
                self.url,
            )
            return await resp.text()

    async def create_promo(self):
        """
        Function creates promocodes by sending request with next format
            data = {
                "Name": "",
                "DateStart": "",
                "DateEnd": "",
                "TypeCode": "",
                "Code": "",
                "StartCode": "",
                "EndCode": "",
                "CountCodeGen": "",
                "StartCodeGen": "",
                "EndCodeGen": "",
                "CountActivate": "1",
                "MaxDiscountAmount": "0",
                "OnlyNewPartners": "false",
                "ActivateType": "0",
                "Comment": "",
                "Phone": "",
                "PhoneComment": "",
                "IdGoodCore": "1",
                "TypeAction": "2",
                "Value": "0",
            }
        """
        data = {
            "Name": "TestForBot",
            "DateStart": "28.09.2023",
            "DateEnd": "28.10.2023",
            "TypeCode": "0",
            "Code": "1234567",
            "StartCode": "",
            "EndCode": "",
            "CountCodeGen": "",
            "StartCodeGen": "",
            "EndCodeGen": "",
            "CountActivate": "1",
            "MaxDiscountAmount": "0",
            "OnlyNewPartners": "false",
            "ActivateType": "0",
            "Comment": "1123",
            "Phone": "",
            "PhoneComment": "",
            "IdGoodCore": "1",
            "TypeAction": "2",
            "Value": "0",
        }
        async with self._session.post(
            self.url
            + "/Modules/ModulePartial_Post?ModuleUrl=http://localhost:8084&ActionUrl=Promocodes/Create",
            data=data,
        ) as resp:
            print(resp.raw_headers)
