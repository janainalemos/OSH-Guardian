import string
import random
import jwt
from decouple import config


JWT_SECRET = config("OSH40_KEY_JWT")
JWT_ALGORITHM = config("JWT_ALGORITHM")


class GenerateToken(object):
		def __init__(self, _passphrase="", _length_key=64):
				self.passphrase = _passphrase
				self.len_key = _length_key
		
		"""Generate one key for JWT SECRET"""
		def generate_key(self):
				characters = string.ascii_letters + "0123456789" + "!#$%&*+-.<=>?@^_|~/"
				char_set = self.passphrase + ''.join(ch if ch not in self.passphrase else '' for ch in characters)
				u_rand = random.SystemRandom()
				return ''.join([u_rand.choice(char_set) for _ in range(self.len_key)])
				
		"""Genereate Bearer Token is using JWT_SECRET"""
		def jwt_token(self, payload):
				return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


if __name__ == "__main__":
		gen_keys = GenerateToken("OSH40_RESERVED_JCSL", 64)
		"""Generate one key for JWT SECRET"""
		JWT_SECRET = gen_keys.generate_key()
		print("JWT SECRET: {}".format(JWT_SECRET))
		

		"""Genereate Bearer Token is using JWT_SECRET"""
		payload = {"university": "Beira Interior - Portugal",
							 "owner": "Janaina Lemos", "email": "janaina.lemos@gmail.com",
							 "service": "System for Individual Environmental Risk", "expires": 1741541935}
		print("BEARER TOKEN: {}".format(gen_keys.jwt_token(payload)))
