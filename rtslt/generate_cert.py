from OpenSSL import crypto

# Generate a key
key = crypto.PKey()
key.generate_key(crypto.TYPE_RSA, 2048)

# Create a certificate
cert = crypto.X509()
cert.get_subject().CN = '192.168.100.201'
cert.set_serial_number(1000)
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(365*24*60*60)
cert.set_issuer(cert.get_subject())
cert.set_pubkey(key)
cert.sign(key, 'sha256')

# Write to files
with open('cert.pem', 'wb') as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
with open('key.pem', 'wb') as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

print('✓ SSL cert generated: cert.pem, key.pem')
