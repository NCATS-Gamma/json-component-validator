#!/usr/bin/env python
"""Provide API for validating Translator Interchange API messages."""

import re
import copy
import argparse
from urllib.request import urlopen
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import jsonschema
from flask import Flask, request, abort, Response
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from
from flask_cors import CORS


def swag_validate_schema(component_name):
    """Produce schema for validation endpoint for component 'schema'."""
    return {
        'tag': 'validation',
        'description': 'Just checking.',
        'requestBody': {
            'description': 'Input object',
            'required': True,
            'content': {
                'application/json': {
                    'schema': {
                        '$ref': f'#/components/schemas/{component_name}'
                    }
                }
            }
        },
        'responses': {
            '200': {
                'description': 'Success',
                'content': {
                    'text/plain': {
                        'schema': {
                            'type': 'string'
                        }
                    }
                }
            },
            '400': {
                'description': 'Failure',
                'content': {
                    'text/plain': {
                        'schema': {
                            'type': 'string'
                        }
                    }
                }
            }
        }
    }

if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='JSON Component Validation API')
    parser.add_argument('file')
    parser.add_argument('--port', action="store", dest="port", default=7071, type=int)
    args = parser.parse_args()

    # set up Flask
    app = Flask(__name__)
    api = Api(app)
    CORS(app)

    # Try loading as url, fall back to loading as local file
    try:
        to_load = urlopen(args.file).read().decode()
    except ValueError as e:
        with open(args.file, 'r') as file_obj:
            to_load = file_obj.read()

    # load spec from yaml string
    spec = yaml.load(to_load, Loader=Loader)

    # get OpenAPI version
    if (spec.get('swagger', None) or spec.get('openapi')).startswith('2'):
        version = 2
    elif spec.get('openapi').startswith('3'):
        version = 3
    else:
        raise ValueError('Unrecognized OpenAPI version.')

    # get components/definitions
    if version == 2:
        to_load = re.sub(r'(?<=\$ref: [\'\"]#/)definitions(?=/)', 'components/schemas', to_load)
        components = yaml.load(to_load)['definitions']
    else:
        components = spec['components']['schemas']

    # build validator API spec, minus endpoints
    template = {
        'openapi': '3.0',
        'info': {
            'description': f"Validation of components/definitions for '{spec['info']['title']}'",
            'title': 'JSON Component Validator',
            'contact': {
                'email': 'patrick@covar.com'
            }
        },
        'components': {
            'schemas': components
        }
    }

    # configure Flasgger
    app.config['SWAGGER'] = {
        'title': "JSON Component Validator",
        'uiversion': 3
    }
    swagger = Swagger(app, template=template)

    # add an endpoint validating each component
    components = template['components']['schemas']
    for component_name in components:
        # build json schema against which we validate
        other_components = copy.deepcopy(components)
        json_schema = other_components.pop(component_name)
        json_schema['components'] = {'schemas': other_components}

        # build endpoint
        class Validate(Resource):
            """Validation endpoint."""

            def __init__(self, schema):
                """Initialize validation endpoint."""
                self.schema = schema

            @swag_from(swag_validate_schema(component_name))
            def post(self):
                """Validate input component."""
                try:
                    jsonschema.validate(request.json, self.schema)
                except jsonschema.exceptions.ValidationError as error:
                    return Response(str(error), 400)
                return "Successfully validated", 200
            post.__doc__ = f"Validate '{component_name}' against the spec."

        # add endpoint to API
        endpoint = f"/validate_{component_name.replace(' ', '_').lower()}"
        endpoint_type = type(f"Validate_{component_name.replace(' ', '_')}", (Validate,), {})
        api.add_resource(endpoint_type, endpoint, resource_class_args=(json_schema,))

    # start server
    app.run(
        host='0.0.0.0',
        port=args.port,
        debug=False,
        use_reloader=True
    )
