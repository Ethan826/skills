module NewtypeDeriveInnerControl.Main where

import Prelude

newtype Cents = Cents Int

derive newtype instance Eq Cents

newtype Price = Price Cents

derive newtype instance Eq Price
