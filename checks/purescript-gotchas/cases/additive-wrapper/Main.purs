module AdditiveWrapper.Main where

import Prelude

import Data.Monoid.Additive (Additive(..))

newtype Kilograms = Kilograms (Additive Number)

derive newtype instance Semigroup Kilograms
derive newtype instance Monoid Kilograms

total :: Kilograms
total = Kilograms (Additive 1.5) <> Kilograms (Additive 2.0) <> mempty
