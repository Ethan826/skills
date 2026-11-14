module SemiringFourMembers.Main where

import Prelude

newtype Price = Price Int

instance Semiring Price where
  add (Price a) (Price b) = Price (a + b)
  zero = Price 0
