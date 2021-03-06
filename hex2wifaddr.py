#! /usr/bin/env python

# convert a hexadecimal private key to WIF and retrieve the associated address
# cribbed heavily from code at https://bitcointalk.org/index.php?topic=23241.0

import random
import hashlib
import getopt
import sys

class CurveFp( object ):
  def __init__( self, p, a, b ):
    self.__p = p
    self.__a = a
    self.__b = b

  def p( self ):
    return self.__p

  def a( self ):
    return self.__a

  def b( self ):
    return self.__b

  def contains_point( self, x, y ):
    return ( y * y - ( x * x * x + self.__a * x + self.__b ) ) % self.__p == 0

class Point( object ):
  def __init__( self, curve, x, y, order = None ):
    self.__curve = curve
    self.__x = x
    self.__y = y
    self.__order = order
    if self.__curve: assert self.__curve.contains_point( x, y )
    if order: assert self * order == INFINITY
 
  def __add__( self, other ):
    if other == INFINITY: return self
    if self == INFINITY: return other
    assert self.__curve == other.__curve
    if self.__x == other.__x:
      if ( self.__y + other.__y ) % self.__curve.p() == 0:
        return INFINITY
      else:
        return self.double()

    p = self.__curve.p()
    l = ( ( other.__y - self.__y ) * \
          inverse_mod( other.__x - self.__x, p ) ) % p
    x3 = ( l * l - self.__x - other.__x ) % p
    y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
    return Point( self.__curve, x3, y3 )

  def __mul__( self, other ):
    def leftmost_bit( x ):
      assert x > 0
      result = 1L
      while result <= x: result = 2 * result
      return result / 2

    e = other
    if self.__order: e = e % self.__order
    if e == 0: return INFINITY
    if self == INFINITY: return INFINITY
    assert e > 0
    e3 = 3 * e
    negative_self = Point( self.__curve, self.__x, -self.__y, self.__order )
    i = leftmost_bit( e3 ) / 2
    result = self
    while i > 1:
      result = result.double()
      if ( e3 & i ) != 0 and ( e & i ) == 0: result = result + self
      if ( e3 & i ) == 0 and ( e & i ) != 0: result = result + negative_self
      i = i / 2
    return result

  def __rmul__( self, other ):
    return self * other

  def __str__( self ):
    if self == INFINITY: return "infinity"
    return "(%d,%d)" % ( self.__x, self.__y )

  def double( self ):
    if self == INFINITY:
      return INFINITY

    p = self.__curve.p()
    a = self.__curve.a()
    l = ( ( 3 * self.__x * self.__x + a ) * \
          inverse_mod( 2 * self.__y, p ) ) % p
    x3 = ( l * l - 2 * self.__x ) % p
    y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
    return Point( self.__curve, x3, y3 )

  def x( self ):
    return self.__x

  def y( self ):
    return self.__y

  def curve( self ):
    return self.__curve
  
  def order( self ):
    return self.__order
    
INFINITY = Point( None, None, None )

def inverse_mod( a, m ):
  if a < 0 or m <= a: a = a % m
  c, d = a, m
  uc, vc, ud, vd = 1, 0, 0, 1
  while c != 0:
    q, c, d = divmod( d, c ) + ( c, )
    uc, vc, ud, vd = ud - q*uc, vd - q*vc, uc, vc
  assert d == 1
  if ud > 0: return ud
  else: return ud + m

# secp256k1
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
_b = 0x0000000000000000000000000000000000000000000000000000000000000007L
_a = 0x0000000000000000000000000000000000000000000000000000000000000000L
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L

class Signature( object ):
  def __init__( self, r, s ):
    self.r = r
    self.s = s
    
class Public_key( object ):
  def __init__( self, generator, point ):
    self.curve = generator.curve()
    self.generator = generator
    self.point = point
    n = generator.order()
    if not n:
      raise RuntimeError, "Generator point must have order."
    if not n * point == INFINITY:
      raise RuntimeError, "Generator point order is bad."
    if point.x() < 0 or n <= point.x() or point.y() < 0 or n <= point.y():
      raise RuntimeError, "Generator point has x or y out of range."

  def verifies( self, hash, signature ):
    G = self.generator
    n = G.order()
    r = signature.r
    s = signature.s
    if r < 1 or r > n-1: return False
    if s < 1 or s > n-1: return False
    c = inverse_mod( s, n )
    u1 = ( hash * c ) % n
    u2 = ( r * c ) % n
    xy = u1 * G + u2 * self.point
    v = xy.x() % n
    return v == r

class Private_key( object ):
  def __init__( self, public_key, secret_multiplier ):
    self.public_key = public_key
    self.secret_multiplier = secret_multiplier

  def der( self ):
    hex_der_key = '06052b8104000a30740201010420' + \
                  '%064x' % self.secret_multiplier + \
                  'a00706052b8104000aa14403420004' + \
                  '%064x' % self.public_key.point.x() + \
                  '%064x' % self.public_key.point.y()
    return hex_der_key.decode('hex')

  def sign( self, hash, random_k ):
    G = self.public_key.generator
    n = G.order()
    k = random_k % n
    p1 = k * G
    r = p1.x()
    if r == 0: raise RuntimeError, "amazingly unlucky random number r"
    s = ( inverse_mod( k, n ) * \
          ( hash + ( self.secret_multiplier * r ) % n ) ) % n
    if s == 0: raise RuntimeError, "amazingly unlucky random number s"
    return Signature( r, s )

curve_256 = CurveFp( _p, _a, _b )
generator_256 = Point( curve_256, _Gx, _Gy, _r )
g = generator_256

b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def hex_open_key_to_hex_hash160(hex_open_key, compressed):
    h160 = hashlib.new('ripemd160')
    if compressed == False:
      h160.update(hashlib.sha256(('04'+hex_open_key).decode('hex')).hexdigest().decode('hex'))
    else:
      if int(hex_open_key[127:], 16)%2 == 0:
        h160.update(hashlib.sha256(('02'+hex_open_key[:64]).decode('hex')).hexdigest().decode('hex'))
      else:
        h160.update(hashlib.sha256(('03'+hex_open_key[:64]).decode('hex')).hexdigest().decode('hex'))
    return h160.hexdigest()
    
def hex_hash160_to_hex_addr_v0(hex_hash160, version="00"):
    return version+hex_hash160+hashlib.sha256(hashlib.sha256((version+hex_hash160).decode('hex')).hexdigest().decode('hex')).hexdigest()[0:8]
    
def hex_addr_v0_to_hex_hash160(hex_addr_v0):
    return hex_addr_v0[2:-8]

def hex_to_base58(hex_data):
    base58 = ''
    int_data = int(hex_data, 16)
    while int_data >= len(b58chars):
        base58 = b58chars[int_data%len(b58chars)] + base58
        int_data = int_data/len(b58chars)
    base58 = b58chars[int_data%len(b58chars)] + base58
    for i in xrange(len(hex_data)/2):
        if hex_data[i*2:i*2+2] == '00':
            base58 = '1' + base58
        else:
            break
    return base58
    
def base58_to_hex(base58):
    hex_data = ''
    int_data = 0
    for i in xrange(-1, -len(base58)-1, -1):
        int_data += (b58chars.index(base58[i]))*58**(-i-1)
    hex_data = hex(int_data)[2:-1]
    for i in xrange(len(base58)):
        if base58[i] == '1':
            hex_data = '00' + hex_data
        else:
            break
    return hex_data

def usage():
  print "Usage: hex2wifaddr.py [options] hexkey1 hexkey2 ..."
  print ""
  print "Options:"
  print "  -l|--litecoin    decode to Litecoin address"
  print "  -c|--compressed  get compressed address"
  print "  -h|--help        print this help"
  return;

def main():
  version="00"
  prefix="80"
  compressed=False

  try:
    opts, args = getopt.getopt(sys.argv[1:], "hlc", ["help", "litecoin", "compressed"])
  except getopt.GetoptError as err:
    print str(err)
    usage()
    sys.exit(2)
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit(2)
    elif o in ("-l", "--litecoin"):
      version="30"
      prefix="B0"
    elif o in ("-c", "--compressed"):
      compressed=True
    else:
      assert False, "unhandled option"

  for a in args:
    ### set privkey
    secret=int(a,16)

    ### echo hexkey
    print "hexkey ", ("00"+hex(secret)[:-1][2:])[-64:]

    ### decode privkey to WIF
    secret_txt=prefix+("0000000000000000000000000000000000000000000000000000000000000000"+hex(secret)[2:][:-1])[-64:]
    if compressed == True:
      secret_txt=secret_txt+"01"
    print "privkey", hex_to_base58(secret_txt+hashlib.sha256(hashlib.sha256(secret_txt.decode("hex")).hexdigest().decode("hex")).hexdigest()[:8])
  
    ### retrieve pubkey
    pubkey = Public_key( g, g * secret )
    hex_open_key=("00"+hex(pubkey.point.x())[:-1][2:])[-64:]+("00"+hex(pubkey.point.y())[:-1][2:])[-64:]

    ### print pubkey
    print "address", hex_to_base58(hex_hash160_to_hex_addr_v0(hex_open_key_to_hex_hash160(hex_open_key, compressed), version))

if __name__ == "__main__":
  sys.exit(main())
  