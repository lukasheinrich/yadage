import jsonpointer
from .wflowstate import make_deserializer
from .steering_object import YadageSteering
from .utils import setupbackend_fromstring

def connect(metadir, accept_metadir, ctrlstring, ctrlopts, modelsetup, modelopts, backendstring):
    ys = YadageSteering.connect(
        accept_metadir = accept_metadir,
        metadir = metadir,
        ctrlstring = ctrlstring,
        ctrlopts = ctrlopts,
        modelsetup = modelsetup,
        modelopts = modelopts
    )
    if backendstring:
        ys.controller.backend = setupbackend_fromstring(backendstring)
    return ys

def preview_rule(wflow, name = None, identifier=None):
    stateopts = {}
    wflowmaker = make_deserializer(stateopts)
    newflow = wflowmaker(wflow.json())

    if identifier:
        rule = newflow.view().getRule(identifier=identifier)
    else:
        offset, name = name.split('/')
        rule = newflow.view(offset).getRule(name)

    if not rule.applicable(newflow):
        return

    rule.apply(newflow)
    newflow.rules.remove(rule)
    newflow.applied_rules.append(rule)

    existing_rules = [x.identifier for x in (wflow.rules + wflow.applied_rules)]
    existing_nodes = wflow.dag.nodes()

    new_rules = [{'name': x.rule.name, 'offset': x.offset} for x in newflow.rules if x.identifier not in existing_rules]
    new_nodes = [{'name': newflow.dag.getNode(n).name, 'parents': newflow.dag.predecessors(n)} for n in newflow.dag.nodes() if n not in existing_nodes]
    return new_rules, new_nodes
