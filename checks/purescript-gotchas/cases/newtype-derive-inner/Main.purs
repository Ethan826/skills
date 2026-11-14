module NewtypeDeriveInner.Main where

import Prelude

newtype Cents = Cents Int

newtype Price = Price Cents

derive newtype instance Eq Price
