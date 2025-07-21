import os
from dotenv import load_dotenv
from zeep import Client, Settings
from zeep.wsse.username import UsernameToken
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from lxml import etree
from requests import Session

load_dotenv()

class KonikClient:
    def __init__(self, wsdl_url=None, service_url=None, username=None, password=None, timeout=15):
        self.wsdl_url = wsdl_url or os.getenv("WSDL_URL")
        self.service_url = service_url or os.getenv("SERVICE_URL")
        self.username = username or os.getenv("KONIK_USERNAME")
        self.password = password or os.getenv("KONIK_PASSWORD")
        self.timeout = timeout

        self.history = HistoryPlugin()
        session = Session()
        session.verify = False
        transport = Transport(session=session, timeout=self.timeout)
        settings = Settings(strict=False)

        self.client = Client(
            wsdl=self.wsdl_url,
            transport=transport,
            wsse=UsernameToken(self.username, self.password),
            settings=settings,
            plugins=[self.history]
        )

        # This is the Zeep service object you'll use to call methods
        self.service = self.client.create_service(
            "{http://konik.cgrate.com}KonikWsBinding",
            self.service_url
        )

    def get_raw_request(self):
        if self.history.last_sent:
            return etree.tostring(self.history.last_sent["envelope"], pretty_print=True, encoding="unicode")
        return "No request sent yet."

    def get_raw_response(self):
        if self.history.last_received:
            return etree.tostring(self.history.last_received["envelope"], pretty_print=True, encoding="unicode")
        return "No response received yet."
                