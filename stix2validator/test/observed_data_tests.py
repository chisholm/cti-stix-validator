import unittest
import copy
import json
from . import ValidatorTest
from .. import validate_string

VALID_OBSERVED_DATA_DEFINITION = """
{
  "type": "observed-data",
  "id": "observed-data--b67d30ff-02ac-498a-92f9-32f845f448cf",
  "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
  "created": "2016-04-06T19:58:16Z",
  "modified": "2016-04-06T19:58:16Z",
  "first_observed": "2015-12-21T19:00:00Z",
  "last_observed": "2015-12-21T19:00:00Z",
  "number_observed": 50,
  "objects": {
    "0": {
      "type": "file",
      "name": "foo.zip",
      "hashes": {
        "MD5": "B365B9A80A06906FC9B400C06C33FF43"
      },
      "mime_type": "application/zip",
      "extensions": {
        "archive-ext": {
          "contains_refs": [
            "1"
          ],
          "version": "5.0"
        }
      }
    },
    "1": {
      "type": "file",
      "hashes": {
        "MD5": "A2FD2B3F4D5A1BD5E7D283299E01DCE9"
      },
      "name": "qwerty.dll"
    }
  },
  "granular_markings": [
    {
      "marking_ref": "marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da",
      "selectors": [ "objects.0.type" ]
    }
  ]
}
"""


class ObservedDataTestCases(ValidatorTest):
    valid_observed_data = json.loads(VALID_OBSERVED_DATA_DEFINITION)

    def test_wellformed_observed_data(self):
        results = validate_string(VALID_OBSERVED_DATA_DEFINITION, self.options)
        self.assertTrue(results.is_valid)

    def test_number_observed(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['number_observed'] = -1
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

    def test_selector_invalid_property(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['granular_markings'][0]['selectors'][0] = "foobar"
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

    def test_selector_invalid_index(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['granular_markings'][0]['selectors'] = [
            "objects.0.extensions.archive-ext.contains_refs.[5]"
        ]
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

    def test_selector_invalid_list(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['granular_markings'][0]['selectors'] = [
          "objects.[0].extensions"
        ]
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

    def test_selector_invalid_property2(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['granular_markings'][0]['selectors'] = [
          "objects.[0].extensions.archive-ext.contains_refs.[0].type"
        ]
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

    def test_selectors_multiple(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['granular_markings'][0]['selectors'] = [
          "objects.0.extensions.archive-ext.contains_refs.[5]",
          "objects.0.addons",
          "objects.9"
        ]
        observed_data = json.dumps(observed_data)
        results = validate_string(observed_data, self.options)
        self.assertTrue(len(results.errors) == 3)
        self.assertFalse(results.is_valid)

    def test_dict_key_uppercase(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['x_s_dicts'] = {
            'FOOBAR': {
                "foo": "bar"
            }
        }
        observed_data = json.dumps(observed_data)
        results = validate_string(observed_data, self.options)
        self.assertTrue(len(results.errors) == 1)
        self.assertFalse(results.is_valid)

        self.check_ignore(observed_data, 'observable-dictionary-keys')

    def test_dict_key_length(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['x_s_dicts'] = {
            'foofoobarfoofoobarbarfoofoobarbarbar': {
                "foo": "bar"
            }
        }
        observed_data = json.dumps(observed_data)
        results = validate_string(observed_data, self.options)
        self.assertTrue(len(results.errors) == 1)
        self.assertFalse(results.is_valid)

        self.check_ignore(observed_data, 'observable-dictionary-keys')

    def test_vocab_account_type(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "user-account",
            "user_id": "1001",
            "account_login": "bwayne",
            "account_type": "superhero"
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'account-type')

    def test_vocab_windows_pebinary_type(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['windows-pebinary-ext'] = {
            "pe_type": "elf"
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'windows-pebinary-type')

    def test_vocab_encryption_algo(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['encryption_algorithm'] = "MDK"
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'encryption-algo')

    def test_vocab_file_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['hashes'] = {
            "something": "foobar"
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'hash-algo')

    def test_vocab_artifact_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "artifact",
            "hashes": {
                "foo": "B4D33B0C7306351B9ED96578465C5579"
            }
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'hash-algo')

    def test_vocab_certificate_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "x509-certificate",
            "hashes": {
                "foo": "B4D33B0C7306351B9ED96578465C5579"
            }
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'hash-algo')

    def test_vocab_pebinary_sections_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['windows-pebinary-ext'] = {
            "sections": [
                {
                    "name": "CODE",
                    "entropy": 0.061089,
                    "hashes": {
                        "foo": "1C19FC56AEF2048C1CD3A5E67B099350"
                    }
                }
            ]
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'hash-algo')

    def test_vocab_pebinary_optional_header_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['windows-pebinary-ext'] = {
            "optional_header": {
                "hashes": {
                    "foo": "1C19FC56AEF2048C1CD3A5E67B099350"
                }
            }
        }
        self.assertFalseWithOptions(json.dumps(observed_data))

        self.check_ignore(json.dumps(observed_data), 'hash-algo')

        observed_data['objects']['0']['extensions']['windows-pebinary-ext']['optional_header']['hashes'] = {
            "x_foo": "1C19FC56AEF2048C1CD3A5E67B099350"
        }
        self.assertTrueWithOptions(json.dumps(observed_data))

    def test_vocab_pebinary_file_header_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['windows-pebinary-ext'] = {
            "file_header_hashes": {
                "foo": "1C19FC56AEF2048C1CD3A5E67B099350"
            }
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'hash-algo')

    def test_vocab_pebinary_multiple_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['windows-pebinary-ext'] = {
            "file_header_hashes": {
                "foo": "1C19FC56AEF2048C1CD3A5E67B099350"
            },
            "optional_header": {
                "hashes": {
                    "foo": "1C19FC56AEF2048C1CD3A5E67B099350"
                }
            }
        }
        observed_data = json.dumps(observed_data)
        results = validate_string(observed_data, self.options)
        self.assertTrue(len(results.errors) == 2)
        self.assertFalse(results.is_valid)

        self.check_ignore(observed_data, 'hash-algo')

    def test_vocab_ntfs_alternate_data_streams_hashes(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['ntfs-ext'] = {
            "alternate_data_streams": [
                  {
                      "name": "second.stream",
                      "size": 25536,
                      "hashes": {
                          "foo": "B4D33B0C7306351B9ED96578465C5579"
                      }
                  }
              ]
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'hash-algo')

    def test_observable_object_keys(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['abc'] = {
            "type": "x509-certificate",
            "hashes": {
                "MD5": "B4D33B0C7306351B9ED96578465C5579"
            }
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'observable-object-keys')

    def test_observable_object_types(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['type'] = "foo"
        self.assertFalseWithOptions(json.dumps(observed_data))

        self.check_ignore(json.dumps(observed_data),
            'custom-observable-object-prefix,custom-observable-object-prefix-lax')

        observed_data['objects']['0']['type'] = "x-c-foo"
        self.assertTrueWithOptions(json.dumps(observed_data))
        self.assertFalseWithOptions(json.dumps(observed_data), strict_types=True)

    def test_observable_object_extensions(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['foobar'] = {
            "foo": "bar"
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data,
            'custom-object-extension-prefix,custom-object-extension-prefix-lax')

    def test_observable_object_custom_properties(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['foo'] = "bar"
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data,
            'custom-observable-properties-prefix,custom-observable-properties-prefix-lax')

    def test_observable_object_extension_custom_properties(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['archive-ext']['foo'] = "bar"
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data,
            'custom-observable-properties-prefix,custom-observable-properties-prefix-lax')

    def test_observable_object_embedded_custom_properties(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "x509-certificate",
            "x509_v3_extensions": {
              "foo": "bar"
            }
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data,
            'custom-observable-properties-prefix,custom-observable-properties-prefix-lax')

    def test_observable_object_embedded_dict_custom_properties(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "windows-registry-key",
            "key": "hkey_local_machine\\system\\bar\\foo",
            "values": [
                {
                    "name": "Foo",
                    "data": "qwerty",
                    "data_type": "REG_SZ",
                    "foo": "buzz"
                }
            ]
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data,
            'custom-observable-properties-prefix,custom-observable-properties-prefix-lax')

    def test_observable_object_extension_embedded_custom_properties(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['ntfs-ext'] = {
            "alternate_data_streams": [
                  {
                      "name": "second.stream",
                      "size": 25536,
                      "foo": "bar"
                  }
              ]
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data,
            'custom-observable-properties-prefix,custom-observable-properties-prefix-lax')

    def test_observable_object_property_reference(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
          "type": "directory",
          "path": "C:\\Windows\\System32",
          "contains_refs": ['0']
        }
        self.assertTrueWithOptions(json.dumps(observed_data))

        observed_data['objects']['2']['contains_refs'] = ['999']
        self.assertFalseWithOptions(json.dumps(observed_data))

        observed_data['objects']['3'] = {
          "type": "ipv4-addr",
          "value": "203.0.113.1"
        }
        observed_data['objects']['2']['contains_refs'] = ['3']
        self.assertFalseWithOptions(json.dumps(observed_data))

    def test_observable_object_embedded_property_reference(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['extensions']['archive-ext']['contains_refs'][0] = '999'
        self.assertFalseWithOptions(json.dumps(observed_data))

        observed_data['objects']['2'] = {
          "type": "directory",
          "path": "C:\\Windows\\System32",
          "contains_refs": ['0']
        }
        observed_data['objects']['0']['extensions']['archive-ext']['contains_refs'][0] = '2'
        self.assertFalseWithOptions(json.dumps(observed_data))

    def test_vocab_windows_process_priority(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "process",
            "pid": 314,
            "name": "foobar.exe",
            "extensions": {
                "windows-process-ext": {
                    "aslr_enabled": True,
                    "dep_enabled": True,
                    "priority": "HIGH_PRIORITY",
                    "owner_sid": "S-1-5-21-186985262-1144665072-74031268-1309"
                }
            }
        }
        self.assertFalseWithOptions(json.dumps(observed_data))

        observed_data['objects']['2']['extensions']['windows-process-ext']['priority'] = 'HIGH_PRIORITY_CLASS'
        self.assertTrueWithOptions(json.dumps(observed_data))

        self.check_ignore(json.dumps(observed_data), 'windows-process-priority-format')

    def test_file_mime_type(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['mime_type'] = "bla"
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

        self.check_ignore(observed_data, 'mime-type')

    def test_artifact_mime_type(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "artifact",
            "hashes": {
                "foo": "B4D33B0C7306351B9ED96578465C5579"
            },
            "mime_type": "bla/blabla"
        }
        observed_data = json.dumps(observed_data)
        self.assertFalseWithOptions(observed_data)

    def test_network_traffic_ports(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "network-traffic",
            "protocols": [
                "ipv4",
                "tcp"
            ]
        }
        self.assertFalseWithOptions(json.dumps(observed_data))

        observed_data['objects']['2']['src_port'] = 3372
        self.assertFalseWithOptions(json.dumps(observed_data))

        self.check_ignore(json.dumps(observed_data), 'network-traffic-ports')

        observed_data['objects']['2']['dst_port'] = 80
        self.assertTrueWithOptions(json.dumps(observed_data))

    def test_file_character_set(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['0']['name_enc'] = "blablabla"
        self.assertFalseWithOptions(json.dumps(observed_data))

        observed_data['objects']['0']['name_enc'] = "ISO-8859-2"
        self.assertTrueWithOptions(json.dumps(observed_data))

    def test_directory_character_set(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
          "type": "directory",
          "path": "C:\\Windows\\System32",
          "path_enc": "blablabla"
        }
        self.assertFalseWithOptions(json.dumps(observed_data))

        observed_data['objects']['2']['path_enc'] = "US-ASCII"
        self.assertTrueWithOptions(json.dumps(observed_data))

    def test_network_traffic_protocols(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "network-traffic",
            "src_port": 24678,
            "dst_port": 80,
            "protocols": [
                "ipv4",
                "tcp",
                "foobar"
            ]
        }
        self.assertFalseWithOptions(json.dumps(observed_data))
        self.check_ignore(json.dumps(observed_data), 'protocols')

        observed_data['objects']['2']['protocols'][2] = 'https'
        self.assertTrueWithOptions(json.dumps(observed_data))

    def test_network_traffic_ipfix(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "network-traffic",
            "src_port": 24678,
            "dst_port": 80,
            "ipfix": {
                "minimumIpTotalLength": 32,
                "maximumIpTotalLength": 2556,
                "foo": "bar"
            }
        }
        self.assertFalseWithOptions(json.dumps(observed_data))
        self.check_ignore(json.dumps(observed_data), 'ipfix')

    def test_network_traffic_http_request_header(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "network-traffic",
            "src_port": 24678,
            "dst_port": 80,
            "extensions": {
                "http-request-ext": {
                    "request_method": "get",
                    "request_value": "/download.html",
                    "request_version": "http/1.1",
                    "request_header": {
                        "Accept-Encoding": "gzip,deflate",
                        "Host": "www.example.com",
                        "x-foobar": "something"
                    }
                }
            }
        }
        self.assertFalseWithOptions(json.dumps(observed_data))
        self.check_ignore(json.dumps(observed_data), 'http-request-headers')

    def test_network_traffic_socket_options(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "network-traffic",
            "src_port": 24678,
            "dst_port": 80,
            "extensions": {
                "socket-ext": {
                  "address_family": "AF_INET",
                  "socket_type": "SOCK_STREAM",
                  "options": {
                    "foo": "bar"
                  }
                }
            }
        }
        self.assertFalseWithOptions(json.dumps(observed_data))

    def test_pdf_doc_info(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "file",
            "name": "foo.pdf",
            "extensions": {
                "pdf-ext": {
                    "version": "1.7",
                    "document_info_dict": {
                        "Title": "Sample document",
                        "foo": "bar"
                    }
                }
            }
        }
        self.assertFalseWithOptions(json.dumps(observed_data))
        self.check_ignore(json.dumps(observed_data), 'pdf-doc-info')

    def test_software_language(self):
        observed_data = copy.deepcopy(self.valid_observed_data)
        observed_data['objects']['2'] = {
            "type": "software",
            "name": "word",
            "language": "bbb"
        }
        self.assertFalseWithOptions(json.dumps(observed_data))

        observed_data['objects']['2']['language'] = 'eng'
        self.assertTrueWithOptions(json.dumps(observed_data))


if __name__ == "__main__":
    unittest.main()
