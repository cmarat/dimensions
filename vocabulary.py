"""
Generate Pint config from QUDT

Requires a SPARQL endpoint with following data:
    OSG_vaem-(v1.2).ttl
    OSG_dimension-(v1.1).ttl
    OSG_dtype-(v1.0).ttl
    OSG_quantity-(v1.1).ttl
    OSG_qudt-(v1.01).ttl
    OSG_voag-(v1.0).ttl
    OVG_dimensionalunits-qudt-(v1.1).ttl
    OVG_dimensions-qudt-(v1.1).ttl
    OVG_quantities-qudt-(v1.1).ttl
    OVG_units-qudt-(v1.1).ttl
"""
import codecs
import SPARQLWrapper

sparql = SPARQLWrapper.SPARQLWrapper('http://localhost:5820/QUDT/query')
sparql.setReturnFormat('json')
sparql.addParameter('reasoning', 'true')

name = lambda uri: uri.split('#', 1)[1]
prefix_formatter = lambda binding: u"{}- = {} = {}-".format(
    name(binding['prefix']['value']),
    binding['multiplier']['value'],
    binding['symbol']['value'])
ref_unit_formatter = lambda binding: u"{} = [{}] = {}".format(
    name(binding['unit']['value']),
    name(binding['quantity']['value']),
    binding['symbol']['value'])
rel_unit_formatter = lambda binding: u"{} = {} = {}".format(
    name(binding['unit']['value']),
    binding['dimension']['value'],
    binding['symbol']['value'])
prefix_query = '''
    PREFIX unit: <http://qudt.org/vocab/unit#>
    PREFIX qudt: <http://qudt.org/schema/qudt#>
    SELECT ?prefix ?multiplier ?symbol {
      unit:SystemOfUnits_SI qudt:systemPrefixUnit ?prefix .
      ?prefix qudt:symbol ?symbol; qudt:conversionMultiplier ?multiplier .
    }
    '''
ref_unit_query = '''
    PREFIX qudt: <http://qudt.org/schema/qudt#>
    SELECT distinct ?unit ?symbol ?quantity {
      ?unit a qudt:SIBaseUnit; qudt:symbol ?symbol; qudt:quantityKind ?quantity
    }
    '''
rel_unit_query = '''
    PREFIX qudt: <http://qudt.org/schema/qudt#>
    SELECT ?unit ?symbol (GROUP_CONCAT(?dim; separator=" * ") AS ?dimension) {{
      SELECT distinct ?unit ?symbol ?dim {
        ?unit a qudt:Unit; qudt:symbol ?symbol; qudt:quantityKind ?quantity .
        ?dimension qudt:referenceQuantity ?quantity;
            qudt:dimensionVector ?vector .
        ?vector qudt:basisElement ?basisQuantity;
            qudt:vectorMagnitude ?vectorMagnitude .
        ?basisUnit a qudt:BaseUnit; qudt:quantityKind ?basisQuantity .
        [] qudt:systemDimension ?dimension .
        FILTER(?vectorMagnitude != 0)
        MINUS {[] qudt:systemBaseUnit ?unit}
        MINUS {?unit a qudt:PrefixUnit}
        BIND (CONCAT(
            STRAFTER(STR(?basisUnit), "http://qudt.org/vocab/unit#"),
            "**", STR(?vectorMagnitude)) AS ?dim)
    }}}
    GROUP BY ?unit ?symbol
    ORDER BY ?unit
    '''


def pint_config(query, formatter):
    sparql.setQuery(query)
    bindings = sparql.queryAndConvert()['results']['bindings']
    return u'\n'.join((formatter(b) for b in bindings)) + '\n'

prefixes = pint_config(prefix_query, prefix_formatter)
ref_units = pint_config(ref_unit_query, ref_unit_formatter)
rel_units = pint_config(rel_unit_query, rel_unit_formatter)

with codecs.open('vocabulary.txt', 'w', encoding='utf-8') as fout:
    fout.write(u"# Prefixes\n{}\n".format(prefixes))
    fout.write(u"# Reference units\n{}\n".format(ref_units))
    fout.write(u"# Derived units:n{}\n".format(rel_units))
