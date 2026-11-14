module SemigroupInt.Main where

import Prelude

newtype Count = Count Int

derive newtype instance Semigroup Count
