# -*- coding: utf-8 -*-
from aiida.parsers.parser import Parser
from aiida.orm.calculation.job.nwchem.basic import BasicCalculation
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import calc_states

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class BasicParser(Parser):
    """
    Parser for the output of nwchem.
    """
    def __init__(self,calc):
        """
        Initialize the instance of BasicParser
        """
        # check for valid input
        self._check_calc_compatibility(calc)
        super(BasicParser, self).__init__(calc)

    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,BasicCalculation):
            raise ParsingError("Input calc must be a BasicCalculation")

    def parse_with_retrieved(self,retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """       
        from aiida.common.exceptions import InvalidOperation
        import os

        output_path = None
        error_path  = None
        try:
            output_path, error_path = self._fetch_output_files(retrieved)
        except InvalidOperation:
            raise
        except IOError as e:
            self.logger.error(e.message)
            return False, ()

        if output_path is None and error_path is None:
            self.logger.error("No output files found")
            return False, ()

        return True, self._get_output_nodes(output_path, error_path)

    def _fetch_output_files(self, retrieved):
        """
        Checks the output folder for standard output and standard error
        files, returns their absolute paths on success.
        
        :param retrieved: A dictionary of retrieved nodes, as obtained from the
          parser.
        """
        from aiida.common.exceptions import InvalidOperation
        import os

        # check in order not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )

        # Check that the retrieved folder is there 
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            raise IOError("No retrieved folder found")        

        list_of_files = out_folder.get_folder_list()

        output_path = None
        error_path  = None

        if self._calc._DEFAULT_OUTPUT_FILE in list_of_files:
            output_path = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_OUTPUT_FILE )
        if self._calc._DEFAULT_ERROR_FILE in list_of_files:
            error_path  = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_ERROR_FILE )

        return output_path, error_path

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from aiida.orm.data.array.trajectory import TrajectoryData
        import re

        state = None
        step = None
        scale = None
        with open(output_path) as f:
            lines = [x.strip('\n') for x in f.readlines()]

        result_dict = dict()
        trajectory = None
        for line in lines:
            if state is None and re.match('^\s*NWChem SCF Module\s*$',line):
                state = 'nwchem-scf-module'
                continue
            if state is None and re.match('^\s*NWChem Geometry Optimization\s*$',line):
                state = 'nwchem-geometry-optimisation'
                trajectory = TrajectoryData()
                continue
            if state == 'nwchem-scf-module' and re.match('^\s*Final RHF \s*results\s*$',line):
                state = 'final-rhf-results'
                continue
            if re.match('^\s*\-*\s*$',line):
                continue
            if state == 'final-rhf-results':
                result = re.match('^\s*([^=]+?)\s*=\s*([\-\d\.]+)$',line)
                if result:
                    key = re.sub('[^a-zA-Z0-9]+', '_', result.group(1).lower())
                    result_dict[key] = result.group(2)
                else:
                    state = 'nwchem-scf-module'
            if state == 'nwchem-geometry-optimisation' and re.match('^\s*Step\s+\d+\s*$',line):
                result = re.match('^\s*Step\s+(\d+)\s*$',line)
                step = result.group(1)
                continue
            if state == 'nwchem-geometry-optimisation' and
                re.match('^\s*Output coordinates in a.u.',line):
                state = 'nwchem-geometry-optimisation-coordinates'
                result = re.match('scale by \s(*[\-\d\.]+)',line)
                scale = result.group(1)
                continue
        return [('parameters', ParameterData(dict=result_dict))]
