# coding=UTF8
# Python module for the AM03127 (a.k.a. AM004-03127) LED display module.

# The device has 16 elements of 7 rows x 5 columns == 7 rows x 80 columns

import serial, operator, datetime, functools, re, logging

class CommunicationError(Exception):
    """This exception is raised if a communication error is detected."""
    pass

Replacements = {
        "€": "<U00>",
        "↑": "<U01>",
        "↓": "<U02>",
        "→": "<U26>",
        "←": "<U27>",
        "Ä": "<U44>",
        "ä": "<U64>",
        "Ü": "<U5C>",
        "ü": "<U7C>",
        "Ö": "<U56>",
        "ö": "<U76>",
        "ß": "<U5F>",
    }

class LedDisplay:

    DEFAULT_RETRY = 3

    @staticmethod
    def _checkDeviceId(deviceId):
        if isinstance(deviceId, int) and (1 <= deviceId <= 8):
            return deviceId
        raise ValueError("{} is not a valid device ID.".format(deviceId))

    @staticmethod
    def _checkSchedule(schedule):
        if isinstance(schedule, str) and (len(schedule) == 1) and ("A" <= schedule <= "E"):
            return schedule
        raise ValueError("{} is not a valid schedule.".format(schedule))

    @staticmethod
    def _checkPage(page):
        if isinstance(page, str) and (len(page) == 1) and ("A" <= page <= "E"):
            return page
        raise ValueError("{} is not a valid page.".format(page))

    @staticmethod
    def _checkSchedulePages(schedulePages):
        if isinstance(schedulePages, str) and (len(schedulePages) <= 31):
            for page in schedulePages:
                LedDisplay._checkPage(page)
            return schedulePages
        raise ValueError("{} is not a valid page schedule.".format(schedulePages))

    @staticmethod
    def _checkLine(line):
        if isinstance(line, int) and (1 <= line <= 8):
            return line
        raise ValueError("{} is not a valid line.".format(line))

    @staticmethod
    def _checkBrightness(brightness):
        if isinstance(brightness, str) and (len(brightness) == 1) and ("A" <= brightness <= "D"):
            return brightness
        raise ValueError("{} is not a valid brightness.".format(brightness))

    @staticmethod
    def _checkGraphicsPage(graphicsPage):
        if isinstance(graphicsPage, str) and (len(graphicsPage) == 1) and ("A" <= graphicsPage <= "P"):
            return graphicsPage
        raise ValueError("{} is not a valid graphicsPage.".format(graphicsPage))

    @staticmethod
    def _checkGraphicsBlock(graphicsBlock):
        if isinstance(graphicsBlock, int) and (1 <= graphicsBlock <= 8):
            return graphicsBlock
        raise ValueError("{} is not a valid graphics block.".format(graphicsBlock))

    @staticmethod
    def _checkGraphics(graphics):
        if isinstance(graphics, str) and re.match("^[RGBO]{224}$", graphics):
            return graphics
        raise ValueError("{} is not valid graphics data.".format(graphics))

    def __init__(self, device, device_id = 1, timeout = 1.0):

        self._logger = logging.getLogger("LedDisplay {!r}".format(device))

        self._device    = device
        self._device_id = self._checkDeviceId(device_id)
        self._timeout   = timeout

        self._logger.debug("Opening serial port ...")

        self._port = serial.Serial(self._device, 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, self._timeout, False, False)

    def __del__(self):

        if self._port is not None:
            self._logger.error("The __del__ method of class LedDisplay was called while the serial port was still open. Please use explicit close() method.")
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._port is not None:
            self.close()

    def close(self):

        assert self._port is not None

        self._logger.debug("Closing serial port ...")

        self._port.close()
        self._port = None

    def send(self, data_packet, max_retry = DEFAULT_RETRY):
        """Assemble standard packet and send command."""

        if isinstance(data_packet, str):
            for (a, b) in Replacements.items():
                data_packet = data_packet.replace(a, b)
            data_packet = data_packet.encode("ASCII")

        assert isinstance(data_packet, bytes)

        # checksum = functools.reduce(operator.__xor__, data_packet, 0)

        checksum = 0
        for c in data_packet:
            checksum ^= ord(c)

        command_prefix = "<ID{:02X}>".format(self._device_id).encode()
        command_suffix = "{:02X}<E>".format(checksum).encode()

        command = command_prefix + data_packet + command_suffix

        print "TX:[" + command + "]"
        expected_response = "ACK".encode("ASCII")

        # Try up to "max_retry" times...

        for i in range(max_retry):

            self._logger.info("Sending to device: {!r}".format(command))
            self._port.write(command)

            response = self._port.read(3)

            if response == expected_response:
                self._logger.debug("Received expected response: {!r}.".format(response))
                break # Success!

            response = response + self._port.read(1000) # Read garbage, if any (will timeout).

            self._logger.warning("Received unexpected response: {!r}".format(response))

        else:
            # If we get here, we didn't get an ACK after retries.
            raise CommunicationError("Command {!r} was not acknowledged by device.".format(command))

    def setDeviceId(self, new_device_id, max_retry = DEFAULT_RETRY):
        """Paragraph 4.1: ID setting.
           Note that we cannot use the standard send() routine here. The "set ID" command
           is special because it lacks an ID number and a checksum."""

        command = "<ID><{:02X}><E>".format(new_device_id).encode("ASCII")

        expected_response = "{:02X}".format(new_device_id).encode("ASCII")

        # Try up to "max_retry" times...

        for i in range(max_retry):

            self._logger.info("Sending to device: {!r}".format(command))
            self._port.write(command)

            response = self._port.read(2)

            if response == expected_response:
                self._logger.debug("Received expected response: {!r}.".format(response))
                break # Success!

            response = response + self._port.read(1000) # Read garbage, if any (will timeout).
            self._logger.warning("Received unexpected response: {!r}.".format(response))

        else:
            # If we get here, we didn't get an acknowledgement.
            raise CommunicationError("Command {!r} was not acknowledged by device.".format(command))

    def setRealtimeClock(self, timestamp = None):
        """ Paragraph 4.2.1: Real Time Clock Setting"""
        if timestamp is None:
            timestamp = datetime.datetime.now()
        else:
            assert isinstance(timestamp, datetime.datetime)

        command = "<SC>%02d%02d%02d%02d%02d%02d%02d" % (
            timestamp.year % 100,
            timestamp.isoweekday(),
            timestamp.month,
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second
        )

        self.send(command)

    def setPageContent(self, content):
        """
        Paragraph 4.2.2: Sending Page content
        Format: <Ln><Pn><FX><MX><WX><FY>...message...
        Ln Line
        Pn Page
        FX leading command
        MX display method while waiting
        WX wait
        FY lagging effect
        """

        assert False # TODO: implement and test

        # Leading command:
        #   A immediate             Message will be immediately displayed
        #   B Xopen                 Image will be shown from center and extend to 4 sides
        #   C Curtain Up            Image will be shown line by line, bottom to top
        #   D Curtain Down          Image will be shown line by line, top to bottom
        #   E Scroll Left           Image will be scrolled from Right to Left
        #   F Scroll Right          Image will be scrolled from Left to Right
        #   G Vopen
        #   H Hopen
        #   I Scroll Up
        #   J Scroll Down
        #   K Hold
        #   L Snow
        #   M Twinkle
        #   N Block Move
        #   P Random
        #   Q Pen writing 'Hello World'
        #   R Pen writing 'Welcome'
        #   S Pen writing 'Amplus'
        #
        # Lagging command:
        #   A immediate             Message will be immediately displayed
        #   B Xopen                 Image will be shown from center and extend to 4 sides
        #   C Curtain Up            Image will be shown line by line, bottom to top
        #   D Curtain Down          Image will be shown line by line, top to bottom
        #   E Scroll Left           Image will be scrolled from Right to Left
        #   F Scroll Right          Image will be scrolled from Left to Right
        #   G Vopen
        #   H Hopen
        #   I Scroll Up
        #   J Scroll Down
        #   K Hold
        #
        # 4.2.2.7 Message Directives:
        #
        # 4.2.2.7.1 Font color of following characters
        #
        #     <AA> font size 5x7 (Normal)
        #     <AB> font size 6x7 (Bold)
        #     <AC> font size 4x7 (Narrow)
        #     <AD> font size 7x13 (Top half)
        #     <AE> font size 7x13 (Bottom half)
        #     <AF> font size 6x8 (Top part)
        #     <AG> etc -- not interpreted as directives.
        #
        # 4.2.2.7.2 Bell
        #
        #     <BA>  0.5 seconds
        #     <BB>  1.0 seconds
        #      ..
        #     <BZ> 13.0 seconds
        #
        # 4.2.2.7.3 Color of the following characters
        #
        #     <CA> red    foreground, black  background (spec says: dim red)
        #     <CB> red    foreground, black  background
        #     <CC> red    foreground, black  background (spec says: bright red)
        #     <CD> green  foreground, black  background (spec says: dim green)
        #     <CE> green  foreground, black  background
        #     <CF> green  foreground, black  background (spec says: bright green)
        #     <CG> orange foreground, black  background (spec says: dim orange)
        #     <CH> orange foreground, black  background
        #     <CI> orange foreground, black  background (spec says: bright orange)
        #     <CJ> orange foreground, black  background (spec says: yellow)
        #     <CK> orange foreground, black  background (spec says: lime)
        #     <CL> black  foreground, red    background
        #     <CM> black  foreground, green  background
        #     <CN> black  foreground, orange background
        #     <CO> orange foreground. green  background
        #     <CP> red    foreground, green  background (spec says: dim green)
        #     <CQ> green  foreground, red    background (spec says: dim red)

        #     <CR> "rasta:" 2 lines red, three lines orange, 2 lines green
        #     <CS> "sparkly": active bits are randomly set to red/orange/green.

        #     <CT>, <CU>, <CV>, <CW>, <CX>, <CY>, <CZ>: red (out-of-spec)


    def setSchedule(self, schedule, pages, startTime = None, stopTime = None):
        """ Paragraph 4.2.3: Sending Schedule"""

        if startTime is None:
            startTime = datetime.datetime(2000, 1, 1, 0, 0, 0)
        else:
            assert isinstance(startTime, datetime.datetime)

        if stopTime is None:
            stopTime = datetime.datetime(2099, 12, 31, 23, 59, 59)
        else:
            assert isinstance(stopTime, datetime.datetime)

        command = "<T%s>%02d%02d%02d%02d%02d%02d%02d%02d%02d%02d%s" % (
            self._checkSchedule(schedule),
            startTime.year % 100,
            startTime.month,
            startTime.day,
            startTime.hour,
            startTime.minute,
            stopTime.year % 100,
            stopTime.month,
            stopTime.day,
            stopTime.hour,
            stopTime.minute,
            self._checkSchedulePages(pages)
        )
        self.send(command)

    def setGraphicsBlock(self, graphicsPage, graphicsBlock, graphics):
        """ Paragraph 4.2.4: Send Graphic Block"""

        # A single Graphics block is 7 rows x 32 columns worth of pixels.
        # Each pixel can take any of four values, so it takes two bits to specify a single pixel:
        #
        #   00 -> black
        #   01 -> green
        #   10 -> red
        #   11 -> orange
        #
        # E.g., to specify 4 horizontal pixels with colors RED, BLACK, ORANGE, RED translates to
        # binary 10001110, or a byte with value 0x8e.
        #
        # A graphics block is actually specified transmitted an 8 rows x 32 columns image of pixels;
        # the last row is not used. The 8x32 pixel image is encoded into 64 binary bytes,
        #
        # This is the order of the bytes used. Each byte specifies 4 adjacent pixels, which
        # corresponds to the example above.
        #
        #  0   1  16  17  32  33  48  49
        #  2   3  18  19  34  35  50  51
        #  4   5  20  21  36  37  52  53
        #  6   7  22  23  38  39  54  55
        #  8   9  24  25  40  41  56  57
        # 10  11  26  27  42  43  58  59
        # 12  13  28  29  44  45  60  61
        # 14  15  30  31  46  47  62  63 --> pixels of this row (row 8) are not used.
        #
        # We expect the graphics specified in a string of length 7x32 (== 224), consisting
        # of the letters "B", "G", "R", "O", for Black, Green, Red, and Orange, respectively.

        graphics = graphics.replace(".", "B")

        self._checkGraphics(graphics)

        gr = []
        for i in range(64):

            # Determine (px, py) as coordinates pointing into the 'graphics' array.

            px = (i % 2) + (i // 16) * 2
            # 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1
            # 2 3 2 3 2 3 2 3 2 3 2 3 2 3 2 3
            # 4 5 4 5 4 5 4 5 4 5 4 5 4 5 4 5
            # 6 7 6 7 6 7 6 7 6 7 6 7 6 7 6 7

            py = (i // 2) % 8
            # 0 0 1 1 2 2 3 3 4 4 5 5 6 6 7 7
            # 0 0 1 1 2 2 3 3 4 4 5 5 6 6 7 7
            # 0 0 1 1 2 2 3 3 4 4 5 5 6 6 7 7
            # 0 0 1 1 2 2 3 3 4 4 5 5 6 6 7 7

            if py == 7:
                pixels = "BBBB"
            else:
                pixels = graphics[py * 32 + 4 * px:py * 32 + 4 * px + 4]

            v = 0
            for p in pixels:
                v *= 4
                if p in "GO": v += 1
                if p in "RO": v += 2

            gr.append(v)

        print("v -->", gr)

        command_prefix = "<G{}{}>".format(self._checkGraphicsPage(graphicsPage), self._checkGraphicsBlock(graphicsBlock)).encode("ASCII")
        command = command_prefix + bytes(gr)

        self.send(command)

    def deletePage(self, line, page):
        """Paragraph 4.2.5.1: Delete page"""
        command = "<DL%sP%s>" % (self._checkLine(line), self._checkPage(page))
        self.send(command)

    def deleteSchedule(self, schedule):
        """Paragraph 4.2.5.2: Delete schedule"""
        command = "<DT%s>" % self._checkSchedule(schedule)
        self.send(command)

    def deleteAll(self):
        """Paragraph 4.2.5.3: Delete all"""
        command = "<D*>"
        self.send(command)

    def setDefaultRunPage(self, page):
        """Paragraph 4.2.6: Assign a default run page"""
        command = "<RP%s>" % self._checkPage(page)
        self.send(command)

    def setBrightnessLevel(self, brightness):
        """Paragraph 4.2.7: Assign Display Brightness level"""
        command = "<B%s>" % self._checkBrightness(brightness)
        self.send(command)

    def changeFactoryDefaultEuropeanCharacterTable(self, fontSelect, fontEntry, fontData):
        """Paragraph 4.2.8: Change factory default European char table"""
        # All character sets use all the 8 bits. The difference is in how many places the column pointer is progressed.
        #
        # The "A" (normal) alphabet increases the column index by 6. The glyph takes up the 5 leftmost bits, by convention.
        # The "B" (wide)   alphabet increases the column index by 7. The glyph takes up the 6 leftmost bits, by convention.
        # The "C" (tight)  alphabet increases the column index by 5. The glyph takes up the 4 leftmost bits, by convention.

        assert len(fontData) == 8
        command = "<F%s%02X>%s" % (fontSelect, fontEntry, fontData)
        self.send(command)

    def recallFactoryDefaultEuropeanCharacterTable(self):
        """Paragraph 4.2.9: Recall factory default European char table"""
        command = "<DU>"
        self.send(command)
