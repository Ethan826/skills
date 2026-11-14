module LawsProxyNeedsArbitraryControl.Main where

import Prelude

import Effect (Effect)
import Test.QuickCheck.Arbitrary (class Arbitrary)
import Test.QuickCheck.Laws.Data.Semigroup (checkSemigroup)
import Type.Proxy (Proxy(..))

newtype Name = Name String

derive newtype instance Eq Name
derive newtype instance Semigroup Name
derive newtype instance Arbitrary Name

checkNames :: Effect Unit
checkNames = checkSemigroup (Proxy :: Proxy Name)
