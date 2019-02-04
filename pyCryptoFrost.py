import hashlib
import hmac
import Crypto
import Crypto.Cipher.AES
import Crypto.Util.Padding
import secrets
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from binascii import hexlify
from binascii import unhexlify
from pyDes import *
import pickle


def generate_master_key(algorithm_choice, password=b'>>$$MasterPassword9000$$<<'):
    """Creation of master key using PBKDF#2 hashed with either SHA256 or SHA512.
    Salt is a randomly generated 16 characters in hex format.

    Args:
        algorithm_choice (string):
            An integer who's value determines which algorithm is
            going to be used.
        password (byte):
            The password used to generate the master encryption
            keys.

    Return:
        key (byte):
            The generated master key to be used for encryption and
            hashing derivation.
    """
    key = "Invalid algorithm"
    try:
        salt = str.encode(secrets.token_hex(8))
        if algorithm_choice == 'sha256':
            key = hashlib.pbkdf2_hmac('sha256', password, salt, 100000)
        elif algorithm_choice == 'sha512':
            key = hashlib.pbkdf2_hmac('sha512', password, salt, 100000)
        else:
            raise TypeError
    except TypeError:
        print(str(TypeError) + " Expected \'sha256\' or \'sha512\'")
    return key


def generate_encryption_key(hash_choice, master_key=""):
    """Derivation of encryption key using PBKDF#2.
    Hashed and salted.

    Args:
        hash_choice (string):
            Length of the key needed to be generated.
            accepts multiples of 16, expecting values
            of either 16 or 32.

        master_key (byte):
            The master key used to generate the derived
            encryption key.

    Return:
        key (byte):
            The encryption key for each algorithm.
    """
    salt = str.encode(secrets.token_hex(8))
    key = "Invalid key Length"
    try:
        if hash_choice == 'sha256':
            key = hashlib.pbkdf2_hmac('sha256', master_key, salt, 1, 16)
        elif hash_choice == 'sha512':
            key = hashlib.pbkdf2_hmac('sha512', master_key, salt, 1, 32)
        else:
            raise TypeError
    except TypeError:
        print(str(TypeError) + " Invalid key length")
    return key


def generate_hmac(key, data=b'123'):
    """Generate of the HMAC.

    Args:
        data (byte):
            The cipher text to be hashed. Default data
            to prevent errors.
        key (byte):
            The derived key from the master encryption key.

    Return:
        HMAC (byte):
            The HMAC of the cipher text.
    """
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def generate_hmac_key(key_length=16, master_key=""):
    """Derivation of HMAC key using PBKDF#2.
    Hashed and salted.

    Args:
        key_length (integer):
            Length of the key needed to be generated.
            accepts multiples of 16, expecting values
            of either 16 or 32.

        master_key (byte):
            The master key used to generate the derived
            encryption key.

    Return:
        key (byte):
            The HMAC key.
    """
    salt = str.encode(secrets.token_hex(8))
    key = "Invalid key Length"
    try:
        if key_length == 16:
            key = hashlib.pbkdf2_hmac('sha256', master_key, salt, 1, key_length)
        elif key_length == 32:
            key = hashlib.pbkdf2_hmac('sha512', master_key, salt, 1, key_length)
        else:
            raise TypeError
    except TypeError:
        print(str(TypeError) + " Invalid key length")
    return key


def generate_iv(block_size=56):
    """Generated random bytes of various block size to
    be used as an IV.

    Args:
        block_size (integer):
            The size of the desired block.

    Return:
        random_bytes (byte):
            "block_size" amount of randomly generated bytes
            to be used as an injection vector.
    """
    return get_random_bytes(block_size)


def encrypt_aes(plaintext,
                encryption_key=generate_master_key
                ("sha256", b'>>$$MasterPassword9000$$<<'),
                algorithm="aes128"):
    """Implementation of AES Encryption. Encrypts either AES128
    or AES256. By default, will generate a key and use aes128.
    PKCS7 padding.

    Args:
        plaintext (byte):
            The plain text to be encrypted.
        encryption_key (byte):
            The key used to encrypt the data.
        algorithm (string):


    Return: None.
    """
    # Initial set up of encryption cipher.
    local_hash = ""
    try:
        if algorithm == "aes128":
            key_size = 16
            local_hash = "sha256"
        elif algorithm == "aes256":
            key_size = 32
            local_hash = "sha512"
        else:
            raise TypeError
    except TypeError:
        print(str(TypeError) + " Invalid key length")
    block_size = 16
    encryption_key = generate_encryption_key(local_hash, encryption_key)
    iv = generate_iv(block_size)
    plaintext = Crypto.Util.Padding.pad(plaintext, block_size, style='pkcs7')
    cipher = AES.new(encryption_key, AES.MODE_CBC, iv)

    # Encryption of data.
    ciphertext = cipher.encrypt(plaintext)

    # Write encrypted data to file.
    try:
        with open("encrypted.txt", "wb") as f:
            f.write(hexlify(ciphertext))
    except FileNotFoundError:
        print("Can not find file!")

    # Generate and serialize cipher metadata.
    local_keys = dict(int_list=[],
                      my_keys=encryption_key,
                      my_iv=iv,
                      my_block_size=block_size,
                      my_algorithm=algorithm,
                      my_key_size=key_size)

    with open('keys.pkl', 'wb') as f:
        pickle.dump(local_keys, f)
    return ciphertext


def encrypt_3des(plaintext):
    """Implementation of 3DES. Key size of 126 bits with
    a block size of 56 bits. PKCS7 padding. Encrypts using 3DES
    to a file. Additionally, an HMAC is generated to verify
    data integrity.

    Args:
        plaintext (byte):
            The plain text to be encrypted.

    Return: None.
    """
    # Initial set up
    algorithm = "3des"
    key_size = 16
    block_size = 16
    iv = generate_iv(8)
    encryption_key = generate_encryption_key('sha256', generate_master_key
                                             ("sha256", b'>>$$MasterPassword9000$$<<'))
    plaintext = Crypto.Util.Padding.pad(plaintext, block_size, style='pkcs7')
    cipher = triple_des(encryption_key, CBC, iv, pad=None)

    # Encryption of data and generation of HMAC.
    ciphertext = cipher.encrypt(plaintext)

    # Write encrypted data to file.
    with open("encrypted.txt", "wb") as f:
        f.write(hexlify(ciphertext))

    # Generate and serialize cipher metadata.
    local_keys = dict(int_list=[],
                      my_keys=encryption_key,
                      my_iv=iv,
                      my_block_size=block_size,
                      my_algorithm=algorithm,
                      my_key_size=key_size)

    with open('keys.pkl', 'wb') as f:
        pickle.dump(local_keys, f)
    return ciphertext


def decrypt(ciphertext=""):
    """Decrypts from input or a text file cipher text that has been
    generated using algorithms 3DES, AES128, or AES256. Reads metadata from
    keys.pkl. Will detect algorithm used and send plaintext to
    "plaintext.txt".

    Args: None

    Return: None
    """
    # Initialize variables
    algorithm = "Unknown Algorithm"
    encryption_key = ""
    iv = ""
    block_size = ""

    # Unpack the data and ensure format is correct.
    try:
        with open('keys.pkl', 'rb') as f:
            enc_meta = pickle.load(f)
        encryption_key = enc_meta['my_keys']
        iv = enc_meta['my_iv']
        block_size = enc_meta['my_block_size']
        algorithm = enc_meta['my_algorithm']
    except (FileNotFoundError, RuntimeError):
        print("File format is incorrect. Encrypt the data using this program.")

    # Ensure it is a registered algorithm.
    if algorithm != "aes128" and algorithm != "aes256" and algorithm != "3des":
        print("Error trying to decrypt " + algorithm)
        sys.exit(0)

    # Opening file and reading ciphertext.
    if ciphertext == "":
        try:
            with open("encrypted.txt", "br") as f:
                ciphertext = f.read()
        except FileNotFoundError:
            print("Can not find file!")

    # Choose decryption algorithm.
    if algorithm == "aes128" or algorithm == "aes256":
        decipher = AES.new(encryption_key, AES.MODE_CBC, iv)
    else:
        decipher = triple_des(encryption_key, CBC, iv, pad=None)

    # Decrypt and decode.
    try:
        plaintext = decipher.decrypt(unhexlify(ciphertext))
        plaintext = Crypto.Util.Padding.unpad(plaintext, block_size, style='pkcs7')
        return plaintext.decode()
    except:
        print("Incorrect String Format")
