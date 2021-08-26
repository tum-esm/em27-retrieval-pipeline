
from cerberus import Validator as cerberus_validator


class Validator:

    __float_list = {'type': 'list', 'required': True, 'schema': {'type': 'float'}}
    __string_list = {'type': 'list', 'required': True, 'schema': {'type': 'string'}}
    __string = {'type': 'string', 'required': True}
    __optional_string = {'type': 'string'}
    __gas_dict = {
        'type': 'dict',
        'require_all': True,
        'schema': {
            'TUM_I': __float_list,
            'GRA': __float_list,
            'FEL': __float_list,
            'OBE': __float_list,
            'TAU': __float_list,
        }
    }
    __day_json_validator = cerberus_validator({
        'date': __string,
        'timestamps': __float_list,
        'co2': __gas_dict,
        'ch4': __gas_dict
    })

    __meta_json_validator = cerberus_validator({
        'tag': __string,
        'days': __string_list,
        'stations': __string_list,
        'gases': __string_list,
        'units': __string_list,
        'display_day': __optional_string
    })

    @staticmethod
    def __validate(validator, document):
        valid = validator.validate(document)
        if not valid:
            raise Exception(
                f'Errors: {validator.errors}'
            )

    @staticmethod
    def day(document):
        """
        Validate the format of a given day document
        """
        Validator.__validate(
            Validator.__day_json_validator, document
        )

    @staticmethod
    def meta(document):
        """
        Validate the format of a given meta document
        """
        Validator.__validate(
            Validator.__meta_json_validator, document
        )
