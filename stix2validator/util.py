import argparse
from argparse import RawDescriptionHelpFormatter
from collections import Iterable
import datetime
import errno
import os
import sys
import textwrap

from appdirs import AppDirs
import requests_cache

from .output import error, set_level, set_silent

DEFAULT_VER = "2.1"

CODES_TABLE = """
The following is a table of all the recommended "best practice" checks which
the validator performs, along with the code to use with the --enable or
--disable options. By default, the validator checks all of them.

+------+-----------------------------+----------------------------------------+
| Code | Name                        | Ensures...                             |
+------+-----------------------------+----------------------------------------+
|  1   | format-checks               | all 1xx checks are run                 |
| 101  | custom-prefix               | names of custom object types,          |
|      |                             | properties, observable objects,        |
|      |                             | observable object properties, and      |
|      |                             | observable object extensions follow    |
|      |                             | the correct format                     |
| 102  | custom-prefix-lax           | same as 101 but more lenient; no       |
|      |                             | source identifier needed in prefix     |
| 111  | open-vocab-format           | values of open vocabularies follow the |
|      |                             | correct format                         |
| 121  | kill-chain-names            | kill-chain-phase name and phase follow |
|      |                             | the correct format                     |
| 141  | observable-object-keys      | observable object keys follow the      |
|      |                             | correct format                         |
| 142  | observable-dictionary-keys  | dictionaries in cyber observable       |
|      |                             | objects follow the correct format      |
| 149  | windows-process-priority-   | windows-process-ext's 'priority'       |
|      |     format                  | follows the correct format             |
| 150  | hash-length                 | keys in 'hashes'-type properties are   |
|      |                             | not too long                           |
|      |                             |                                        |
|  2   | approved-values             | all 2xx checks are run                 |
| 201  | marking-definition-type     | marking definitions use a valid        |
|      |                             | definition_type                        |
| 202  | relationship-types          | relationships are among those defined  |
|      |                             | in the specification                   |
| 203  | duplicate-ids               | objects in a bundle with duplicate IDs |
|      |                             | have different `modified` timestamps   |
| 210  | all-vocabs                  | all of the following open vocabulary   |
|      |                             | checks are run                         |
| 211  | attack-motivation           | certain property values are from the   |
|      |                             | attack_motivation vocabulary           |
| 212  | attack-resource-level       | certain property values are from the   |
|      |                             | attack_resource_level vocabulary       |
| 213  | identity-class              | certain property values are from the   |
|      |                             | identity_class vocabulary              |
| 214  | indicator-label             | certain property values are from the   |
|      |                             | indicator_label vocabulary             |
| 215  | industry-sector             | certain property values are from the   |
|      |                             | industry_sector vocabulary             |
| 216  | malware-label               | certain property values are from the   |
|      |                             | malware_label vocabulary               |
| 218  | report-label                | certain property values are from the   |
|      |                             | report_label vocabulary                |
| 219  | threat-actor-label          | certain property values are from the   |
|      |                             | threat_actor_label vocabulary          |
| 220  | threat-actor-role           | certain property values are from the   |
|      |                             | threat_actor_role vocabulary           |
| 221  | threat-actor-sophistication | certain property values are from the   |
|      |                             | threat_actor_sophistication vocabulary |
| 222  | tool-label                  | certain property values are from the   |
|      |                             | tool_label vocabulary                  |
| 241  | hash-algo                   | certain property values are from the   |
|      |                             | hash-algo vocabulary                   |
| 242  | encryption-algo             | certain property values are from the   |
|      |                             | encryption-algo vocabulary             |
| 243  | windows-pebinary-type       | certain property values are from the   |
|      |                             | windows-pebinary-type vocabulary       |
| 244  | account-type                | certain property values are from the   |
|      |                             | account-type vocabulary                |
| 270  | all-external-sources        | all of the following external source   |
|      |                             | checks are run                         |
| 271  | mime-type                   | file.mime_type is a valid IANA MIME    |
|      |                             | type                                   |
| 272  | protocols                   | certain property values are valid IANA |
|      |                             | Service and Protocol names             |
| 273  | ipfix                       | certain property values are valid IANA |
|      |                             | IP Flow Information Export (IPFIX)     |
|      |                             | Entities                               |
| 274  | http-request-headers        | certain property values are valid HTTP |
|      |                             | request header names                   |
| 275  | socket-options              | certain property values are valid      |
|      |                             | socket options                         |
| 276  | pdf-doc-info                | certain property values are valid PDF  |
|      |                             | Document Information Dictionary keys   |
| 301  | network-traffic-ports       | network-traffic objects contain both   |
|      |                             | src_port and dst_port                  |
| 302  | extref-hashes               | external references SHOULD have hashes |
|      |                             | if they have a url                     |
+------+-----------------------------+----------------------------------------+
"""


class NewlinesHelpFormatter(RawDescriptionHelpFormatter):
    """Custom help formatter to insert newlines between argument help texts.
    """
    def _split_lines(self, text, width):
        text = self._whitespace_matcher.sub(' ', text).strip()
        txt = textwrap.wrap(text, width)
        txt[-1] += '\n'
        return txt


def parse_args(cmd_args, is_script=False):
    """Parses a list of command line arguments into a ValidationOptions object.

    Args:
        cmd_args (list of str): The list of command line arguments to be parsed.
        is_script: Whether the arguments are intended for use in a stand-alone
            script or imported into another tool.

    Returns:
        Instance of ``ValidationOptions``

    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=NewlinesHelpFormatter,
        epilog=CODES_TABLE
    )

    # Input options
    if is_script:
        parser.add_argument(
            "files",
            metavar="FILES",
            nargs="*",
            default=sys.stdin,
            help="A whitespace separated list of STIX files or directories of "
                 "STIX files to validate. If none given, stdin will be used."
        )
    parser.add_argument(
        "-r",
        "--recursive",
        dest="recursive",
        action="store_true",
        default=True,
        help="Recursively descend into input directories."
    )
    parser.add_argument(
        "-s",
        "--schemas",
        dest="schema_dir",
        help="Custom schema directory. If provided, input will be validated "
             "against these schemas in addition to the STIX schemas bundled "
             "with this script."
    )
    parser.add_argument(
        "--version",
        dest="version",
        help="The version of the STIX specification to validate against."
    )

    # Output options
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="Print informational notes and more verbose error messages."
    )

    parser.add_argument(
        "-q",
        "--silent",
        dest="silent",
        action="store_true",
        default=False,
        help="Silence all output to stdout."
    )

    parser.add_argument(
        "-d",
        "--disable",
        "--ignore",
        dest="disabled",
        default="",
        help="A comma-separated list of recommended best practice checks to "
             "skip. By default, no checks are disabled. \n\n"
             "Example: --disable 202,210"
    )

    parser.add_argument(
        "-e",
        "--enable",
        "--select",
        dest="enabled",
        default="",
        help="A comma-separated list of recommended best practice checks to "
             "enable. If the --disable option is not used, no other checks "
             "will be run. By default, all checks are enabled.\n\n"
             "Example: --enable 218"
    )

    parser.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        default=False,
        help="Treat warnings as errors and fail validation if any are found."
    )

    parser.add_argument(
        "--strict-types",
        dest="strict_types",
        action="store_true",
        default=False,
        help="Ensure that no custom object types are used, only those defined"
             " in the STIX specification."
    )

    parser.add_argument(
        "--strict-properties",
        dest="strict_properties",
        action="store_true",
        default=False,
        help="Ensure that no custom properties are used, only those defined"
             " in the STIX specification."
    )

    parser.add_argument(
        "--no-cache",
        dest="no_cache",
        action="store_true",
        default=False,
        help="Disable the caching of external source values."
    )

    parser.add_argument(
        "--refresh-cache",
        dest="refresh_cache",
        action="store_true",
        default=False,
        help="Clears the cache of external source values, then "
             "during validation downloads them again."
    )

    parser.add_argument(
        "--clear-cache",
        dest="clear_cache",
        action="store_true",
        default=False,
        help="Clear the cache of external source values after validation."
    )

    args = parser.parse_args(cmd_args)

    if not is_script:
        args.files = ""
    if not args.version:
        args.version = DEFAULT_VER

    return ValidationOptions(args)


class ValidationOptions(object):
    """Collection of validation options which can be set via command line or
    programmatically in a script.

    It can be initialized either by passing in the result of parse_args() from
    argparse to the cmd_args parameter, or by specifying individual options
    with the other parameters.

    Attributes:
        cmd_args: An instance of ``argparse.Namespace`` containing options
            supplied on the command line.
        version: The version of the STIX specification to validate against.
        verbose: True if informational notes and more verbose error messages
            should be printed to stdout/stderr.
        silent: True if all output to stdout should be silenced.
        files: A list of input files and directories of files to be
            validated.
        recursive: Recursively descend into input directories.
        schema_dir: A user-defined schema directory to validate against.
        disabled: List of "SHOULD" checks that will be skipped.
        enabled: List of "SHOULD" checks that will be performed.
        strict: Specifies that recommended requirements should produce errors
            instead of mere warnings.
        strict_types: Specifies that no custom object types be used, only
            those defined in the STIX specification.
        strict_properties: Specifies that no custom properties be used, only
            those defined in the STIX specification.
        no_cache: Specifies that caching of values from external sources should
            be disabled.
        refresh_cache: Specifies that the cache of values from external sources
            should be cleared before validation, and then re-downloaded during
            validation.
        clear_cache: Specifies that the cache of values from external sources
            should be cleared after validation.

    """
    def __init__(self, cmd_args=None, version=DEFAULT_VER, verbose=False, silent=False,
                 files=None, recursive=False, schema_dir=None,
                 disabled="", enabled="", strict=False,
                 strict_types=False, strict_properties=False, no_cache=False,
                 refresh_cache=False, clear_cache=False):

        if cmd_args is not None:
            self.version = cmd_args.version
            self.verbose = cmd_args.verbose
            self.silent = cmd_args.silent
            self.files = cmd_args.files
            self.recursive = cmd_args.recursive
            self.schema_dir = cmd_args.schema_dir
            self.disabled = cmd_args.disabled
            self.enabled = cmd_args.enabled
            self.strict = cmd_args.strict
            self.strict_types = cmd_args.strict_types
            self.strict_properties = cmd_args.strict_properties
            self.no_cache = cmd_args.no_cache
            self.refresh_cache = cmd_args.refresh_cache
            self.clear_cache = cmd_args.clear_cache
        else:
            # input options
            self.version = version
            self.files = files
            self.recursive = recursive
            self.schema_dir = schema_dir

            # output options
            self.verbose = verbose
            self.silent = silent
            self.strict = strict
            self.strict_types = strict_types
            self.strict_properties = strict_properties
            self.disabled = disabled
            self.enabled = enabled

            # cache options
            self.no_cache = no_cache
            self.refresh_cache = refresh_cache
            self.clear_cache = clear_cache

        # Set the output level (e.g., quiet vs. verbose)
        if self.silent and self.verbose:
            error('Error: Output can either be silent or verbose, but not both.')
        set_level(self.verbose)
        set_silent(self.silent)

        # Convert string of comma-separated checks to a list,
        # and convert check code numbers to names
        if self.disabled:
            self.disabled = self.disabled.split(",")
            self.disabled = [CHECK_CODES[x] if x in CHECK_CODES else x
                             for x in self.disabled]
        if self.enabled:
            self.enabled = self.enabled.split(",")
            self.enabled = [CHECK_CODES[x] if x in CHECK_CODES else x
                            for x in self.enabled]


# Mapping of check code numbers to names
CHECK_CODES = {
    '1': 'format-checks',
    '101': 'custom-prefix',
    '102': 'custom-prefix-lax',
    '111': 'open-vocab-format',
    '121': 'kill-chain-names',
    '141': 'observable-object-keys',
    '142': 'observable-dictionary-keys',
    '149': 'windows-process-priority-format',
    '150': 'hash-length',
    '2': 'approved-values',
    '201': 'marking-definition-type',
    '202': 'relationship-types',
    '203': 'duplicate-ids',
    '210': 'all-vocabs',
    '211': 'attack-motivation',
    '212': 'attack-resource-level',
    '213': 'identity-class',
    '214': 'indicator-label',
    '215': 'industry-sector',
    '216': 'malware-label',
    '218': 'report-label',
    '219': 'threat-actor-label',
    '220': 'threat-actor-role',
    '221': 'threat-actor-sophistication',
    '222': 'tool-label',
    '241': 'hash-algo',
    '242': 'encryption-algo',
    '243': 'windows-pebinary-type',
    '244': 'account-type',
    '270': 'all-external-sources',
    '271': 'mime-type',
    '272': 'protocols',
    '273': 'ipfix',
    '274': 'http-request-headers',
    '275': 'socket-options',
    '276': 'pdf-doc-info',
    '301': 'network-traffic-ports',
    '302': 'extref-hashes',
}


def has_cyber_observable_data(instance):
    """Return True only if the given instance is an observed-data object
    containing STIX Cyber Observable objects.
    """
    if (instance['type'] == 'observed-data' and
            'objects' in instance and
            type(instance['objects']) is dict):
        return True
    return False


def cyber_observable_check(original_function):
    """Decorator for functions that require cyber observable data.
    """
    def new_function(*args, **kwargs):
        if not has_cyber_observable_data(args[0]):
            return
        func = original_function(*args, **kwargs)
        if isinstance(func, Iterable):
            for x in original_function(*args, **kwargs):
                yield x
    new_function.__name__ = original_function.__name__
    return new_function


def init_requests_cache(refresh_cache=False):
    """
    Initializes a cache which the ``requests`` library will consult for
    responses, before making network requests.

    :param refresh_cache: Whether the cache should be cleared out
    """
    # Cache data from external sources; used in some checks
    dirs = AppDirs("stix2-validator", "OASIS")
    # Create cache dir if doesn't exist
    try:
        os.makedirs(dirs.user_cache_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    requests_cache.install_cache(
        cache_name=os.path.join(dirs.user_cache_dir, 'py{}cache'.format(
            sys.version_info[0])),
        expire_after=datetime.timedelta(weeks=1))

    if refresh_cache:
        clear_requests_cache()


def clear_requests_cache():
    """
    Clears all cached responses.
    """
    now = datetime.datetime.utcnow()
    requests_cache.get_cache().remove_old_entries(now)
