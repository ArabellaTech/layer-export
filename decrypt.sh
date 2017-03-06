# path to the file you just downloaded
export ENCRYPTED_TARBALL=export/export.enc.tar.gz
# path for the unencrypted tar
export OUTPUT_TAR=export/export.tar.gz
# path to the private key
export PRIVATE_KEY_PATH=key.private
# the encrypted_aes_key from the export json
export ENCRYPTED_AES_KEY=FROM JSON
# the aes_iv key from the export json
export AES_IV=FROM JSON

a=$(echo $ENCRYPTED_AES_KEY | base64 --decode | /usr/local/opt/openssl/bin/openssl rsautl -decrypt -inkey $PRIVATE_KEY_PATH | hexdump -ve '1/1 "%.2x"')
b=$(echo $AES_IV | base64 --decode | hexdump -ve '1/1 "%.2x"')
/usr/local/opt/openssl/bin/openssl enc -in $ENCRYPTED_TARBALL -out $OUTPUT_TAR -d -aes-256-cbc -K $a -iv $b
tar -xzf export/export.tar.gz -C export
