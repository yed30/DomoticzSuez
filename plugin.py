#           Suez Plugin (toutsurmoneau)
#
#           Authors:
#           Copyright (C) 2022 Yed30
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
<plugin key="suez" name="Suez" author="Yed30" version="1.0.6" externallink="https://github.com/yed30/DomoticzSuez">
    <params>
        <param field="Username" label="Username" width="200px" required="true" default=""/>
        <param field="Password" label="Password" width="200px" required="true" default="" password="true"/>
        <param field="Mode6" label="Counter ID" width="200px" required="true" default="" />
        <param field="Mode1" label="Days" width="50px" required="false" default="3"/>
        <param field="Mode3" label="Debug" width="75px">
            <options>
                <option label="False" value="0"  default="true" />
                <option label="True" value="1"/>
                <option label="Advanced" value="2"/>
            </options>
        </param>
    </params>
</plugin>
"""
# See https://www.domoticz.com/wiki/Developing_a_Python_plugin
# We do not use the Domoticz FW to handle connection as it has an issue with toutsurmoneau web site

try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

import re
from datetime import datetime
from datetime import timedelta
import time
import requests

BASE_URI = "https://www.toutsurmoneau.fr"
API_ENDPOINT_LOGIN = "/mon-compte-en-ligne/je-me-connecte"
API_ENDPOINT_DATA = "/mon-compte-en-ligne/statJData/"
DEVICE_NAME = "Suez"
DEVICE_DESCRIPTION = "Compteur Suez"
# integer: type (pTypeGeneral)
DEVICE_TYPE = 0xF3
# integer: index of the Suez device
DEVICE_INDEX_UNIT = 1
# integer: subtype (sTypeManagedCounter)
DEVICE_SUB_TYPE = 0x21

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept-Language": "fr,fr-FR;q=0.8,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Mobile Safari/537.36",
    "Connection": "keep-alive",
    "Cookie": "",
}


class BasePlugin:
    """The Plugin Class"""

    # int: debug mode
    iDebugLevel = 0
    # boolean: to check that we are started, to prevent error messages when disabling or restarting the plugin
    isStarted = None
    # integer: switch type (Water m3)
    iSwitchType = 2
    # string: step name of the state machine
    sConnectionStep = None
    # boolean: true if a step failed
    bHasAFail = None
    # string: counter ID for history
    sCounter = None
    # string: current year for history
    sYear = None
    # string: current month for history
    sMonth = None
    # date : current date for history
    dateCurrentData = None
    # string: end year for history
    sEndYear = None
    # string: end month for history
    sEndMonth = None
    # integer: number of days of data to grab for history
    iHistoryDaysForDaysView = 30
    # integer: number of days left for next batch of data
    iDaysLeft = None
    # boolean: is this the batch of the most recent history
    bFirstMonths = None
    # string: username for Suez website
    sUser = None
    # string: password for Suez website
    sPassword = None
    # string: consumption to show = current week ("week"), the previous week ("lweek", the current month ("month"), the previous month ("lmonth"), or year ("year")

    def __init__(self):
        self.isStarted = False
        self.sConnectionStep = "idle"
        self.bHasAFail = False
        self.iDaysLeft = False
        self._token = ""
        self._headers = {}
        self.data = {}
        self.attributes = {}
        self.success = False
        self._session = None
        self._timeout = None
        self.state = 0
        self.nextConnection = datetime.now()

    def myDebug(self, message):
        """Debug function"""
        if self.iDebugLevel:
            Domoticz.Log(message)

    def _get_token(self):
        """Get the token"""
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "fr,fr-FR;q=0.8,en;q=0.6",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Mobile Safari/537.36",
            "Connection": "keep-alive",
            "Cookie": "",
        }
        #    global BASE_URI

        url = BASE_URI + API_ENDPOINT_LOGIN
        try:
            response = requests.get(url, headers=headers, timeout=self._timeout)
        except Exception:
            Domoticz.Error("Can not access site " + BASE_URI)
            return False
        else:
            headers["Cookie"] = ""
            for key in response.cookies.get_dict():
                if headers["Cookie"]:
                    headers["Cookie"] += "; "
                headers["Cookie"] += key + "=" + response.cookies[key]

            phrase = re.compile('_csrf_token" value="(.*)"/>')
            result = phrase.search(response.content.decode("utf-8"))
            self._token = result.group(1)
            self._headers = headers
            return True

    def _get_cookie(self):
        """Connect and get the cookie"""
        if self._session is None:
            self._session = requests.Session()

        if self._get_token():
            data = {
                "_username": self.sUser,
                "_password": self.sPassword,
                "_csrf_token": self._token,
                "signin[username]": self.sUser,
                "signin[password]": None,
                "tsme_user_login[_username]": self.sUser,
                "tsme_user_login[_password]": self.sPassword,
            }
            url = BASE_URI + API_ENDPOINT_LOGIN
            try:
                self._session.post(
                    url,
                    headers=self._headers,
                    data=data,
                    allow_redirects=False,
                    timeout=self._timeout,
                )
            except OSError:
                Domoticz.Error("Can not submit login form.")
                return False

            if "eZSESSID" not in self._session.cookies.get_dict():
                Domoticz.Error("Login error: Please check your username/password.")
                return False

            self._headers["Cookie"] = ""
            self._headers["Cookie"] = "eZSESSID=" + self._session.cookies.get(
                "eZSESSID"
            )
            return True
        # self._get_token() returned False
        return False

    def _fetch_data(self):
        """Fetch latest data from Suez."""
        url = BASE_URI + API_ENDPOINT_DATA
        url += f"/{self.sYear}/{self.sMonth}/{self.sCounter}"

        if self._get_cookie():
            Domoticz.Log(url)
            self.data = requests.get(url, headers=self._headers, timeout=self._timeout)
            return True
        # self._get_cookie() returned False
        self.data = None
        return False

    def createDevice(self):
        """Create Domoticz device."""
        # Only if not already done
        if DEVICE_INDEX_UNIT not in Devices:
            Domoticz.Device(
                Name=DEVICE_NAME,
                Unit=DEVICE_INDEX_UNIT,
                Type=DEVICE_TYPE,
                Subtype=DEVICE_SUB_TYPE,
                Switchtype=self.iSwitchType,
                Description=DEVICE_DESCRIPTION,
                Used=1,
            ).Create()
            if DEVICE_INDEX_UNIT not in Devices:
                Domoticz.Error(
                    "Cannot add Suez device to database. Check in settings that Domoticz is set up to accept new devices"
                )
                return False
        return True

    def createAndAddToDevice(self, usage, usageTotal, Date):
        """Create device and insert usage in Domoticz DB"""
        if not self.createDevice():
            return False

        sNewValue = str(usageTotal) + ";" + str(usage) + ";" + str(Date)
        self.myDebug("Insert this value into the DB: " + sNewValue)
        Devices[DEVICE_INDEX_UNIT].Update(
            nValue=0,
            sValue=sNewValue,
            Type=DEVICE_TYPE,
            Subtype=DEVICE_SUB_TYPE,
            Switchtype=self.iSwitchType,
        )
        return True

    def updateDevice(self, usage, usageTotal):
        """Update value shown on Domoticz dashboard"""
        if not self.createDevice():
            return False

        sUpdateValue = str(usageTotal) + ";" + str(usage)
        self.myDebug("Update dashboard with this value: " + sUpdateValue)
        Devices[DEVICE_INDEX_UNIT].Update(
            nValue=0,
            sValue=sUpdateValue,
            Type=DEVICE_TYPE,
            Subtype=DEVICE_SUB_TYPE,
            Switchtype=self.iSwitchType,
        )
        return True

    def showStepError(self, days, logMessage):
        """Show error in state machine context"""
        if days:
            Domoticz.Error(
                logMessage
                + " during step "
                + self.sConnectionStep
                + " for days of year "
                + self.sYear
                + " and month "
                + self.sMonth
            )
        else:
            Domoticz.Error(
                logMessage
                + " during step "
                + self.sConnectionStep
                + " for months of year "
                + self.sYear
            )

    def exploreDataDays(self):
        """Grab days data inside received JSON data for history"""
        self.myDebug("Begin Data Days")
        Domoticz.Log("days left " + str(self.iDaysLeft))
        curDay = None
        curIndexDay = None
        curTotalIndexDay = None

        if not self.data:
            Domoticz.Error(True, "Didn't received data")
            return False

        try:
            dJson = self.data.json()
            dJson.reverse()
        except (ValueError, TypeError) as err:
            Domoticz.Error(True, "Data received are not JSON: " + str(err))
            return False
        else:
            for day in range(len(dJson)):
                for i, value in enumerate(dJson[day]):
                    if i == 0:
                        try:
                            curDay = suezDateToDatetime(value)
                        except Exception as err:
                            self.showStepError(
                                True,
                                "Error in received JSON data time format: " + str(err),
                            )
                            return False
                    if i == 1:
                        # Convert m3 consumption to liter (DON'T FORGET TO SET DEVICE LIMITER TO 1000)
                        curIndexDay = float(value) * 1000.0
                    if i == 2:
                        curTotalIndexDay = float(value) * 1000.0
                # Update only if there is a value
                if curIndexDay > 0.0:
                    self.myDebug(
                        "Value "
                        + str(curIndexDay)
                        + " with total of "
                        + str(curTotalIndexDay)
                        + " for "
                        + datetimeToSQLDateString(curDay)
                    )
                    if not self.createAndAddToDevice(
                        curIndexDay,
                        curTotalIndexDay,
                        datetimeToSQLDateString(curDay),
                    ):
                        return False
                    # If we are on the most recent batch and end date, use the most recent data for Domoticz dashboard
                    if self.bFirstMonths:
                        self.bFirstMonths = False
                        if not self.updateDevice(curIndexDay, curTotalIndexDay):
                            return False
            return True

    def calculateMonthData(self):
        """Calculate year and month for data pulling"""
        self.myDebug("Number of days left: " + str(self.iDaysLeft))
        # Remove one day to get correct data and avoid month change issue
        self.dateCurrentData = (
            datetime.now() - timedelta(days=self.iDaysLeft) - timedelta(days=1)
        )
        self.myDebug(str(self.dateCurrentData))
        bNewData = False
        # Set year and month for data request
        if (self.sYear is None) or (self.sYear != str(self.dateCurrentData.year)):
            self.sYear = str(self.dateCurrentData.year)
            bNewData = True

        if (self.sMonth is None) or (self.sMonth != str(self.dateCurrentData.month)):
            self.sMonth = str(self.dateCurrentData.month)
            bNewData = True

        if (self.sMonth == self.sEndMonth) and (self.sYear == self.sEndYear):
            self.bFirstMonths = True

        if bNewData:
            return

        if (self.sYear == str(self.dateCurrentData.year)) and (
            self.sMonth == str(self.dateCurrentData.month)
        ):
            self.myDebug("Same year: " + self.sYear + " and month: " + self.sMonth)
            if self.iDaysLeft > 0:
                self.iDaysLeft = self.iDaysLeft - 1
                self.calculateMonthData()

    def setNextConnection(self, tomorrow):
        """Calculate next complete grab, for tomorrow between 8 and 9 am if tomorrow is true, for next hour otherwise"""
        if tomorrow:
            self.nextConnection = datetime.now() + timedelta(days=1)
            self.nextConnection = self.nextConnection.replace(hour=8)
            if self.iDaysLeft == 0:
                self.iDaysLeft = 1
        else:
            self.nextConnection = datetime.now() + timedelta(hours=1)
        # Randomize minutes to lower load on toutsurmoneau website
        # We take microseconds to randomize
        minutesRand = round(datetime.now().microsecond / 10000) % 60
        self.nextConnection = self.nextConnection + timedelta(minutes=minutesRand)

    def handleConnection(self, Data=None):
        """Handle the connection state machine"""
        self.calculateMonthData()
        if self.iDaysLeft == 0:
            # We have parsed everything
            self.bHasAFail = False
            self.sConnectionStep = "idle"
            Domoticz.Log("Done")
        else:
            if self._fetch_data():

                Domoticz.Log(
                    "Parsing data for year: "
                    + self.sYear
                    + " and month: "
                    + self.sMonth
                )

                if not self.exploreDataDays():
                    self.bHasAFail = True
                    self.sConnectionStep = "idle"
                else:
                    Domoticz.Log(
                        "Got data for year: "
                        + self.sYear
                        + " and month: "
                        + self.sMonth
                    )
                    if self.iDaysLeft > 0:
                        # self.bFirstMonths = False
                        # self.nextConnection = datetime.now()
                        self.sConnectionStep = "logconnected"
                        self.handleConnection()
                    # We have parsed everything
                    else:
                        self.sConnectionStep = "idle"
                        Domoticz.Log("Done")
            else:
                Domoticz.Log("Error Connecting to Site")
                self.bHasAFail = True
                self.sConnectionStep = "idle"
            # Next connection time depends on success
            if self.sConnectionStep == "idle":
                if self.bHasAFail:
                    self.setNextConnection(False)

    def onStart(self):
        """Handle plugin start"""
        Domoticz.Heartbeat(20)
        self.myDebug("onStart called")

        self.sUser = Parameters["Username"]
        self.sPassword = Parameters["Password"]
        try:
            self.sCounter = Parameters["Mode6"]
        except Exception:
            self.sConnectionStep = "idle"
            self.bHasAFail = True
        # History for short log is 1000 days max (default to 365)
        try:
            self.iHistoryDaysForDaysView = int(Parameters["Mode1"])
        except Exception:
            self.iHistoryDaysForDaysView = 365
        if self.iHistoryDaysForDaysView < 1:
            self.iHistoryDaysForDaysView = 1
        elif self.iHistoryDaysForDaysView > 1000:
            self.iHistoryDaysForDaysView = 1000

        # enable debug if required
        try:
            self.iDebugLevel = int(Parameters["Mode3"])
        except ValueError:
            self.iDebugLevel = 0

        if self.iDebugLevel > 1:
            Domoticz.Debugging(1)

        Domoticz.Log("Username set to " + self.sUser)
        Domoticz.Log("Counter ID set to " + self.sCounter)
        if Parameters["Password"]:
            Domoticz.Log("Password is set")
        else:
            Domoticz.Log("Password is not set")
        Domoticz.Log(
            "Days to grab for daily view set to " + str(self.iHistoryDaysForDaysView)
        )
        Domoticz.Log("Debug set to " + str(self.iDebugLevel))

        # most init
        # init(self)

        if self.createDevice():
            self.nextConnection = datetime.now()
        else:
            self.setNextConnection(False)

        self.sEndYear = str(datetime.now().year)
        self.sEndMonth = str(datetime.now().month)
        self.iDaysLeft = self.iHistoryDaysForDaysView

        # Now we can enabling the plugin
        self.isStarted = True

    def onHeartbeat(self):
        """Handle Domoticz Heartbeat"""
        Domoticz.Debug("onHeartbeat() called")
        self.iDaysLeft = self.iHistoryDaysForDaysView
        self.sYear = None
        self.sMonth = None
        if datetime.now() > self.nextConnection:
            # We immediatly program next connection for tomorrow, if there is a problem, we will reprogram it sooner
            self.setNextConnection(True)
            self.handleConnection()
            Domoticz.Log(
                "Next connection: " + datetimeToSQLDateTimeString(self.nextConnection)
            )


_plugin = BasePlugin()


def onStart():
    """Domoticz FW onStart."""
    _plugin.onStart()


def onStop():
    """Domoticz FW onStop."""
    Domoticz.Log("onStop - Plugin is stopping.")


def onConnect(Connection, Status, Description):
    """Domoticz FW onConnect."""
    Domoticz.Log("onConnect")


def onMessage(Connection, Data):
    """Domoticz FW onMessage."""
    Domoticz.Log("onMessage")


def onCommand(Unit, Command, Level, Hue):
    """Domoticz FW onCommand."""
    Domoticz.Log("onCommand")


def onDeviceAdded(Unit):
    """Domoticz FW onDeviceAdded."""
    Domoticz.Log("onDeviceAdded")


def onDeviceModified(Unit):
    """Domoticz FW onDeviceModified."""
    Domoticz.Log("onDeviceModified")


def onDeviceRemoved(Unit):
    """Domoticz FW onDeviceRemoved."""
    Domoticz.Log("onDeviceRemoved")


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    """Domoticz FW onNotification."""
    Domoticz.Log("onNotification")


def onDisconnect(Connection):
    """Domoticz FW onDisconnect."""
    Domoticz.Log("onDisconnect")


def onHeartbeat():
    """Domoticz FW onHeartbeat."""
    _plugin.onHeartbeat()


def suezDateToDatetime(datetimeStr):
    """Convert Suez date string to datetime object"""
    return datetime(*(time.strptime(datetimeStr, "%d/%m/%Y")[0:6]))


def datetimeToSQLDateString(datetimeObj):
    """Convert datetime object to Domoticz date string"""
    return datetimeObj.strftime("%Y-%m-%d")


def datetimeToSQLDateTimeString(datetimeObj):
    """Convert datetime object to Domoticz date and time string"""
    return datetimeObj.strftime("%Y-%m-%d %H:%M:%S")
