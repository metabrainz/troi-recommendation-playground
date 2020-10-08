import os
import unittest
from unittest.mock import patch

from datasethoster.main import register_query, convert_http_args_to_json, error_check_arguments

class TestMain(unittest.TestCase):

    def test_convert_http_args_to_json(self):

        inputs = ['in_0', '[in_1]']
        req_args = {
            'in_0': 'value0',
            '[in_1]': 'value1,value2'
        }
        args, error = convert_http_args_to_json(inputs, req_args)
        self.assertEqual(error, "")
        self.assertEqual(len(args), 2)
        self.assertEqual(args[0]['in_0'], 'value0')
        self.assertEqual(args[0]['[in_1]'], 'value1')
        self.assertEqual(args[1]['in_0'], 'value0')
        self.assertEqual(args[1]['[in_1]'], 'value2')

        req_args = {
            '[in_1]': 'value1,value2'
        }
        args, error = convert_http_args_to_json(inputs, req_args)
        self.assertEqual(error, "Missing parameter 'in_0'.")
    
        req_args = {
            '[in_6]': 'value1,value2'
        }
        args, error = convert_http_args_to_json(inputs, req_args)
        self.assertEqual(error, "Missing parameter 'in_0'.")

        inputs = ['in_0', '[in_1]', '[in_2]']
        req_args = {
            'in_0': 'value0',
            '[in_1]': 'value1,value2',
            '[in_2]': 'value1'
        }
        args, error = convert_http_args_to_json(inputs, req_args)
        self.assertEqual(error, "Lists passed as parameters must all be the same length.")

    def test_error_check_arguments(self):
        inputs = ['in_0', '[in_1]']
        req_args = [ {
               'in_0': 'value0',
               '[in_1]': ['value1','value3']
            }, {
               'in_0': 'value2',
               '[in_1]': ['value5','value7']
            }
        ]
        error = error_check_arguments(inputs, req_args)
        self.assertEqual(error, "")
        
        req_args = [ {
               'in_0': 'value0',
               '[in_1]': ['value1','value3']
            }, {
               'in_0': 'value2',
               'in_1': ['value5','value7']
            }
        ]
        error = error_check_arguments(inputs, req_args)
        self.assertEqual(error, "Required parameter '[in_1]' missing in row 1.")

        req_args = [ {
               'in_0': 'value0',
               '[in_1]': ['value1','value3']
            }, {
               'in_0': '',
               'in_1': ['value5','value7']
            }
        ]
        error = error_check_arguments(inputs, req_args)
        self.assertEqual(error, "Required parameter 'in_0' cannot be blank in row 1.")
