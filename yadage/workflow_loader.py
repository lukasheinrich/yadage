import pkg_resources
import json
import os
import jsonschema
import jsonref
import requests
import yaml
import urllib2
from jsonschema import Draft4Validator, validators
import logging

log = logging.getLogger(__name__)

def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.iteritems():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
            validator, properties, instance, schema,
        ):
            yield error

    return validators.extend(
        validator_class, {"properties" : set_defaults},
    )

DefaultValidatingDraft4Validator = extend_with_default(Draft4Validator)

def loader(toplevel):
    base_uri = None
    if toplevel == 'from-github':
        base_uri = 'https://raw.githubusercontent.com/lukasheinrich/yadage-workflows/master/'
    else:
        base_uri = 'file://' + os.path.abspath(toplevel) + '/'
    
    def yamlloader(uri):
        try:
            log.info('trying to get uri {}'.format(uri))
            data = requests.get(uri).content
            log.info('got data\n{}'.format(data))
            return yaml.load(data)
        except:
            try:
                data = urllib2.urlopen(uri).read()
                return yaml.load(data)
            except:
                log.exception('loading error: cannot find URI {}'.format(uri))
                raise RuntimeError
    def load(uri):
        full_uri = '{}/{}'.format(base_uri,uri)
        log.info('trying to load uri: {}'.format(full_uri))
        return jsonref.load_uri(full_uri, base_uri = base_uri, loader = yamlloader)
    return load

def workflow_loader(workflowyml,toplevel):
    log.info('loading from toplevel: {}'.format(toplevel))
    refloader = loader(toplevel)
    workflow = refloader(workflowyml)
    return workflow

def validator(schema_name,schemadir):
    relpath     = '{}/{}.json'.format(schemadir,schema_name)
    abspath = os.path.abspath(relpath)
    absbase = os.path.dirname(abspath)
    schema_base_uri = 'file://' + absbase + '/'
    schema   = json.load(open(relpath))
    resolver = jsonschema.RefResolver(schema_base_uri, schema)
    return DefaultValidatingDraft4Validator(schema, resolver = resolver)

def validate_workflow(workflowyml, toplevel, schemadir):
    workflow = workflow_loader(workflowyml,toplevel)
    try:
        validator('workflow-schema',schemadir).validate(workflow)
    except jsonschema.RefResolutionError as e:
        raise RuntimeError('could not resolve reference {}'.format(e))
    return True, workflow
    
def workflow(name,toplevel):
    schemas  = pkg_resources.resource_filename('yadage','schema/spec')
    ok, workflow =  validate_workflow(name,toplevel,schemas)
    if ok:
        return workflow
    else:
        raise RuntimeError('Schema is not validating')