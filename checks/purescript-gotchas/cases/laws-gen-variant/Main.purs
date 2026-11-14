module LawsGenVariant.Main where

import Prelude

import Effect (Effect)
import Test.QuickCheck.Gen (Gen)
import Test.QuickCheck.Laws.Data.Semigroup (checkSemigroupGen)

checkStrings :: Gen String -> Effect Unit
checkStrings = checkSemigroupGen
