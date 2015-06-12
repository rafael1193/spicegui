# -*- coding: utf-8 -*-
#
# SpiceGUI
# Copyright (C) 2014-2015 Rafael Bailón-Ruiz <rafaelbailon@ieee.org>
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

from __future__ import print_function

import csv
import locale
import os.path
import re
import subprocess
import datetime

from gi.repository import Gio
from matplotlib.figure import Figure
from threading import Event, Lock, Thread

import config


class NgspiceOutput():
    """Ngspice output management.

    Attributes:
        name: Name.
        values: Data.
        SUPPORTED_ANALYSES: Supported analyses.
    """

    SUPPORTED_ANALYSES = ["Transient Analysis", "AC Analysis", "DC transfer characteristic"]

    class DataLine():
        """Set of values obtained from simulation.

        Represents a table column in a ngspice output.

        Attributes:
            name: Name.
            values: Data.
            independent: True if it is an independent data set.
        """

        def __init__(self, name, values):
            """Inits DataLine with name and values.

            Args:
                name: Column name.
                values: Column data.
            """
            self.name = name
            # Cairo limitation. See backend_cairo.py line 142 in matplotlib package.
            if len(values) > 18980:
                raise ValueError(_("There are too much data points in simulation."))
            else:
                self.values = values

            if name in ["Index", "time", "frequency", "v-sweep", "res-sweep", "temp-sweep", "i-sweep"]:
                self.independent = True
            else:
                self.independent = False

            parentheses_index = self.name.find("(")
            if parentheses_index > 0:
                self.magnitude = self.name[:parentheses_index]

        def get_magnitude_and_unit(self):
            """
            Guess magnitude and unit of DataLine from name.

            Returns:
                Magnitude, unit.

                If magnitude is unknown returns ``("","")``
            """
            if self.name == "Index":
                return "Index", ""
            elif self.name == "time":
                return "Time", "s"
            elif self.name == "frequency":
                return "Frequency", "Hz"
            elif self.name == "v-sweep":
                return "Voltage", "V"
            elif self.name == "res-sweep":
                return "Resistance", u"Ω"
            elif self.name == "temp-sweep":
                return "Temperature", u"℃"
            elif self.name == "i-sweep":
                return "Current", "A"
            elif self.name.endswith("#branch"):
                return "Current", "A"
            elif self.name.startswith("v"):
                if self.name.startswith("vdb("):
                    return "Voltage", u"dB"
                elif self.name.startswith("vr("):
                    return "Voltage", "V"
                elif self.name.startswith("vi("):
                    return "Voltage", "V"
                elif self.name.startswith("vm("):
                    return "Voltage", "V"
                elif self.name.startswith("vp("):
                    return "Phase", u"rad"
                else:
                    return "Voltage", "V"
            elif self.name.startswith("i"):
                return "Current", "A"
            elif self.name.startswith("@"):
                inst_parameter = self.name[self.name.find("[") + 1: -1]
                if inst_parameter.startswith("i"):
                    return "Current", "A"
                elif inst_parameter.startswith("p"):
                    return "Power", "W"
                elif inst_parameter.startswith("c"):
                    return "Capacitance", "F"
                elif inst_parameter == "gm":
                    return "Transconductance", u"A⁄V"
                else:
                    return "", ""
            else:
                return "", ""

        def extend(self, other_data_line):
            """Extends DataLine with contents of another one.

            Args:
                other_data_line: another DataLine.
            Raises:
                ValueError: If other_data_line has not the same name and magnitude.
            """
            if other_data_line.name == self.name and other_data_line.magnitude == self.magnitude:
                self.values.extend(other_data_line.values)
            else:
                raise ValueError("Data lines have not the same name nor magnitude.")

    def __init__(self, raw_text):
        """Inits NgspiceOutput with ngspice output text.

        Args:
            raw_text: Ngspice output text.
        """
        self.circuit_name = None
        self._parse(raw_text)

    @classmethod
    def parse_file(cls, ngspice_result_file):
        """Inits NgspiceOutput with ngspice output file path.

        Args:
            ngspice_result_file: Ngspice output file path.
        """
        with open(ngspice_result_file) as f:
            return cls(f.read())

    @staticmethod
    def _parse_ngspice_output_date(raw_date):
        """Parses a date in the form 'Mon Jun  8 23:05:46  2015'.

        Returns:
            date: datetime.datetime object.
        """
        months = {'Jan': 1,
                  'Feb': 2,
                  'Mar': 3,
                  'Apr': 4,
                  'May': 5,
                  'Jun': 6,
                  'Jul': 7,
                  'Aug': 8,
                  'Sep': 9,
                  'Oct': 10,
                  'Nov': 11,
                  'Dec': 12}

        # if day is less than 10, separation is two spaces. Removing this ambiguity
        raw_date = raw_date.replace('  ', ' ')
        # separate (weekday month, day hour:minute:second, year)
        wday, month, day, hms, year = raw_date.split(' ')
        hour, minute, second = hms.split(':')

        return datetime.datetime(int(year), int(months[month]), int(day), int(hour), int(minute), int(second))

    def _parse(self, raw_text):
        """Ngspice simulation output parser.

         1. Find "Circuit: 'circuit name'
         2. Keep iterating until an space--striped line is 'circuit name'
         3. Enter table parser
          3.1. it is already implemented on stable version
         4. If not EOF, goto 2.

        Remarks:
         - Initial transient solutions are not parsed
         - Works for *tran*, *ac* (no complex values) and *dc*
         - "No. of Data Rows" value is not used
         - GUI can only handle one analysis, but parser could be extended
           to support more

         Raises:
             ValueError:
             ExecutionError:
        """

        def table_parser(table_start_pos):
            """
            Parses a ngspice output table handling page breaks.

            Returns:
                (analysis, date, data_lines, table_end_pos)
            """

            table_content = file_content[table_start_pos:]

            # table_content[0] is circuit name

            # table_content[1] is analysis and date
            # extract data from it
            analysis_line = table_content[1].strip()
            analysis_sep_index = analysis_line.find("  ")
            analysis = analysis_line[:analysis_sep_index]
            date = NgspiceOutput._parse_ngspice_output_date(analysis_line[analysis_sep_index + 2:].strip())

            # table_content[2] is a line of dashes

            # table_content[3] contains column headers
            columns_headers_line = table_content[3]
            headers = tuple(filter(None, columns_headers_line.strip().split(" ")))

            # table_content[4] is a line of dashes

            # from table_content[5] onwards, there is data
            table_sep = '\f'
            table_data = table_content[5:]
            l = 0
            tuple_values = []

            while l < xrange(len(table_data)):
                row = table_data[l]
                if row != table_sep and row != '':
                    splitted = row.strip().split("\t")
                    if splitted:
                        if splitted[0].isdigit():  # It's an Index row item
                            tuple_values.append(tuple(filter(None, splitted)))
                        else:
                            raise ValueError("PARSING ERROR: Line has not digits")
                else:
                    if table_data[l + 2].startswith('-----'):
                        # new page header detected
                        l += 2  # skip it
                    else:
                        # table ended
                        break
                l += 1

            # Simulation data is given as tuples and it need to be converted to lists
            list_values = self._transpose_table(tuple_values)
            data_lines = []

            # Finally, DataLine objects are created from list data
            for i in range(len(headers)):
                if headers[i] != "Index":  # "Index" data-line is discarded because it's not useful
                    data_lines.append(NgspiceOutput.DataLine(headers[i], list_values[i]))

            return analysis, date, data_lines, l

        file_content = raw_text.split("\n")
        tables = []  # List of (analysis, date, data_lines)

        joined_tables = []

        self.circuit_name = None
        for i in range(len(file_content)):
            stripped = file_content[i].strip()

            if stripped.startswith("Circuit: "):
                circuit_name = stripped[len("Circuit: "):]
                self.circuit_name = circuit_name

            elif stripped.startswith("Error"):
                raise ExecutionError(stripped)

            elif self.circuit_name is not None:
                if stripped.startswith(self.circuit_name):
                    # table found!
                    tables.append(table_parser(i))
                    break  # TODO remove this when multiple table support is implemented

        if self.circuit_name is None:
            raise ValueError("circuit_name is None")

        if not tables:
            raise ExecutionError(_("No simulations were done."))
        else:
            self.analysis = tables[0][0]  # analysis
            self.date = tables[0][1]  # date
            joined_tables = tables[0][2]  # Include first table
            for table in tables[1:]:  # Include dependent data lines of other tables
                # Process one type of simulation only.
                if table[0] == self.analysis:
                    # Discard independent data lines because they were just included.
                    filtered = [d for d in table[2] if not d.independent]
                    if filtered is not None:
                        joined_tables.extend(filtered)
            self.data_lines = joined_tables  # datalines

    def _transpose_table(self, table):
        """Returns a list of columns in table formed by rows"""
        transposed = []
        for item in table[0]:
            transposed.append([])

        for row in table:
            for i in range(len(row)):
                transposed[i].append(row[i])
        return transposed

    def get_figure(self):
        """Creates a Figure representing simulation data output.

        Returned object is suitable to be drawn on a gtk3 canvas.

        Returns:
            A ``matplotlib.figure.Figure`` object.
        """
        settings = Gio.Settings.new(config.GSETTINGS_BASE_KEY)

        f = Figure(figsize=(16, 7), dpi=100)
        a = f.add_subplot(111)
        indep_data_line = None
        dep_data_lines = []

        for data_line in self.data_lines:
            if data_line.independent is True:
                indep_data_line = data_line
            else:
                dep_data_lines.append(data_line)
        for line in dep_data_lines:
            a.plot(indep_data_line.values, line.values, label=line.name)

        # Decorations
        if settings.get_boolean("show-legend"):
            legend_position = settings.get_string("legend-position")
            a.legend(loc=legend_position)
        a.set_title(self.analysis)

        # Set x axis
        x_axe_magnitude, x_axe_unit = indep_data_line.get_magnitude_and_unit()
        if x_axe_magnitude and x_axe_unit:
            a.set_xlabel(unicode(x_axe_magnitude) + " [" + unicode(x_axe_unit) + "]")
            if x_axe_unit == "Hz":
                a.set_xscale("log")

        # Set y axis
        y_axe_magnitude, y_axe_unit = dep_data_lines[0].get_magnitude_and_unit()
        if y_axe_magnitude and y_axe_unit:
            a.set_ylabel(unicode(y_axe_magnitude) + " [" + unicode(y_axe_unit) + "]")
            if self.analysis == "AC Analysis" and y_axe_unit == "V":
                a.set_yscale("log")

        # Set grids
        if settings.get_boolean("show-grids"):
            a.grid(b=True, which='major', color='0.65', linestyle='-')
            a.grid(b=True, which='minor', color='0.9', linestyle='-')

        f.subplots_adjust(left=0.11, bottom=0.150, right=0.9, top=0.90, wspace=0.2, hspace=0.2)
        a.autoscale(enable=None, axis=u'y', tight=False)

        return f

    def save_csv(self, file_path):
        """Saves simulation data to csv file.

        Args:
            file_path: Output file path.
        """
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            # column headers
            row = []
            for line in self.data_lines:
                row.append(line.name)
            writer.writerow(row)

            # content
            if self.data_lines is not None:
                for row_i in xrange(len(self.data_lines[0].values)):  # assume all data lines have the same length
                    row = []
                    for line in self.data_lines:
                        row.append(line.values[row_i])
                    writer.writerow(row)


class Ngspice():
    @classmethod
    def simulatefile(cls, netlist_path):
        """Launches ngspice simulation o netlist file.

        Args:
            netlist_path: Netlist file path.
        """
        process = subprocess.Popen(["ngspice", "-b", "-o", str(netlist_path) + ".out", str(netlist_path)], shell=False,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        encoding = locale.getdefaultlocale()[1]
        stdout_b, stderr_b = process.communicate()
        stdout, stderr = stdout_b.decode(encoding), stderr_b.decode(encoding)

        if stderr:
            stderr_l = stderr.split("\n")
            error_lines = ""
            for line in stderr_l:
                if line.startswith("Error:"):
                    if len(error_lines) > 0:
                        error_lines += "\n"
                    error_lines += line
            if error_lines != "":
                raise Exception(error_lines)


class NgspiceAsync():
    def __init__(self):
        """Inits NgspiceAsync."""
        self.thread = None
        self.result = None
        self.errors = None
        self.end_event = Event()
        self._lock_result = Lock()
        self._lock_errors = Lock()

    def simulatefile(self, netlist_path):
        """
        Simulate asyncrhonously netlist_path file with ngspice.

        Args:
            netlist_path: Netlist file path.

        Returns:
            None.

            Sets self.result with (``stout``, ``stderr``).
            Sets self.errors with a list of ``ExecutionError`` if ``stderr`` is not void.
        """
        self.result = None
        self.errors = None
        self.end_event.clear()
        self.thread = Thread(group=None, name="ngspice-thread",
                             target=self._run_simulation, args=(netlist_path,))
        self.thread.start()

    def _run_simulation(self, netlist_path):
        self.process = subprocess.Popen(["ngspice", "-b", "-o",
                                         str(netlist_path) + ".out",
                                         str(netlist_path)],
                                        shell=False,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

        encoding = locale.getdefaultlocale()[1]
        stdout_b, stderr_b = self.process.communicate()
        stdout, stderr = stdout_b.decode(encoding), stderr_b.decode(encoding)
        with self._lock_result:
            self.result = (stdout, stderr)
        if stderr:
            if "Error:" in stderr:
                errors = [ExecutionError(err) for err in stderr.splitlines() if err]
                with self._lock_errors:
                    self.errors = errors
        self.end_event.set()

    def terminate(self):
        """Kills executing ngspice process.

        Calls ``terminate()`` method of ``subprocess.Popen``.
        """
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()


class ExecutionError(Exception):
    """Execution of process failed."""
    pass


class Gnetlist():
    @classmethod
    def create_netlist_file(cls, schematic_path, netlist_path):
        """Creates a spice netlist file from a gschem file with spice-sdb backend.

        Args:
            schematic_path: Gschem file path.
            netlist_path: Netlist file path.

        Raises:
            ExecutionError: When gnetlist process writes on stderr.
        """
        process = subprocess.Popen(["gnetlist", "-g", "spice-sdb", "-o", str(netlist_path), "--", str(schematic_path)],
                                   shell=False, cwd=os.path.dirname(netlist_path), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        encoding = locale.getdefaultlocale()[1]
        stdout_b, stderr_b = process.communicate()
        stdout, stderr = stdout_b.decode(encoding), stderr_b.decode(encoding)
        if stderr:
            stderr_l = stderr.split("\n")
            error_lines = ""
            for line in stderr_l:
                if line.startswith("ERROR:"):
                    if len(error_lines) > 0:
                        error_lines += "\n"
                    error_lines += line
            if error_lines != "":
                raise ExecutionError(error_lines)


class Netlist(object):
    def __init__(self, source):
        self.source = source

    def get_title(self):
        match = re.search("^\.title (?P<title>.*)$", self.source, flags=re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group("title").strip()
        else:
            title = str(self.source[0:self.source.find("\n")])
            if len(title) > 0:
                if title.startswith("*"):
                    return title[1:].strip()
                else:
                    return title.strip()
