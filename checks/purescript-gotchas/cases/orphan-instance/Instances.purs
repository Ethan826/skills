module OrphanInstance.Instances where

import Prelude

import OrphanInstance.Types (Price(..))

instance Eq Price where
  eq (Price a) (Price b) = a == b
