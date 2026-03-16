# Senotype Editor
## add_terms Python script

The **add_terms.py** script updates the _senotypejson_ fields
in the _senotype_ table of the SenLib database.

In the initial release of the SenoType Editor, elements in **objects** arrays of the 
JSONs in the _senotypejson_ field were strictly encoded, with only _code_ and _source_ keys:

```azure
"assertions": [
    {
      "objects": [
        {
          "code": "NCBI:9606",
          "source": "valueset"
        }
      ],
      "predicate": {
        "IRI": "http://purl.obolibrary.org/obo/RO_0002162",
        "term": "in_taxon"
      }
    }
```

When displaying a senotype, the Senotype Editor obtained terms for each object code by 
executing REST API calls. 

Fetching code terms in real time proved to require too much time. The Senotype Editor now 
stores terms with codes:

```azure
"assertions": [
    {
      "objects": [
        {
          "code": "NCBI:9606",
          "term": "human",
          "source": "valueset"
        }
      ],
      "predicate": {
        "IRI": "http://purl.obolibrary.org/obo/RO_0002162",
        "term": "in_taxon"
      }
    },
```

The **add_terms.py** script retroactively updates senotype data added by the first release of the Senotype Editor.

# To run
Execute **add_terms.py** with up to two command-line arguments:
* **-g**, _required_ : a Globus group token for the user in the SenNet Consortium
* **-i**, _optional_: a specific senotype ID. By default, the application updates all senotypes.

