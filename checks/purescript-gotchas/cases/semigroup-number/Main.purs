module SemigroupNumber.Main where

import Prelude

newtype Kilograms = Kilograms Number

derive newtype instance Semigroup Kilograms
