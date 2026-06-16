acmt001 Documentation
=====================

**acmt001** is a Python library for generating ISO 20022 acmt Account
Management XML messages (account opening, maintenance, closing, and
identification). It supports all 21 acmt message types
(acmt.001.001.08 through acmt.024.001.04).

Quick Start
-----------

.. code-block:: python

   from acmt001 import generate_xml_string

   data = [{
       "msg_id": "MSG-001",
       "creation_date_time": "2026-01-15T10:30:00",
       "process_id": "PROC-001",
       "account_id": "GB29NWBK60161331926819",
       "account_currency": "EUR",
       "account_name": "Acme Corp Operating Account",
       "account_type_cd": "CACC",
       "account_servicer_bic": "DEUTDEFF",
       "account_owner_name": "Acme Corp",
       "account_owner_country": "DE",
       "org_full_legal_name": "Acme Corporation GmbH",
       "org_id_lei": "529900T8BM49AURSDO55",
   }]

   xml = generate_xml_string(
       data,
       "acmt.007.001.05",
       "acmt001/templates/acmt.007.001.05/template.xml",
       "acmt001/templates/acmt.007.001.05/acmt.007.001.05.xsd",
   )
   print(xml)

Design History File
-------------------

.. toctree::
   :maxdepth: 2
   :caption: Design History File (DHF)

   dhf/index

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
