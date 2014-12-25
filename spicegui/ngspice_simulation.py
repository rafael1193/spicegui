# -*- coding: utf-8 -*-
#
# SpiceGUI
# Copyright (C) 2014 Rafael Bailón-Ruiz <rafaelbailon@ieee.org>
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

from gi.repository import Gio
from matplotlib.figure import Figure
from threading import Event, Lock, Thread

import preferences_gui


class NgspiceOutput():

    SUPPORTED_ANALYSES = ["Transient Analysis", "AC Analysis", "DC transfer characteristic"]

    class DataLine():

        def __init__(self, name, values):
            self.name = name
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
            Guess magnitude and unit of DataLine from name
            """
            
            if self.name == "Index":
                return ("Index","")
            elif self.name == "time":
                return ("Time", "s")
            elif self.name == "frequency":
                return ("Frequency", "Hz")
            elif self.name == "v-sweep":
                return ("Voltage", "V")
            elif self.name == "res-sweep":
                return ("Resistance", u"Ω")
            elif self.name == "temp-sweep":
                return ("Temperature", u"℃")
            elif self.name == "i-sweep":
                return ("Current", "A")
            elif self.name.endswith("#branch"):
                return ("Current", "A")
            elif self.name.startswith("v"):
                if self.name.startswith("vdb("):
                    return ("Voltage", u"dB")
                elif self.name.startswith("vr("):
                    return ("Voltage", "V")
                elif self.name.startswith("vi("):
                    return ("Voltage", "V")
                elif self.name.startswith("vm("):
                    return ("Voltage", "V")
                elif self.name.startswith("vp("):
                    return ("Phase", u"rad")
                else:
                    return ("Voltage","V")
            elif self.name.startswith("i"):
                return ("Current","A")
            elif self.name.startswith("@"):
                inst_parameter = self.name[self.name.find("[") + 1: -1]
                if inst_parameter.startswith("i"):
                    return ("Current","A")
                elif inst_parameter.startswith("p"):
                    return ("Power","W")
                elif inst_parameter.startswith("c"):
                    return ("Capacitance","F")
                elif inst_parameter == "gm":
                    return ("Transconductance",u"A⁄V")
                else:
                    return ("","")
            else:
                return ("","")
            

    def __init__(self, raw_text):
        self.circuit_name = None
        self._parse(raw_text)

    @classmethod
    def parse_file(cls, ngspice_result_file):
        with open(ngspice_result_file) as f:
            return cls(f.read())

    def _parse(self, raw_text):
        """
        ngspice simulation output parser.

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
        """

        def table_parser(table_start_pos):
            """
            Parses a ngspice output table

            Returns (analysis, date, data_lines, table_end_pos)
            """
            table_content = file_content[table_start_pos:]

            # table_content[0] is circuit name

            analysis_line = table_content[1].strip()
            analysis_sep_index = analysis_line.find("  ")
            analysis = analysis_line[:analysis_sep_index]
            date = analysis_line[analysis_sep_index + 2:]

            # table_content[2] is a line of dashes

            headers = tuple(filter(None, table_content[3].strip().split(" ")))

            # table_content[4] is a line of dashes

            tuple_values = []
            for row in table_content[5:]:
                if row != "":
                    tuple_values.append(tuple(filter(None, row.strip().split("\t"))))
                else:
                    break

            # Simulation data is given as tuples and need to be converted to lists
            list_values = self._transpose_table(tuple_values)
            data_lines = []

            #Finally, DataLine objects are created from list data
            for i in range(len(headers)):
                if headers != "Index":  # "Index" data-line is discarded because is not useful
                    data_lines.append(NgspiceOutput.DataLine(headers[i], list_values[i]))

            return analysis, date, data_lines

        file_content = raw_text.split("\n")
        n_simulations = 0

        self.circuit_name = None
        for i in range(len(file_content)):
            stripped = file_content[i].strip()

            if stripped.startswith("Circuit: "):
                circuit_name = stripped[len("Circuit: "):]
                self.circuit_name = circuit_name

            elif stripped.startswith("Error"):
                raise Exception(stripped)

            elif self.circuit_name is not None:
                if stripped.startswith(self.circuit_name):
                    # table found!
                    analysis, date, data_lines = table_parser(i)
                    print(analysis, date, data_lines)
                    n_simulations += 1

        if self.circuit_name is None:
            raise Exception("circuit_name is None")

        if n_simulations <= 0:
            raise Exception("No simulations were done")

        self.analysis = analysis
        self.data_lines = data_lines
        self.date = date

    def _transpose_table(self, table):
        """
        Returns list of columns in table formed by rows
        """
        transposed = []
        for item in table[0]:
            transposed.append([])

        for row in table:
            for i in range(len(row)):
                transposed[i].append(row[i])
        return transposed

    def get_figure(self):
        """
        returns a Figure representing simulation data output, suitable
        to be drawn on a gtk3 canvas.
        """

        settings = Gio.Settings.new(preferences_gui.Preferences.GSETTINGS_BASE_KEY)

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
            legend_position=settings.get_string("legend-position")
            a.legend(loc=legend_position)
        a.set_title(self.analysis)

        # Set x axis
        x_axe_magnitude, x_axe_unit = indep_data_line.get_magnitude_and_unit()
        if x_axe_magnitude and x_axe_unit:
            a.set_xlabel(str(x_axe_magnitude) + " [" + str(x_axe_unit)+"]")
            if x_axe_unit == "Hz":
                a.set_xscale("log")

        # Set y axis
        y_axe_magnitude, y_axe_unit = dep_data_lines[0].get_magnitude_and_unit()
        if y_axe_magnitude and y_axe_unit:
            a.set_ylabel(str(y_axe_magnitude) + " [" + str(y_axe_unit)+"]")
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
        """
        Saves simulation data to csv file
        """
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            #column headers
            row = []
            for line in self.data_lines:
                row.append(line.name)
            writer.writerow(row)

            #content
            if self.data_lines is not None:
                for row_i in xrange(len(self.data_lines[0].values)):  # assume all data lines have the same length
                    row = []
                    for line in self.data_lines:
                        row.append(line.values[row_i])
                    writer.writerow(row)


class Ngspice():

    @classmethod
    def simulatefile(cls, netlist_path):
        process = subprocess.Popen(["ngspice", "-b", "-o", str(netlist_path) + ".out", str(netlist_path)], shell=False,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        encoding = locale.getdefaultlocale()[1]
        stdout_b, stderr_b = process.communicate()
        stdout, stderr = stdout_b.decode(encoding), stderr_b.decode(encoding)
        print(stdout, stderr)
        if stderr:
            stderr_l = stderr.split("\n")
            error_lines=""
            for line in stderr_l:
                if line.startswith("Error:"):
                    if len(error_lines) > 0:
                        error_lines += "\n"
                    error_lines += line
            if error_lines != "":
                print(error_lines)
                raise Exception(error_lines)


class Ngspice_async():

    def __init__(self):
        self.thread = None
        self.result = None
        self.errors = None
        self.end_event = Event()
        self._lock_result = Lock()
        self._lock_errors = Lock()
           
    def simulatefile(self, netlist_path):
        """
        simulate asyncrhonously netlist_path file with ngspice
        
        set self.result with (stout, stderr)
        """
        self.result = None
        self.error = None
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
            stderr_l = stderr.split("\n")
            error_lines=""
            for line in stderr_l:
                if line.startswith("Error:"):
                    if len(error_lines) > 0:
                        error_lines += "\n"
                    error_lines += line
            if error_lines != "":
                with self._lock_errors:
                    self.errors = Exception(error_lines)
        self.end_event.set()
    
    def terminate(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()


class Gnetlist():

    @classmethod
    def create_netlist_file(cls, schematic_path, netlist_path):
        """
        Calls gnetlist with spice-sdb backend and converts a gschem file
        to netlist.

        raises ValueError when gnetlist process writes on stderr
        """
        process = subprocess.Popen(["gnetlist", "-g", "spice-sdb", "-o", str(netlist_path), "--", str(schematic_path)], shell=False, cwd=os.path.dirname(netlist_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        encoding = locale.getdefaultlocale()[1]
        stdout_b, stderr_b = process.communicate()
        stdout, stderr = stdout_b.decode(encoding), stderr_b.decode(encoding)
        print(stdout, stderr)
        if stderr:
            stderr_l = stderr.split("\n")
            error_lines=""
            for line in stderr_l:
                if line.startswith("ERROR:"):
                    if len(error_lines) > 0:
                        error_lines += "\n"
                    error_lines += line
            if error_lines != "":
                print(error_lines)
                raise Exception(error_lines)
            print("Error: " + stderr)


###############################################################################
###############################################################################
###############################################################################


class Component(object):

    def __init__(self, **kwargs):
        """
        __init__(self,component_type, id ,nodes)

        ================ ======================================================
        *component_type* str of component type. ie. R for resistor, V
                         for independent voltaje source...
        ---------------- ------------------------------------------------------
        *id*             str that identifies a component within a type
        ---------------- ------------------------------------------------------
        *terminals*      component terminals as tuple
        ---------------- ------------------------------------------------------

        ================ ======================================================
        """
        self.device = kwargs["device"]
        self.name = kwargs["name"]
        self.terminals = kwargs["terminals"]
        self.parameters = kwargs["parameters"]

    def __str__(self):
        result = self.device + " " + self.name
        for term in self.terminals:
            result += " " + term

        for param in self.parameters:
            result += " " + param

        return result


class Circuit(object):

    def __init__(self, netlist):
        """ Netlist as str """

        self._netlist = netlist.split("\n")
        self._parser = NetlistParser()
        self._components, self._nodes = self.parser.parse(self._netlist)
        self._options = ["nopage"]

    def get_netlist(self):
        return self._netlist

    def get_components(self):
        return self._components

    def get_nodes(self):
        return self._nodes

    def __str__(self):
        if self.simulation:
            pass

    def transient_simulation(self, start, end, steps=50, devices=None, nodes=None, uic=False):
        tran_stm = TransientSimulation(start, end, steps, uic)
        #print_stm =

        end_index = _find_statement(netlist, ".ends")

    def _find_statement(self, l, statement):
        """
        returns first occurrence index of 'statment' on list 'l'
        if 'statment' is not found, returns None
        """
        for i in range(len(l)):
            if l[i] == statement:
                return i
        return None

    def _simulate_file(self, netlistfile):
        subprocess.call(["ngspice", "-b", "-c " + str(netlistfile), "-o " + str(netlistfile) + ".out"])

    def _parse_ngspice_result(self, ngspice_result_file):
        result = {}
        with open(ngspice_result_file) as f:
            file_content = f.read().split("\n")
            table_start_pos = None
            data_row_number = None
            for i in range(len(file_content)):
                if file_content[i].strip().starts_with("No. of Data Rows:"):
                    table_start_pos = i + 1
                    data_row_number = int(file_content[i].strip()[len("No. of Data Rows:"):])  # keep number of rows
                    break
            data_content = file_content[table_start_pos:]
            result["description"] = data_content[0].strip()
            result["analysis type"] = data_content[1].strip()
            #result["data"] =
            ### consulta "cat caca.out | less" para seguir interpretando el archivo


class ControlStatement(object):

    def __init__(self, statement, **kwargs):
        pass


class TransientSimulation(ControlStatement):

    def __init__(self, start, end, steps=50, uic=False):
        ControlStatement.__init__(self, "tran", {"start":start, "end":end, "steps":steps, "uic":uic})
        self.start = start
        self.end = end
        self.steps = steps
        #TODO: Use initial conditions

    def __str__(self):
        """tran tstep tstop <tstart <tmax>> <uic>"""

        directive = ".tran"

        if self.start:
            if self.start >= 0:
                tstart = str(self.start)
            else:
                tstart = str(0)
        else:
            tstart = str(0)

        if self.end:
            if self.end > self.start:
                tstop = str(self.end)
            else:
                raise ValueError("stop time must be greater than start time")
        else:
            raise ValueError("stop time must be set")

        if self.steps > 0:
            tstep = str((self.end - self.start) / float(self.steps))
        else:
            tstep = str(50)

        return directive + " " + tstep + " " + tstop + " " + tstart


class PrintSimulation(ControlStatement):

    def __init__(self, nodes, components):
        ControlStatement.__init__(self, "print", {"start":start, "end":end, "steps":steps, "uic":uic})
        self.start = start
        self.end = end
        self.steps = steps
        #TODO: Use initial conditions

    def __str__(self):
        """
        tran tstep tstop <tstart <tmax>> <uic>
        """

        directive = ".tran"

        if self.start:
            if self.start >= 0:
                tstart = str(self.start)
            else:
                tstart = str(0)
        else:
            tstart = str(0)

        if self.end:
            if self.end > self.start:
                tstop = str(self.end)
            else:
                raise ValueError("stop time must be greater than start time")
        else:
            raise ValueError("stop time must be set")

        if self.steps > 0:
            tstep = str((self.end - self.start) / float(self.steps))
        else:
            tstep = str(50)

        return directive + " " + tstep + " " + tstop + " " + tstart


class Netlist(object):

    def __init__(self, source):
        self.source = source
#        self.regex = {}
#        self.regex["comment"] = re.compile("^\*.")
#        self.regex["device"] = re.compile("^(?P<device>[a-zA-Z])(?<name>.*?)\s") #R, L, C

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

    def parse(self, netlist):
        devices = []
        nodes = set()
        devices = self._tokenize(netlist)
        return devices, nodes

    def _get_number_of_terminals(self, device):
        component_pin_number = {
            'A':None,  # TODO: check pin numbervalue
            'B':2,
            'C':2,
            'D':2,
            'E':4,  # TODO: check non linear version
            'F':2,
            'G':4,
            'H':2,
            'I':2,
            'J':3,
            'K':0,
            'L':2,
            'M':4,
            'N':None,
            'O':4,
            'P':None,
            'Q':3,  # TODO: Detect substrate pin!
            'R':2,
            'S':4,
            'T':4,
            'U':3,
            'V':2,
            'W':2,
            'X':None,  # TODO: parameters - 1
            'Y':4,
            'Z':3}
        if component_pin_number[device] is not None:
            return component_pin_number[device]
        else:
            raise NotImplementedError("component type '"+str(device)+"' handling is not implemented")

    def _tokenize(self, raw_netlist):

        # Now, it is only needed information about device names and terminals, not other parameters or directives
        tokens = []
        nodes = set()

        for line in raw_netlist.split("\n"):
            tok = {}
            line = line.strip()  # remove begining and leading spaces
            if re.match(self.regex["comment"], line):  # Discard comments
                continue
            splitted = line.split()
            m = re.match(self.regex["device"], line)
            if m:  # is a device
                tok = m.groupdict()
                tok = {}
                tokens.append(tok)
                # basic device terminal handling
                if self._get_number_of_terminals(tok["device"]) == 2:
                    tok["terminals"] = (splitted[1 + 0], splitted[1 + 1])
                if self._get_number_of_terminals(tok["device"]) == 3:
                    tok["terminals"] = (splitted[1 + 0], splitted[1 + 1], splitted[1 + 2])
                for pin in tok["terminals"]:
                    nodes.add(pin)

        return tokens, nodes
