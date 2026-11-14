module QuickcheckTypes.Main where

import Prelude

import Test.QuickCheck (Result, (===), (<?>))

check :: Int -> Int -> Result
check x y = (x === y) <?> "equal"
