#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Secure config related stuff"""
import subprocess
from os.path import join, isfile
import secrets
import string
from typing import List

from .global_config import get_ssl_dir, RunConfig, get_run_configs_dir
from .utils import create_dir_if_not_exist

SSL_PROPERTIES_FILE = 'ssl.properties'
PROJECTOR_JKS_NAME = 'projector'
HTTP_SERVER = 'http_server'

DEF_TOKEN_LEN = 20
CA_NAME = 'ca'
CA_PASSWORD = '85TibAyPS3NZX3'


def generate_token() -> str:
    """Generates token to access server's secrets"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(DEF_TOKEN_LEN))


def get_http_cert_file(config_name: str) -> str:
    """Returns full path to http server certificate file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.crt')


def get_http_key_file(config_name: str) -> str:
    """Returns full path to http server key file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.key')


def get_http_csr_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.csr')


def get_http_jks_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.jks')


def get_ssl_properties_file(config_name: str) -> str:
    """Returns full path to ssl.properties file"""
    return join(get_run_configs_dir(), config_name, SSL_PROPERTIES_FILE)


def get_projector_jks_file(config_name: str) -> str:
    """Returns full path to projector server key file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.jks')


def get_projector_pkcs12_file(config_name: str) -> str:
    """Returns full path to projector server key file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.p12')


def get_projector_csr_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.csr')


def get_projector_cert_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.crt')


def get_ca_cert_file() -> str:
    """Returns full path to ca certificate file"""
    return join(get_ssl_dir(), f'{CA_NAME}.crt')


def get_ca_key_file() -> str:
    """Returns full path to ca key file"""
    return join(get_ssl_dir(), f'{CA_NAME}.key')


def get_ca_jks_file() -> str:
    """Returns full path to ca keystore"""
    return join(get_ssl_dir(), f'{CA_NAME}.jks')


def get_ca_pkcs12_file() -> str:
    """Returns full path to ca keystore"""
    return join(get_ssl_dir(), f'{CA_NAME}.p12')


def is_ca_exist() -> bool:
    """Checks if ca already generated"""
    ret = isfile(get_ca_jks_file())
    ret = ret and isfile(get_ca_cert_file())
    return ret


DIST_CA_NAME = 'CN=PROJECTOR-CA, OU=Development, O=Projector, L=SPB, S=SPB, C=RU'


def get_generate_ca_command():
    """Returns list of args for generate ca"""
    return ['-genkeypair', '-alias', CA_NAME,
            '-dname', DIST_CA_NAME, '-keystore', get_ca_jks_file(),
            '-keypass', CA_PASSWORD, '-storepass', CA_PASSWORD,
            '-keyalg', 'RSA', '-keysize', '4096',
            '-ext', 'KeyUsage:critical=keyCertSign',
            '-ext', 'BasicConstraints:critical=ca:true',
            '-validity', '9999'
            ]


def get_export_ca_command() -> List[str]:
    """Returns list of args for export ca.crt"""
    return ['-export', '-alias', CA_NAME, '-file', get_ca_cert_file(), '-keypass', CA_PASSWORD,
            '-storepass', CA_PASSWORD, '-keystore', get_ca_jks_file(), '-rfc']


def get_convert_ca_to_pkcs12() -> List[str]:
    return [
        '-importkeystore', '-srckeystore', get_ca_jks_file(),
        '-srcstoretype', 'JKS',
        '-srcstorepass', CA_PASSWORD,
        '-destkeystore', get_ca_pkcs12_file(),
        '-deststoretype', 'pkcs12',
        '-deststorepass', CA_PASSWORD
    ]


# # extract ca.key from pkcs12
# openssl
# pkcs12 - in ca.p12 - nodes - nocerts - out
# ca.key - passin
# env: PW


def get_extract_ca_key_args():
    return [
        'pkcs12',
        '-in', get_ca_pkcs12_file(),
        '-nodes',
        '-nocerts',
        '-out', get_ca_key_file(),
        '-passin', f'pass:{CA_PASSWORD}'
    ]


def generate_ca(keytool_path: str) -> None:
    """Creates CA"""
    create_dir_if_not_exist(get_ssl_dir())

    cmd = [keytool_path] + get_generate_ca_command()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

    cmd = [keytool_path] + get_export_ca_command()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

    cmd = [keytool_path] + get_convert_ca_to_pkcs12()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

    cmd = ['openssl'] + get_extract_ca_key_args()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


DIST_PROJECTOR_NAME = 'CN=Idea, OU=Development, O=Idea, L=SPB, S=SPB, C=RU'


def get_projector_gen_jks_args(run_config: RunConfig) -> List[str]:
    """keytool args for projector jks generation"""
    return [
        '-genkeypair', '-alias', PROJECTOR_JKS_NAME, '-dname', DIST_PROJECTOR_NAME,
        '-keystore', get_projector_jks_file(run_config.name),
        '-keypass', run_config.token, '-storepass', run_config.token,
        '-keyalg', 'RSA', '-keysize', '4096', '-validity', '4500'
    ]


def get_projector_cert_sign_request_args(run_config: RunConfig) -> List[str]:
    return [
        '-certreq', '-alias', PROJECTOR_JKS_NAME, '-keypass', run_config.token, '-storepass', run_config.token,
        '-keystore', get_projector_jks_file(run_config.name), '-file', get_projector_csr_file(run_config.name)
    ]


# TODO: Fix is_ip_address function
def is_ip_address(address: str):
    """Detects if given string is IP address"""
    return address != 'localhost'


def get_san_value(http_address: str) -> str:
    if is_ip_address(http_address):
        return 'IP:' + http_address

    return 'DNS:' + http_address


def get_projector_cert_sign_args(run_config: RunConfig) -> List[str]:
    return [
        '-gencert',
        '-alias', CA_NAME,
        '-keypass', run_config.token,
        '-storepass', CA_PASSWORD,
        '-keystore', get_ca_jks_file(),
        '-infile', get_projector_csr_file(run_config.name),
        '-outfile', get_projector_cert_file(run_config.name),
        '-ext', 'KeyUsage:critical=digitalSignature,keyEncipherment',
        '-ext', 'EKU=serverAuth',
        '-ext', 'SAN=DNS:localhost',
        '-rfc'
    ]


def get_projector_import_ca_args(run_config: RunConfig) -> List[str]:
    return [
        '-import', '-alias', CA_NAME,
        '-file', get_ca_cert_file(),
        '-keystore', get_projector_jks_file(run_config.name),
        '-storetype', 'JKS',
        '-storepass', run_config.token,
        '-noprompt'
    ]


def get_projector_import_cert_args(run_config: RunConfig) -> List[str]:
    return [
        '-import', '-alias', PROJECTOR_JKS_NAME,
        '-file', get_projector_cert_file(run_config.name),
        '-keystore', get_projector_jks_file(run_config.name),
        '-storetype', 'JKS',
        '-storepass', run_config.token
    ]


def generate_projector_jks(run_config: RunConfig) -> None:
    """Generates projector jks for given config"""

    keytool_path = get_jbr_keytool(run_config.path_to_app)

    cmd = [keytool_path] + get_projector_gen_jks_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_cert_sign_request_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_cert_sign_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_import_ca_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_import_cert_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


DIST_HTTP_NAME = 'CN=Http, OU=Development, O=Idea, L=SPB, S=SPB, C=RU'


def get_http_gen_args(run_config: RunConfig) -> List[str]:
    """keytool args for http keypair generation"""
    return [
        '-genkeypair', '-alias', HTTP_SERVER, '-dname', DIST_HTTP_NAME,
        '-keystore', get_http_jks_file(run_config.name),
        '-keypass', run_config.token, '-storepass', run_config.token,
        '-keyalg', 'RSA', '-keysize', '4096', '-validity', '4500'
    ]


def get_http_cert_sign_request_args(run_config: RunConfig) -> List[str]:
    return [
        '-certreq', '-alias', HTTP_SERVER, '-keypass', run_config.token, '-storepass', run_config.token,
        '-keystore', get_http_jks_file(run_config.name), '-file', get_http_csr_file(run_config.name)
    ]


def get_http_cert_sign_args(run_config: RunConfig) -> List[str]:
    return [
        '-gencert',
        '-alias', CA_NAME,
        '-keypass', run_config.token,
        '-storepass', CA_PASSWORD,
        '-keystore', get_ca_jks_file(),
        '-infile', get_http_csr_file(run_config.name),
        '-outfile', get_http_cert_file(run_config.name),
        '-ext', 'KeyUsage:critical=digitalSignature,keyEncipherment',
        '-ext', 'EKU=serverAuth',
        '-ext', f'SAN={get_san_value(run_config.http_address)}',
        '-rfc'
    ]


def get_convert_to_pkcs12_args(run_config: RunConfig) -> List[str]:
    return [
        '-importkeystore', '-srckeystore', get_projector_jks_file(run_config.name),
        '-srcstoretype', 'JKS',
        '-srcstorepass', run_config.token,
        '-destkeystore', get_projector_pkcs12_file(run_config.name),
        '-deststoretype', 'pkcs12',
        '-deststorepass', run_config.token
    ]


def get_extract_http_key_args(run_config: RunConfig):
    return [
        'pkcs12',
        '-in', get_projector_pkcs12_file(run_config.name),
        '-nodes',
        '-nocerts',
        '-out', get_http_key_file(run_config.name),
        '-passin', f'pass:{run_config.token}'
    ]


#
# def generate_http_cert(run_config: RunConfig) -> None:
#     """Generates http certificate and key files"""
#     keytool_path = get_jbr_keytool(run_config.path_to_app)
#
#     # generate keypair
#     cmd = [keytool_path] + get_http_gen_args(run_config)
#     subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
#
#     # create request for signing
#     cmd = [keytool_path] + get_http_cert_sign_request_args(run_config)
#     subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
#
#     # create cert signed with CA
#     cmd = [keytool_path] + get_http_cert_sign_args(run_config)
#     subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
#
#     # convert projector jks to pkcs12
#     cmd = [keytool_path] + get_convert_to_pkcs12_args(run_config)
#     subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
#
#     # export http key with openssl
#     cmd = ['openssl'] + get_extract_http_key_args(run_config)
#     # subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
#     subprocess.check_call(cmd)

# http server self signed cert
# generate key
# openssl genrsa -out http_server.key 2048
# genearte cert request
# openssl req -new -key http_server.key -out http_server.csr

# sign with ca.key
# openssl x509 -req -in http_server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out http_server.crt -days 5000

def get_openssl_generate_key_args(run_config: RunConfig) -> List[str]:
    return ['genrsa',
            '-out', get_http_key_file(run_config.name),
            '2048'
            ]


def get_openssl_generate_cert_req(run_config: RunConfig) -> List[str]:
    return ['req', '-new',
            '-key', get_http_key_file(run_config.name),
            '-out', get_http_csr_file(run_config.name)
            ]


def get_openssl_sign_args(run_config: RunConfig) -> List[str]:
    return [
        'x509', '-req',
        '-in', get_http_csr_file(run_config.name),
        '-CA', get_ca_cert_file(),
        '-CAkey', get_ca_key_file(),
        '-CAcreateserial',
        '-out', get_http_cert_file(run_config.name),
        '-days', '4500'
    ]


def generate_http_cert(run_config: RunConfig) -> None:
    """Generates http certificate and key files"""
    cmd = ['openssl'] + get_openssl_generate_key_args(run_config)
    subprocess.check_call(cmd)

    cmd = ['openssl'] + get_openssl_generate_cert_req(run_config)
    subprocess.check_call(cmd)

    cmd = ['openssl'] + get_openssl_sign_args(run_config)
    subprocess.check_call(cmd)


def generate_ssl_properties_file(config_name: str, token: str) -> None:
    """Generates ssl.properties file for given config"""
    with open(get_ssl_properties_file(config_name), "w") as file:
        print('STORE_TYPE=JKS', file=file)
        print(f'FILE_PATH={get_projector_jks_file(config_name)}', file=file)
        print(f'STORE_PASSWORD={token}', file=file)
        print(f'KEY_PASSWORD={token}', file=file)


def get_jbr_keytool(path_to_app: str) -> str:
    """Returns full path to keytool for given config"""
    return join(path_to_app, 'jbr', 'bin', 'keytool')


def generate_server_secrets(run_config: RunConfig) -> None:
    """Generate all secret connection related stuff for given config"""
    keytool_path = get_jbr_keytool(run_config.path_to_app)
    if not is_ca_exist():
        generate_ca(keytool_path)

    generate_projector_jks(run_config)
    generate_ssl_properties_file(run_config.name, run_config.token)
    generate_http_cert(run_config)
