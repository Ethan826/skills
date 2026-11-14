module OrphanInstanceControl.Types (Price(..)) where

import Prelude

newtype Price = Price Int

instance Eq Price where
  eq (Price a) (Price b) = a == b
